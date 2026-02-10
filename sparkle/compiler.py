"""
Minecraft .mcfunction 编译器。
负责将 ParticleShape / ParticleAnimation 编译为 particle 命令并输出为 .mcfunction 文件。
所有 Minecraft 特定逻辑集中在此模块。
"""

import os
from typing import List

from .shape import ParticleShape
from .animation import ParticleAnimation


class ParticleCompiler:
    """
    将 ParticleShape / ParticleAnimation 编译为 Minecraft particle 命令，
    并输出为 .mcfunction 文件。
    """

    # ----------------------------------------------------------
    #  命令编译
    # ----------------------------------------------------------

    @staticmethod
    def _fmt_coord(v: float, prec: int = 4) -> str:
        """格式化相对坐标值。"""
        v = v if v != 0 else 0.0
        return f"~{v:.{prec}f}"

    @staticmethod
    def compile(shape: ParticleShape, prec: int = 4) -> List[str]:
        """将 ParticleShape 编译为 Minecraft particle 命令列表。"""
        fmt = ParticleCompiler._fmt_coord
        commands = []
        for i, (px, py, pz) in enumerate(shape.points):
            if shape.motions is not None:
                mx, my, mz = shape.motions[i]
                cmd = (
                    f"particle {shape.particle} "
                    f"{fmt(px, prec)} {fmt(py, prec)} {fmt(pz, prec)} "
                    f"{mx:.{prec}f} {my:.{prec}f} {mz:.{prec}f} {shape.speed} 0"
                )
            else:
                dx, dy, dz = shape.delta
                cmd = (
                    f"particle {shape.particle} "
                    f"{fmt(px, prec)} {fmt(py, prec)} {fmt(pz, prec)} "
                    f"{dx} {dy} {dz} {shape.speed} {shape.count}"
                )
            commands.append(cmd)
        return commands

    # ----------------------------------------------------------
    #  单帧文件输出
    # ----------------------------------------------------------

    @staticmethod
    def save(shape: ParticleShape, filename: str, prec: int = 4) -> str:
        """
        将 ParticleShape 保存为 .mcfunction 文件。

        filename: 输出文件路径（自动补 .mcfunction 后缀）
        prec: 坐标小数位数（默认 4）
        返回文件的绝对路径。
        """
        if not filename.endswith(".mcfunction"):
            filename += ".mcfunction"
        os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
        commands = ParticleCompiler.compile(shape, prec)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 由 Sparkle 生成\n")
            f.write(f"# 粒子数量: {len(commands)}\n\n")
            for cmd in commands:
                f.write(cmd + "\n")
        print(f"已保存: {filename} ({len(commands)} 条命令)")
        return os.path.abspath(filename)

    # ----------------------------------------------------------
    #  动画文件输出
    # ----------------------------------------------------------

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
            <directory>/main.mcfunction            ← 入口，召唤锚点 + 调用第一帧
            <directory>/frame_XXXX.mcfunction      ← 调度帧，execute at 锚点 + 调用粒子帧
            <directory>/particles_XXXX.mcfunction  ← 纯粒子命令（~ 相对坐标）
            <directory>/stop.mcfunction            ← 停止播放 + 移除锚点
        """
        os.makedirs(directory, exist_ok=True)
        sorted_ticks = sorted(anim.frames.keys())
        if not sorted_ticks:
            print("警告: 动画无帧，跳过保存")
            return directory

        tag = func_path.replace(":", "_").replace("/", "_")
        frame_names = []

        for i, tick in enumerate(sorted_ticks):
            frame_name = f"frame_{tick:04d}"
            particles_name = f"particles_{tick:04d}"
            frame_names.append((tick, frame_name))
            frame_shape = anim.frames[tick]

            # --- 粒子文件 ---
            particle_cmds = ParticleCompiler.compile(frame_shape, prec)
            particles_file = f"{directory}/{particles_name}.mcfunction"
            with open(particles_file, "w", encoding="utf-8") as f:
                f.write(f"# 帧 {tick}/{sorted_ticks[-1]}  粒子: {len(frame_shape.points)}\n")
                for cmd in particle_cmds:
                    f.write(cmd + "\n")

            # --- 调度帧 ---
            frame_cmds = [
                f"execute at @e[tag={tag},limit=1] run function {func_path}/{particles_name}"
            ]
            if i + 1 < len(sorted_ticks):
                next_tick = sorted_ticks[i + 1]
                delay = next_tick - tick
                next_frame = f"frame_{next_tick:04d}"
                frame_cmds.append(f"schedule function {func_path}/{next_frame} {delay}t")
            elif loop:
                first_frame = f"frame_{sorted_ticks[0]:04d}"
                frame_cmds.append(f"schedule function {func_path}/{first_frame} 1t")

            frame_file = f"{directory}/{frame_name}.mcfunction"
            with open(frame_file, "w", encoding="utf-8") as f:
                for cmd in frame_cmds:
                    f.write(cmd + "\n")
                if i + 1 == len(sorted_ticks):
                    f.write(f"kill @e[tag={tag}]\n")

        # 入口文件
        first_frame = frame_names[0][1]
        main_file = f"{directory}/main.mcfunction"
        with open(main_file, "w", encoding="utf-8") as f:
            f.write(f"# 粒子动画入口 — 由 Sparkle 生成\n")
            mode = "循环" if loop else "单次"
            f.write(f"# 总帧数: {len(sorted_ticks)}, 时长: {sorted_ticks[-1] + 1} ticks ({(sorted_ticks[-1] + 1) / 20:.1f}s), 模式: {mode}\n")
            f.write(f"# 停止: /function {func_path}/stop\n\n")
            f.write(f"kill @e[tag={tag}]\n")
            f.write(f'summon marker ~ ~ ~ {{Tags:["{tag}"]}}\n')
            f.write(f"function {func_path}/{first_frame}\n")

        # 停止文件
        stop_file = f"{directory}/stop.mcfunction"
        with open(stop_file, "w", encoding="utf-8") as f:
            f.write(f"# 停止粒子动画并移除锚点\n")
            for _, frame_name in frame_names:
                f.write(f"schedule clear {func_path}/{frame_name}\n")
            f.write(f"kill @e[tag={tag}]\n")

        total_cmds = sum(len(anim.frames[t].points) for t in sorted_ticks)
        loop_str = ", 循环" if loop else ""
        print(f"已保存动画: {directory}/ ({len(sorted_ticks)} 帧, {sorted_ticks[-1] + 1} ticks, 共 {total_cmds} 条粒子命令{loop_str})")
        return os.path.abspath(directory)
