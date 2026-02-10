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

# ==============================================================
print("=" * 62)
print(f"  结果: {PASS} passed, {FAIL} failed")
print("=" * 62)
sys.exit(1 if FAIL else 0)
