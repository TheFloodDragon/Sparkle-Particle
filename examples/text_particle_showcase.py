"""字符转粒子独立示例（Pillow 跨平台版）。

通过 Pillow 将 Unicode 文本渲染成灰度位图，再按可调精度采样为粒子点。
不依赖内置字符点阵表，支持中文、英文、数字以及多数 Unicode 字符。

依赖：
    pip install pillow
"""

from __future__ import annotations

import argparse
import functools
import math
import os
import sys
from pathlib import Path

from _example_utils import OUTPUT_ROOT, bootstrap_repo_path

bootstrap_repo_path()

from sparkle import ParticleAnimation, ParticleCompiler, ParticleShape, dust  # noqa: E402

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError as exc:
    raise SystemExit("缺少 Pillow，请先执行: pip install pillow") from exc


DEFAULT_TEXT = "Sparkle|粒子文字"
DEFAULT_FONT = "auto"
DEFAULT_FONT_SIZE = 64
DEFAULT_SAMPLE_STEP = 1
DEFAULT_WORLD_STEP = 0.10
DEFAULT_THRESHOLD = 40.0
ANIM_DURATION = 80
STATIC_OUTPUT = OUTPUT_ROOT / "text_particle_showcase"
ANIM_OUTPUT = OUTPUT_ROOT / "text_particle_wave"
ANIM_FUNC_PATH = "p:text_particle_wave"
FONT_EXTS = (".ttf", ".otf", ".ttc", ".otc")

PLATFORM_FONT_CANDIDATES = {
    "win32": ["msyh.ttc", "msyhbd.ttc", "simhei.ttf", "simsun.ttc", "segoeui.ttf", "arial.ttf"],
    "darwin": ["PingFang.ttc", "Hiragino Sans GB.ttc", "Arial Unicode.ttf", "Helvetica.ttc"],
    "default": [
        "NotoSansCJK-Regular.ttc",
        "NotoSansCJKSC-Regular.otf",
        "NotoSansSC-Regular.otf",
        "WenQuanYi Zen Hei.ttf",
        "SourceHanSansSC-Regular.otf",
        "DejaVuSans.ttf",
        "LiberationSans-Regular.ttf",
    ],
}


def default_font_candidates() -> list[str]:
    return PLATFORM_FONT_CANDIDATES.get(sys.platform, PLATFORM_FONT_CANDIDATES["default"])


def normalize_text(text: str) -> str:
    """统一换行写法，支持 | 和字面量 \n。"""
    return text.replace("\\n", "\n").replace("|", "\n")


def normalize_name(name: str) -> str:
    """把字体名规整成便于匹配的形式。"""
    return "".join(char for char in name.lower() if char.isalnum())


@functools.lru_cache(maxsize=1)
def system_font_dirs() -> tuple[Path, ...]:
    """返回常见系统字体目录。"""
    directories: list[Path] = []

    if sys.platform == "win32":
        directories.append(Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts")
    elif sys.platform == "darwin":
        directories.extend([
            Path("/System/Library/Fonts"),
            Path("/Library/Fonts"),
            Path.home() / "Library" / "Fonts",
        ])
    else:
        directories.extend([
            Path.home() / ".fonts",
            Path.home() / ".local" / "share" / "fonts",
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
        ])

    existing: list[Path] = []
    seen: set[str] = set()
    for directory in directories:
        key = str(directory)
        if key in seen or not directory.exists():
            continue
        seen.add(key)
        existing.append(directory)
    return tuple(existing)


@functools.lru_cache(maxsize=1)
def available_font_files() -> tuple[Path, ...]:
    """扫描系统中常见字体目录。"""
    files: list[Path] = []
    for directory in system_font_dirs():
        for ext in FONT_EXTS:
            files.extend(directory.rglob(f"*{ext}"))
    return tuple(files)


def match_font_paths(font_spec: str) -> list[str]:
    """按文件名或近似名称匹配系统字体。"""
    target = normalize_name(Path(font_spec).stem or font_spec)
    exact: list[str] = []
    fuzzy: list[str] = []

    for path in available_font_files():
        file_name = path.name
        stem_name = path.stem
        normalized_file = normalize_name(file_name)
        normalized_stem = normalize_name(stem_name)

        if font_spec.lower() == file_name.lower() or target == normalized_file or target == normalized_stem:
            exact.append(str(path))
        elif target and (target in normalized_file or target in normalized_stem):
            fuzzy.append(str(path))

    return exact + fuzzy


def resolve_font_candidates(font_spec: str) -> list[str]:
    """生成字体加载候选。支持 auto、字体路径和字体文件名。"""
    specs = default_font_candidates() if font_spec == "auto" else [font_spec]
    candidates: list[str] = []
    seen: set[str] = set()

    for spec in specs:
        value = spec.strip()
        if not value:
            continue

        path = Path(value)
        if path.exists():
            resolved = str(path)
            if resolved not in seen:
                seen.add(resolved)
                candidates.append(resolved)

        if value not in seen:
            seen.add(value)
            candidates.append(value)

        for matched in match_font_paths(value):
            if matched not in seen:
                seen.add(matched)
                candidates.append(matched)

    return candidates


def load_font(font_spec: str, font_size: int) -> tuple[ImageFont.FreeTypeFont, str]:
    """加载字体，并返回实际使用的字体标识。"""
    errors: list[str] = []
    for candidate in resolve_font_candidates(font_spec):
        try:
            return ImageFont.truetype(candidate, font_size), candidate
        except OSError as exc:
            errors.append(f"{candidate}: {exc}")

    hint = "请通过 --font 指定字体路径或系统中存在的字体文件名"
    example = default_font_candidates()[0]
    detail = "；".join(errors[:3])
    raise RuntimeError(f"无法加载字体 {font_spec}。{hint}，例如：{example}。{detail}")


def render_text_image(
    text: str,
    font: ImageFont.FreeTypeFont,
    padding: int = 12,
    line_gap_px: int = 0,
    bold: bool = False,
) -> Image.Image:
    """将文本渲染为灰度图。"""
    content = normalize_text(text) or " "
    stroke_width = 1 if bold else 0

    temp_image = Image.new("L", (1, 1), 255)
    temp_draw = ImageDraw.Draw(temp_image)
    left, top, right, bottom = temp_draw.multiline_textbbox(
        (0, 0),
        content,
        font=font,
        spacing=line_gap_px,
        stroke_width=stroke_width,
    )

    width = max(1, int(math.ceil(right - left)) + padding * 2)
    height = max(1, int(math.ceil(bottom - top)) + padding * 2)

    image = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(image)
    draw.multiline_text(
        (padding - left, padding - top),
        content,
        fill=0,
        font=font,
        spacing=line_gap_px,
        stroke_width=stroke_width,
        stroke_fill=0,
    )
    return image


def bitmap_to_points(
    width: int,
    height: int,
    gray: bytes,
    sample_step: int = DEFAULT_SAMPLE_STEP,
    world_step: float = DEFAULT_WORLD_STEP,
    threshold: float = DEFAULT_THRESHOLD,
) -> list[tuple[float, float, float]]:
    """把灰度位图按网格采样为粒子点。"""
    sample_step = max(1, int(sample_step))
    threshold = float(threshold)

    points: list[tuple[float, float, float]] = []
    for top in range(0, height, sample_step):
        bottom = min(height, top + sample_step)
        for left in range(0, width, sample_step):
            right = min(width, left + sample_step)
            darkness_sum = 0.0
            count = 0

            for y in range(top, bottom):
                row_base = y * width
                for x in range(left, right):
                    darkness_sum += 255.0 - gray[row_base + x]
                    count += 1

            if darkness_sum / max(1, count) < threshold:
                continue

            center_x = (left + right) * 0.5 * world_step
            center_y = -(top + bottom) * 0.5 * world_step
            points.append((center_x, center_y, 0.0))

    return points


def center_shape(shape: ParticleShape) -> ParticleShape:
    """将粒子图形居中到原点附近。"""
    if not shape.points:
        return shape
    min_x = min(x for x, _, _ in shape.points)
    max_x = max(x for x, _, _ in shape.points)
    min_y = min(y for _, y, _ in shape.points)
    max_y = max(y for _, y, _ in shape.points)
    return shape.offset(x=-(min_x + max_x) / 2.0, y=-(min_y + max_y) / 2.0)


def build_text_shape(
    text: str,
    font_spec: str = DEFAULT_FONT,
    font_size: int = DEFAULT_FONT_SIZE,
    sample_step: int = DEFAULT_SAMPLE_STEP,
    world_step: float = DEFAULT_WORLD_STEP,
    threshold: float = DEFAULT_THRESHOLD,
    padding: int = 12,
    line_gap_px: int = 0,
    bold: bool = False,
    particle: str = "minecraft:end_rod",
    options: dict | None = None,
    center: bool = True,
) -> tuple[ParticleShape, str]:
    """把 Unicode 文本转换为粒子图形。"""
    font, font_used = load_font(font_spec, font_size)
    image = render_text_image(
        text=text,
        font=font,
        padding=padding,
        line_gap_px=line_gap_px,
        bold=bold,
    )
    points = bitmap_to_points(
        width=image.width,
        height=image.height,
        gray=image.tobytes(),
        sample_step=sample_step,
        world_step=world_step,
        threshold=threshold,
    )

    shape = ParticleShape(points, particle=particle, options=options)
    if center:
        shape = center_shape(shape)
    return shape, font_used


def wave_text_shape(base_shape: ParticleShape, progress: float, amplitude: float = 0.35) -> ParticleShape:
    """给文字增加轻微波浪效果。"""
    phase = progress * math.tau * 2.0
    points = []
    for x, y, z in base_shape.points:
        offset_y = amplitude * math.sin(x * 1.2 + phase)
        offset_z = amplitude * 0.65 * math.cos(x * 0.9 - phase)
        points.append((x, y + offset_y, z + offset_z))
    return ParticleShape(points, particle=base_shape.particle, options=base_shape.options)


def build_animation(base_shape: ParticleShape, duration: int = ANIM_DURATION, amplitude: float = 0.35) -> ParticleAnimation:
    """基于静态文字生成循环波浪动画。"""
    animation = ParticleAnimation()
    for tick in range(duration):
        progress = tick / max(1, duration - 1)
        animation.add_frame(tick, wave_text_shape(base_shape, progress, amplitude=amplitude))
    return animation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="把任意 Unicode 文本转换为 Sparkle 粒子示例。")
    parser.add_argument("text", nargs="*", help="要转换的文本；可用 | 或 \\n 表示换行")
    parser.add_argument("--font", default=DEFAULT_FONT, help="字体路径、字体文件名或 auto（默认）")
    parser.add_argument("--font-size", type=int, default=DEFAULT_FONT_SIZE, help="字体渲染尺寸（像素），越大越细")
    parser.add_argument("--sample-step", type=int, default=DEFAULT_SAMPLE_STEP, help="采样步长（像素），越小越精细")
    parser.add_argument("--world-step", type=float, default=DEFAULT_WORLD_STEP, help="每个采样单元在游戏中的间距")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="取样阈值 0~255，越小越保留边缘")
    parser.add_argument("--padding", type=int, default=12, help="文字位图四周留白（像素）")
    parser.add_argument("--line-gap-px", type=int, default=0, help="额外行距（像素）")
    parser.add_argument("--bold", action="store_true", help="使用描边模拟更粗的文字")
    parser.add_argument("--y-offset", type=float, default=5.0, help="整体抬升高度")
    parser.add_argument("--wave-amplitude", type=float, default=0.35, help="波浪动画振幅")
    parser.add_argument("--duration", type=int, default=ANIM_DURATION, help="波浪动画总时长（tick）")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    text = normalize_text(" ".join(args.text).strip() or DEFAULT_TEXT)
    particle, options = dust(color="#7CDBFF", scale=0.9)

    base_shape, font_used = build_text_shape(
        text=text,
        font_spec=args.font,
        font_size=max(1, args.font_size),
        sample_step=max(1, args.sample_step),
        world_step=max(0.001, args.world_step),
        threshold=max(0.0, min(255.0, args.threshold)),
        padding=max(0, args.padding),
        line_gap_px=max(0, args.line_gap_px),
        bold=args.bold,
        particle=particle,
        options=options,
    )
    base_shape = base_shape.offset(y=args.y_offset)

    static_path = ParticleCompiler.save(base_shape, str(STATIC_OUTPUT))
    animation_path = ParticleCompiler.save_animation(
        build_animation(base_shape, duration=max(1, args.duration), amplitude=args.wave_amplitude),
        str(ANIM_OUTPUT),
        func_path=ANIM_FUNC_PATH,
        loop=True,
    )

    print(f"文字内容: {text.replace(chr(10), ' / ')}")
    print(f"平台: {sys.platform}")
    print(f"字体: {font_used}")
    print(f"粒子数: {len(base_shape.points)}")
    print(
        "渲染参数: "
        f"font_size={args.font_size}, sample_step={args.sample_step}, "
        f"world_step={args.world_step}, threshold={args.threshold}"
    )
    print(f"静态文字已保存到: {static_path}")
    print(f"波浪动画已保存到: {animation_path}")
    print(f"动画调用: /function {ANIM_FUNC_PATH}/main")


if __name__ == "__main__":
    main()
