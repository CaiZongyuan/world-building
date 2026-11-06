# 05 建模

## 这一步做什么

把参考图和尺寸表变成三样东西：可渲染的视觉模型、可仿真的 MJCF、以及两者之间的映射表。三者都从同一个参数源生成，不手工维护两份几何。

## 输入 / 产物 / 完成判据

- 输入：`04-reference/dimensions.md`、`load_path.svg`、参考图；`03-plan/thresholds.json` 的 modelling 段。
- 产物（`05-modelling/`）：
  - `design.py` → `design.json`：唯一参数源
  - `build_blender.py` → `incubator.blend`、`incubator_visual.glb`、`mapping.json`、`glb_readback.json`
  - `build_mjcf.py` → `incubator.xml`
  - `render_preview.py` → `preview/*.webp`
  - `compare_p1b.json`
- 完成判据：`uv run --extra sim wb gate <项目> modelling` 判 PASS（M1–M6 加预览证据）。

## 工具与调用方式

- Blender 5.4 headless：`blender.exe -b --factory-startup --python build_blender.py -- <目录的 Windows 路径>`。
- 命名约定：
  - `ROOT_<body>`：physics-root 空物体，放在关节或铰链的轴上
  - `VIS_<body>__<part>`：视觉
  - `COL_<body>__<part>`：碰撞代理，设置 `hide_render`，放在单独的 collection
- 导出 GLB 时只选中 `VIS_` 和 `ROOT_`，用白名单，不依赖隐藏状态。
- 验证门直接解析 GLB 的 JSON 块读出节点名，验证的是导出的文件本身，不依赖 Blender。
- MJCF 和 Blender 都读 design.json。碰撞几何只取 `collision=True` 的部件；视觉几何放 group 2，不参与碰撞。

## 标准做法

1. **先做几何干涉核查，再写建模脚本。** 逐一核对工件尺寸、夹爪行程、TCP 伸入深度、接收位的墙和槽、隔板间距。本项目两次设计返工都是在这一步发现的。
2. 门由执行器驱动时，用 `<exclude>` 排除门与箱体之间的碰撞，不靠精确的间隙去避免穿透；门与机器人、门与工件之间的碰撞照常保留，因为验证门要检查禁止接触对。
3. 隔板这类承托件，直接做成箱体上的固定几何（承托面就是碰撞面）。工件保持自由体。
4. 预览渲染用 Cycles OptiX，64 采样加降噪，每张约 6 s，作为证据，不需要审批。
5. 门限放在 `03-plan/thresholds.json`（plan 冻结时一并生成），验证门只读这个文件。
6. **参数化硬表面与 AI 3D 生成（Pixal3D）的分工边界**：
   - **大件规整家具/箱体（冰箱、双门玻璃试剂柜、铝型材实验台、护栏）一律用 Blender 参数化建模**：透明柜体用 Blender 做外壳、隔板与透射玻璃门（`Transmission=0.92`），里面的试剂瓶等小物件再用 3D 模型逐个生成摆入；实心冰箱用 Blender 做规整几何体加正面控制面板贴图。直接用单图 3D 扩散生成整台大柜子会导致大平面边缘发肉、烘焙阴影显脏，且 `o_voxel` 的 `OPAQUE` 材质会把透明玻璃门封死成实心白门。
   - **非接触异形机电小件与散装容器**（带盘绕电线的台下 UPS 电源盒、蓝色波纹排风管与金属喉箍、带插头线的墙面插座、培养基玻璃瓶、废料桶）在 Colab L4 上批量运行 `TencentARC/Pixal3D` 生成 `.glb`，再经 Blender 空间容差（`2 mm`）去碎块和最小包围盒自动调平后合入。详见 `docs/lessons/09-pixal3d-colab-scene-dressing.md`。

## 踩过的坑

- **Blender 5.x**：
  - 先建材质、后调用 `read_factory_settings` 会把材质清掉，重置要放在脚本最开头。
  - 新建 world 默认没有 Background 节点，要手动创建并连线。
- **`/mnt/d` 上的文件复制**：不能 copystat，复制树要用只复制文件内容的方式。
- **参考图阶段的尺寸不是终版。** 夹爪伸入深度、接收位开槽，都要到建模阶段做干涉核查时才会暴露问题。这类修订要回写到尺寸表，并在阶段日志里记为返工。

## 阶段日志摘要

约 0.5 h。构建本身 1.3 s，3 张预览约 18 s。设计返工 2 次，脚本报错 2 次，验证门一次通过。
