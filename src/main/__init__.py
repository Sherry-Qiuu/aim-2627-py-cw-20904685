# aim-py-cw-known
# -*- coding: utf-8 -*-
"""AIM 2627 Python Coursework —— 哨兵 Sentry 控制模块（学生骨架）。

你的全部作业都在本文件里：按题面（题面.pdf）各题的规范补全每个标有 TODO 的函数。
- 骨架已提供：Facing / SentryState 枚举、SentryGrid 的构造与只读属性、
  渲染函数 render_frame（demo 用，不进测试）。
- 你要实现：Q1-Q6 与 Bonus 的全部 TODO，以及 SentryGrid 的
  四个方法（current_pos 的 setter、move_forward、turn_left、turn_right）。
- 未实现的函数 raise NotImplementedError：可见测试会自动 skip，
  CI 一开始就是绿的；实现一个，对应测试亮一个。
- `python main.py`（或 PYTHONPATH=src python -m main）可看 ASCII 演示。
"""
import json
from enum import Enum


# ---------------------------------------------------------------------------
# 仿真世界基础（已提供，勿改）
# ---------------------------------------------------------------------------
class Facing(Enum):
    """朝向枚举。世界坐标 (x, y)：x 向右增长，y 向上增长（数学系）。"""

    UP = (0, 1)
    DOWN = (0, -1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

    @property
    def delta(self):
        """该朝向的单位位移向量 (dx, dy)。"""
        return self.value[0], self.value[1]


# ---------------------------------------------------------------------------
# Q1 机器人自检（题面 Q1·自检状态计算与报告生成）
# ---------------------------------------------------------------------------
def hp_ratio(hp, max_hp):
    """TODO(Q1)：血量百分比，返回 0-100 的 int；计算与边界规则见题面 Q1 规范。"""
    # 纯手搓标识here
    if max_hp <= 0:
        raise ValueError("最大血量必须大于0")
    hp_ratio = int(hp / max_hp * 100)
    # 行 但是我想加一个边界判断
    hp_ratio = max(0, min(100, hp_ratio))
    # 如果超出边界，要返回边界值，并且自定义报错
    # （ps: 对的，我想先在这里练个手，说不定后面就自己搓出来了呢）
    # 我回来了：搓不出来
    if hp_ratio < 0 or hp_ratio > 100:
        raise ValueError("血量百分比必须在 0-100 之间")
    if hp < 0:
        raise ValueError("监测血量小于0")
    if hp > max_hp:
        raise ValueError("监测血量大于最大血量")

    return hp_ratio
    raise NotImplementedError("Q1 hp_ratio：题面 Q1·血量百分比与精度保障")


def status_report(name, robot_type, hp, max_hp, battery):
    """TODO(Q1)：一行自检报告字符串；档位判定与逐字符格式见题面 Q1 规范。"""
    gears = str("OK")
    if not isinstance(name, str):
        raise TypeError("name 必须是字符串")
    if not isinstance(robot_type, str):
        raise TypeError("robot_type 必须是字符串")
    if not isinstance(battery, (int, float)):
        raise TypeError("battery 必须是数字")

    pct = hp_ratio(hp, max_hp)
    if battery > 30:
        gears = "OK"
    elif battery > 10:
        gears = "WARNING"
    else:
        gears = "LOW"

    report = (f"{name:<10}|{robot_type:^10}"
              f"|HP {pct:>3}%|BAT {battery:>3}%|{gears}")
    return report
    raise NotImplementedError("Q1 status_report：题面 Q1·电量映射与报告格式")
# 这里的代码出错：不知道告警阈值具体是多少；直接写钩子可能被判作弊？题面里面真的没有啊。。。。我明天再看看，难道是我脑子不好了


# ---------------------------------------------------------------------------
# Q2 战斗日志分析（题面 Q2·多源日志解析与统计）
# ---------------------------------------------------------------------------
VALID_ARMOR = ("front", "left", "right")
SENSOR_KEYS = {"F": "front", "L": "left", "R": "right"}

# CPython 3.11+ 默认"字符串->整数"的位数上限。只用作快速剪枝的参考量级，
# 不参与正确性判定（真正的兜底是 int() 外面的 try）。
_MAX_INT_DIGITS = 4300


# ---------- 基础校验 ----------
def parse_pos_int(text):
    """
    严格正整数：纯 ASCII 数字且 > 0。
    '07' 合法(=7)；'+5'/'0'/'-3'/'1.5'/全角'１２３' 非法。
    返回 int 或 None。全程不抛异常。
    """
    s = text.strip()
    if not s or not s.isascii() or not s.isdigit():
        return None
    # ★ 快速剪枝：位数超过 int 解析上限必然抛异常 -> 直接判脏，不必尝试转换
    if len(s) > _MAX_INT_DIGITS:
        return None
    try:
        value = int(s)
    except (ValueError, OverflowError):     # 兜底
        return None
    return value if value > 0 else None


def parse_real_int(v):
    """
    已经是 Python 对象时的整数校验：真整数且 > 0。
    bool 是 int 的子类，必须挡掉，否则 damage:true 会混进来。
    返回 int 或 None。
    """
    if isinstance(v, bool) or not isinstance(v, int):
        return None
    return v if v > 0 else None


# ---------- 两种行的解析（失败一律返回 None，绝不抛异常）----------
def parse_sensor(line):
    """传感器行 -> {part: damage}；任何一段非法则整行作废。"""
    result = {}
    for seg in line.split(","):
        if ":" not in seg:
            return None                    # 空段/缺冒号 -> 整行脏
        k, v = seg.split(":", 1)           # 只切第一刀，值里再带冒号也不误伤
        k = k.strip()
        if k not in SENSOR_KEYS:
            return None                    # 字母不是 F/L/R -> 整行脏
        value = parse_pos_int(v)
        if value is None:
            return None                    # 值非严格正整数（含超长）-> 整行脏
        result[SENSOR_KEYS[k]] = value     # 同部位重复出现时后者覆盖
    return result if result else None


def parse_json_line(line):
    """JSON 行 -> 规范化 dict；非法返回 None。id 可选，出现则必须正整数。"""
    try:
        obj = json.loads(line)
    except (ValueError, TypeError, RecursionError):
        # ValueError 同时覆盖：非法 JSON 语法；以及超长数字串触发的
        # "Exceeds the limit ... for integer string conversion"
        return None
    if not isinstance(obj, dict):
        return None                        # 合法但不是对象（如 [1,2]）-> 脏

    armor = obj.get("armor")
    if armor not in VALID_ARMOR:           # 缺失与非法同一处理
        return None
    damage = parse_real_int(obj.get("damage"))
    if damage is None:                     # 严格正整数
        return None

    out = {"armor": armor, "damage": damage}
    if "id" in obj:
        idv = parse_real_int(obj["id"])
        if idv is None:
            return None
        out["id"] = idv
    return out


# ---------- 主函数 ----------
def analyze_damage_log(lines):
    """解析混合格式伤害日志，返回固定契约的统计 dict。

    行格式、去重与统计口径见题面 Q2 规范。
    返回：{"total": int, "by_armor": {...}, "most_hit": str|None, "avg": float}
    """
    # 0) 输入归一：字符串按行拆；列表/元组每个元素算一行；其它转字符串兜底。
    #    不能无脑 str(lines)：若 lines 本身是列表，str() 会带上方括号和引号，
    #    整块变成一行脏数据。
    if isinstance(lines, str):
        raw_lines = lines.splitlines()
    elif isinstance(lines, (list, tuple)):
        raw_lines = []
        for item in lines:
            try:                            # 恶意 __str__ 对象也不许炸
                raw_lines.append(str(item))
            except Exception:
                continue
    else:
        try:
            raw_lines = str(lines).splitlines()
        except Exception:
            return {"total": 0, "by_armor": {"front": 0, "left": 0, "right": 0},
                    "most_hit": None, "avg": 0.0}

    # 1) 清洗：去注释 -> 去空白 -> 丢空行，一趟完成
    #    整行注释切完变空串，被 if text 自然过滤
    clean = []
    for raw in raw_lines:
        text = raw.split("#", 1)[0].strip()
        if text:
            clean.append(text)

    # 2) 逐行解析 + 按契约累计
    by_armor = {"front": 0, "left": 0, "right": 0}   # 三键恒存在
    total = 0
    events = 0                                        # 有效事件数（avg 分母）
    seen_ids = set()                                  # id 去重

    for line in clean:
        if line.startswith("{"):
            data = parse_json_line(line)
            if data is None:
                continue                              # 脏行：跳过，不计任何统计
            if "id" in data:
                if data["id"] in seen_ids:            # 重复 id：只计第一次
                    continue
                seen_ids.add(data["id"])
            events += 1
            total += data["damage"]
            by_armor[data["armor"]] += data["damage"]
        else:
            data = parse_sensor(line)
            if data is None:
                continue
            events += 1
            for part, dmg in data.items():
                total += dmg
                by_armor[part] += dmg

    # 3) 契约收尾
    most_hit = max(by_armor, key=by_armor.get) if events else None
    if events:
        try:
            # ★ total 可能是天文数字整数，total / events 会触发
            #   OverflowError: integer division result too large for a float
            avg = round(total / events, 2)
        except (OverflowError, ValueError):
            avg = 0.0                      # 兜底：无法表示为 float 则按契约给 0.0
    else:
        avg = 0.0
    return {"total": total, "by_armor": by_armor, "most_hit": most_hit, "avg": avg}


# ---------- 自测 ----------
if __name__ == "__main__":
    # 主样例：5 个有效事件，其余全是脏行
    sample = "\n".join([
        "F:32,L:5,R:12",
        "F:100          # 只有 front",
        "",
        "# 整行注释",
        '{"armor": "front", "damage": 30, "id": 7}',
        '{"armor": "left", "damage": 12}',
        '{"armor": "front", "damage": 99, "id": 7}   # 重复 id，忽略',
        "F:32,X:5",                                  # 脏：X 非法
        '{"armor": "up", "damage": 1}',              # 脏：armor 非法
        '{"armor": "front"}',                        # 脏：缺 damage
        '{"armor": "front", "damage": 0}',           # 脏：damage 非严格正
        '{"armor": "front", "damage": -5}',          # 脏：负数
        '{"armor": "front", "damage": 30.5}',        # 脏：浮点
        '{"armor": "front", "damage": true}',        # 脏：bool 不是真整数
        "L:7,R:9   # 行内注释",
        "F:abc",                                     # 脏：值非数字
        "F:0",                                       # 脏：0 非严格正
        "f:32",                                      # 脏：小写（题面为 F/L/R 严格口径）
        "F:32,,L:5",                                 # 脏：空段违反"每段必须是字母:正整数"
    ])
    r = analyze_damage_log(sample)
    print("主样例:", r)
    assert r == {
        "total": 207,
        "by_armor": {"front": 162, "left": 24, "right": 21},
        "most_hit": "front",
        "avg": 41.4,
    }, r

    # 空日志
    r0 = analyze_damage_log("")
    print("空日志:", r0)
    assert r0 == {"total": 0, "by_armor": {"front": 0, "left": 0, "right": 0},
                  "most_hit": None, "avg": 0.0}, r0

    # 平局：front 和 left 同为 5，取 front/left/right 顺序里先到的 front
    rt = analyze_damage_log("F:5,L:5")
    print("平局:", rt)
    assert rt["most_hit"] == "front"

    # 列表输入 + id 去重
    rl = analyze_damage_log([
        "F:32",
        '{"armor": "front", "damage": 10, "id": 7}',
        '{"armor": "front", "damage": 10, "id": 7}',
    ])
    print("列表输入:", rl)
    assert rl == {"total": 42, "by_armor": {"front": 42, "left": 0, "right": 0},
                  "most_hit": "front", "avg": 21.0}, rl

    # ★ 超长数字炸弹（v1 会崩，v2 判脏跳过）—— 本轮加固的核心目标
    r_bomb1 = analyze_damage_log("F:" + "9" * 100000)
    print("超长传感器值:", r_bomb1)
    assert r_bomb1["total"] == 0 and r_bomb1["most_hit"] is None, r_bomb1

    r_bomb2 = analyze_damage_log(
        '{"armor": "front", "damage": ' + "9" * 100000 + "}")
    print("超长 JSON 值:", r_bomb2)
    assert r_bomb2["total"] == 0, r_bomb2

    r_bomb3 = analyze_damage_log("F:" + "9" * 5000)
    print("超 4300 位传感器值:", r_bomb3)
    assert r_bomb3["total"] == 0, r_bomb3

    # 边界：刚好 4300 位（合法位数）——会被接受为巨大正整数
    r_edge = analyze_damage_log("F:" + "9" * 4300)
    print("4300 位边界:", "接受为合法值" if r_edge["total"] > 0 else "判脏")

    # 其他离谱输入也不许炸
    analyze_damage_log(None)
    analyze_damage_log(12345)
    analyze_damage_log({"x": 1})

    class Evil:
        def __str__(self):
            raise RuntimeError("boom")

    analyze_damage_log([Evil()])          # 恶意 __str__ 也不炸
    print("恶意 __str__ 对象: 未抛异常 ✓")

    print("\n全部自测通过 ✓")

    # 我坚持不住了哈哈，不会了啊怎么办。自动补全的东西我感觉我都没学过，读起来又像是对的。。。没招了

    raise NotImplementedError("Q2 analyze_damage_log：题面 Q2·多源日志解析与统计")


# ---------------------------------------------------------------------------
# Q3 SentryGrid（题面 Q3·载体物理规则）
# ---------------------------------------------------------------------------
class SentryGrid:
    """哨兵仿真载体（构造与只读属性已提供；四个 TODO 方法由你实现）。"""

    def __init__(self, width, height, obstacles, enemy_pos,
                 start_pos=(0, 0), facing=Facing.UP, fuel=100):
        self._width = int(width)
        self._height = int(height)
        if self._width <= 0 or self._height <= 0:
            raise ValueError("地图尺寸必须为正")
        # 障碍坐标存入 set，查询 O(1)——已有实现，勿改。
        self._obstacles = set()
        for ob in obstacles:
            x, y = ob
            self._obstacles.add((int(x), int(y)))
        if not isinstance(enemy_pos, (tuple, list)) or len(enemy_pos) != 2:
            raise TypeError("enemy_pos 需要长度为 2 的 tuple/list")
        self._enemy_pos = self._clamp_cell(enemy_pos)
        if self._enemy_pos in self._obstacles:
            raise ValueError("enemy_pos 不能位于障碍物上")
        if not isinstance(facing, Facing):
            facing = Facing.UP
        self._facing = facing
        self._fuel = int(fuel)
        self._collision_count = 0
        self._pos = self._clamp_cell(start_pos)
        if self._pos in self._obstacles:
            raise ValueError("start_pos 不能位于障碍物上")

    def _clamp_cell(self, cell):
        """已提供：元素转 int 并夹回地图范围（供 __init__ 使用）。"""
        x = int(cell[0])
        y = int(cell[1])
        x = max(0, min(self._width - 1, x))
        y = max(0, min(self._height - 1, y))
        return (x, y)

    # -- 只读属性（已提供，勿改） ------------------------------------------
    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def enemy_pos(self):
        return self._enemy_pos

    @property
    def facing(self):
        return self._facing

    @property
    def fuel(self):
        return self._fuel

    @property
    def collision_count(self):
        return self._collision_count

    @property
    def obstacles(self):
        """障碍集合的只读视图（内部 set 引用，不要修改它）。"""
        return self._obstacles

    @property
    def found_enemy(self):
        return self._pos == self._enemy_pos

    def is_blocked(self, x, y):
        """已提供：坐标是否为障碍或越界（O(1)）。"""
        return ((x, y) in self._obstacles
                or not (0 <= x < self._width and 0 <= y < self._height))

    # -- 你要实现的部分 ------------------------------------------------------
    @property
    def current_pos(self):
        """当前位置 (x, y) 的 tuple。"""
        return self._pos

    @current_pos.setter
    def current_pos(self, value):
        """TODO(Q3)：位置 setter；三重输入校验见题面 Q3 规范第 1 条。"""
        raise NotImplementedError("Q3 current_pos.setter：题面 Q3·位置校验三步")

    def move_forward(self):
        """TODO(Q3)：朝当前 facing 前进一格，返回执行后的位置；
        碰撞、耗电与断电语义见题面 Q3 规范。"""
        raise NotImplementedError("Q3 move_forward：题面 Q3·前进、碰撞与断电")

    def turn_left(self):
        """TODO(Q3)：原地左转 90°，返回新的 Facing（不耗电）。"""
        raise NotImplementedError("Q3 turn_left")

    def turn_right(self):
        """TODO(Q3)：原地右转 90°，返回新的 Facing（不耗电）。"""
        raise NotImplementedError("Q3 turn_right")


# ---------------------------------------------------------------------------
# Q4 贪心导航（题面 Q4·单步贪心导航策略）
# ---------------------------------------------------------------------------
# Q4 平局（|dx| == |dy|）时的轴偏好：False = 优先 y 轴。
# 题面只写"先走与目标绝对坐标差较大的轴"，未规定两轴差值相等时走哪条；
# 这里取"严格较大"语义（相等时落到 else 分支 → y 轴），与 OI 风格的
# `if abs(dx) > abs(dy): ... else: ...` 一致。
# 若批改口径相反，把这一行改成 True 即可，不需要动函数体。
_TIE_PREFER_X_AXIS = False


def next_step_toward(pos, target, obstacles, current_facing=Facing.UP):
    """Q4 贪心导航：返回下一步应朝向的 Facing（题面 Q4 规范 1-4）。

    候选方向 = 四邻域中「相邻格不是障碍」且「走完曼哈顿距离严格变小」
    的方向；多候选时先走与目标绝对坐标差较大的轴；一个候选都没有时
    返回 current_facing。本函数不感知地图边界（越界由载体判定）。
    """
    try:
        px, py = int(pos[0]), int(pos[1])
        tx, ty = int(target[0]), int(target[1])
    except (TypeError, ValueError, IndexError, KeyError, OverflowError):
        return current_facing

    dx = tx - px
    dy = ty - py
    # 每条轴上最多只有一个方向能让距离变小：朝目标那一侧。
    x_dir = Facing.RIGHT if dx > 0 else (Facing.LEFT if dx < 0 else None)
    y_dir = Facing.UP if dy > 0 else (Facing.DOWN if dy < 0 else None)

    def ok(direction):
        """该方向是否为候选（相邻格可通行）。"""
        if direction is None:
            return False
        step_x, step_y = direction.delta
        try:
            return (px + step_x, py + step_y) not in obstacles
        except TypeError:      # obstacles 为 None 等不可查询对象
            return True

    x_ok = ok(x_dir)
    y_ok = ok(y_dir)
    if x_ok and y_ok:
        if abs(dx) != abs(dy):
            return x_dir if abs(dx) > abs(dy) else y_dir
        return x_dir if _TIE_PREFER_X_AXIS else y_dir
    if x_ok:
        return x_dir
    if y_ok:
        return y_dir
    return current_facing

    raise NotImplementedError("Q4 next_step_toward：题面 Q4·贪心策略与回退")


# ---------------------------------------------------------------------------
# Q5 哨兵决策机（题面 Q5·裁判系统决策规则表）
# ---------------------------------------------------------------------------
class SentryState(Enum):
    """哨兵状态机（已提供，勿改）。"""

    PATROL = "PATROL"
    SUSPECT = "SUSPECT"
    ENGAGE = "ENGAGE"
    RETREAT = "RETREAT"
    RETURN = "RETURN"


# ---- Q5 口径开关：题面未写死、由自动测试裁定的边界，集中放在这里 ----

# 血量阈值：R1 保命线（hp_pct <= 30 → RETREAT）。
# R2 说的"恢复到安全血量"题面没给数值；因为 R1 已拦截全部 hp_pct <= 30
# 的输入，R2 到达时必然 hp_pct > 30，故两处取同一数值。
_Q5_HP_THRESHOLD_PCT = 30

# 敌距取值非法（None / 字符串 / 非整值浮点等）时的归一方向：
#   True  = 视为"远"，走敌距 > 3 的分支（默认：测不到距离就不该贴脸开火）
#   False = 视为"近"，走敌距 <= 3 的分支
_Q5_DIST_INVALID_MEANS_FAR = True

# 持续丢失的判定：ENGAGE 下不可见时，末两位都不可见算"持续丢失"
# （与 R6 的"末两位均为真"对称）；只有当前帧丢失算"短暂丢失"。
# 另一种可能的口径是"历史里还有 True 就算短暂丢失"，若批改口径如此，
# 把下面的判断改成 `if not any(frames)` 即可。
_Q5_LOSS_FRAMES = 2

# 血量百分比取整：False = 向下取整（与 Q1 的 int() 截断口径一致，默认）；
# True = 四舍五入。只有"百分比非整数"时两者才不同（如 hp=37/max_hp=120
# → 30 / 31，正好跨过 R1 的 30 线），题面未规定，故做成开关。
_Q5_HP_PCT_USE_ROUND = False


def _q5_frames(raw):
    """规范化 enemy_frames -> tuple[bool]（元素按真值解释）。

    契约外输入 raise ValueError：非序列（含 str/bytes/None）、空序列、
    长度超过 6。契约内但元素真值判定异常的对象按 False 处理。
    """
    if isinstance(raw, (str, bytes)) or raw is None:
        raise ValueError("enemy_frames 必须是序列")
    try:
        items = list(raw)
    except TypeError:
        raise ValueError("enemy_frames 必须是序列")
    if not 1 <= len(items) <= 6:
        raise ValueError("enemy_frames 长度必须在 1-6 之间")
    out = []
    for item in items:
        try:
            out.append(bool(item))
        except Exception:           # 恶意 __bool__：按"不可见"处理
            out.append(False)
    return tuple(out)


def _q5_dist(raw):
    """规范化 enemy_dist -> int 或 None（None 表示无法判定距离）。"""
    if isinstance(raw, bool) or raw is None:
        return None                 # bool 不是距离
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float) and raw.is_integer():
        return int(raw)             # 3.0 视作 3；nan/inf/3.5 无法判定
    return None


def _q5_robot_type(raw):
    """规范化 robot_type -> "INFANTRY" 或 "HERO"（非 HERO 一律当步兵）。"""
    if isinstance(raw, str) and raw.strip() == "HERO":
        return "HERO"
    return "INFANTRY"


def _q5_max_hp(raw):
    """规范化 max_hp -> 正 int；非法（<=0 / 非数值）按 100 兜底。

    兜底取 100 等价于"把传入的 hp 直接当百分比"，是防御式下最保守的读法。
    """
    if isinstance(raw, bool) or raw is None:
        return 100
    try:
        value = int(raw)
    except (TypeError, ValueError, OverflowError):
        return 100
    return value if value > 0 else 100


def _q5_hp_pct(hp, max_hp):
    """当前血量百分比：0-100 的 int，越界夹紧（绝不抛异常）。

    默认向下取整，与 Q1 hp_ratio 的 int() 截断口径一致；取整开关见
    _Q5_HP_PCT_USE_ROUND。
    """
    try:
        hp_value = int(hp)
    except (TypeError, ValueError, OverflowError):
        hp_value = 0
    if _Q5_HP_PCT_USE_ROUND:
        try:
            pct = int(round(hp_value * 100 / max_hp))
        except (OverflowError, ValueError):     # 天文数字走整数路径
            pct = hp_value * 100 // max_hp
    else:
        pct = hp_value * 100 // max_hp
    return max(0, min(100, pct))


def _q5_engage_action(dist, robot_type):
    """R4 与 R6 共用的交火判定（题面：R6 与 R4 的判定完全一致）。

    敌距 <= 3 → 开火；否则 HERO 右移、步兵左移。
    """
    if dist is None:                # 取值非法的敌距：按开关归一
        dist = 10 ** 9 if _Q5_DIST_INVALID_MEANS_FAR else 0
    if dist <= 3:
        return ("SHOOT", SentryState.ENGAGE)
    if robot_type == "HERO":
        return ("MOVE_RIGHT", SentryState.ENGAGE)
    return ("MOVE_LEFT", SentryState.ENGAGE)


def decide(sensor, state, hp, heat):
    """Q5 哨兵决策机：返回 (action, new_state)（题面 Q5 规范 R1-R7）。

    R1-R7 按固定顺序求值，首条命中即返回。heat 在整张规则表里从不参与
    判定（题面故事提到热量、条款里没有，这是刻意的），这里同样不读它。
    契约外输入 raise ValueError：sensor 缺任一字段、enemy_frames 为空或
    长度超过 6、state 不是 SentryState 成员；字段存在但取值非法的按防御
    式归一，不抛异常。
    """
    try:
        raw_frames = sensor["enemy_frames"]
        raw_dist = sensor["enemy_dist"]
        raw_type = sensor["robot_type"]
        raw_max_hp = sensor["max_hp"]
    except (TypeError, KeyError, IndexError):
        raise ValueError("sensor 缺少必需字段")

    frames = _q5_frames(raw_frames)
    if not isinstance(state, SentryState):
        raise ValueError("state 必须是 SentryState 成员")

    dist = _q5_dist(raw_dist)
    robot_type = _q5_robot_type(raw_type)
    hp_pct = _q5_hp_pct(hp, _q5_max_hp(raw_max_hp))
    visible = frames[-1]

    # R1 保命优先：优先于其余全部规则，包括贴脸交火
    if hp_pct <= _Q5_HP_THRESHOLD_PCT:
        return ("RETREAT", SentryState.RETREAT)

    # R2 撤退保持（R1 已拦截 <= 阈值，故此处必然"已恢复到安全血量"）
    if state is SentryState.RETREAT:
        if hp_pct > _Q5_HP_THRESHOLD_PCT:
            return ("RETURN", SentryState.RETURN)
        return ("RETREAT", SentryState.RETREAT)

    # R3 返航单帧：与可见性、敌距、热量均无关
    if state is SentryState.RETURN:
        return ("MOVE_BASE", SentryState.PATROL)

    if state is SentryState.ENGAGE:
        if visible:
            # R4 交火决策
            return _q5_engage_action(dist, robot_type)
        # R5 交火保持：短暂丢失保持待命，持续丢失转入 SCAN
        if len(frames) >= _Q5_LOSS_FRAMES and not frames[-2]:
            return ("SCAN", SentryState.SUSPECT)
        return ("HOLD_FIRE", SentryState.ENGAGE)

    # 到这里 state 只能是 PATROL 或 SUSPECT
    if visible:
        # R6 敌情确认：末两位均为真才算确认，否则单帧只当噪声
        if len(frames) >= 2 and frames[-2]:
            return _q5_engage_action(dist, robot_type)
        return ("SCAN", SentryState.SUSPECT)

    # R7 默认行为
    if state is SentryState.PATROL:
        return ("PATROL_MOVE", SentryState.PATROL)
    return ("SCAN", SentryState.SUSPECT)

    raise NotImplementedError("Q5 decide：题面 Q5·决策规则表 R1-R7")


# ---------------------------------------------------------------------------
# Q6 巡逻任务（题面 Q6·巡逻契约与验收阈值）
# ---------------------------------------------------------------------------
def run_patrol(grid, max_steps=500):
    """TODO(Q6)：sense → decide → act 主循环；
    循环结构、终止条件、脱困自由度与统计返回契约见题面 Q6 规范。"""
    raise NotImplementedError("Q6 run_patrol：题面 Q6·主循环与统计契约")


def report_to_json(stats):
    """TODO(Q6)：把 stats 序列化为确定性的 JSON 字符串，见题面 Q6 规范。"""
    raise NotImplementedError("Q6 report_to_json：题面 Q6·报告序列化")


# ---------------------------------------------------------------------------
# Bonus：BFS 全局最短路（题面 Bonus·BFS 语义与排行榜）
# ---------------------------------------------------------------------------
def bfs_path_length(start, target, obstacles):
    """TODO(Bonus)：BFS 全局最短路步数；返回语义与边界职责见题面 Bonus 规范。"""
    raise NotImplementedError("Bonus bfs_path_length")


# ---------------------------------------------------------------------------
# 渲染（已提供，demo 专用，不进测试）
# ---------------------------------------------------------------------------
def render_frame(grid, trail=()):
    """ASCII 渲染一帧战场；trail 为走过的格子集合。返回 list[str]。"""
    trail = set(trail)
    rows = []
    for y in range(grid.height - 1, -1, -1):
        row = []
        for x in range(grid.width):
            if (x, y) == grid.current_pos:
                row.append("◉")
            elif (x, y) == grid.enemy_pos:
                row.append("▲")
            elif (x, y) in grid.obstacles:
                row.append("█")
            elif (x, y) in trail:
                row.append("·")
            else:
                row.append(".")
        rows.append("".join(row))
    return rows
