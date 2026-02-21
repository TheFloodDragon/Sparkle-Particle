"""
Minecraft 粒子效果生成器 — 使用 Sparkle 库
生成各种粒子图形、运动效果和动画的 .mcfunction 文件示例。
"""

import math
import os

from sparkle import (
    ParticleShape,
    ParticleAnimation,
    ParticleCompiler,
    circle,
    sphere,
    helix,
    heart,
    sine_wave,
    star,
    torus,
    line,
    parametric_curve,
    parametric_surface,
    polygon,
    tetrahedron,
    cube,
    octahedron,
    dodecahedron,
    icosahedron,
    dust,
    dust_transition,
    block_particle,
    item_particle,
    entity_effect,
)


def main():
    output_dir = "output"

    # ================================================================
    #  1. 基础图形
    # ================================================================

    print("=== 1. 基础图形 ===")

    ParticleCompiler.save(circle(radius=3, points=80), f"{output_dir}/circle")

    ParticleCompiler.save(sphere(radius=4, u_points=36, v_points=18), f"{output_dir}/sphere")

    ParticleCompiler.save(heart(size=4, points=160).offset(y=5), f"{output_dir}/heart")

    ParticleCompiler.save(star(outer_r=5, inner_r=2, n_points=5, samples=300), f"{output_dir}/star")

    ParticleCompiler.save(helix(radius=2, height=10, turns=3, points=200), f"{output_dir}/helix")

    ParticleCompiler.save(torus(major_r=4, minor_r=1.5, u_points=48, v_points=24), f"{output_dir}/torus")

    ParticleCompiler.save(sine_wave(amplitude=2, wavelength=5, length=20, points=200), f"{output_dir}/sine_wave")

    ParticleCompiler.save(line(start=(0, 0, 0), end=(10, 5, 3), points=50), f"{output_dir}/line")

    # ================================================================
    #  2. 空间变换
    # ================================================================

    print("\n=== 2. 空间变换 ===")

    # 缩放：巨型心形
    ParticleCompiler.save(heart(size=4, points=200).scale(2.0).offset(y=10), f"{output_dir}/heart_giant")

    # 旋转：倾斜的圆环（绕 X 轴旋转 45°）
    ParticleCompiler.save(
        circle(radius=4, points=100, particle="minecraft:end_rod").rotate_x(math.pi / 4),
        f"{output_dir}/circle_tilted",
    )

    # 组合变换：绕 Y 轴旋转的星星 + 抬升
    ParticleCompiler.save(
        star(outer_r=3, inner_r=1, n_points=6, samples=200).rotate_y(math.pi / 6).offset(y=3),
        f"{output_dir}/star_rotated",
    )

    # ================================================================
    #  3. 图形合并与组合
    # ================================================================

    print("\n=== 3. 图形合并与组合 ===")

    # 三环交叉（三个正交圆环）
    ring_x = circle(radius=3, points=80, particle="minecraft:flame")
    ring_y = circle(radius=3, points=80, axis="x", particle="minecraft:soul_fire_flame")
    ring_z = circle(radius=3, points=80, axis="z", particle="minecraft:end_rod")
    ParticleCompiler.save(ring_x + ring_y + ring_z, f"{output_dir}/three_rings")

    # 球体 + 赤道环
    planet = sphere(radius=3, u_points=24, v_points=12, particle="minecraft:end_rod")
    equator = circle(radius=3.5, points=100, particle="minecraft:flame")
    ParticleCompiler.save(planet + equator, f"{output_dir}/planet_with_ring")

    # 双螺旋（DNA 风格）
    dna_a = helix(radius=2, height=12, turns=4, points=300, particle="minecraft:end_rod")
    dna_b = helix(radius=2, height=12, turns=4, points=300, particle="minecraft:soul_fire_flame").rotate_y(math.pi)
    ParticleCompiler.save(dna_a + dna_b, f"{output_dir}/dna_double_helix")

    # 同心圆（涟漪效果）
    ripple = circle(radius=1, points=40, particle="minecraft:cloud")
    for r in [2, 3, 4, 5, 6]:
        ripple = ripple + circle(radius=r, points=int(40 * r), particle="minecraft:cloud")
    ParticleCompiler.save(ripple, f"{output_dir}/ripple")

    # ================================================================
    #  4. 粒子运动
    # ================================================================

    print("\n=== 4. 粒子运动 ===")

    # 圆环 + 向上飘动
    ParticleCompiler.save(
        circle(radius=3, points=80).with_motion(0, 0.3, 0, speed=0.5),
        f"{output_dir}/circle_rising",
    )

    # 球体 + 向外爆炸
    ParticleCompiler.save(
        sphere(radius=2, u_points=24, v_points=12).with_radial_motion(speed=0.8),
        f"{output_dir}/sphere_explode",
    )

    # 圆环 + 沿切线流动
    ParticleCompiler.save(
        circle(radius=4, points=120, particle="minecraft:soul_fire_flame").with_tangent_motion(speed=0.3),
        f"{output_dir}/circle_flow",
    )

    # 螺旋 + 自定义运动（向外旋转飞散）
    ParticleCompiler.save(
        helix(radius=2, height=8, turns=3, points=300).with_custom_motion(
            lambda x, y, z: (x * 0.2, 0.5, z * 0.2), speed=0.6
        ),
        f"{output_dir}/helix_scatter",
    )

    # 心形 + 向外辐射（心碎效果）
    ParticleCompiler.save(
        heart(size=4, points=200, particle="minecraft:damage_indicator")
            .offset(y=5)
            .with_radial_motion(speed=0.4, center=(0, 5, 0)),
        f"{output_dir}/heart_shatter",
    )

    # 环面 + 切线旋转（甜甜圈旋转流动）
    ParticleCompiler.save(
        torus(major_r=3, minor_r=1, u_points=36, v_points=18, particle="minecraft:flame")
            .with_tangent_motion(speed=0.2),
        f"{output_dir}/torus_flow",
    )

    # 向内收缩的球体（黑洞吸引效果）
    ParticleCompiler.save(
        sphere(radius=5, u_points=24, v_points=12, particle="minecraft:portal")
            .with_radial_motion(speed=-0.6),
        f"{output_dir}/sphere_implode",
    )

    # ================================================================
    #  5. 自定义参数方程
    # ================================================================

    print("\n=== 5. 自定义参数方程 ===")

    # 利萨如曲线 (Lissajous)
    ParticleCompiler.save(
        parametric_curve(
            func=lambda t: (4 * math.sin(3 * t), 4 * math.sin(2 * t), 0),
            t_range=(0, 2 * math.pi),
            points=300,
            particle="minecraft:end_rod",
        ),
        f"{output_dir}/lissajous",
    )

    # 玫瑰曲线 (rhodonea)  r = cos(k*θ), k=3 → 三瓣玫瑰
    ParticleCompiler.save(
        parametric_curve(
            func=lambda t: (
                4 * math.cos(3 * t) * math.cos(t),
                0,
                4 * math.cos(3 * t) * math.sin(t),
            ),
            t_range=(0, 2 * math.pi),
            points=400,
            particle="minecraft:cherry_leaves",
        ),
        f"{output_dir}/rose_curve",
    )

    # 蝴蝶曲线 (butterfly curve)
    def butterfly(t):
        r = math.exp(math.sin(t)) - 2 * math.cos(4 * t) + math.sin((2 * t - math.pi) / 24) ** 5
        return (r * math.sin(t) * 2, r * math.cos(t) * 2, 0)

    ParticleCompiler.save(
        parametric_curve(func=butterfly, t_range=(0, 24 * math.pi), points=800,
                         particle="minecraft:end_rod").offset(y=5),
        f"{output_dir}/butterfly",
    )

    # 莫比乌斯带 (Mobius strip)
    def mobius(u, v):
        half_v = v - 0.5
        x = (3 + half_v * math.cos(u / 2)) * math.cos(u)
        y = half_v * math.sin(u / 2)
        z = (3 + half_v * math.cos(u / 2)) * math.sin(u)
        return (x, y, z)

    ParticleCompiler.save(
        parametric_surface(func=mobius, u_range=(0, 2 * math.pi), v_range=(0, 1),
                           u_points=60, v_points=10, particle="minecraft:end_rod"),
        f"{output_dir}/mobius_strip",
    )

    # 螺旋球面（球面螺线）
    def sphere_spiral(t):
        phi = t * 20
        theta = math.pi * t
        r = 4
        return (r * math.sin(theta) * math.cos(phi), r * math.cos(theta), r * math.sin(theta) * math.sin(phi))

    ParticleCompiler.save(
        parametric_curve(func=sphere_spiral, t_range=(0, 1), points=500,
                         particle="minecraft:end_rod"),
        f"{output_dir}/sphere_spiral",
    )

    # 圆锥面
    ParticleCompiler.save(
        parametric_surface(
            func=lambda u, v: (v * 3 * math.cos(u), v * 5, v * 3 * math.sin(u)),
            u_range=(0, 2 * math.pi), v_range=(0, 1),
            u_points=36, v_points=10, particle="minecraft:flame",
        ),
        f"{output_dir}/cone",
    )

    # 阿基米德螺线（平面渐开螺旋）
    ParticleCompiler.save(
        parametric_curve(
            func=lambda t: (t / (2 * math.pi) * math.cos(t), 0, t / (2 * math.pi) * math.sin(t)),
            t_range=(0, 6 * math.pi), points=300, particle="minecraft:flame",
        ),
        f"{output_dir}/archimedes_spiral",
    )

    # ================================================================
    #  6. 动画效果
    # ================================================================

    print("\n=== 6. 动画效果 ===")

    # 6-1 静态心形，淡入 + 淡出消散（循环）
    ParticleCompiler.save_animation(
        ParticleAnimation.static(
            heart(size=4, points=120, particle="minecraft:heart").offset(y=5),
            duration=60, fade_in=10, fade_out=20,
        ),
        f"{output_dir}/anim_heart", func_path="p:anim_heart", loop=True,
    )

    # 6-2 扩散爆炸环：半径从 0 扩大到 8，最后消散
    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(
            shape_func=lambda p: circle(radius=0.5 + p * 8, points=int(40 + p * 160),
                                        particle="minecraft:flame")
                                  .with_radial_motion(speed=0.1 + p * 0.5),
            duration=30, fade_out=10,
        ),
        f"{output_dir}/anim_explosion", func_path="p:anim_explosion",
    )

    # 6-3 上升消散的螺旋
    def rising_helix(progress):
        h = helix(radius=2, height=1 + progress * 10, turns=2 + progress * 3,
                  points=200, particle="minecraft:end_rod")
        return h.with_motion(0, 0.2, 0, speed=0.1 + progress * 0.3)

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(rising_helix, duration=40, fade_out=15),
        f"{output_dir}/anim_helix_rise", func_path="p:anim_helix_rise",
    )

    # 6-4 脉冲球体：球体反复缩放呼吸（循环）
    def breathing_sphere(progress):
        scale = 2 + math.sin(progress * 2 * math.pi) * 1.5
        return sphere(radius=scale, u_points=20, v_points=10, particle="minecraft:end_rod")

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(breathing_sphere, duration=40, fade_out=0),
        f"{output_dir}/anim_breathing", func_path="p:anim_breathing", loop=True,
    )

    # 6-5 旋转五角星
    def spinning_star(progress):
        angle = progress * 2 * math.pi
        return star(outer_r=4, inner_r=1.5, n_points=5, samples=200,
                    particle="minecraft:crit").rotate_y(angle).offset(y=3)

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(spinning_star, duration=40, fade_out=0),
        f"{output_dir}/anim_spinning_star", func_path="p:anim_spinning_star", loop=True,
    )

    # 6-6 粒子喷泉：向上扩散的圆环序列
    def fountain(progress):
        layers = ParticleShape(particle="minecraft:cloud")
        n_layers = max(1, int(progress * 8))
        for i in range(n_layers):
            layer_progress = i / max(1, n_layers - 1)
            r = 0.5 + layer_progress * 3
            y = layer_progress * 6
            ring = circle(radius=r, points=int(30 + r * 20), particle="minecraft:cloud").offset(y=y)
            ring = ring.with_motion(0, 0.3 * (1 - layer_progress), 0, speed=0.2)
            layers = layers + ring
        return layers

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(fountain, duration=40, fade_out=10),
        f"{output_dir}/anim_fountain", func_path="p:anim_fountain",
    )

    # 6-7 传送门：旋转的圆环面 + 中心发光
    def portal_effect(progress):
        angle = progress * 4 * math.pi
        ring = torus(major_r=3, minor_r=0.5, u_points=32, v_points=12,
                     particle="minecraft:portal").rotate_x(angle * 0.3).rotate_z(angle * 0.2)
        center_glow = sphere(radius=0.5 + math.sin(progress * 6 * math.pi) * 0.3,
                             u_points=8, v_points=4, particle="minecraft:end_rod")
        return ring + center_glow

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(portal_effect, duration=60, fade_out=0),
        f"{output_dir}/anim_portal", func_path="p:anim_portal", loop=True,
    )

    # 6-8 火焰龙卷风：旋转上升的多层圆环
    def fire_tornado(progress):
        shape = ParticleShape(particle="minecraft:flame")
        n_layers = 12
        for i in range(n_layers):
            h = i * 0.8
            r = 3 - i * 0.2
            angle_offset = progress * 4 * math.pi + i * 0.5
            ring = circle(radius=max(0.3, r), points=int(40 + r * 15),
                          particle="minecraft:flame").rotate_y(angle_offset).offset(y=h)
            ring = ring.with_motion(0, 0.3 + i * 0.05, 0, speed=0.2)
            shape = shape + ring
        return shape

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(fire_tornado, duration=60, fade_out=15),
        f"{output_dir}/anim_fire_tornado", func_path="p:anim_fire_tornado",
    )

    # ================================================================
    #  7. 复合场景
    # ================================================================

    print("\n=== 7. 复合场景 ===")

    # 魔法阵：多层同心圆 + 六角星 + 竖直光柱
    inner_ring = circle(radius=2, points=60, particle="minecraft:enchanted_hit")
    outer_ring = circle(radius=5, points=120, particle="minecraft:enchanted_hit")
    hex_star = star(outer_r=4, inner_r=2.5, n_points=6, samples=300, particle="minecraft:end_rod")
    pillar = line(start=(0, 0, 0), end=(0, 8, 0), points=40, particle="minecraft:end_rod")
    ParticleCompiler.save(inner_ring + outer_ring + hex_star + pillar, f"{output_dir}/magic_circle")

    # 原子模型：中心球 + 三个正交轨道椭圆
    nucleus = sphere(radius=0.8, u_points=12, v_points=6, particle="minecraft:flame")
    orbit1 = circle(radius=4, points=100, particle="minecraft:end_rod")
    orbit2 = circle(radius=4, points=100, particle="minecraft:end_rod").rotate_x(math.pi / 3)
    orbit3 = circle(radius=4, points=100, particle="minecraft:end_rod").rotate_z(math.pi / 3)
    ParticleCompiler.save((nucleus + orbit1 + orbit2 + orbit3).offset(y=5), f"{output_dir}/atom_model")

    # 树形：圆锥树冠 + 直线树干
    trunk = line(start=(0, 0, 0), end=(0, 4, 0), points=30, particle="minecraft:composter")
    crown = ParticleShape(particle="minecraft:happy_villager")
    for layer_y in range(5):
        r = 3 - layer_y * 0.6
        if r > 0:
            ring = circle(radius=r, points=int(40 * r), particle="minecraft:happy_villager").offset(y=4 + layer_y)
            crown = crown + ring
    ParticleCompiler.save(trunk + crown, f"{output_dir}/tree")

    # 银河漩涡：多条阿基米德螺旋臂 + 中心光球
    galaxy = sphere(radius=1, u_points=10, v_points=5, particle="minecraft:end_rod")
    n_arms = 4
    for arm_i in range(n_arms):
        base_angle = 2 * math.pi * arm_i / n_arms
        arm = parametric_curve(
            func=lambda t, ba=base_angle: (
                (1 + t * 5) * math.cos(t * 2 + ba),
                (0.3 * math.sin(t * 4)),
                (1 + t * 5) * math.sin(t * 2 + ba),
            ),
            t_range=(0, 3), points=150, particle="minecraft:end_rod",
        )
        galaxy = galaxy + arm
    ParticleCompiler.save(galaxy, f"{output_dir}/galaxy")

    # 笼形结构：立方体的 12 条棱
    s = 3
    vertices = [
        (-s, -s, -s), (s, -s, -s), (s, -s, s), (-s, -s, s),
        (-s, s, -s), (s, s, -s), (s, s, s), (-s, s, s),
    ]
    edges = [
        (0,1),(1,2),(2,3),(3,0),
        (4,5),(5,6),(6,7),(7,4),
        (0,4),(1,5),(2,6),(3,7),
    ]
    wireframe = ParticleShape(particle="minecraft:end_rod")
    for a, b in edges:
        edge = line(start=vertices[a], end=vertices[b], points=20, particle="minecraft:end_rod")
        wireframe = wireframe + edge
    ParticleCompiler.save(wireframe.offset(y=5), f"{output_dir}/wireframe_cube")

    # ================================================================
    #  8. 正多面体与复杂几何
    # ================================================================

    print("\n=== 8. 正多面体与复杂几何 ===")

    # 8-1 五种正多面体（Platonic Solids）静态展示
    ParticleCompiler.save(
        tetrahedron(size=3, particle="minecraft:flame").offset(y=5),
        f"{output_dir}/tetrahedron",
    )
    ParticleCompiler.save(
        cube(size=3, particle="minecraft:soul_fire_flame").offset(y=5),
        f"{output_dir}/cube",
    )
    ParticleCompiler.save(
        octahedron(size=3, particle="minecraft:end_rod").offset(y=5),
        f"{output_dir}/octahedron",
    )
    ParticleCompiler.save(
        dodecahedron(size=3, particle="minecraft:cloud").offset(y=5),
        f"{output_dir}/dodecahedron",
    )
    ParticleCompiler.save(
        icosahedron(size=3, particle="minecraft:crit").offset(y=5),
        f"{output_dir}/icosahedron",
    )

    # 8-2 正多边形：正六边形和正八边形
    ParticleCompiler.save(
        polygon(n=6, radius=4, samples=180, particle="minecraft:end_rod"),
        f"{output_dir}/hexagon",
    )
    ParticleCompiler.save(
        polygon(n=8, radius=4, samples=200, particle="minecraft:soul_fire_flame"),
        f"{output_dir}/octagon",
    )

    # 8-3 正方体呼吸（放大缩小循环）
    def breathing_cube(progress):
        scale = 2 + math.sin(progress * 2 * math.pi) * 1.5
        return cube(size=scale, points_per_edge=15, particle="minecraft:end_rod").offset(y=5)

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(breathing_cube, duration=60, fade_out=0),
        f"{output_dir}/anim_cube_breathing", func_path="p:anim_cube_breath", loop=True,
    )

    # 8-4 旋转正二十面体
    def spinning_icosahedron(progress):
        angle = progress * 2 * math.pi
        return (icosahedron(size=3, particle="minecraft:soul_fire_flame")
                .rotate_y(angle).rotate_x(angle * 0.3).offset(y=5))

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(spinning_icosahedron, duration=60, fade_out=0),
        f"{output_dir}/anim_spinning_icosa", func_path="p:anim_spin_icosa", loop=True,
    )

    # 8-5 正方体 → 球体 平滑变形
    def cube_to_sphere_morph(progress):
        c = cube(size=3, points_per_edge=15, particle="minecraft:end_rod")
        pts = []
        for x, y, z in c.points:
            r = math.sqrt(x * x + y * y + z * z)
            if r > 0:
                sx, sy, sz = 3 * x / r, 3 * y / r, 3 * z / r
                t = 0.5 - 0.5 * math.cos(progress * 2 * math.pi)  # 来回 ease
                pts.append((x + (sx - x) * t, y + (sy - y) * t, z + (sz - z) * t))
            else:
                pts.append((x, y, z))
        return ParticleShape(pts, particle="minecraft:end_rod").offset(y=5)

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(cube_to_sphere_morph, duration=60, fade_out=0),
        f"{output_dir}/anim_cube_sphere", func_path="p:anim_cube_sphere", loop=True,
    )

    # 8-6 嵌套正多面体（俄罗斯套娃式）
    nested = (
        tetrahedron(size=1.5, particle="minecraft:flame")
        + cube(size=2.5, particle="minecraft:soul_fire_flame")
        + octahedron(size=3.5, particle="minecraft:end_rod")
        + icosahedron(size=5, particle="minecraft:cloud")
    ).offset(y=5)
    ParticleCompiler.save(nested, f"{output_dir}/nested_polyhedra")

    # 8-7 正十二面体爆炸（径向扩散）
    ParticleCompiler.save(
        dodecahedron(size=3, points_per_edge=12, particle="minecraft:flame")
            .offset(y=5)
            .with_radial_motion(speed=0.6, center=(0, 5, 0)),
        f"{output_dir}/dodecahedron_explode",
    )

    # 8-8 正多面体轮播（循环切换五种正多面体并旋转）
    def polyhedra_showcase(progress):
        builders = [
            lambda: tetrahedron(size=3, particle="minecraft:flame"),
            lambda: cube(size=3, particle="minecraft:soul_fire_flame"),
            lambda: octahedron(size=3, particle="minecraft:end_rod"),
            lambda: dodecahedron(size=3, particle="minecraft:cloud"),
            lambda: icosahedron(size=3, particle="minecraft:crit"),
        ]
        idx = min(int(progress * len(builders)), len(builders) - 1)
        angle = progress * 6 * math.pi
        return builders[idx]().rotate_y(angle).rotate_x(angle * 0.3).offset(y=5)

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(polyhedra_showcase, duration=100, fade_out=0),
        f"{output_dir}/anim_poly_showcase", func_path="p:anim_poly_show", loop=True,
    )

    # 8-9 正方体面填充（实心面）
    def cube_solid_surface(size=3, n_per_face=10, particle="minecraft:end_rod"):
        s = size / math.sqrt(3)
        faces = [
            ((-s, -s, -s), (2*s, 0, 0), (0, 2*s, 0)),  # z=-s
            ((-s, -s,  s), (2*s, 0, 0), (0, 2*s, 0)),  # z=+s
            ((-s, -s, -s), (0, 0, 2*s), (0, 2*s, 0)),  # x=-s
            (( s, -s, -s), (0, 0, 2*s), (0, 2*s, 0)),  # x=+s
            ((-s, -s, -s), (2*s, 0, 0), (0, 0, 2*s)),  # y=-s
            ((-s,  s, -s), (2*s, 0, 0), (0, 0, 2*s)),  # y=+s
        ]
        pts = []
        for origin, u_vec, v_vec in faces:
            for i in range(n_per_face):
                for j in range(n_per_face):
                    u = i / (n_per_face - 1)
                    v = j / (n_per_face - 1)
                    pts.append((
                        origin[0] + u * u_vec[0] + v * v_vec[0],
                        origin[1] + u * u_vec[1] + v * v_vec[1],
                        origin[2] + u * u_vec[2] + v * v_vec[2],
                    ))
        return ParticleShape(pts, particle)

    ParticleCompiler.save(
        cube_solid_surface(size=3, n_per_face=10, particle="minecraft:end_rod").offset(y=5),
        f"{output_dir}/cube_solid",
    )

    # 8-10 旋转正八面体 + 尾迹（轨迹残影效果）
    def octahedron_trail(progress):
        shape = ParticleShape(particle="minecraft:end_rod")
        n_ghosts = 5
        for g in range(n_ghosts):
            t = progress - g * 0.02
            if t < 0:
                continue
            angle = t * 4 * math.pi
            alpha = 1.0 - g * 0.18
            n_pts = max(5, int(20 * alpha))
            ghost = octahedron(size=3, points_per_edge=n_pts, particle="minecraft:end_rod")
            ghost = ghost.rotate_y(angle).rotate_z(angle * 0.5)
            shape = shape + ghost
        return shape.offset(y=5)

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(octahedron_trail, duration=60, fade_out=0),
        f"{output_dir}/anim_octa_trail", func_path="p:anim_octa_trail", loop=True,
    )

    # ================================================================
    #  9. 高级参数曲线与曲面
    # ================================================================

    print("\n=== 9. 高级参数曲线与曲面 ===")

    # 9-1 三叶结 (Trefoil Knot)
    def trefoil_knot(t):
        x = math.sin(t) + 2 * math.sin(2 * t)
        y = math.cos(t) - 2 * math.cos(2 * t)
        z = -math.sin(3 * t)
        return (x, y, z)

    ParticleCompiler.save(
        parametric_curve(trefoil_knot, t_range=(0, 2 * math.pi), points=400,
                         particle="minecraft:end_rod").offset(y=5),
        f"{output_dir}/trefoil_knot",
    )

    # 9-2 洛伦兹吸引子 (Lorenz Attractor) —— 数值积分
    def lorenz_attractor(n_points=2000, dt=0.005, sigma=10, rho=28, beta=8/3, scale=0.15):
        x, y, z = 1.0, 1.0, 1.0
        pts = []
        for _ in range(n_points):
            dx = sigma * (y - x)
            dy = x * (rho - z) - y
            dz = x * y - beta * z
            x += dx * dt
            y += dy * dt
            z += dz * dt
            pts.append((x * scale, z * scale - 3, y * scale))
        return ParticleShape(pts, particle="minecraft:end_rod")

    ParticleCompiler.save(
        lorenz_attractor().offset(y=5),
        f"{output_dir}/lorenz_attractor",
    )

    # 9-3 克莱因瓶 (Klein Bottle) 参数曲面
    def klein_bottle(u, v):
        if u < math.pi:
            x = 3 * math.cos(u) * (1 + math.sin(u)) + 2 * (1 - math.cos(u) / 2) * math.cos(u) * math.cos(v)
            z = -8 * math.sin(u) - 2 * (1 - math.cos(u) / 2) * math.sin(u) * math.cos(v)
        else:
            x = 3 * math.cos(u) * (1 + math.sin(u)) + 2 * (1 - math.cos(u) / 2) * math.cos(v + math.pi)
            z = -8 * math.sin(u)
        y = -2 * (1 - math.cos(u) / 2) * math.sin(v)
        return (x * 0.3, y * 0.3, z * 0.3)

    ParticleCompiler.save(
        parametric_surface(klein_bottle, u_range=(0, 2 * math.pi), v_range=(0, 2 * math.pi),
                           u_points=50, v_points=20, particle="minecraft:end_rod").offset(y=5),
        f"{output_dir}/klein_bottle",
    )

    # 9-4 圆环结 (Torus Knot) p=2, q=3
    def torus_knot(t, p=2, q=3, R=3, r=1):
        angle = q * t
        x = (R + r * math.cos(angle)) * math.cos(p * t)
        y = r * math.sin(angle)
        z = (R + r * math.cos(angle)) * math.sin(p * t)
        return (x, y, z)

    ParticleCompiler.save(
        parametric_curve(torus_knot, t_range=(0, 2 * math.pi), points=500,
                         particle="minecraft:soul_fire_flame").offset(y=5),
        f"{output_dir}/torus_knot",
    )

    # 9-5 球面谐函数可视化（球面变形 Y_3^2 模式）
    def spherical_harmonic(u, v, amplitude=0.6):
        theta, phi_angle = v, u
        r_base = 3
        # Y_3^2 球面谐函数的简化形式
        deformation = amplitude * (math.sin(theta) ** 2) * math.cos(2 * phi_angle)
        r = r_base + deformation
        x = r * math.sin(theta) * math.cos(phi_angle)
        y = r * math.cos(theta)
        z = r * math.sin(theta) * math.sin(phi_angle)
        return (x, y, z)

    ParticleCompiler.save(
        parametric_surface(spherical_harmonic, u_range=(0, 2 * math.pi), v_range=(0, math.pi),
                           u_points=40, v_points=20, particle="minecraft:end_rod").offset(y=5),
        f"{output_dir}/spherical_harmonic",
    )

    # ================================================================
    #  10. 高级动画
    # ================================================================

    print("\n=== 10. 高级动画 ===")

    # 10-1 正多面体逐级生长（从正四面体到正二十面体连续变换）
    def polyhedra_growth(progress):
        stages = [
            (0.0, lambda: tetrahedron(size=3, particle="minecraft:flame")),
            (0.2, lambda: cube(size=3, particle="minecraft:soul_fire_flame")),
            (0.4, lambda: octahedron(size=3, particle="minecraft:end_rod")),
            (0.6, lambda: dodecahedron(size=3, particle="minecraft:cloud")),
            (0.8, lambda: icosahedron(size=3, particle="minecraft:crit")),
        ]
        for i in range(len(stages) - 1, -1, -1):
            if progress >= stages[i][0]:
                shape = stages[i][1]()
                # 出现时从小放大
                local_p = (progress - stages[i][0]) / 0.2
                scale = min(1.0, local_p * 2) if local_p < 0.5 else 1.0
                return shape.scale(scale).offset(y=5)
        return tetrahedron(size=0.1, particle="minecraft:flame").offset(y=5)

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(polyhedra_growth, duration=100, fade_out=10),
        f"{output_dir}/anim_poly_growth", func_path="p:anim_poly_growth",
    )

    # 10-2 三叶结旋转发光
    def spinning_trefoil(progress):
        angle = progress * 2 * math.pi
        knot = parametric_curve(trefoil_knot, t_range=(0, 2 * math.pi), points=300,
                                particle="minecraft:end_rod")
        return knot.rotate_y(angle).rotate_x(math.pi / 6).offset(y=5)

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(spinning_trefoil, duration=60, fade_out=0),
        f"{output_dir}/anim_spinning_knot", func_path="p:anim_spin_knot", loop=True,
    )

    # 10-3 双正方体对旋（两个正方体反向旋转 + 呼吸缩放）
    def dual_cube_spin(progress):
        angle = progress * 2 * math.pi
        scale = 2.5 + math.sin(progress * 4 * math.pi) * 0.8
        c1 = cube(size=scale, points_per_edge=12, particle="minecraft:flame").rotate_y(angle).rotate_x(0.3)
        c2 = cube(size=scale, points_per_edge=12, particle="minecraft:soul_fire_flame").rotate_y(-angle).rotate_z(0.3)
        return (c1 + c2).offset(y=5)

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(dual_cube_spin, duration=60, fade_out=0),
        f"{output_dir}/anim_dual_cube", func_path="p:anim_dual_cube", loop=True,
    )

    # 10-4 正二十面体内爆收缩 → 爆炸扩散
    def icosa_implosion(progress):
        if progress < 0.5:
            # 收缩阶段
            t = progress / 0.5
            scale = 4 * (1 - t) + 0.3 * t
            return icosahedron(size=scale, points_per_edge=15, particle="minecraft:portal").offset(y=5)
        else:
            # 爆炸阶段
            t = (progress - 0.5) / 0.5
            scale = 0.3 + t * 6
            shape = icosahedron(size=scale, points_per_edge=15, particle="minecraft:flame")
            return shape.offset(y=5).with_radial_motion(speed=0.3 + t * 0.8, center=(0, 5, 0))

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(icosa_implosion, duration=60, fade_out=10),
        f"{output_dir}/anim_icosa_implode", func_path="p:anim_icosa_impl",
    )

    # 10-5 粒子矩阵立方体（面填充 + 旋转）
    def rotating_solid_cube(progress):
        angle = progress * 2 * math.pi
        return (cube_solid_surface(size=2.5, n_per_face=8, particle="minecraft:end_rod")
                .rotate_y(angle).rotate_x(angle * 0.6).offset(y=5))

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(rotating_solid_cube, duration=60, fade_out=0),
        f"{output_dir}/anim_solid_cube_spin", func_path="p:anim_solidcube", loop=True,
    )

    # 10-6 DNA 双螺旋 + 正八面体节点装饰
    def dna_decorated(progress):
        angle_offset = progress * 2 * math.pi
        h1 = helix(radius=2, height=12, turns=4, points=250,
                    particle="minecraft:end_rod").rotate_y(angle_offset)
        h2 = helix(radius=2, height=12, turns=4, points=250,
                    particle="minecraft:soul_fire_flame").rotate_y(angle_offset + math.pi)
        # 在螺旋节点处放置小正八面体
        decorations = ParticleShape(particle="minecraft:flame")
        n_nodes = 8
        for i in range(n_nodes):
            t = i / n_nodes
            y = t * 12
            theta = 4 * 2 * math.pi * t + angle_offset
            x, z = 2 * math.cos(theta), 2 * math.sin(theta)
            node = octahedron(size=0.4, points_per_edge=5, particle="minecraft:flame").offset(x=x, y=y, z=z)
            decorations = decorations + node
        return h1 + h2 + decorations

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(dna_decorated, duration=60, fade_out=0),
        f"{output_dir}/anim_dna_decorated", func_path="p:anim_dna_deco", loop=True,
    )

    # ================================================================
    #  11. 粒子选项（SNBT 参数）
    # ================================================================

    print("\n=== 11. 粒子选项 ===")

    # 11-1 红色灰尘圆环
    p_type, p_opts = dust(color="#FF0000", scale=2.0)
    ParticleCompiler.save(
        circle(radius=3, points=80, particle=p_type).with_options(**p_opts),
        f"{output_dir}/dust_circle",
    )

    # 11-2 渐变灰尘球体（红→蓝）
    p_type, p_opts = dust_transition(from_color="#FF0000", to_color="#0000FF", scale=1.5)
    ParticleCompiler.save(
        sphere(radius=3, u_points=24, v_points=12, particle=p_type).with_options(**p_opts).offset(y=5),
        f"{output_dir}/dust_transition_sphere",
    )

    # 11-3 方块粒子螺旋
    p_type, p_opts = block_particle("minecraft:diamond_block")
    ParticleCompiler.save(
        helix(radius=2, height=8, turns=3, points=200, particle=p_type).with_options(**p_opts),
        f"{output_dir}/block_helix",
    )

    # 11-4 物品粒子星形
    p_type, p_opts = item_particle("minecraft:nether_star")
    ParticleCompiler.save(
        star(outer_r=4, inner_r=1.5, n_points=5, samples=300, particle=p_type).with_options(**p_opts).offset(y=3),
        f"{output_dir}/item_star",
    )

    # 11-5 实体效果粒子心形（带半透明紫色）
    p_type, p_opts = entity_effect(color="#AA00FF", alpha=0.6)
    ParticleCompiler.save(
        heart(size=4, points=160, particle=p_type).with_options(**p_opts).offset(y=5),
        f"{output_dir}/entity_effect_heart",
    )

    # 11-6 彩虹灰尘环动画（颜色随时间渐变）
    def rainbow_dust_ring(progress):
        import colorsys
        r, g, b = colorsys.hsv_to_rgb(progress, 1.0, 1.0)
        p_type, p_opts = dust(color=(r, g, b), scale=1.5)
        return circle(radius=3 + math.sin(progress * 4 * math.pi), points=100,
                      particle=p_type).with_options(**p_opts).offset(y=3)

    ParticleCompiler.save_animation(
        ParticleAnimation.expanding(rainbow_dust_ring, duration=60, fade_out=0),
        f"{output_dir}/anim_rainbow_dust", func_path="p:anim_rainbow_dust", loop=True,
    )

    # ================================================================
    #  完成
    # ================================================================

    print(f"\n所有文件已保存到 {os.path.abspath(output_dir)}/ 目录")
    print("\n使用方法:")
    print("  1. 将生成的 .mcfunction 文件放入数据包 data/<namespace>/function/ 目录")
    print("  2. 单帧图形: /function <namespace>:<name>")
    print("  3. 动画: /function <namespace>:<name>/main")
    print("  4. 停止动画: /function <namespace>:<name>/stop")


if __name__ == "__main__":
    main()
