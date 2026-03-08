"""独立炫酷粒子动画示例。"""

from __future__ import annotations

import colorsys
import math

from _example_utils import OUTPUT_ROOT, bootstrap_repo_path

bootstrap_repo_path()

from sparkle import (  # noqa: E402
    ParticleAnimation,
    ParticleCompiler,
    ParticleShape,
    dust_transition,
    helix,
    sphere,
    star,
    torus,
)


DURATION_TICKS = 280  # 14 秒
OUTPUT_DIR = OUTPUT_ROOT / "glamorous_particle"
FUNC_PATH = "p:glamorous_particle"


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    t = clamp((value - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def hsv_hex(hue: float, saturation: float, value: float) -> str:
    red, green, blue = colorsys.hsv_to_rgb(hue % 1.0, clamp(saturation), clamp(value))
    return f"#{int(red * 255):02X}{int(green * 255):02X}{int(blue * 255):02X}"


def add_layer(scene: ParticleShape, layer: ParticleShape, density: float) -> ParticleShape:
    if density <= 0.02:
        return scene
    return scene + layer.sampled(clamp(density))


def matrix_panel(size: float, lines: int, samples: int, warp: float, phase: float) -> ParticleShape:
    points = []
    for i in range(lines + 1):
        u = -size + 2.0 * size * i / max(1, lines)
        for j in range(samples):
            v = -size + 2.0 * size * j / max(1, samples - 1)
            w = warp * math.sin((u + v) * 1.9 + phase)
            points.append((u, v, w))
            points.append((v, u, -w))
    return ParticleShape(points)


def scene_at(progress: float) -> ParticleShape:
    tau = math.tau
    pulse = 0.5 + 0.5 * math.sin(progress * tau * 6.0)
    spin = progress * tau

    intro = 1.0 - smoothstep(0.20, 0.38, progress)
    middle = smoothstep(0.12, 0.34, progress) * (1.0 - smoothstep(0.62, 0.84, progress))
    finale = smoothstep(0.58, 0.84, progress)

    from_color = hsv_hex(0.56 + 0.22 * math.sin(spin * 0.8), 0.78, 1.0)
    to_color = hsv_hex(0.92 + 0.18 * math.sin(spin * 1.4 + 1.2), 0.70, 1.0)
    particle, options = dust_transition(from_color=from_color, to_color=to_color, scale=0.9 + pulse * 0.55)

    scene = ParticleShape(particle=particle, options=options)

    core = sphere(radius=0.8 + intro * 0.7 + pulse * 0.3, u_points=14, v_points=8).offset(y=4.8)
    scene = add_layer(scene, core, 0.45 + 0.35 * intro)

    orbit_radius = 4.2 + 1.2 * middle + 0.7 * math.sin(spin * 1.3)
    panel_density = 0.28 + 0.55 * (middle + 0.3 * finale)

    for index in range(4):
        phase = spin * 1.45 + index * (tau / 4.0)
        drift = 0.55 * math.sin(spin * 1.1 + index * 0.8)
        x = (orbit_radius + drift) * math.cos(phase)
        z = (orbit_radius + drift) * math.sin(phase)
        y = 3.4 + 1.9 * math.sin(spin * 1.7 + index * 0.9)

        panel = matrix_panel(
            size=2.1 + 0.55 * pulse,
            lines=8,
            samples=14,
            warp=0.18 + 0.28 * middle + 0.12 * finale,
            phase=spin * 5.0 + index * 1.3,
        )
        panel = panel.rotate_y(phase + math.pi / 2.0).rotate_x(0.18 * math.sin(spin * 2.2 + index)).offset(x=x, y=y, z=z)
        scene = add_layer(scene, panel, panel_density)

        seed = torus(
            major_r=0.55 + 0.22 * pulse,
            minor_r=0.12 + 0.08 * middle,
            u_points=14,
            v_points=7,
        ).rotate_y(spin * 5.5 + index).offset(x=x, y=y, z=z)
        scene = add_layer(scene, seed, 0.30 + 0.45 * (middle + finale))

    helix_points = 140 + int(80 * (middle + finale * 0.8))
    helix_height = 3.2 + 4.8 * (middle + finale * 0.7)
    helix_turns = 2.4 + 3.6 * (middle + finale)
    radius = 1.1 + 1.3 * (middle + finale * 0.4)

    ribbon_a = helix(radius=radius, height=helix_height, turns=helix_turns, points=helix_points).offset(y=1.6).rotate_y(spin * 4.8)
    ribbon_b = helix(radius=radius, height=helix_height, turns=helix_turns, points=helix_points).offset(y=1.6).rotate_y(spin * 4.8 + math.pi)
    scene = add_layer(scene, ribbon_a, 0.10 + 0.55 * (middle + finale * 0.2))
    scene = add_layer(scene, ribbon_b, 0.10 + 0.55 * (middle + finale * 0.2))

    crown = star(
        outer_r=5.2 + 0.8 * finale + 0.4 * math.sin(spin * 3.0),
        inner_r=2.1 + 0.35 * middle,
        n_points=8,
        samples=300,
    ).rotate_x(math.pi / 2).rotate_y(spin * 3.8).offset(y=3.8)
    scene = add_layer(scene, crown, 0.08 + 0.48 * (middle + finale * 0.6))

    bloom = sphere(radius=1.5 + 4.8 * finale, u_points=18, v_points=10).offset(y=4.0)
    scene = add_layer(scene, bloom, 0.35 * finale)
    return scene


def build_animation() -> ParticleAnimation:
    return ParticleAnimation.expanding(scene_at, duration=DURATION_TICKS, fade_out=0)


def main() -> None:
    output_dir = ParticleCompiler.save_animation(
        build_animation(),
        str(OUTPUT_DIR),
        func_path=FUNC_PATH,
        loop=True,
    )
    print(f"已保存炫酷动画到: {output_dir}")
    print(f"时长: {DURATION_TICKS} tick ({DURATION_TICKS / 20:.1f}s)")
    print(f"游戏内调用: /function {FUNC_PATH}/main")


if __name__ == "__main__":
    main()
