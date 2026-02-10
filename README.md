# Sparkle — Minecraft 粒子效果生成器

用数学函数生成 Minecraft Java Edition 的 `.mcfunction` 粒子命令文件。

核心库 **sparkle** 提供图形构建、空间变换、运动控制和动画编排能力，生成可直接放入数据包使用的 `.mcfunction` 文件。

目标版本：**Java Edition 1.20+**

## 项目结构

```
Sparkle/
├── sparkle/                     # 核心库
│   ├── __init__.py              # 包入口，导出全部公共 API
│   ├── shape.py                 # ParticleShape — 3D 点集与空间变换
│   ├── animation.py             # ParticleAnimation — 多帧动画编排
│   ├── primitives.py            # 几何图元工厂函数
│   ├── compiler.py              # ParticleCompiler — 命令编译与 .mcfunction 输出
│   └── sps.py                   # SPS 格式编解码器
├── particle_generator.py        # 示例程序（40+ 案例）
├── test_sps.py                  # SPS 格式往返测试
└── output/                      # 生成的文件
```

## 快速开始

```python
from sparkle import ParticleCompiler, circle

# 生成一个火焰圆环
ParticleCompiler.save(circle(radius=3, points=80), "output/circle")
```

将生成的 `output/circle.mcfunction` 放入数据包的 `data/<namespace>/function/` 目录，在游戏中执行：

```
/function <namespace>:circle
```

## 核心 API

### 几何图元 (`primitives`)

| 函数 | 说明 |
|------|------|
| `circle(radius, points, axis, particle)` | 圆形 |
| `sphere(radius, u_points, v_points, particle)` | 球体表面 |
| `helix(radius, height, turns, points, particle)` | 螺旋线 |
| `heart(size, points, particle)` | 心形曲线 |
| `star(outer_r, inner_r, n_points, samples, particle)` | 星形 |
| `torus(major_r, minor_r, u_points, v_points, particle)` | 圆环面 |
| `line(start, end, points, particle)` | 直线段 |
| `sine_wave(amplitude, wavelength, length, points, particle)` | 正弦波 |
| `parametric_curve(func, t_range, points, particle)` | 自定义参数曲线 |
| `parametric_surface(func, u_range, v_range, u_points, v_points, particle)` | 自定义参数曲面 |
| `polygon(n, radius, axis, particle)` | 正多边形线框 |
| `tetrahedron(size, samples_per_edge, particle)` | 正四面体线框 |
| `cube(size, samples_per_edge, particle)` | 正六面体（立方体）线框 |
| `octahedron(size, samples_per_edge, particle)` | 正八面体线框 |
| `dodecahedron(size, samples_per_edge, particle)` | 正十二面体线框 |
| `icosahedron(size, samples_per_edge, particle)` | 正二十面体线框 |

### ParticleShape — 空间变换

```python
shape.offset(x=0, y=5, z=0)    # 平移
shape.scale(2.0)                 # 缩放
shape.rotate_x(angle)            # 绕 X 轴旋转（弧度）
shape.rotate_y(angle)            # 绕 Y 轴旋转
shape.rotate_z(angle)            # 绕 Z 轴旋转
```

所有变换返回新对象，支持链式调用：

```python
heart(size=4).scale(2).offset(y=10).rotate_y(math.pi / 4)
```

### ParticleShape — 运动控制

```python
shape.with_motion(dx, dy, dz, speed)           # 统一方向运动
shape.with_radial_motion(speed, center)         # 从中心辐射（爆炸）
shape.with_tangent_motion(speed)                # 沿切线流动
shape.with_custom_motion(func, speed)           # 自定义运动函数
```

### ParticleShape — 图形组合

```python
ring_a + ring_b + ring_c        # 用 + 合并多个图形
shape_a.merge(shape_b)          # 等价写法
```

### ParticleAnimation — 动画

```python
from sparkle import ParticleAnimation, ParticleCompiler

# 静态图形 + 淡入淡出
anim = ParticleAnimation.static(shape, duration=60, fade_in=10, fade_out=20)

# 随时间变化的图形（如扩散环）
anim = ParticleAnimation.expanding(lambda p: circle(radius=p*8), duration=30, fade_out=10)

# 手动时间线
anim = ParticleAnimation.sequence([(0, shape_a), (20, shape_b), (40, shape_c)])

# 保存
ParticleCompiler.save_animation(anim, "output/anim_name", func_path="pack:anim_name", loop=True)
```

### ParticleCompiler — 编译与输出

```python
from sparkle import ParticleCompiler

ParticleCompiler.save(shape, "output/my_effect")                              # 保存为 .mcfunction
ParticleCompiler.save(shape, "output/my_effect", prec=6)                      # 自定义精度（小数位数）
ParticleCompiler.save_animation(anim, "output/my_anim", func_path="p:anim")  # 保存动画文件包
commands = ParticleCompiler.compile(shape)                                     # 仅生成命令列表
```

### SPS 格式 — 紧凑粒子数据存储

SPS (Sparkle Particle Storage) 是一种紧凑可读的中间格式，用于保存和加载粒子数据。相比 `.mcfunction`，SPS 通过增量编码、游程编码和轴省略实现显著压缩。

```python
from sparkle import save_sps, load_sps, circle

# 保存
save_sps(circle(radius=3, points=80), "output/circle")  # → circle.sps

# 加载
shape = load_sps("output/circle.sps")

# 动画同样支持
save_sps(anim, "output/my_anim")
anim = load_sps("output/my_anim.sps")
```

压缩策略：

- **增量编码** — 坐标序列存储相邻点的差值
- **游程编码** — 重复的增量模式用 `= k n` 合并（线段/线框可极端压缩）
- **局部轴省略** — 连续零值轴自动省略，减少一个分量
- **数值紧凑化** — `0.5000`→`.5`，`-0.3000`→`-.3`，`3.0`→`3`
- **帧间继承** — 动画中相邻帧的粒子参数相同时省略

典型压缩率为 `.mcfunction` 的 **17~32%**。

## 示例一览

运行 `python particle_generator.py` 生成全部示例：

**基础图形** — 圆形、球体、心形、星形、螺旋、环面、正弦波、直线

**空间变换** — 缩放心形、倾斜圆环、旋转星星

**图形组合** — 三环交叉、行星环、DNA 双螺旋、同心涟漪

**粒子运动** — 上升飘动、爆炸扩散、切线流动、飞散效果、心碎辐射、甜甜圈旋转、黑洞吸引

**参数方程** — 利萨如曲线、玫瑰曲线、蝴蝶曲线、莫比乌斯带、球面螺线、圆锥面、阿基米德螺线

**动画效果** — 心形淡入淡出、爆炸环、上升螺旋、呼吸球体、旋转星星、粒子喷泉、传送门、火焰龙卷风

**复合场景** — 魔法阵、原子模型、粒子树、银河漩涡、线框立方体

**正多面体** — 正四面体、立方体、正八面体、正十二面体、正二十面体

## 使用方法

1. 将 `.mcfunction` 文件放入数据包 `data/<namespace>/function/` 目录
2. 单帧图形：`/function <namespace>:<name>`
3. 动画入口：`/function <namespace>:<name>/main`
4. 停止动画：`/function <namespace>:<name>/stop`

## 依赖

Python 3.10+，无第三方依赖。
