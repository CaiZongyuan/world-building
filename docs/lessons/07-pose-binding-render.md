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

## Look-dev v2：Blender 侧真实感（cell-passaging-lab，对照 `*_real.webp` 逐项校准）

上面六步做完，画面仍然一眼假：整体发白发灰、没有明暗层次、材质像塑料、背景是一堵白墙。原因不在模型，而在 Blender 侧的四件事：反照率、灯光、表面微细节、相机。做法收在项目的 `07-render/lookdev_v2/lookdev_realism.py`（在已绑定的 `render_scene.blend` 上运行，另存 `render_scene_lookdev.blend`），静帧用 `render_lookdev.py` + `shots.json`。

1. **先量化再调**：用亮度统计对比参考图（均值、p5/p50/p95、>0.98 的削顶比例、饱和度 max−min、B−R 冷暖偏移）。旧渲染 p50 0.82、饱和度 0.01（几乎纯灰），参考图 p50 0.57、p95 0.83、饱和度 0.04、偏冷。之后每轮改动都看这几个数，不靠肉眼猜曝光。
2. **反照率回到真实范围**：白漆、白塑料原来是 0.86–1.0，真实白粉末涂层约 0.70–0.78。白墙 0.9 → 0.60（偏冷），地面颗粒 PVC 灰底约 0.11，理化板约 0.035。全白场景里只要有一个纯白反照率，二次反弹就把整个画面冲灰。
3. **灯光换成真实吸顶照明**：删掉 6 盏 1 m 裸面光，加天花板（0.68）和 600×600 面板阵列（区域光 + 自发光漫射板，反射里能看到灯盘），色温偏冷 (0.92, 0.965, 1.0)；世界背景 0.03 只做兜底。没有天花板时光往上漏、墙面靠世界光提亮，明暗是平的。
4. **表面微细节**（每个都很便宜，叠起来决定真假）：
   - 所有不透明硬表面加 Bevel 着色器（白漆 2.5 mm、铝 1.2 mm）：6 面方盒的棱角也能接到高光；
   - 粗糙度噪声（±0.05）、白漆橘皮凹凸（Noise 2600/m，强度 0.035）、Coat 0.12；
   - 地面：Voronoi 380/m 每格随机色 → 常值 ColorRamp 映到深/灰/浅/白四档颗粒，再叠 ±6% 大尺度明暗和 0.30–0.58 污渍粗糙度；
   - 理化台面：颗粒要细（1400/m）且对比低，否则读成花岗岩；
   - 4040 铝型材：6 面方盒换成带 T 槽的截面（`tslot_mesh`，53 根），这是参考图里最显眼的工业特征。
5. **玻璃：Fresnel 混合但背面不取 Fresnel**：薄玻璃仍用 Transparent（零折射，见上文第 2 步），混合系数从常数 0.03 改为 Fresnel(1.5)。坑：Fresnel 节点在背面按 1/IOR 计算，掠射角全内反射，整片玻璃渲成黑镜子。用 `Fresnel × (1 − Backfacing)` 只让入射面反射。
6. **背景纵深**：东墙换成铝框玻璃隔断，后面程序化生成一间邻实验室（5 个围栏工作站、岛台、远墙高柜、风管，`random.Random(7)` 固定），透过玻璃看到的是"还有别的实验室"而不是白墙。南北墙加服务带、Unistrut 立槽、桥架、PVC 线管、压缩空气管。
7. **墙组隐藏改用 `visible_camera`**：原来按机位切 `hide_render`，墙一隐藏就不挡光也不反射，房间漏光。改为把 hide_render 关键帧转成 `visible_camera` 关键帧；新加的墙面管线直接共用墙的 action（`ad.action` + `action_slot`），机位切换时一起对相机隐藏。
8. **标签贴花**：numpy 生成条码标签和黄色警示三角（感叹号/闪电），打包进 .blend，贴在培养箱、成像仪、离心机、开盖器、工作站、滑台立柱、台沿共 17 张；运动件上的贴花挂到对应 ROOT 下（局部坐标），开合的培养箱门按 frame 0 的门矩阵换算后挂在门根上。
9. **相机与合成**：按机位段给景深（全景 f/8、工作站 f/4、离心机 f/5.6）和曝光（−1.0 / −0.5 / −0.9 / −1.0）打 CONSTANT 关键帧；合成用 Blender 5.4 的 `scene.compositing_node_group`（没有 `scene.node_tree`、没有 Composite 节点，输出是 Group Output，混合用 ShaderNodeMix）：色散 0.006、Bloom（阈值 4.0、强度 0.06）、暗角、静帧加胶片颗粒。
   - **Bloom 阈值别低于场景白**：第一版阈值 1.2，白墙本身就超过阈值，整张图像蒙了一层雾。
   - **颗粒只给静帧**：颗粒用的是一张固定噪声图，逐帧不变，放进成片就像镜头脏了。存盘的 .blend 颗粒为 0，`render_lookdev.py` 渲静帧时才打开。
10. **AgX + Medium High Contrast**：5.4 的 look 名带前缀 `"AgX - Medium High Contrast"`。
11. **静帧连渲不要让镜头之间串状态**：某个镜头要用另一个机位段的墙组可见性时（`shots.json` 的 `vis_frame`），会清掉墙组动作、写死 visible_camera。同一进程里的下一个镜头会继承这个状态：06 因此少了南墙，左侧成了黑洞。每个镜头开始前先还原墙组原始动作。贴花也要逐个镜头检查：工作站下柜的条码一开始盖住了门上的 LUMEN TECH 丝印。

12. **成片低采样下透明耗材会出"碎冰"闪点**：静帧 512 spp 很干净，成片 draft（720p / 16 spp）里孔板、储液槽、吸头却满是闪点，加到 128 spp 仍在。有两个原因：
    - 这些耗材还是 Principled 折射透射，look-dev 第一轮只改了门窗玻璃；
    - OptiX 降噪器压不住多层透明件的噪声：每一层都在透明和反射之间随机选分支，各像素选中的组合不同。

    处理分两步：
    - 把薄壁塑料和薄液层（`clear_pp`、`PP_natural`、`plate_clear`、四种液体等 8 种）也改成零折射薄层：Transparent 与按原透射比例混入的 Diffuse 组成本体，再按正面 Fresnel 混 Glossy。清澈塑料单层的透射色只保留 30% 色偏，否则孔板多层叠起来发蓝。
    - 成片降噪器改为 OIDN（GPU，精确预滤波）。16 spp 下闪点消失，耗时和 OptiX 一样。
13. **换外观重渲前先清空 `frames/`**：`render_frames.py` 会跳过已存在的帧（为了能中断续跑），旧画面的帧留在目录里就不会被重渲。`render_full.sh` 加了 `lookdev` 步（camera 之后、render 之前），render 步改读 `render_scene_lookdev.blend`。

实测（RTX 3070 Ti Laptop）：
- 预览 836×470 / 64 spp：每张 3–5 s（首张含内核编译和 BVH 约 100 s）。
- 终版 1672×941 / 512 spp：每张 53–86 s。
- 成片 draft（720p / 16 spp / OIDN）：每帧 1.5–2.1 s，首帧约 4 s。旧画面是 1.1 s/帧。
- draft 改采样数，OptiX 降噪：32 spp 3.6–3.9 s/帧，64 spp 6.4–6.9 s/帧，128 spp 12–13 s/帧，基本按采样数线性增长，自适应采样省不下多少。
- 工作站近景 150 帧连续片段：静止区域相邻帧平均差约 0.1/255（种子固定为 0、不随帧变化），没有降噪闪烁。

**校验**：对比 `render_scene.blend` 和 `render_scene_lookdev.blend`，6 帧 × 48 个刚体根的世界矩阵最大差 0；V1 无碰撞对象。look-dev 只改视觉，不需要重跑仿真。

**结果**（同帧同机位，与参考图对比）：全景均值 0.537 / p50 0.585 / p95 0.830 / 饱和度 0.037，参考图 0.548 / 0.573 / 0.835 / 0.040；工作站、离心机机位同样落在参考图附近，无削顶。

## 阶段日志摘要

构建与绑定约 0.3 h，返工 4 次（含画质档位）。全片 1621 帧用 draft 档位渲染，共 16.3 min，平均 0.6 s/帧。V1–V4 全部 PASS，成片 54.033 s。
