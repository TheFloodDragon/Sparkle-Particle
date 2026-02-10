"""
Sparkle — Minecraft 粒子命令生成库
通过数学函数生成 .mcfunction 文件，用粒子命令构成各种图形与动画。
目标版本：Java Edition 1.20+
"""

from .shape import ParticleShape, Point3D
from .animation import ParticleAnimation
from .compiler import ParticleCompiler
from .sps import save as save_sps, load as load_sps
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
    # 正多面体与多边形
    polygon,
    tetrahedron,
    cube,
    octahedron,
    dodecahedron,
    icosahedron,
)

__all__ = [
    # 核心类
    "ParticleShape",
    "ParticleAnimation",
    "ParticleCompiler",
    # 类型
    "Point3D",
    # SPS 格式
    "save_sps",
    "load_sps",
    # 基础图形
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
    # 正多面体与多边形
    "polygon",
    "tetrahedron",
    "cube",
    "octahedron",
    "dodecahedron",
    "icosahedron",
]
