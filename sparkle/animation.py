"""
多帧粒子动画，支持淡入淡出与循环播放。
纯动画逻辑模块，不包含文件 I/O。
"""

from typing import Callable, List, Tuple

from .shape import ParticleShape


class ParticleAnimation:
    """
    多帧粒子动画。
    存储 tick → ParticleShape 的帧映射，支持淡入淡出（消散）。
    文件输出请使用 ParticleCompiler。
    """

    def __init__(self):
        self.frames: dict[int, ParticleShape] = {}  # tick -> shape

    def add_frame(self, tick: int, shape: ParticleShape):
        """在指定 tick 添加一帧粒子。"""
        self.frames[tick] = shape

    @staticmethod
    def static(
        shape: ParticleShape,
        duration: int = 40,
        fade_in: int = 0,
        fade_out: int = 0,
    ) -> "ParticleAnimation":
        """
        从单个图形创建静态动画（每 tick 重复显示同一图形）。

        duration: 总时长（tick），20 tick = 1 秒
        fade_in:  淡入时长（tick），期间粒子密度从 0 渐增至 100%
        fade_out: 淡出时长（tick），期间粒子密度从 100% 渐减至 0（消散效果）
        """
        anim = ParticleAnimation()
        for tick in range(duration):
            density = 1.0
            if fade_in > 0 and tick < fade_in:
                density = (tick + 1) / fade_in
            if fade_out > 0 and tick >= duration - fade_out:
                density = (duration - tick) / fade_out
            density = max(0.01, min(1.0, density))
            anim.frames[tick] = shape.sampled(density)
        return anim

    @staticmethod
    def expanding(
        shape_func: Callable[[float], ParticleShape],
        duration: int = 40,
        fade_out: int = 10,
    ) -> "ParticleAnimation":
        """
        创建随时间变化的动画（如扩散环、膨胀球体）。

        shape_func(progress) -> ParticleShape
            progress: 0.0 ~ 1.0，表示动画进度
        duration: 总时长（tick）
        fade_out: 尾部消散时长（tick）
        """
        anim = ParticleAnimation()
        for tick in range(duration):
            progress = tick / max(1, duration - 1)
            frame = shape_func(progress)
            if fade_out > 0 and tick >= duration - fade_out:
                density = (duration - tick) / fade_out
                frame = frame.sampled(max(0.01, density))
            anim.frames[tick] = frame
        return anim

    @staticmethod
    def sequence(timeline: List[Tuple[int, ParticleShape]]) -> "ParticleAnimation":
        """从时间线列表创建动画。timeline: [(tick, shape), ...]"""
        anim = ParticleAnimation()
        for tick, shape in timeline:
            anim.frames[tick] = shape
        return anim
