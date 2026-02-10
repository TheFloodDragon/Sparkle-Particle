"""
SPS (Sparkle Particle Storage) 格式编解码器。
采用增量存储与游程编码的紧凑可读粒子数据格式。

格式规范 (v1):
    #SPS1                       文件头（版本 1）
    @s                          单一形状块
    @a                          动画块
    t <type>                    粒子类型（省略 minecraft: 前缀，增量：仅变化时写出）
    d <x> <y> <z>              扩散参数（默认值 0 0 0 时省略）
    v <speed>                   速度（为 0 时省略）
    c <count>                   数量（为 1 时省略）
    ? <axis>                    局部轴省略（0/1/2 代表 x/y/z）
    P <x> <y> <z>              坐标起点（绝对坐标，始终 3D）
    <dx> <dy> <dz>             增量行（无前缀；轴省略模式下省一个分量）
    = <k> <n>                  模式游程：重复上 k 行增量 n 次
    M <x> <y> <z>              运动向量起点（绝对，始终 3D）
    > <tick>                    动画帧标记（刻）
    # ...                       注释行

精度策略：
    编码时先将所有原始点四舍五入到指定精度，再从四舍五入后的点计算增量。
    这样增量本身就是精确的 prec 位小数差值，解码器累加后可精确还原。
"""

import os

from .shape import ParticleShape, Point3D
from .animation import ParticleAnimation


# ============================================================
#  数值格式化
# ============================================================


def _fmt(v: float, prec: int) -> str:
    """紧凑格式化：0.5→'.5'  -0.3→'-.3'  3.0→'3'  0.0→'0'"""
    v = round(v, prec)
    if v == 0.0:
        return "0"
    s = f"{v:.{prec}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    if s.startswith("0."):
        s = s[1:]
    elif s.startswith("-0."):
        s = "-" + s[2:]
    return s


def _fmt3(p, prec):
    return f"{_fmt(p[0], prec)} {_fmt(p[1], prec)} {_fmt(p[2], prec)}"


def _fmtD(p, prec, drop=None):
    """格式化坐标，可选省略 drop 轴。"""
    if drop is None:
        return _fmt3(p, prec)
    vals = [_fmt(p[i], prec) for i in range(3) if i != drop]
    return " ".join(vals)


def _numify(v):
    """浮点整数值转 int，匹配 ParticleShape 原始类型约定。"""
    return int(v) if v == int(v) else v


def _numify3(t):
    return (_numify(t[0]), _numify(t[1]), _numify(t[2]))


def _round3(p, prec):
    """三分量四舍五入。"""
    return (round(p[0], prec), round(p[1], prec), round(p[2], prec))


# ============================================================
#  局部轴省略规划
# ============================================================


def _plan_drops(deltas):
    """
    为每个增量规划轴省略。
    返回长度为 len(deltas) 的列表，每项为省略轴索引（0/1/2）或 None。
    仅当连续 >=3 个增量在某轴为 0 时才启用省略。
    deltas 应为已四舍五入后的精确增量。
    """
    n = len(deltas)
    if n == 0:
        return []

    # 找出每个轴的零值连续段
    runs = []
    for axis in range(3):
        i = 0
        while i < n:
            if deltas[i][axis] == 0:
                j = i
                while j < n and deltas[j][axis] == 0:
                    j += 1
                if j - i >= 3:
                    runs.append((i, j, axis, j - i))
                i = j
            else:
                i += 1

    # 按长度降序排列，贪心分配（不重叠）
    runs.sort(key=lambda r: r[3], reverse=True)
    drop_map = [None] * n
    for start, end, axis, _ in runs:
        if all(drop_map[k] is None for k in range(start, end)):
            for k in range(start, end):
                drop_map[k] = axis

    return drop_map


# ============================================================
#  编码（Python 对象 → SPS 文本）
# ============================================================


def _encode_pts(pts, tag, prec):
    """增量 + 局部轴省略 + 模式游程编码点列表。"""
    if not pts:
        return []

    # 先将所有点四舍五入到指定精度，后续一切计算基于四舍五入后的值
    rpts = [_round3(p, prec) for p in pts]

    out = [f"{tag} {_fmt3(rpts[0], prec)}"]
    if len(rpts) < 2:
        return out

    # 从四舍五入后的点计算增量（精确差值，无累积误差）
    deltas = []
    for i in range(1, len(rpts)):
        d = (rpts[i][0] - rpts[i - 1][0],
             rpts[i][1] - rpts[i - 1][1],
             rpts[i][2] - rpts[i - 1][2])
        deltas.append(d)

    # 模拟解码器累加，用于 RLE 验证
    dec_pts = [rpts[0]]
    acc = rpts[0]
    for d in deltas:
        acc = (acc[0] + d[0], acc[1] + d[1], acc[2] + d[2])
        dec_pts.append(acc)

    # 规划局部轴省略
    drop_map = _plan_drops(deltas)

    # 按轴省略状态分段，每段内应用模式游程编码
    current_drop = None
    i = 0
    while i < len(deltas):
        # 轴省略状态切换
        if drop_map[i] != current_drop:
            current_drop = drop_map[i]
            if current_drop is not None:
                out.append(f"? {current_drop}")

        # 当前段末尾
        seg_end = i + 1
        while seg_end < len(deltas) and drop_map[seg_end] == current_drop:
            seg_end += 1

        # 段内模式游程编码
        j = i
        while j < seg_end:
            best_k, best_n = 0, 0
            max_k = min((seg_end - j) // 2, 8)
            for k in range(1, max_k + 1):
                pattern = deltas[j : j + k]
                # 模拟解码器验证每次重复
                n = 0
                sim_acc = dec_pts[j + k]
                pos = j + k
                while pos + k <= seg_end:
                    test_acc = sim_acc
                    ok = True
                    for jj in range(k):
                        test_acc = (test_acc[0] + pattern[jj][0],
                                    test_acc[1] + pattern[jj][1],
                                    test_acc[2] + pattern[jj][2])
                        target = dec_pts[pos + jj + 1]
                        if (round(test_acc[0], prec) != round(target[0], prec)
                                or round(test_acc[1], prec) != round(target[1], prec)
                                or round(test_acc[2], prec) != round(target[2], prec)):
                            ok = False
                            break
                    if ok:
                        sim_acc = test_acc
                        n += 1
                        pos += k
                    else:
                        break
                if n > 0 and n * k > best_n * best_k:
                    best_k = k
                    best_n = n

            if best_n > 0:
                for jj in range(best_k):
                    out.append(_fmtD(deltas[j + jj], prec, current_drop))
                out.append(f"= {best_k} {best_n}")
                j += best_k + best_n * best_k
            else:
                out.append(_fmtD(deltas[j], prec, current_drop))
                j += 1

        i = seg_end

    return out


def _encode_shape(shape, prec, prev=None):
    """编码单个形状，返回 (行列表, 当前状态)。"""
    lines = []
    sp = shape.particle[10:] if shape.particle.startswith("minecraft:") else shape.particle
    cd = shape.delta
    cv = shape.speed
    cc = shape.count
    state = {"t": sp, "d": cd, "v": cv, "c": cc}

    # 粒子类型增量编码
    if prev is None or sp != prev["t"]:
        lines.append(f"t {sp}")

    if prev is None:
        if cd != (0, 0, 0):
            lines.append(f"d {_fmt3(cd, prec)}")
        if cv != 0:
            lines.append(f"v {_fmt(cv, prec)}")
        if cc != 1:
            lines.append(f"c {cc}")
    else:
        if cd != prev["d"]:
            lines.append(f"d {_fmt3(cd, prec)}")
        if cv != prev["v"]:
            lines.append(f"v {_fmt(cv, prec)}")
        if cc != prev["c"]:
            lines.append(f"c {cc}")

    lines.extend(_encode_pts(shape.points, "P", prec))
    if shape.motions:
        lines.extend(_encode_pts(shape.motions, "M", prec))
    return lines, state


# ============================================================
#  保存
# ============================================================


def save(data, filename, precision=4):
    """
    保存 ParticleShape 或 ParticleAnimation 为 .sps 文件。
    precision: 坐标小数位数（默认 4，与 Minecraft particle 命令精度一致）
    返回文件绝对路径。
    """
    if not filename.endswith(".sps"):
        filename += ".sps"
    os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)

    buf = ["#SPS1"]

    if isinstance(data, ParticleShape):
        buf.append("@s")
        body, _ = _encode_shape(data, precision)
        buf.extend(body)
    elif isinstance(data, ParticleAnimation):
        buf.append("@a")
        prev = None
        for t in sorted(data.frames):
            buf.append(f"> {t}")
            body, prev = _encode_shape(data.frames[t], precision, prev)
            buf.extend(body)
    else:
        raise TypeError(f"不支持的数据类型: {type(data)}")

    with open(filename, "w", encoding="utf-8") as fh:
        fh.write("\n".join(buf) + "\n")

    size = os.path.getsize(filename)
    if isinstance(data, ParticleShape):
        info = f"{len(data.points)} 点"
    else:
        nf = len(data.frames)
        np_ = sum(len(s.points) for s in data.frames.values())
        info = f"{nf} 帧, {np_} 点"
    print(f"已保存: {filename} ({info}, {size} 字节)")
    return os.path.abspath(filename)


# ============================================================
#  解码（SPS 文本 → Python 对象）
# ============================================================

_DEFAULTS = {"t": "flame", "d": (0, 0, 0), "v": 0.0, "c": 1}


def _is_data_line(line):
    """判断是否为增量数据行（以数字、负号、点号开头）。"""
    c = line[0]
    return c.isdigit() or c == "-" or c == "."


def _parse_vals(s):
    """解析空格分隔的数值串。"""
    return [float(v) for v in s.split()]


def _decode_pts(lines, pos):
    """从 pos 解码点序列（P/M 行 + 后续增量/?/游程行）。"""
    pts = []
    recent_deltas = []  # 最近的增量元组，供模式游程回溯
    drop = None
    # 起点始终 3D
    header = lines[pos].split(maxsplit=1)[1]
    pts.append(tuple(_parse_vals(header)))
    pos += 1

    while pos < len(lines):
        line = lines[pos]

        # 局部轴省略指令
        if line.startswith("? "):
            drop = int(line.split()[1])
            pos += 1
            continue

        # 游程行：= k n
        if line.startswith("="):
            parts = line.split()
            k = int(parts[1])
            n = int(parts[2])
            pattern = recent_deltas[-k:]
            for _ in range(n):
                for d in pattern:
                    prev = pts[-1]
                    pts.append((prev[0] + d[0], prev[1] + d[1], prev[2] + d[2]))
            pos += 1
            continue

        if not _is_data_line(line):
            break

        vals = [float(v) for v in line.split()]
        if drop is not None and len(vals) == 2:
            vals.insert(drop, 0.0)
        d = tuple(vals)

        prev = pts[-1]
        pts.append((prev[0] + d[0], prev[1] + d[1], prev[2] + d[2]))
        recent_deltas.append(d)

        pos += 1

    return pts, pos


def _decode_shape(lines, defaults):
    """解析一帧的形状行。"""
    p = defaults["t"]
    d = defaults["d"]
    v = defaults["v"]
    c = defaults["c"]
    points = []
    motions = []

    i = 0
    while i < len(lines):
        if _is_data_line(lines[i]):
            i += 1
            continue

        parts = lines[i].split(maxsplit=1)
        cmd = parts[0]

        if cmd == "t":
            p = parts[1]
            i += 1
        elif cmd == "d":
            d = tuple(_parse_vals(parts[1]))
            i += 1
        elif cmd == "v":
            v = float(parts[1])
            i += 1
        elif cmd == "c":
            c = int(parts[1])
            i += 1
        elif cmd == "P":
            points, i = _decode_pts(lines, i)
        elif cmd == "M":
            motions, i = _decode_pts(lines, i)
        else:
            i += 1

    particle = p if ":" in p else f"minecraft:{p}"
    state = {"t": p, "d": d, "v": v, "c": c}
    return ParticleShape(
        points=points,
        particle=particle,
        delta=_numify3(d),
        speed=_numify(v),
        count=c,
        motions=motions or None,
    ), state


# ============================================================
#  加载
# ============================================================


def load(filename):
    """
    加载 .sps 文件。
    返回 ParticleShape（@s 块）或 ParticleAnimation（@a 块）。
    """
    with open(filename, "r", encoding="utf-8") as fh:
        raw = fh.readlines()
    lines = [l.strip() for l in raw if l.strip() and not l.strip().startswith("#")]
    if not lines:
        raise ValueError("空的 SPS 文件")

    tag = lines[0]
    body = lines[1:]

    if tag == "@s":
        shape, _ = _decode_shape(body, dict(_DEFAULTS))
        return shape

    if tag == "@a":
        anim = ParticleAnimation()
        frames = []
        tick = -1
        buf = []
        for line in body:
            parts = line.split()
            if parts[0] == ">":
                if tick >= 0:
                    frames.append((tick, buf))
                tick = int(parts[1])
                buf = []
            else:
                buf.append(line)
        if tick >= 0:
            frames.append((tick, buf))
        state = dict(_DEFAULTS)
        for t, flines in frames:
            shape, state = _decode_shape(flines, state)
            anim.frames[t] = shape
        return anim

    raise ValueError(f"未知的 SPS 块类型: {tag}")
