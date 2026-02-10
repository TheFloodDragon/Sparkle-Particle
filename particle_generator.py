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
    cube = ParticleShape(particle="minecraft:end_rod")
    for a, b in edges:
        edge = line(start=vertices[a], end=vertices[b], points=20, particle="minecraft:end_rod")
        cube = cube + edge
    ParticleCompiler.save(cube.offset(y=5), f"{output_dir}/wireframe_cube")

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
