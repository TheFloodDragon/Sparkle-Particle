"""
Minecraft .mcfunction 编译器。

负责将 `ParticleShape` / `ParticleAnimation` 编译为粒子命令文件。
"""

import os
from typing import List

from .animation import ParticleAnimation
from .shape import ParticleShape
from .snbt import to_snbt


class ParticleCompiler:
    """将 Sparkle 粒子数据编译并保存为 mcfunction 文件。"""

    @staticmethod
    def _fmt_particle(shape: ParticleShape) -> str:
        """格式化粒子类型（包含可选 SNBT 选项）。"""
        if not shape.options:
            return shape.particle
        return f"{shape.particle}{to_snbt(shape.options)}"

    @staticmethod
    def _fmt_coord(v: float, prec: int = 4) -> str:
        """格式化 Minecraft 粒子命令中的相对坐标。"""
        v = v if v != 0 else 0.0
        return f"~{v:.{prec}f}"

    @staticmethod
    def compile(shape: ParticleShape, prec: int = 4) -> List[str]:
        """将一个 `ParticleShape` 编译为粒子命令列表。"""
        fmt = ParticleCompiler._fmt_coord
        particle_str = ParticleCompiler._fmt_particle(shape)
        commands: List[str] = []

        for i, (px, py, pz) in enumerate(shape.points):
            if shape.motions is not None:
                mx, my, mz = shape.motions[i]
                cmd = (
                    f"particle {particle_str} "
                    f"{fmt(px, prec)} {fmt(py, prec)} {fmt(pz, prec)} "
                    f"{mx:.{prec}f} {my:.{prec}f} {mz:.{prec}f} {shape.speed} 0"
                )
            else:
                dx, dy, dz = shape.delta
                cmd = (
                    f"particle {particle_str} "
                    f"{fmt(px, prec)} {fmt(py, prec)} {fmt(pz, prec)} "
                    f"{dx} {dy} {dz} {shape.speed} {shape.count}"
                )
            commands.append(cmd)

        return commands

    @staticmethod
    def save(shape: ParticleShape, filename: str, prec: int = 4) -> str:
        """
        保存单个 `ParticleShape` 到 `<filename>.mcfunction`。

        返回输出文件的绝对路径。
        """
        if not filename.endswith(".mcfunction"):
            filename += ".mcfunction"

        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        commands = ParticleCompiler.compile(shape, prec)

        with open(filename, "w", encoding="utf-8") as f:
            f.write("# 由 Sparkle 生成\n")
            f.write(f"# 粒子命令数: {len(commands)}\n\n")
            for cmd in commands:
                f.write(cmd + "\n")

        print(f"已保存: {filename} ({len(commands)} 条命令)")
        return os.path.abspath(filename)

    @staticmethod
    def save_animation(
        anim: ParticleAnimation,
        directory: str,
        func_path: str = "p:anim",
        loop: bool = False,
        prec: int = 4,
    ) -> str:
        """
        将 ParticleAnimation 保存为一组 .mcfunction 文件。

        通过召唤 marker 实体作为坐标锚点，使 schedule 后的帧仍能使用 ~ 相对坐标。
        锚点在 main 中以执行者位置召唤，每帧通过 execute at 恢复位置上下文。

        directory:  文件输出目录
        func_path:  数据包中的函数路径前缀，如 "mypack:effects/circle"
                    帧文件会生成为 func_path/frame_XXXX
        loop:       True 时最后一帧会重新调度第一帧，实现无限循环播放。
                    用 /function func_path/stop 停止。
        prec:  坐标小数位数（默认 4）

        生成结构:
            <directory>/main.mcfunction                   ← 入口，召唤锚点 + 调用第一帧
            <directory>/stop.mcfunction                   ← 停止播放 + 移除锚点
            <directory>/frames/frame_XXXX.mcfunction      ← 调度帧，execute at 锚点 + 调用粒子帧
            <directory>/frames/particles_XXXX.mcfunction  ← 纯粒子命令（~ 相对坐标）
        """
        os.makedirs(directory, exist_ok=True)
        frames_dir = os.path.join(directory, "frames")
        os.makedirs(frames_dir, exist_ok=True)

        sorted_ticks = sorted(anim.frames.keys())
        if not sorted_ticks:
            print("警告: 动画无帧，已跳过保存。")
            return directory

        tag = func_path.replace(":", "_").replace("/", "_")
        frame_ids: List[str] = []

        for i, tick in enumerate(sorted_ticks):
            frame_name = f"frame_{tick:04d}"
            particles_name = f"particles_{tick:04d}"
            frame_ids.append(frame_name)
            frame_shape = anim.frames[tick]

            particle_cmds = ParticleCompiler.compile(frame_shape, prec)
            particles_file = os.path.join(frames_dir, f"{particles_name}.mcfunction")
            with open(particles_file, "w", encoding="utf-8") as f:
                f.write(f"# 帧 {tick}/{sorted_ticks[-1]} 粒子数: {len(frame_shape.points)}\n")
                for cmd in particle_cmds:
                    f.write(cmd + "\n")

            particles_func = f"{func_path}/frames/{particles_name}"
            frame_func = f"{func_path}/frames/{frame_name}"

            frame_cmds = [f"execute at @e[tag={tag},limit=1] run function {particles_func}"]
            if i + 1 < len(sorted_ticks):
                next_tick = sorted_ticks[i + 1]
                delay = next_tick - tick
                next_frame_func = f"{func_path}/frames/frame_{next_tick:04d}"
                frame_cmds.append(f"schedule function {next_frame_func} {delay}t")
            elif loop:
                first_frame_func = f"{func_path}/frames/frame_{sorted_ticks[0]:04d}"
                frame_cmds.append(f"schedule function {first_frame_func} 1t")

            frame_file = os.path.join(frames_dir, f"{frame_name}.mcfunction")
            with open(frame_file, "w", encoding="utf-8") as f:
                for cmd in frame_cmds:
                    f.write(cmd + "\n")
                if i + 1 == len(sorted_ticks) and not loop:
                    f.write(f"kill @e[tag={tag}]\n")

        first_frame_func = f"{func_path}/frames/{frame_ids[0]}"
        main_file = os.path.join(directory, "main.mcfunction")
        with open(main_file, "w", encoding="utf-8") as f:
            f.write("# Sparkle 动画入口\n")
            f.write(
                f"# 帧数: {len(sorted_ticks)}, 时长: {sorted_ticks[-1] + 1} ticks "
                f"({(sorted_ticks[-1] + 1) / 20:.1f}s), 循环: {loop}\n"
            )
            f.write(f"# 停止命令: /function {func_path}/stop\n\n")
            f.write(f"kill @e[tag={tag}]\n")
            f.write(f'summon marker ~ ~ ~ {{Tags:["{tag}"]}}\n')
            f.write(f"function {first_frame_func}\n")

        stop_file = os.path.join(directory, "stop.mcfunction")
        with open(stop_file, "w", encoding="utf-8") as f:
            f.write("# 停止动画并清理已调度帧\n")
            for frame_name in frame_ids:
                f.write(f"schedule clear {func_path}/frames/{frame_name}\n")
            f.write(f"kill @e[tag={tag}]\n")

        total_cmds = sum(len(anim.frames[t].points) for t in sorted_ticks)
        loop_str = ", 循环" if loop else ""
        print(
            f"已保存动画: {directory}/ "
            f"({len(sorted_ticks)} 帧, {sorted_ticks[-1] + 1} ticks, "
            f"共 {total_cmds} 条粒子命令{loop_str})"
        )
        return os.path.abspath(directory)
