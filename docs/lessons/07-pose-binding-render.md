# 07 位姿绑定与渲染

## 这一步做什么

把 MuJoCo 记录下来的刚体位姿逐帧写进 Blender 的视觉根对象，再用 Cycles 渲出与仿真等长的成片：不加速，不剪辑。画面里的每一个动作都必须来自物理仿真，不允许手动打关键帧（ADR-0003）。

## 输入 / 产物 / 完成判据

- 输入：
  - `06-simulation/states_30fps.npz`：每帧所有 body 的 xpos 与 xquat
  - `06-simulation/scene_layout.json`：布局、开槽、相机参数
  - `incubator.blend`：新建资产
  - 复用资产的 `.blend` 文件、Menagerie 的 OBJ
- 产物（`07-render/`）：
  - `build_render_scene.py` → `render_scene.blend`、`binding_report.json`
  - `render_frames.py` → `frames/`
  - `finish.sh` → `film.mp4`、`keyframes/*.webp`
- 完成判据：`uv run --extra sim wb gate <项目> render` 的 V1–V4 全部判 PASS。

## 标准做法

1. **只按白名单导入**，名字里带 `COL_` 或 collision 的对象直接排除，而不是导入后隐藏。复用资产里的灯光、相机、展示台也不要导入。
2. **视觉根和 MuJoCo body 一一对应**：
   - 每个根对象都不设父级，直接把该帧仿真的世界位置和四元数写进去，关键帧插值用 CONSTANT。
   - 全程不动的 body 不打关键帧。
   - 复用资产的根对象原点必须和 MJCF 的 body 坐标系一致；观察站和底座原本就一致，按原样导入即可。
3. **仿真里改过的几何，视觉模型要同步改**。例如托槽开槽在 Blender 里用布尔 DIFFERENCE 做出来；偏置宽指的零件挂到 Panda 手指根对象下，零件坐标就是手指的局部坐标。
4. **绑定之后马上自检**：
   - V1：场景中不能有碰撞代理。
   - V3：抽查若干帧，Blender 里的世界位姿要和仿真记录一致；比较四元数时要考虑 q 与 −q 表示同一旋转。
5. **默认用 draft 档位**：成片是给工程审阅看动作和干涉的，不是展示片。`render_frames.py` 有三个档位，只改采样和分辨率，不动机位、灯光、材质：
   - `draft`（默认）：Cycles OptiX 720p、16 spp、自适应采样加 OptiX 降噪，约 0.55 s/帧；
   - `final`：1080p、128 spp，约 13.5 s/帧，用户明确要展示级画质时才用；
   - `eevee`：最快，但玻璃门会渲成不透明，挡住箱内动作，本场景不用。
6. **先测吞吐，再开全片**：先渲染 3–6 帧，检查曝光、机位和每帧耗时，再渲全片。逐帧写盘，已经存在的帧会跳过，中断后可以接着渲。渲完由收尾脚本编码成片并运行验证门。

## 踩过的坑

- **收尾脚本死等**：用 `pgrep -f render_frames.py` 判断渲染是否结束，会匹配到父 shell 自己的命令行，所以永远等不完。要按进程名检查 `blender.exe`。

- **Windows 版 Blender 读不到 WSL 的 `/tmp`**：Blender 脚本和中间文件都要放在 `/mnt/d` 下。
- **第一版灯光严重过曝**：沿用了建模预览的灯光强度，而整个场景几乎全是白色材质。降到约三分之一，再把曝光调到 −0.5 才正常。
- **机位**：最初从右前方平视，观察站正好挡在前景，取板动作看不清。改成右前方高位俯视后，培养箱内部、机械臂和抽屉三者都能看到。
- **一开始就用了展示级档位**：1080p、128 spp 下每帧 13–15 s（RTX 3070 Ti Laptop），全片 1621 帧要约 6 h。渲到第 490 帧时用户指出没必要，改成 draft 档位后每帧约 0.55 s，快了约 25 倍，画面只是玻璃门上多一点颗粒。要先问清楚成片给谁看，审阅用途就用 draft 档位。P3 当年用 CPU 渲染，每帧 89–192 s。

## 全流程实验室（cell-passaging-lab）新增经验

- **复用资产的父对象绑定**：复用资产（工作站、离心机）的视觉不在 body 原点，父对象按下式取位姿：
  `对象世界 = S_body(t) @ R_body_rest⁻¹ @ StationT @ E_rest`
  - `S_body(t)`：仿真里这个 body 当前的世界位姿；
  - `R_body_rest`：原始模型零位下这个 body 的世界位姿，由 `prep_render.py` 写进 `rest_frames.json`；
  - `StationT`：工位的摆放变换；
  - `E_rest`：父空物体在资产文件里的矩阵。

  有三个坑：
  - 从库里追加进来的对象，在 `view_layer.update()` 之前 `matrix_world` 是单位阵；
  - 离心机盖的空物体存档时是打开的（−100°），要先复位到关闭；
  - 把适配器改挂到转子下时要保留世界矩阵，否则整体偏 0.145 m。
- **字幕**：用 ffmpeg 的 libass 叠 ASS 字幕，字体用 Noto Sans SC。字幕显示当前步骤、教学等待的倒计时，计数结果之类的数值加"模拟数据"标注。
- **进展截图**：开发中途只渲关键帧，不渲成片。`render_shots.py` 在已经装配好的 `render_scene.blend` 上换机位重渲，不用重建场景；装配一次 1.1 万帧的场景要十几分钟，换机位要避免重建。`progress/make_sheet.py` 把截图拼成带说明的 WebP。
- **全程成片**：全程只装配一次，`set_camera_segments.py` 给每期设一个固定机位（CONSTANT 关键帧，期间硬切），渲完再按期的边界切出各期成片（`render_full.sh`）。2.7 万帧 PNG 约 25 GB，上传 HF 时只传成片和关键帧。教学等待用每秒一行字幕显示倒计时。
- **Blender 5 的分层动作**：`action.fcurves` 已经不存在，要经 `action.layers → strips → channelbags → fcurves` 取。用 `getattr(action, "fcurves", [])` 会静默拿到空列表，插值没改成 CONSTANT。相机分段于是在两个机位之间渐变；刚体每帧都有关键帧，所以不受影响。改法：按分层 API 取 fcurve，并在每段末帧再压一个同值关键帧。
- **传给 Windows 版 Blender 的输出目录要用绝对路径**：`wslpath -w` 对相对路径原样返回，Blender 的工作目录是 `C:\`，帧就写到了 `C:\<目录名>`，项目目录里看不到。之前"渲了却没有文件"就是这个原因。
- **分期的状态文件**：`build_render_scene.py` 的第二个参数可以指定状态文件。状态文件里没有的刚体整棵隐藏；后加的板复制观察站自带的板、盖视觉。
- **非接触场景陈设（Scene Dressing）合入**：不参与碰撞的丰富件（墙面线槽插座、台下 UPS 电源盒、顶部波纹管集气罩、玻璃柜内试剂瓶）以 `VIS_pixal3d__*` / `VIS_dress__*` 命名挂入独立 Collection，不在 `states_30fps.npz` 中打关键帧；大件规整箱体（冰箱、透明玻璃门试剂柜）用 Blender 参数化外壳 + 贴图或透明玻璃门，内部摆放生成的 3D 小件。WSL 调用 Windows `blender.exe` 须先 `cd /mnt/d/...` 并加 `< /dev/null` 防止管道挂起。详见 `docs/lessons/09-pixal3d-colab-scene-dressing.md`。
- **从仿真白盒到真实感实验室的六步 Look-Dev 流程**：
  1. **结构底图 + 2D AI 概念图锚定质感（Style Lock）**：从已绑定位姿的 Blender 场景按分期机位导出白盒结构图，在严格锁死透视构图的前提下生成真实感目标图（`01_overview_real.webp`、`02_workstation_real.webp`、`03_centrifuge_real.webp`），拆解出材质配方、机电陈设、打光与品牌标识清单。
  2. **根治透明防护门折射重影（Zero-Refraction Thin Architectural Glass）**：对有厚度的聚碳酸酯前门（`front_door_clear_-1/1`）、侧/后透明板（`left_clear_panel`、`rear_clear_panel`）或亚克力护栏，若使用 `Principled BSDF(Alpha=0.28, Transmission=0.96, IOR=1.06)`，Cycles 会把 72% 不偏折的直线穿透光线（`IOR=1.0`）与 28% 经厚板折射偏移的光线（`IOR=1.06`）叠加，在 `0.3–0.6 m` 观察距离下产生约 `2 cm` 横向错位的“双重曝光重影”，同时高反射还会把箱外机械臂倒映进箱内。**标准解法**：一律改用 `Mix Shader(fac=0.03)` 混合 `97% Transparent BSDF`（零折射直线穿透）与 `3% Glossy BSDF(Roughness=0.03)`，并隐藏移液头 `v03_Z_joint` 上烘焙的静态吸头 `v03_tip_200ul`（避免与动态 `VIS_tip_0..7` 重叠）。
  3. **消除墙面插座与设备间“断头电线”伪影**：单图 3D 生成的插座模型（`clean_wall_socket_clean.glb`）在底部 `4.8 cm` 处把参考图里的断头短线与白墙背景烘焙成了凸出网格（`y = -1.420`），会遮挡后方的手写电缆形成“白色断口”；同时若电缆终点只停在设备包围盒外侧（如 `y = -0.94` 而非离心机壳体内部 `y = -0.76`），俯视镜头下会露出悬空断头。**标准解法**：① 导入插座 GLB 后用 `bmesh.ops.bisect_plane(plane_co=(0,0,0.048), plane_no=(0,0,1), clear_inner=True)` 切除底部烘焙残线；② 在插孔正前方放置 3D 模压黑插头护套（`plug_head` + `plug_boot`），4 阶 NURBS 悬链线从黑插头护套内部起算，另一端穿过设备后壁防水接头（`rear_gland`）深入设备机壳内部 `5–8 cm`；③ 将南北墙线槽、插座、插头与连接线归入 `SOUTH_WALL_OBJS` / `NORTH_WALL_OBJS`，随分期镜头朝向同步给 `hide_render` 打 `CONSTANT` 关键帧（看北面时隐藏南墙及南墙线缆，期 3 看南面离心机时显示南墙及南墙线缆、隐藏北墙及北墙线缆）。
  4. **低调克制的工业品牌标识（`LUMEN TECH` & `LAB WORLD`）**：浅色烤漆面板采用哑光深石板灰丝印材质（`Base Color (0.20, 0.22, 0.25), Roughness=0.48`，挤出 `0.4 mm`），深灰理化板台面采用半金属浅银灰激光镭雕材质（`Base Color (0.56, 0.58, 0.61), Metallic=0.65, Roughness=0.32`，挤出 `0.3 mm`）。运动部件上的标识挂为对应刚体（`v03_Z_joint`、`ROOT_rail_carriage`）的子对象；会大幅翻转开启的部件（如期 3 打开 $-100^\circ$ 的离心机盖）不放静态水平文字。
  5. **箱内顶置补光 + AgX 色调映射**：在移液工作站内部顶板下加 `45 W` 面光（`VIS_dress__ws_interior_led`）照亮深灰理化板台面与孔板，配合全局 `AgX` View Transform（`Exposure = -0.65`），兼顾白墙高光不溢出与箱内暗部细节通透。

## 阶段日志摘要

构建与绑定约 0.3 h，返工 4 次（含画质档位）。全片 1621 帧用 draft 档位渲染，共 16.3 min，平均 0.6 s/帧。V1–V4 全部 PASS，成片 54.033 s。
