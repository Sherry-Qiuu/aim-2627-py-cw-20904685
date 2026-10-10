# AIM 2627 Python Coursework —— 哨兵 Sentry 控制模块

> **全部题目、规范、评分、提交见 [题面.pdf](题面.pdf)。** 本 README 只讲怎么把环境跑起来；没在这里出现的规格细节，一律以题面为准。

## 1. 环境要求

- Python 3.8+，仅标准库（不允许第三方运行时依赖）；
- 开发工具只需 `pytest`（测试）与 `autopep8`（风格，CI 会检查）；
- VS Code 打开仓库会推荐安装 `ms-python.autopep8` 插件（`.vscode/extensions.json`），保存即格式化即可过风格检查。

## 2. 快速开始

```bash
# 1. 用 GitHub 的 Use this template 创建你自己的仓库，然后 clone
git clone https://github.com/<你的用户名>/<你的仓库>.git
cd <你的仓库>   # 直接在 main 分支上开发

# 创建虚拟环境

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. 装依赖
python -m pip install pytest autopep8

# 3. 启用 AI 会话归档钩子（课程要求，见下方第 3 节）
python -m pip install 'agent-session-commit[pre-commit]==0.1.3' -i https://pypi.org/simple
agent-session-commit install --pre-commit   # 交互选择你的 AI 助手与会话目录

# 4. 跑测试（刚到手：全部 skip，CI 是绿的）
python -m pytest

# 5. 看演示
python main.py

# 6. 打开 题面.pdf 读题，开始实现 src/main/__init__.py 里的 TODO
```

## 3. AI 会话归档（pre-commit）

本课程允许使用 AI，提交的 commit 需要携带 AI 会话归档作为透明化记录：每次 `git commit` 后，钩子会把新增会话自动 amend 进同一个提交（`.agent-sessions/bundles/`），不产生额外的归档提交。支持 Claude Code、OpenAI Codex CLI、GitHub Copilot CLI、Qoder、ZCode、Trae、Tencent CodeBuddy 等（完整名单见 [AgentLedger](https://github.com/Gentle-Lijie/AgentLedger)）。

- 配置是仓库本地的：每个 clone 运行一次 `agent-session-commit install --pre-commit`，方向键选择 agent、确认其会话目录即可；
- 不想用 TUI 可手动配置：`git config --local agent-session.agent claude`、`git config --local agent-session.source "<会话目录>"`，然后 `python -m pip install 'pre-commit>=3.2.0' && pre-commit install`；
- 归档是普通 Git 内容且会推送到公开仓库——不要在 AI 会话里粘贴令牌等敏感信息；
- 换了 agent 或目录就重跑一次安装命令；卸载：从 `.pre-commit-config.yaml` 移除该条目后重跑 `pre-commit install`。

## 4. 本地开发循环

- **写代码**：全部作业在 `src/main/__init__.py`，按题面各题规范补全每个标有 TODO 的函数；注释里标注了对应的题面主题，推荐顺序 Q1 → Q6。
- **跑测试**：`python -m pytest` —— 可见测试是规格书的一部分，未实现的函数自动 skip，实现一个、对应测试亮一个。本地全绿 ≠ 满分（见题面）。
- **看演示**：`python main.py`（等价于 `PYTHONPATH=src python -m main`），随实现进度逐段点亮，不进测试。
- **Q6 自测**：`python tools/run_seeds.py --q6`（200 张固定地图统计），单 seed 渲染 `python tools/run_seeds.py --q6 --seed <N> --render`，Bonus 模式 `python tools/run_seeds.py --bonus`。

## 5. 仓库结构（哪些能改）

| 路径 | 说明 | 能否修改 |
| --- | --- | --- |
| `src/main/__init__.py` | 你的全部作业（TODO 所在） | ✅ |
| `README.md` | 仅末尾两个"你来写"小节 | ✅ |
| `题面.pdf` | 题面（唯一规格说明） | ❌ 勿改 |
| `src/main/legacy_patrol.py` | Q7 模块（与主体同步发布，修复其缺陷） | Q7 时 ✅ |
| `.pre-commit-config.yaml` | AI 会话归档钩子配置 | ❌ 勿改 |
| `src/tests/`、`tools/`、`.github/`、`conftest.py`、`pytest.ini`、`main.py` | 测试与基础设施 | ❌ 勿改 |

CI 只允许修改 `src/main/**`、`README.md` 与 `.agent-sessions/**`（AI 会话归档）——其余文件改了直接红；autopep8 `--diff` 非空即败。提交方式（push、问卷、commit 粒度）见题面"提交与验收"一节。

## 6. README

(所以写这作业还要顺便学一下markdown怎么写吗sos)

**①很高兴能够这个阶段的培训,我真的学到了很多:**

- **python能力进一步提升:** 虽然在这次的作业中主要体现为看懂代码哈哈
- **和各种AI的深入沟通:** 让我看清了AI很多时候又贵又蠢, 但是AI老师编程还是太强大了(🌹). 我还特意为了能和AI沟通严肃学习了一些东西...
- **心平气和:** 我从前一直以为自己是一个很冷静的人, 这次真的体会到爆炸的感觉了...但是很高兴在坚持不懈的锻炼中最终找到了自己的节奏. 其实这是我认为最最棒的一点了
- **迎难而上:** 其实这个词的意思是:我真的想不好这个readme要怎么写, 所以写下这句话的时候有种迎难而上的感觉╮(╯▽╰)╭
- **三分钟速成Markdown书写**
  
**②AI说明:**

很难过这个作业的AI生成率极高,基本只有Q1 & Q2是我独立写的, 但是测试跑出来总有很多问题, 所以请教AI老师进行修改.

不幸看到了 题面.pdf 上的隐藏条款.

**③本仓库导览：**

其他所有题目的初稿也都是AI写的.我只是看着提建议然后让AI改吧 （详见AI会话）

我觉得如果大家AI率都很高的话，这部分内容应该大差不差。

Additionally，这个题面怎么说我就怎么做。

> 不好意思commit忘记用core标记了
> 以下内容由AI生成

**④AI 会话归档说明（本地环境）：**

本机 WorkBuddy 5.6.2 写出的会话文件，首条记录 `type` 是 `session-meta`（连字符），
而 AgentLedger v0.1.5 的适配器只认 `session_meta`（下划线），导致官方钩子认不出会话
（`Project session files found: 0`）。为不篡改第三方工具，本仓库另建了一条本地归档通道：

- 归档产物：`.agent-sessions/bundles/*.jsonl`（会话原文）+ `.agent-sessions/state.json`（指纹），
  均已随提交入库，`git push` 后远端可见；
- 生成器（**刻意放在仓库外，不污染 CI 白名单**）：
  `~/.workbuddy/wb-archive-helper/archive_sessions.py`
- 钩子：`.git/hooks/post-commit`（调度器，先跑 AgentLedger，再跑本地脚本）；
  AgentLedger 原钩子备份为同目录 `post-commit.agentledger.bak`。

**恢复方法（若钩子被 `pre-commit install` 覆盖，或换了电脑）：**

1. 确认脚本存在：`~/.workbuddy/wb-archive-helper/archive_sessions.py`；若丢失，
   逻辑说明见本节，或从任一历史提交中的 `.agent-sessions/state.json` 元信息确认配置。
2. 重写 `.git/hooks/post-commit`，内容为：

```sh
#!/bin/sh
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
[ -f "$HERE/post-commit.agentledger.bak" ] && sh "$HERE/post-commit.agentledger.bak" "$@" || true
HELPER="$HOME/.workbuddy/wb-archive-helper/archive_sessions.py"
PY="$ROOT/.venv/Scripts/python.exe"
[ -x "$PY" ] || PY="$(command -v python || command -v python3)"
[ -n "$PY" ] && [ -f "$HELPER" ] && AI_CW_REPO="$ROOT" "$PY" "$HELPER" --repo "$ROOT" || true
exit 0
```

3. `chmod +x .git/hooks/post-commit`，然后手动验证：
   `sh .git/hooks/post-commit`，看到 `归属本仓库的会话：N 个` 即恢复成功。

Finally，祝生活愉快。
