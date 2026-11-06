---
title: 05 建模
description: 一个参数源 design.py 生成两份模型：Blender 视觉模型和 MuJoCo 物理模型，靠命名约定和映射表一一对应。
---

# 05 建模

<StageHeader stage="modelling" />

建模阶段把参考图和尺寸表变成三样东西：可渲染的**视觉模型**、可仿真的 **MJCF 物理模型**，以及两者之间的**映射表**。三者都从同一个参数源生成，不手工维护两份几何。

## 一个参数源，两份模型

点下图的每个节点看它负责什么：

<DesignSplit />

为什么要分成两份：渲染要好看，用精细网格；仿真要稳、要快，只用简单的基本形状（box、cylinder、capsule）拼出**碰撞代理**。两者完全分开，靠命名约定区分：

| 前缀 | 是什么 | 规矩 |
|---|---|---|
| `ROOT_<body>` | physics-root 空物体 | 放在关节或铰链的轴上，渲染时由它接收仿真位姿 |
| `VIS_<body>__<part>` | 视觉 | 只有它会被导出到 GLB |
| `COL_<body>__<part>` | 碰撞代理 | `hide_render`，放在单独的 collection；导出时按白名单排除，不依赖隐藏状态 |

碰撞代理只保留**功能面**：支撑面、夹持面、导向面。和功能无关的细节一律不进物理模型。接触数决定仿真速度：全流程实验室里，盖子压在整块垫台上时盖内几百个加强筋小凸块全部接触，产生 444 个接触，实时因子从 0.2 掉到 0.02。物理模型里每个元素是什么，见[一个物体由什么组成](/physics/)。

<div class="wb-grid2">
<figure class="wb-figure"><img :src="$withBase('/img/slice/model_open.webp')" alt="培养箱建模预览" /><figcaption>薄切片 01 培养箱的建模预览（Cycles OptiX，64 采样加降噪，每张约 6 s）。预览只是验证证据，不需要审批。</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/slice/model_fingers.webp')" alt="偏置宽指建模预览" /><figcaption>偏置宽指挂在 Panda 手指根对象下，零件坐标就是手指的局部坐标。</figcaption></figure>
</div>

## 标准做法

1. **先做几何干涉核查，再写建模脚本。** 逐一核对工件尺寸、夹爪行程、TCP 伸入深度、接收位的墙和槽、隔板间距。薄切片 01 的两次设计返工都是在这一步发现的。
2. **门由执行器驱动时，用 `<exclude>` 排除门和箱体之间的碰撞**，不靠精确的间隙去避免穿透；门与机器人、门与工件之间的碰撞照常保留，因为验证门要检查禁止接触对。
3. **承托件直接做成箱体上的固定几何**（承托面就是碰撞面），工件保持自由体。
4. **导出后读回检查。** 验证门直接解析 GLB 的 JSON 块读节点名，验证的是导出的文件本身，不依赖 Blender。
5. **门限放在 `03-plan/thresholds.json`** 的 modelling 段，验证门只读它。
6. **参数化建模与 AI 3D 生成（Pixal3D）明确分工**：
   - **大件规整箱体与透明门柜体**（立式冰箱、双门玻璃试剂柜、实验台架）一律用 Blender 参数化建模：透明柜体用 Blender 做外壳、隔板与透射玻璃门，里面的试剂瓶等小东西逐个用 3D 模型生成后摆进去；或用 Blender 做规整冰箱几何体加外面贴图。直接用单图 3D 扩散生成整台大柜子会导致大平面边缘发肉、烘焙阴影显脏，还会把透明玻璃门封死成不透明白门。
   - **非接触异形机电小件**（带盘绕电线的台下 UPS 电源盒、蓝色波纹排风管与金属喉箍、墙面插座插头、散装试剂瓶、废料桶）在 Colab L4 上批量运行 `Pixal3D` 生成 `.glb`，经 Blender `2 mm` 空间容差去碎块和最小包围盒体积自动调平后作为 `VIS_` 对象合入。详见 `docs/lessons/09-pixal3d-colab-scene-dressing.md`。

调用方式（从 WSL）：

```bash
/mnt/d/Environment/blender-5.4.0/blender.exe -b --factory-startup --python build_blender.py -- "$(wslpath -w 05-modelling)"
uv run --extra sim python 05-modelling/build_mjcf.py
```

Windows 版 Blender 每次启动约 7 秒，多个操作要合并到一个脚本里；路径参数必须先用 `wslpath -w` 转成 Windows 路径。

## 验证门查什么

```bash
uv run --extra sim wb gate <项目> modelling
```

| 编号 | 检查 | 为什么 |
|---|---|---|
| M1 | MJCF 能用 MuJoCo 编译；关节范围与 `thresholds.json` 一致 | 铰链范围在 MjSpec 里默认用度，design 写的是弧度，开盖器摆臂曾因此塌下 |
| M2 | 关键支撑面高度误差 ≤ 1 mm | 取放位姿都按支撑面高度算，差 1 mm 就可能放不稳 |
| M3 | 导出的 GLB 读回后没有碰撞代理 | 保证渲染里看不到 `COL_` 对象 |
| M4 | 映射表覆盖全部部件 | 视觉和物理一一对应，渲染绑定不漏件 |
| M5 | 静置 1 s：没有超过 0.25 mm 的穿透，门和盖保持关闭 | 最便宜的物理检查。管盖的「螺纹」weld 写错时，静置就会掉 6.7 mm |
| M6 | 夹具开口范围覆盖工件尺寸 | 夹爪行程比工件小，后面全部白做 |
| M7 | 执行器清单齐全 | 少一个驱动，仿真里那台设备就动不了 |

另外还要有预览渲染作为证据。

## 踩过的坑

- **MjSpec 组合**（全流程实验室，都写进了 `build_mjcf.py`）：源文件的 keyframe 会被重复复制，要先删掉；同一个源文件 attach 三次，`to_xml` 会写出三份同名默认类，要去重；碰撞体一多，默认 arena 不够（报 "Insufficient arena memory"），接触直接失效，物体穿过台面掉下去，要把 memory 设到 256 MB；源文件的关节名和冻结门限不一致，按门限改名。
- **小件站不稳**：管底是圆柱，压在圆柱座面上只有一个接触点，管子会被横向推开、倒下。改成管底加方垫、座面为方块，周围加 1 mm 间隙的浅杯壁。
- **吸头盒是实心方块**，吸头插进去会穿透，改成镂空四壁加三根顶横条。
- **Blender 5.x**：先建材质、后调用 `read_factory_settings` 会把材质清掉，重置要放在脚本最开头；新建 world 默认没有 Background 节点，要手动建。
- **工作站 Z 轴加长会顶到龙门滑台**：最多只能再加约 0.11 m，可需要 +0.133 m。改法是龙门整体抬高 0.09 m，移液头相对 Y 滑台下移 0.09 m，这样 Z = 0 时吸头位置不变，冻结的 M1 仍然成立。

## 两个项目里的实测

薄切片 01：约 0.5 h，构建 1.3 s，3 张预览约 18 s，设计返工 2 次，验证门一次通过。全流程实验室：MJCF 构建约 10 s，Blender 构建、导出、3 张预览共 14 s，返工 5 次（吸头盒穿透、关节名、默认类重复、arena 内存、管子立不稳）。

经验记录原文：`docs/lessons/05-modelling.md`。
