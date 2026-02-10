"""
Sparkle — Minecraft 粒子命令生成库
通过数学函数生成 .mcfunction 文件，用粒子命令构成各种图形与动画。
目标版本：Java Edition 1.20+
"""

from .shape import ParticleShape, Point3D
from .animation import ParticleAnimation
from .compiler import ParticleCompiler
from .primitives import (
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

__all__ = [
    # 核心类
    "ParticleShape",
    "ParticleAnimation",
    "ParticleCompiler",
    # 类型
    "Point3D",
    # 几何图元
    "circle",
    "sphere",
    "helix",
    "heart",
    "sine_wave",
    "star",
    "torus",
    "line",
    "parametric_curve",
    "parametric_surface",
]
