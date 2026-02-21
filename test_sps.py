"""
SPS 格式往返测试。
验证 save_sps / load_sps 的编解码正确性与压缩率。

运行: python test_sps.py
"""

import math
import os
import sys

from sparkle import (
    ParticleShape,
    ParticleAnimation,
    ParticleCompiler,
    save_sps,
    load_sps,
    circle,
    sphere,
    helix,
    heart,
    star,
    torus,
    line,
)

PASS = 0
FAIL = 0


def check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS  {name}")
    else:
        FAIL += 1
        msg = f"  FAIL  {name}"
        if detail:
            msg += f"  — {detail}"
        print(msg)


def _normalize_cmd(cmd: str) -> str:
    """规范化命令字符串：~-0.0000 → ~0.0000, -0.0000 → 0.0000"""
    return cmd.replace("~-0.0000", "~0.0000").replace(" -0.0000 ", " 0.0000 ")


def _parse_coords(cmd: str):
    """从命令字符串提取所有数值。"""
    parts = cmd.split()
    vals = []
    for p in parts:
        s = p.lstrip("~")
        try:
            vals.append(float(s))
        except ValueError:
            vals.append(s)
    return vals


def cmds_match(a: ParticleShape, b: ParticleShape, tol=5e-8) -> bool:
    """比较两个形状编译后的命令（数值容差比较）。"""
    ca = ParticleCompiler.compile(a)
    cb = ParticleCompiler.compile(b)
    if len(ca) != len(cb):
        return False
    for x, y in zip(ca, cb):
        va, vb = _parse_coords(x), _parse_coords(y)
        if len(va) != len(vb):
            return False
        for a_v, b_v in zip(va, vb):
            if isinstance(a_v, float) and isinstance(b_v, float):
                if abs(a_v - b_v) > tol:
                    return False
            elif a_v != b_v:
                return False
    return True


def first_diff(a: ParticleShape, b: ParticleShape, tol=5e-4) -> str:
    ca = ParticleCompiler.compile(a)
    cb = ParticleCompiler.compile(b)
    for i, (x, y) in enumerate(zip(ca, cb)):
        va, vb = _parse_coords(x), _parse_coords(y)
        for a_v, b_v in zip(va, vb):
            if isinstance(a_v, float) and isinstance(b_v, float):
                if abs(a_v - b_v) > tol:
                    return f"cmd #{i}:\n        orig: {x}\n        load: {y}"
            elif a_v != b_v:
                return f"cmd #{i}:\n        orig: {x}\n        load: {y}"
    if len(ca) != len(cb):
        return f"命令数不同: {len(ca)} vs {len(cb)}"
    return ""


# ==============================================================
print("=" * 62)
print("  SPS 格式往返测试")
print("=" * 62)

# ------ 1. 基础形状往返 + 压缩率 ------
print("\n--- 1. 基础形状往返 + 压缩率 ---\n")
print(f"  {'name':>10s}  {'pts':>5s}  {'SPS':>7s}  {'mcf':>7s}  {'ratio':>6s}")
print("  " + "-" * 48)

shapes = [
    ("circle",  circle(radius=3, points=80)),
    ("sphere",  sphere(radius=4, u_points=24, v_points=12)),
    ("helix",   helix(radius=2, height=10, turns=3, points=200)),
    ("heart",   heart(size=4, points=120).offset(y=5)),
    ("star",    star(outer_r=4, inner_r=1.5, n_points=5, samples=200)),
    ("torus",   torus(major_r=4, minor_r=1.5, u_points=36, v_points=18)),
    ("line",    line(start=(0, 0, 0), end=(10, 5, 3), points=50)),
]

for name, shape in shapes:
    sps_f = f"output_test/test_{name}"
    mc_f = f"output_test/test_{name}_mc"
    save_sps(shape, sps_f)
    ParticleCompiler.save(shape, mc_f)
    loaded = load_sps(sps_f + ".sps")
    ok = cmds_match(shape, loaded)
    sps_sz = os.path.getsize(sps_f + ".sps")
    mc_sz = os.path.getsize(mc_f + ".mcfunction")
    ratio = sps_sz / mc_sz * 100
    tag = "PASS" if ok else "FAIL"
    print(f"  {name:>10s}  {len(shape.points):5d}  {sps_sz:6d}B  {mc_sz:6d}B  {ratio:5.1f}%  {tag}")
    if not ok:
        FAIL += 1
        print(f"        {first_diff(shape, loaded)}")
    else:
        PASS += 1

# ------ 2. 带运动向量的形状 ------
print("\n--- 2. 运动向量 ---")

motion_shapes = [
    ("radial",  sphere(radius=2, u_points=16, v_points=8).with_radial_motion(speed=0.8)),
    ("tangent", circle(radius=4, points=80).with_tangent_motion(speed=0.3)),
    ("uniform", circle(radius=3, points=60).with_motion(0, 0.3, 0, speed=0.5)),
    ("custom",  helix(radius=2, height=8, turns=3, points=100).with_custom_motion(
                    lambda x, y, z: (x * 0.2, 0.5, z * 0.2), speed=0.6)),
]

for name, shape in motion_shapes:
    sps_f = f"output_test/test_motion_{name}"
    save_sps(shape, sps_f)
    loaded = load_sps(sps_f + ".sps")
    ok = cmds_match(shape, loaded)
    check(f"motion_{name} ({len(shape.points)}pts + motions)", ok, first_diff(shape, loaded))

# ------ 3. 非默认参数 ------
print("\n--- 3. 非默认参数 ---")

custom = ParticleShape(
    points=[(1, 2, 3), (4, 5, 6)],
    particle="minecraft:end_rod",
    delta=(0.1, 0.2, 0.3),
    speed=0.5,
    count=3,
)
save_sps(custom, "output_test/test_custom")
lc = load_sps("output_test/test_custom.sps")
check("particle", lc.particle == "minecraft:end_rod", f"got {lc.particle}")
check("delta",    lc.delta == (0.1, 0.2, 0.3),       f"got {lc.delta}")
check("speed",    lc.speed == 0.5,                    f"got {lc.speed}")
check("count",    lc.count == 3,                      f"got {lc.count}")
check("commands", cmds_match(custom, lc),             first_diff(custom, lc))

# ------ 4. 动画往返 ------
print("\n--- 4. 动画往返 ---")

anim = ParticleAnimation.static(
    heart(size=3, points=80, particle="minecraft:heart").offset(y=5),
    duration=10, fade_in=3, fade_out=3,
)
save_sps(anim, "output_test/test_anim")
la = load_sps("output_test/test_anim.sps")
check("anim frame count", sorted(la.frames.keys()) == sorted(anim.frames.keys()))
anim_ok = True
for t in sorted(anim.frames):
    if not cmds_match(anim.frames[t], la.frames[t]):
        check(f"anim frame {t}", False, first_diff(anim.frames[t], la.frames[t]))
        anim_ok = False
if anim_ok:
    check("anim all frames", True)

# ------ 5. 动画粒子类型增量编码 ------
print("\n--- 5. 粒子类型增量编码 ---")

anim2 = ParticleAnimation()
anim2.add_frame(0, circle(radius=2, points=10, particle="minecraft:flame"))
anim2.add_frame(1, circle(radius=3, points=10, particle="minecraft:flame"))
anim2.add_frame(2, circle(radius=4, points=10, particle="minecraft:end_rod"))
anim2.add_frame(3, circle(radius=5, points=10, particle="minecraft:end_rod"))
anim2.add_frame(4, circle(radius=6, points=10, particle="minecraft:flame"))
save_sps(anim2, "output_test/test_anim_incr_type")

# 读取原始文件内容验证 t 行出现次数
with open("output_test/test_anim_incr_type.sps", "r") as f:
    content = f.read()
    lines = content.strip().split("\n")

t_lines = [l for l in lines if l.startswith("t ")]
# 应该有 3 次 t 行：帧0(flame), 帧2(end_rod), 帧4(flame)
check("t lines count = 3", len(t_lines) == 3,
      f"got {len(t_lines)}: {t_lines}")
check("t line values", t_lines == ["t flame", "t end_rod", "t flame"],
      f"got {t_lines}")

la2 = load_sps("output_test/test_anim_incr_type.sps")
for t in sorted(anim2.frames):
    ok = cmds_match(anim2.frames[t], la2.frames[t])
    if not ok:
        check(f"incr_type frame {t}", False, first_diff(anim2.frames[t], la2.frames[t]))
        break
else:
    check("incr_type all frames match", True)

# ------ 6. 边界情况 ------
print("\n--- 6. 边界情况 ---")

# 单点
single = ParticleShape(points=[(1.5, -2.3, 0)])
save_sps(single, "output_test/test_single_pt")
ls = load_sps("output_test/test_single_pt.sps")
check("single point", cmds_match(single, ls))

# 空点集
empty = ParticleShape(points=[])
save_sps(empty, "output_test/test_empty")
le = load_sps("output_test/test_empty.sps")
check("empty shape", len(le.points) == 0)

# ------ 7. 查看生成的文件示例 ------
print("\n--- 7. 文件内容示例 ---\n")

# 线段（极端压缩）
save_sps(line(start=(0, 0, 0), end=(10, 5, 0), points=50), "output_test/demo_line")
print("  === output_test/demo_line.sps ===")
with open("output_test/demo_line.sps") as f:
    print("  " + f.read().replace("\n", "\n  "))

# 小圆
save_sps(circle(radius=2, points=8), "output_test/demo_circle8")
print("  === output_test/demo_circle8.sps ===")
with open("output_test/demo_circle8.sps") as f:
    print("  " + f.read().replace("\n", "\n  "))

# ------ 8. SNBT 序列化 ------
print("\n--- 8. SNBT 序列化 ---")

from sparkle.snbt import to_snbt, from_snbt

# 基础类型序列化
check("to_snbt bool true",  to_snbt(True)  == "1b")
check("to_snbt bool false", to_snbt(False) == "0b")
check("to_snbt int",        to_snbt(42)    == "42")
check("to_snbt float 1.5",  to_snbt(1.5)   == "1.5d")
check("to_snbt float 1.0",  to_snbt(1.0)   == "1.0d")
check("to_snbt string",     to_snbt("hello") == '"hello"')
check("to_snbt list int",   to_snbt([1, 2, 3]) == "[1,2,3]")
check("to_snbt list float", to_snbt([1.0, 0.0]) == "[1.0d,0.0d]")
check("to_snbt dict",       to_snbt({"a": 1}) == "{a:1}")

# 字符串转义
check("to_snbt escape quote",
      to_snbt('say "hi"') == '"say \\"hi\\""')
check("to_snbt escape backslash",
      to_snbt('a\\b') == '"a\\\\b"')

# 序列化→反序列化往返（仅浮点和字符串可完整往返）
for label, val in [
    ("float",  1.5),
    ("string", "hello"),
    ("str_esc", 'a"b\\c'),
    ("dict_float", {"color": [1.0, 0.0, 0.0], "scale": 2.0}),
]:
    check(f"snbt round-trip {label}", from_snbt(to_snbt(val)) == val)

# ------ 9. SNBT 反序列化 ------
print("\n--- 9. SNBT 反序列化 ---")

# 无后缀数值解析为字符串
check("parse int (no suffix)",    from_snbt("42") == "42")
check("parse neg int (no suffix)", from_snbt("-5") == "-5")
check("parse float (no suffix)",  from_snbt("1.5") == "1.5")
check("parse string dq", from_snbt('"hello"') == "hello")
check("parse string sq", from_snbt("'hello'") == "hello")
check("parse list (no suffix)",   from_snbt("[1,2,3]") == ["1", "2", "3"])
check("parse dict (no suffix)",   from_snbt("{a:1}") == {"a": "1"})
check("parse empty dict", from_snbt("{}") == {})
check("parse empty list", from_snbt("[]") == [])

# 布尔值解析为无引号字符串
check("parse true",     from_snbt("true") == "true")
check("parse false",    from_snbt("false") == "false")
check("parse TRUE",     from_snbt("TRUE") == "TRUE")
check("parse False",    from_snbt("False") == "False")
check("parse TrUe",     from_snbt("TrUe") == "TrUe")

# 无引号字符串边界（truevalue 等仍为完整字符串）
check("parse truevalue = unquoted string",
      from_snbt("{a:truevalue}")["a"] == "truevalue")
check("parse falsetto = unquoted string",
      from_snbt("{a:falsetto}")["a"] == "falsetto")

# 转义序列
check("parse \\\"", from_snbt(r'"a\"b"') == 'a"b')
check("parse \\\\", from_snbt(r'"a\\b"') == 'a\\b')
check("parse \\n",  from_snbt(r'"a\nb"') == 'a\nb')
check("parse \\t",  from_snbt(r'"a\tb"') == 'a\tb')
check("parse \\s",  from_snbt(r'"a\sb"') == 'a b')
check("parse \\b",  from_snbt(r'"a\bb"') == 'a\bb')
check("parse \\f",  from_snbt(r'"a\fb"') == 'a\fb')
check("parse \\r",  from_snbt(r'"a\rb"') == 'a\rb')

# 单引号内转义
check("parse sq escape", from_snbt(r"'a\'b'") == "a'b")
check("parse sq dq ok",  from_snbt("'a\"b'") == 'a"b')

# Unicode 转义
check("parse \\x42",   from_snbt(r'"a\x42b"') == 'aBb')
check("parse \\u0041", from_snbt(r'"a\u0041b"') == 'aAb')
check("parse \\U00000041", from_snbt(r'"a\U00000041b"') == 'aAb')

# 带后缀的数值（仅带后缀时解析为数值）
check("parse 1.5f",  from_snbt("1.5f") == 1.5)
check("parse 1.5d",  from_snbt("1.5d") == 1.5)
check("parse 3b",    from_snbt("3b") == 3)
check("parse 100s",  from_snbt("100s") == 100)
check("parse 100i",  from_snbt("100i") == 100)
check("parse 100L",  from_snbt("100L") == 100)
check("parse 42sb",  from_snbt("42sb") == 42)
check("parse 200ub", from_snbt("200ub") == 200)

# 无后缀的十六进制/二进制/下划线/浮点格式 → 字符串
check("parse 0xFF (no suffix)",    from_snbt("0xFF") == "0xFF")
check("parse 0xCAFE (no suffix)",  from_snbt("0xCAFE") == "0xCAFE")
check("parse 0b101 (no suffix)",   from_snbt("0b101") == "0b101")
check("parse -0xFF (no suffix)",   from_snbt("-0xFF") == "-0xFF")
check("parse 1_000 (no suffix)",   from_snbt("1_000") == "1_000")
check("parse 0xAB_CD (no suffix)", from_snbt("0xAB_CD") == "0xAB_CD")
check("parse 0b10_01 (no suffix)", from_snbt("0b10_01") == "0b10_01")
check("parse .5 (no suffix)",     from_snbt(".5") == ".5")
check("parse 1. (no suffix)",     from_snbt("1.") == "1.")
check("parse 1.2e3 (no suffix)",  from_snbt("1.2e3") == "1.2e3")
check("parse 1.2E+3 (no suffix)", from_snbt("1.2E+3") == "1.2E+3")
check("parse 12000e-1 (no suffix)", from_snbt("12000e-1") == "12000e-1")

# 0b 歧义：0 + 字节后缀 b → int 0；0b101 无后缀 → 字符串
check("parse 0b = byte 0", from_snbt("{a:0b}") == {"a": 0})
check("parse 0b101 = string", from_snbt("{a:0b101}") == {"a": "0b101"})

# 类型化数组（as_int 强制转换，无后缀值也能通过 int() 转换）
check("parse [B;1,2]",   from_snbt("[B;1,2]") == [1, 2])
check("parse [I;1,2,3]", from_snbt("[I;1,2,3]") == [1, 2, 3])
check("parse [L;1,2]",   from_snbt("[L;1,2]") == [1, 2])
check("parse [B;]",      from_snbt("[B;]") == [])

# 结尾逗号（无后缀值为字符串）
check("parse [1,2,]",  from_snbt("[1,2,]") == ["1", "2"])
check("parse {a:1,}",  from_snbt("{a:1,}") == {"a": "1"})

# 无引号字符串
check("parse unquoted value",
      from_snbt("{a:test}") == {"a": "test"})
check("parse unquoted key+value",
      from_snbt("{block_state:stone}") == {"block_state": "stone"})

# 带后缀的嵌套结构（典型粒子选项）
check("parse dust options (suffixed)",
      from_snbt('{color:[1.0d,0.0d,0.0d],scale:2.0d}')
      == {"color": [1.0, 0.0, 0.0], "scale": 2.0})
check("parse block options",
      from_snbt('{block_state:"minecraft:stone"}')
      == {"block_state": "minecraft:stone"})
check("parse nested dict (suffixed)",
      from_snbt('{a:{b:1i},c:[2i,3i]}')
      == {"a": {"b": 1}, "c": [2, 3]})

# 带空白的格式
check("parse with whitespace",
      from_snbt('{ color : [1.0d, 0.0d, 0.0d] , scale : 2.0d }')
      == {"color": [1.0, 0.0, 0.0], "scale": 2.0})

# 混合列表
check("parse mixed list",
      from_snbt("['text',{a:1b},123i]") == ["text", {"a": 1}, 123])

# ------ 10. 带粒子选项的 SPS 往返 ------
print("\n--- 10. 带粒子选项的 SPS 往返 ---")

# dust 粒子
dust_shape = ParticleShape(
    points=[(0, 0, 0), (1, 1, 1), (2, 2, 2)],
    particle="minecraft:dust",
    options={"color": [1.0, 0.0, 0.0], "scale": 2.0},
)
save_sps(dust_shape, "output_test/test_dust_opts")
ld = load_sps("output_test/test_dust_opts.sps")
check("dust opts preserved",
      ld.options == dust_shape.options,
      f"got {ld.options}")
check("dust cmds match", cmds_match(dust_shape, ld))

# block 粒子
block_shape = ParticleShape(
    points=[(0, 0, 0), (1, 0, 0)],
    particle="minecraft:block",
    options={"block_state": "minecraft:stone"},
)
save_sps(block_shape, "output_test/test_block_opts")
lb = load_sps("output_test/test_block_opts.sps")
check("block opts preserved",
      lb.options == block_shape.options,
      f"got {lb.options}")

# 验证 SPS 文件中 o 行为 SNBT 格式（无引号键）
with open("output_test/test_dust_opts.sps", "r") as f:
    sps_text = f.read()
o_line = [l.strip() for l in sps_text.split("\n") if l.strip().startswith("o ")][0]
check("sps o line is SNBT",
      "color:" in o_line and '"color"' not in o_line,
      f"got: {o_line}")

# 动画中的选项增量编码
anim3 = ParticleAnimation()
anim3.add_frame(0, ParticleShape(
    points=[(0, 0, 0)], particle="minecraft:dust",
    options={"color": [1.0, 0.0, 0.0], "scale": 1.0}))
anim3.add_frame(1, ParticleShape(
    points=[(1, 0, 0)], particle="minecraft:dust",
    options={"color": [1.0, 0.0, 0.0], "scale": 1.0}))  # 相同
anim3.add_frame(2, ParticleShape(
    points=[(2, 0, 0)], particle="minecraft:dust",
    options={"color": [0.0, 1.0, 0.0], "scale": 2.0}))  # 不同
anim3.add_frame(3, ParticleShape(
    points=[(3, 0, 0)], particle="minecraft:dust",
    options=None))  # 清除

save_sps(anim3, "output_test/test_anim_opts")
la3 = load_sps("output_test/test_anim_opts.sps")
check("anim opts frame 0",
      la3.frames[0].options == {"color": [1.0, 0.0, 0.0], "scale": 1.0})
check("anim opts frame 1 (same, inherited)",
      la3.frames[1].options == {"color": [1.0, 0.0, 0.0], "scale": 1.0})
check("anim opts frame 2 (changed)",
      la3.frames[2].options == {"color": [0.0, 1.0, 0.0], "scale": 2.0})
check("anim opts frame 3 (inherited, null removed)",
      la3.frames[3].options == {"color": [0.0, 1.0, 0.0], "scale": 2.0})

# 验证 o 行增量编码（帧1相同不重复，帧2变化写出，帧3 无选项不写出）
with open("output_test/test_anim_opts.sps", "r") as f:
    anim_opts_text = f.read()
anim_o_lines = [l.strip() for l in anim_opts_text.split("\n") if l.strip().startswith("o ")]
check("o lines count = 2 (initial + change)",
      len(anim_o_lines) == 2,
      f"got {len(anim_o_lines)}: {anim_o_lines}")

# ==============================================================
print("=" * 62)
print(f"  结果: {PASS} passed, {FAIL} failed")
print("=" * 62)
sys.exit(1 if FAIL else 0)
