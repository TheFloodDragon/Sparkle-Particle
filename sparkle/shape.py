"""
核心数据结构：ParticleShape —— 粒子图形的 3D 点集与空间变换。
纯几何模块，不包含任何 Minecraft 特定逻辑。
"""

import math
from typing import Callable, List, Optional, Tuple

Point3D = Tuple[float, float, float]


class ParticleShape:
    """粒子图形，存储一组3D点及其粒子属性，提供空间变换与组合操作。"""

    def __init__(
        self,
        points: List[Point3D] = None,
        particle: str = "minecraft:flame",
        delta: Tuple[float, float, float] = (0, 0, 0),
        speed: float = 0,
        count: int = 1,
        motions: Optional[List[Point3D]] = None,
    ):
        self.points: List[Point3D] = points or []
        self.particle = particle
        self.delta = delta
        self.speed = speed
        self.count = count
        self.motions = motions  # 不为 None 时启用逐点运动模式 (count=0)

    def _copy(self) -> "ParticleShape":
        return ParticleShape(
            list(self.points), self.particle, self.delta, self.speed, self.count,
            list(self.motions) if self.motions is not None else None,
        )

    # ----------------------------------------------------------
    #  运动设置
    # ----------------------------------------------------------

    def with_motion(self, dx: float, dy: float, dz: float, speed: float = 1.0) -> "ParticleShape":
        """
        为所有粒子设置统一运动方向。
        使用 count=0 模式：delta 变为运动向量，speed 为速度倍率。
        """
        new = self._copy()
        new.motions = [(dx, dy, dz)] * len(new.points)
        new.speed = speed
        return new

    def with_radial_motion(self, speed: float = 1.0, center: Point3D = (0, 0, 0)) -> "ParticleShape":
        """为每个粒子设置从中心向外辐射的运动（爆炸效果）。"""
        new = self._copy()
        new.motions = []
        cx, cy, cz = center
        for px, py, pz in new.points:
            dx, dy, dz = px - cx, py - cy, pz - cz
            length = math.sqrt(dx * dx + dy * dy + dz * dz)
            if length > 0:
                new.motions.append((dx / length, dy / length, dz / length))
            else:
                new.motions.append((0, 1, 0))
        new.speed = speed
        return new

    def with_tangent_motion(self, speed: float = 1.0, axis: str = "y") -> "ParticleShape":
        """
        为每个粒子设置切线方向运动（沿曲线流动效果）。
        axis: 用于计算切线的旋转轴 ('x', 'y', 'z')。
        """
        new = self._copy()
        new.motions = []
        for i, (px, py, pz) in enumerate(new.points):
            j = (i + 1) % len(new.points)
            nx, ny, nz = new.points[j]
            dx, dy, dz = nx - px, ny - py, nz - pz
            length = math.sqrt(dx * dx + dy * dy + dz * dz)
            if length > 0:
                new.motions.append((dx / length, dy / length, dz / length))
            else:
                new.motions.append((0, 0, 0))
        new.speed = speed
        return new

    def with_custom_motion(self, func: Callable[[float, float, float], Point3D], speed: float = 1.0) -> "ParticleShape":
        """
        通过自定义函数为每个粒子设置运动方向。
        func(x, y, z) -> (dx, dy, dz)
        """
        new = self._copy()
        new.motions = [func(px, py, pz) for px, py, pz in new.points]
        new.speed = speed
        return new

    # ----------------------------------------------------------
    #  空间变换
    # ----------------------------------------------------------

    def offset(self, x: float = 0, y: float = 0, z: float = 0) -> "ParticleShape":
        """对所有点施加偏移（运动向量不变），返回新的 ParticleShape。"""
        new = self._copy()
        new.points = [(px + x, py + y, pz + z) for px, py, pz in self.points]
        return new

    def scale(self, factor: float) -> "ParticleShape":
        """对所有点进行缩放（运动向量不变），返回新的 ParticleShape。"""
        new = self._copy()
        new.points = [(px * factor, py * factor, pz * factor) for px, py, pz in self.points]
        return new

    def rotate_y(self, angle: float) -> "ParticleShape":
        """绕 Y 轴旋转（弧度），同时旋转运动向量。"""
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        new = self._copy()
        new.points = [
            (px * cos_a + pz * sin_a, py, -px * sin_a + pz * cos_a)
            for px, py, pz in self.points
        ]
        if new.motions is not None:
            new.motions = [
                (mx * cos_a + mz * sin_a, my, -mx * sin_a + mz * cos_a)
                for mx, my, mz in new.motions
            ]
        return new

    def rotate_x(self, angle: float) -> "ParticleShape":
        """绕 X 轴旋转（弧度），同时旋转运动向量。"""
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        new = self._copy()
        new.points = [
            (px, py * cos_a - pz * sin_a, py * sin_a + pz * cos_a)
            for px, py, pz in self.points
        ]
        if new.motions is not None:
            new.motions = [
                (mx, my * cos_a - mz * sin_a, my * sin_a + mz * cos_a)
                for mx, my, mz in new.motions
            ]
        return new

    def rotate_z(self, angle: float) -> "ParticleShape":
        """绕 Z 轴旋转（弧度），同时旋转运动向量。"""
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        new = self._copy()
        new.points = [
            (px * cos_a - py * sin_a, px * sin_a + py * cos_a, pz)
            for px, py, pz in self.points
        ]
        if new.motions is not None:
            new.motions = [
                (mx * cos_a - my * sin_a, mx * sin_a + my * cos_a, mz)
                for mx, my, mz in new.motions
            ]
        return new

    # ----------------------------------------------------------
    #  合并
    # ----------------------------------------------------------

    def merge(self, other: "ParticleShape") -> "ParticleShape":
        """合并两个图形的所有粒子点。粒子类型以 self 为准。"""
        combined_points = self.points + other.points
        combined_motions = None
        if self.motions is not None or other.motions is not None:
            self_m = self.motions if self.motions is not None else [(0, 0, 0)] * len(self.points)
            other_m = other.motions if other.motions is not None else [(0, 0, 0)] * len(other.points)
            combined_motions = self_m + other_m
        return ParticleShape(combined_points, self.particle, self.delta, self.speed, self.count, combined_motions)

    def __add__(self, other: "ParticleShape") -> "ParticleShape":
        return self.merge(other)

    # ----------------------------------------------------------
    #  采样（用于动画淡入淡出）
    # ----------------------------------------------------------

    def sampled(self, density: float) -> "ParticleShape":
        """
        按密度比例均匀采样粒子点，返回新的 ParticleShape。
        density: 0.0~1.0，1.0 表示全部保留。
        """
        n = max(1, int(len(self.points) * max(0.0, min(1.0, density))))
        step = len(self.points) / n
        indices = [int(i * step) % len(self.points) for i in range(n)]
        new_points = [self.points[i] for i in indices]
        new_motions = [self.motions[i] for i in indices] if self.motions is not None else None
        return ParticleShape(new_points, self.particle, self.delta, self.speed, self.count, new_motions)
