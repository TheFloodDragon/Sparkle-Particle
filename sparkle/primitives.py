"""
几何图元：提供常用几何形状的工厂函数。
"""

import math
from typing import Callable, Tuple

from .shape import ParticleShape, Point3D


# ============================================================
#  基础图形
# ============================================================


def circle(
    radius: float = 3.0,
    points: int = 64,
    axis: str = "y",
    particle: str = "minecraft:flame",
) -> ParticleShape:
    """生成圆形。axis 指定法线方向：'x', 'y' 或 'z'。"""
    pts = []
    for i in range(points):
        t = 2 * math.pi * i / points
        a, b = math.cos(t) * radius, math.sin(t) * radius
        if axis == "y":
            pts.append((a, 0.0, b))
        elif axis == "x":
            pts.append((0.0, a, b))
        else:
            pts.append((a, b, 0.0))
    return ParticleShape(pts, particle)


def sphere(
    radius: float = 3.0,
    u_points: int = 32,
    v_points: int = 16,
    particle: str = "minecraft:end_rod",
) -> ParticleShape:
    """生成球体表面。"""
    pts = []
    for i in range(u_points):
        u = 2 * math.pi * i / u_points
        for j in range(v_points):
            v = math.pi * j / (v_points - 1)
            x = radius * math.sin(v) * math.cos(u)
            y = radius * math.cos(v)
            z = radius * math.sin(v) * math.sin(u)
            pts.append((x, y, z))
    return ParticleShape(pts, particle)


def helix(
    radius: float = 2.0,
    height: float = 10.0,
    turns: float = 3.0,
    points: int = 200,
    particle: str = "minecraft:flame",
) -> ParticleShape:
    """生成螺旋线。"""
    pts = []
    for i in range(points):
        t = turns * 2 * math.pi * i / (points - 1)
        x = radius * math.cos(t)
        y = height * i / (points - 1)
        z = radius * math.sin(t)
        pts.append((x, y, z))
    return ParticleShape(pts, particle)


def heart(
    size: float = 3.0,
    points: int = 120,
    particle: str = "minecraft:heart",
) -> ParticleShape:
    """生成心形曲线（竖直平面）。"""
    pts = []
    for i in range(points):
        t = 2 * math.pi * i / points
        x = size * 16 * math.sin(t) ** 3 / 16
        y = size * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16
        pts.append((x, y, 0.0))
    return ParticleShape(pts, particle)


def sine_wave(
    amplitude: float = 2.0,
    wavelength: float = 5.0,
    length: float = 20.0,
    points: int = 200,
    particle: str = "minecraft:flame",
) -> ParticleShape:
    """生成正弦波（沿 X 轴延伸，Y 轴振荡）。"""
    pts = []
    for i in range(points):
        x = length * i / (points - 1)
        y = amplitude * math.sin(2 * math.pi * x / wavelength)
        pts.append((x, y, 0.0))
    return ParticleShape(pts, particle)


def star(
    outer_r: float = 4.0,
    inner_r: float = 1.5,
    n_points: int = 5,
    samples: int = 200,
    particle: str = "minecraft:crit",
) -> ParticleShape:
    """生成星形（水平平面）。"""
    vertices = []
    for i in range(n_points * 2):
        angle = math.pi * i / n_points - math.pi / 2
        r = outer_r if i % 2 == 0 else inner_r
        vertices.append((r * math.cos(angle), 0.0, r * math.sin(angle)))
    vertices.append(vertices[0])

    total_edges = len(vertices) - 1
    pts = []
    for i in range(samples):
        t = total_edges * i / samples
        edge_idx = int(t)
        frac = t - edge_idx
        if edge_idx >= total_edges:
            edge_idx = total_edges - 1
            frac = 1.0
        x0, y0, z0 = vertices[edge_idx]
        x1, y1, z1 = vertices[edge_idx + 1]
        pts.append((
            x0 + (x1 - x0) * frac,
            y0 + (y1 - y0) * frac,
            z0 + (z1 - z0) * frac,
        ))
    return ParticleShape(pts, particle)


def torus(
    major_r: float = 4.0,
    minor_r: float = 1.5,
    u_points: int = 48,
    v_points: int = 24,
    particle: str = "minecraft:end_rod",
) -> ParticleShape:
    """生成圆环面（甜甜圈）。"""
    pts = []
    for i in range(u_points):
        u = 2 * math.pi * i / u_points
        for j in range(v_points):
            v = 2 * math.pi * j / v_points
            x = (major_r + minor_r * math.cos(v)) * math.cos(u)
            y = minor_r * math.sin(v)
            z = (major_r + minor_r * math.cos(v)) * math.sin(u)
            pts.append((x, y, z))
    return ParticleShape(pts, particle)


def line(
    start: Point3D = (0, 0, 0),
    end: Point3D = (10, 5, 0),
    points: int = 50,
    particle: str = "minecraft:flame",
) -> ParticleShape:
    """生成直线段。"""
    pts = []
    for i in range(points):
        t = i / (points - 1) if points > 1 else 0
        x = start[0] + (end[0] - start[0]) * t
        y = start[1] + (end[1] - start[1]) * t
        z = start[2] + (end[2] - start[2]) * t
        pts.append((x, y, z))
    return ParticleShape(pts, particle)


# ============================================================
#  自定义参数方程
# ============================================================


def parametric_curve(
    func: Callable[[float], Point3D],
    t_range: Tuple[float, float] = (0, 2 * math.pi),
    points: int = 200,
    particle: str = "minecraft:flame",
) -> ParticleShape:
    """
    通过自定义参数方程生成曲线。
    func: 接收参数 t，返回 (x, y, z) 的函数
    t_range: 参数范围 (t_min, t_max)
    """
    t_min, t_max = t_range
    pts = []
    for i in range(points):
        t = t_min + (t_max - t_min) * i / (points - 1) if points > 1 else t_min
        pts.append(func(t))
    return ParticleShape(pts, particle)


def parametric_surface(
    func: Callable[[float, float], Point3D],
    u_range: Tuple[float, float] = (0, 2 * math.pi),
    v_range: Tuple[float, float] = (0, math.pi),
    u_points: int = 32,
    v_points: int = 16,
    particle: str = "minecraft:flame",
) -> ParticleShape:
    """
    通过自定义参数方程生成曲面。
    func: 接收参数 (u, v)，返回 (x, y, z) 的函数
    """
    u_min, u_max = u_range
    v_min, v_max = v_range
    pts = []
    for i in range(u_points):
        u = u_min + (u_max - u_min) * i / (u_points - 1) if u_points > 1 else u_min
        for j in range(v_points):
            v = v_min + (v_max - v_min) * j / (v_points - 1) if v_points > 1 else v_min
            pts.append(func(u, v))
    return ParticleShape(pts, particle)
