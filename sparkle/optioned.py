"""
粒子选项工厂函数。
提供便捷方法生成带 SNBT 选项的粒子类型与选项字典元组，
用于 Minecraft 1.20.5+ 的粒子参数配置。

用法示例:
    from sparkle.optioned import dust
    p_type, p_opts = dust(color="#FF0000", scale=2.0)
    shape = circle(radius=3, particle=p_type).with_options(**p_opts)
"""

from typing import List, Tuple, Union


def _parse_color(color: Union[str, Tuple[float, float, float], List[float]]) -> List[float]:
    """
    解析颜色值为 [R, G, B] 浮点列表（0.0~1.0）。
    支持输入格式：
      - "#RRGGBB" 十六进制字符串
      - (R, G, B) 浮点元组/列表（直接透传）
    """
    if isinstance(color, str):
        c = color.lstrip("#")
        if len(c) != 6:
            raise ValueError(f"无效的十六进制颜色: {color}，应为 #RRGGBB 格式")
        r = int(c[0:2], 16) / 255.0
        g = int(c[2:4], 16) / 255.0
        b = int(c[4:6], 16) / 255.0
        return [round(r, 4), round(g, 4), round(b, 4)]
    if isinstance(color, (tuple, list)):
        return [float(color[0]), float(color[1]), float(color[2])]
    raise TypeError(f"不支持的颜色类型: {type(color)}")


def dust(
    color: Union[str, Tuple[float, float, float]] = "#FF0000",
    scale: float = 1.0,
) -> Tuple[str, dict]:
    """
    灰尘粒子。
    返回 (粒子类型, 选项字典)。
    """
    return "minecraft:dust", {"color": _parse_color(color), "scale": scale}


def dust_transition(
    from_color: Union[str, Tuple[float, float, float]] = "#FF0000",
    to_color: Union[str, Tuple[float, float, float]] = "#0000FF",
    scale: float = 1.0,
) -> Tuple[str, dict]:
    """
    渐变灰尘粒子。
    返回 (粒子类型, 选项字典)。
    """
    return "minecraft:dust_color_transition", {
        "from_color": _parse_color(from_color),
        "to_color": _parse_color(to_color),
        "scale": scale,
    }


def block_particle(block_state: str = "minecraft:stone") -> Tuple[str, dict]:
    """
    方块粒子。
    返回 (粒子类型, 选项字典)。
    """
    return "minecraft:block", {"block_state": block_state}


def item_particle(item: str = "minecraft:diamond") -> Tuple[str, dict]:
    """
    物品粒子。
    返回 (粒子类型, 选项字典)。
    """
    return "minecraft:item", {"item": item}


def entity_effect(
    color: Union[str, Tuple[float, float, float, float], List[float]] = "#FFFFFF",
    alpha: float = 1.0,
) -> Tuple[str, dict]:
    """
    实体效果粒子。
    color 可为 #RRGGBB（自动追加 alpha）或 (R, G, B, A) 四分量。
    返回 (粒子类型, 选项字典)。
    """
    if isinstance(color, str):
        rgb = _parse_color(color)
        rgba = rgb + [alpha]
    elif isinstance(color, (tuple, list)) and len(color) == 4:
        rgba = [float(c) for c in color]
    elif isinstance(color, (tuple, list)) and len(color) == 3:
        rgba = [float(c) for c in color] + [alpha]
    else:
        raise TypeError(f"不支持的颜色类型: {type(color)}")
    return "minecraft:entity_effect", {"color": rgba}
