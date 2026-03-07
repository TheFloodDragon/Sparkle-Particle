"""
Standalone Sparkle animation generator.

Creates a 14-second (280 ticks) "gorgeous" looping particle show using the
current Sparkle API and exports it as mcfunction files.
"""

import colorsys
import math

from sparkle import (
    ParticleAnimation,
    ParticleCompiler,
    ParticleShape,
    helix,
    sphere,
    star,
    torus,
    dust_transition,
)


DURATION_TICKS = 280  # 14s at 20 ticks/s
OUTPUT_DIR = "output/glamorous_particle"
FUNC_PATH = "p:glamorous_particle"


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge0 == edge1:
        return 1.0 if x >= edge1 else 0.0
    t = clamp((x - edge0) / (edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def hsv_hex(h: float, s: float, v: float) -> str:
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, clamp(s), clamp(v))
    return f"#{int(r * 255):02X}{int(g * 255):02X}{int(b * 255):02X}"


def add_layer(scene: ParticleShape, layer: ParticleShape, density: float) -> ParticleShape:
    if density <= 0.02:
        return scene
    return scene + layer.sampled(clamp(density, 0.0, 1.0))


def matrix_panel(size: float, lines: int, samples: int, warp: float, phase: float) -> ParticleShape:
    pts = []
    for i in range(lines + 1):
        u = -size + 2.0 * size * i / max(1, lines)
        for j in range(samples):
            v = -size + 2.0 * size * j / max(1, samples - 1)
            w = warp * math.sin((u + v) * 1.9 + phase)
            pts.append((u, v, w))
            pts.append((v, u, -w))
    return ParticleShape(pts)


def scene_at(progress: float) -> ParticleShape:
    tau = 2.0 * math.pi
    pulse = 0.5 + 0.5 * math.sin(progress * tau * 6.0)
    spin = progress * tau

    intro = 1.0 - smoothstep(0.20, 0.38, progress)
    mid = smoothstep(0.12, 0.34, progress) * (1.0 - smoothstep(0.62, 0.84, progress))
    finale = smoothstep(0.58, 0.84, progress)

    color_a = hsv_hex(0.56 + 0.22 * math.sin(spin * 0.8), 0.78, 1.0)
    color_b = hsv_hex(0.92 + 0.18 * math.sin(spin * 1.4 + 1.2), 0.70, 1.0)
    particle, opts = dust_transition(from_color=color_a, to_color=color_b, scale=0.9 + pulse * 0.55)

    scene = ParticleShape(particle=particle, options=opts)

    core = sphere(radius=0.8 + intro * 0.7 + pulse * 0.3, u_points=14, v_points=8).offset(y=4.8)
    scene = add_layer(scene, core, 0.45 + 0.35 * intro)

    orbit_radius = 4.2 + 1.2 * mid + 0.7 * math.sin(spin * 1.3)
    panel_density = 0.28 + 0.55 * (mid + 0.3 * finale)

    for k in range(4):
        phase = spin * 1.45 + k * (tau / 4.0)
        drift = 0.55 * math.sin(spin * 1.1 + k * 0.8)
        x = (orbit_radius + drift) * math.cos(phase)
        z = (orbit_radius + drift) * math.sin(phase)
        y = 3.4 + 1.9 * math.sin(spin * 1.7 + k * 0.9)

        panel = matrix_panel(
            size=2.1 + 0.55 * pulse,
            lines=8,
            samples=14,
            warp=0.18 + 0.28 * mid + 0.12 * finale,
            phase=spin * 5.0 + k * 1.3,
        )
        panel = (
            panel.rotate_y(phase + math.pi / 2.0)
            .rotate_x(0.18 * math.sin(spin * 2.2 + k))
            .offset(x=x, y=y, z=z)
        )
        scene = add_layer(scene, panel, panel_density)

        seed = torus(
            major_r=0.55 + 0.22 * pulse,
            minor_r=0.12 + 0.08 * mid,
            u_points=14,
            v_points=7,
        ).rotate_y(spin * 5.5 + k).offset(x=x, y=y, z=z)
        scene = add_layer(scene, seed, 0.30 + 0.45 * (mid + finale))

    helix_points = 140 + int(80 * (mid + finale * 0.8))
    helix_height = 3.2 + 4.8 * (mid + finale * 0.7)
    helix_turns = 2.4 + 3.6 * (mid + finale)
    ribbon_a = helix(
        radius=1.1 + 1.3 * (mid + finale * 0.4),
        height=helix_height,
        turns=helix_turns,
        points=helix_points,
    ).offset(y=1.6).rotate_y(spin * 4.8)
    scene = add_layer(scene, ribbon_a, 0.10 + 0.55 * (mid + finale * 0.2))

    ribbon_b = helix(
        radius=1.1 + 1.3 * (mid + finale * 0.4),
        height=helix_height,
        turns=helix_turns,
        points=helix_points,
    ).offset(y=1.6).rotate_y(spin * 4.8 + math.pi)
    scene = add_layer(scene, ribbon_b, 0.10 + 0.55 * (mid + finale * 0.2))

    crown = star(
        outer_r=5.2 + 0.8 * finale + 0.4 * math.sin(spin * 3.0),
        inner_r=2.1 + 0.35 * mid,
        n_points=8,
        samples=300,
    ).rotate_x(math.pi / 2).rotate_y(spin * 3.8).offset(y=3.8)
    scene = add_layer(scene, crown, 0.08 + 0.48 * (mid + finale * 0.6))

    bloom = sphere(
        radius=1.5 + 4.8 * finale,
        u_points=18,
        v_points=10,
    ).offset(y=4.0)
    scene = add_layer(scene, bloom, 0.35 * finale)

    return scene


def build_animation() -> ParticleAnimation:
    return ParticleAnimation.expanding(scene_at, duration=DURATION_TICKS, fade_out=0)


def main():
    animation = build_animation()
    out_dir = ParticleCompiler.save_animation(
        animation,
        OUTPUT_DIR,
        func_path=FUNC_PATH,
        loop=True,
    )
    print(f"Saved gorgeous animation to: {out_dir}")
    print(f"Duration: {DURATION_TICKS} ticks ({DURATION_TICKS / 20:.1f}s)")
    print(f"Run in Minecraft: /function {FUNC_PATH}/main")


if __name__ == "__main__":
    main()
