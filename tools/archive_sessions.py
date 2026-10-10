# -*- coding: utf-8 -*-
"""AI 会话归档（本地实现，post-commit 钩子用）。

背景与动机
----------
课程要求用 agent-session-commit（AgentLedger）把 AI 会话归档进提交。
本机 WorkBuddy 5.6.2 写出的会话文件，首条记录 type 是 "session-meta"
（连字符），而 AgentLedger v0.1.5 的适配器只认 "session_meta"（下划线），
导致首条记录被判 unverified、整个会话被跳过（Project session files found: 0）。

本脚本不修改 AgentLedger 的任何代码，而是**另写一份归档实现**，
直接读取 WorkBuddy 的会话目录，把「工作目录等于本仓库根目录」的会话
增量归档进 .agent-sessions/bundles/，让归档记录真实可查。

设计原则
--------
1. 只读源：不改动 WorkBuddy 的会话文件（只读 + 复制）。
2. 严格归属：只归档 cwd 恰等于本仓库根的会话（与 AgentLedger 口径一致）。
3. 增量：用 .agent-sessions/state.json 记录已归档的会话指纹，
   每个会话只在内容变化时重新归档，避免重复写入与无谓的提交污染。
4. 只归档不提交：归档产物写入工作区，由使用者自行决定是否 commit
   （与 AgentLedger 的 amend 行为不同，这里更保守、更可审查）。
5. 永不阻断提交流程：任何异常都吞掉并只打印提示，返回 0。

用法
----
    python tools/archive_sessions.py            # 归档（post-commit 钩子调用）
    python tools/archive_sessions.py --status   # 只看状态，不写文件
    python tools/archive_sessions.py --verbose  # 打印每个被检查的会话

环境变量
--------
    WORKBUDDY_CONFIG_DIR   覆盖 WorkBuddy 配置根目录（默认 ~/.workbuddy）
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# WorkBuddy 会话首条记录的 type 字段取值。本机 5.6.2 观测到 "session-meta"；
# 同时兼容旧版下划线写法，避免以后版本回退时失效。
ACCEPTED_FIRST_TYPES = {"session-meta", "session_meta", "user", "assistant", "progress"}

# 单个会话文件上限，防止读到异常巨大的文件。
MAX_SESSION_BYTES = 50 * 1024 * 1024

BUNDLE_DIRNAME = "bundles"
STATE_FILENAME = "state.json"


def repo_root() -> Path:
    """返回本仓库根目录（本文件位于 <root>/tools/）。"""
    return Path(__file__).resolve().parent.parent


def workbuddy_projects_dir() -> Path:
    """定位 WorkBuddy 的 projects 目录（会话 .jsonl 所在处）。"""
    override = os.environ.get("WORKBUDDY_CONFIG_DIR")
    if override:
        return Path(override).expanduser() / "projects"
    home = Path.home()
    candidates = [home / ".workbuddy-ai" / "projects",
                  home / ".workbuddy" / "projects"]
    return next((p for p in candidates if p.is_dir()), candidates[1])


def normalize(path_str: object) -> str | None:
    """把会话里的 cwd 规范化为可比较的绝对路径字符串。"""
    if not isinstance(path_str, str) or not path_str:
        return None
    p = Path(os.path.expanduser(path_str))
    if not p.is_absolute():
        return None
    try:
        return str(p.resolve(strict=False))
    except (OSError, RuntimeError, ValueError):
        return None


def first_record(path: Path) -> dict | None:
    """读取 .jsonl 首条记录；失败返回 None。"""
    try:
        with path.open("rb") as stream:
            line = stream.readline()
    except OSError:
        return None
    try:
        value = json.loads(line)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return value if isinstance(value, dict) else None


def collect_cwds(path: Path, max_lines: int = 300) -> set[str]:
    """收集会话文件前 max_lines 行里出现的所有 cwd（规范化后）。"""
    found: set[str] = set()
    try:
        with path.open("rb") as stream:
            for index, line in enumerate(stream):
                if index >= max_lines:
                    break
                try:
                    record = json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    continue
                if not isinstance(record, dict):
                    continue
                normal = normalize(record.get("cwd"))
                if normal:
                    found.add(normal)
    except OSError:
        return found
    return found


def belongs_to_repo(cwd: str | None, root: Path) -> bool:
    """严格判断：cwd 必须恰等于仓库根（与 AgentLedger 口径一致）。"""
    if cwd is None:
        return False
    return cwd == str(root.resolve(strict=False))


def session_digest(path: Path) -> str | None:
    """会话内容的 sha256（用作增量归档的指纹）。"""
    try:
        if path.stat().st_size > MAX_SESSION_BYTES:
            return None
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def find_owned_sessions(projects: Path, root: Path) -> list[tuple[Path, str]]:
    """返回属于本仓库的会话 [(路径, 指纹), ...]，按路径排序。"""
    owned: list[tuple[Path, str]] = []
    if not projects.is_dir():
        return owned
    for project_dir in sorted(projects.iterdir()):
        if not project_dir.is_dir() or project_dir.is_symlink():
            continue
        for session in sorted(project_dir.glob("*.jsonl")):
            if not session.is_file() or session.is_symlink():
                continue
            head = first_record(session)
            if head is None:
                continue
            if head.get("type") not in ACCEPTED_FIRST_TYPES:
                continue
            cwds = collect_cwds(session)
            if not any(belongs_to_repo(cwd, root) for cwd in cwds):
                continue
            digest = session_digest(session)
            if digest is None:
                continue
            owned.append((session, digest))
    return owned


def load_state(state_file: Path) -> dict:
    try:
        with state_file.open("r", encoding="utf-8") as stream:
            value = json.load(stream)
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_state(state_file: Path, state: dict) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with state_file.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(state, stream, ensure_ascii=False, indent=2, sort_keys=True)
        stream.write("\n")


def archive(verbose: bool = False, status_only: bool = False) -> int:
    root = repo_root()
    bundle_dir = root / ".agent-sessions" / BUNDLE_DIRNAME
    state_file = root / ".agent-sessions" / STATE_FILENAME
    projects = workbuddy_projects_dir()

    print("AI 会话归档（本地实现）")
    print("  仓库   : ", root)
    print("  会话源 : ", projects)

    if not projects.is_dir():
        print("  [跳过] 会话源目录不存在。")
        return 0

    owned = find_owned_sessions(projects, root)
    print("  归属本仓库的会话：{} 个".format(len(owned)))

    state = load_state(state_file)
    known: dict = state.get("sessions", {}) if isinstance(state.get("sessions"), dict) else {}

    new_count = 0
    for session, digest in owned:
        key = session.stem
        previous = known.get(key)
        previous_digest = previous.get("sha256") if isinstance(previous, dict) else None
        unchanged = previous_digest == digest
        if verbose or not unchanged:
            print("    - {}  {}".format(session.name[:20],
                                       "已归档(未变)" if unchanged else "新增/已更新"))
        if unchanged or status_only:
            continue

        target = bundle_dir / "{}.jsonl".format(key)
        if not status_only:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(session, target)

        size = session.stat().st_size
        known[key] = {
            "sha256": digest,
            "size": size,
            "source": str(session),
            "archived_at": datetime.now(timezone.utc).isoformat(),
            "archived_path": str(target.relative_to(root)).replace("\\", "/"),
        }
        new_count += 1

    if not status_only:
        state = {
            "tool": "tools/archive_sessions.py",
            "agent": "workbuddy",
            "note": ("本地归档实现：适配 WorkBuddy 5.6.2 的 session-meta 首记录格式，"
                     "绕过 AgentLedger v0.1.5 的格式不兼容。"),
            "sessions": known,
        }
        save_state(state_file, state)

    print("  本次归档/更新：{} 个".format(new_count))
    if new_count and not status_only:
        print("  归档目录：{}".format(bundle_dir))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI 会话归档（本地实现）")
    parser.add_argument("--status", action="store_true", help="只查看状态，不写入")
    parser.add_argument("--verbose", action="store_true", help="打印每个会话的检查结果")
    args = parser.parse_args(argv)
    try:
        return archive(verbose=args.verbose, status_only=args.status)
    except Exception as exc:  # 永不阻断 git 提交流程
        print("  [警告] 归档过程出错，已忽略：{}".format(exc), file=sys.stderr)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
