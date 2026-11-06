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

## 阶段日志摘要

构建与绑定约 0.3 h，返工 4 次（含画质档位）。全片 1621 帧用 draft 档位渲染，共 16.3 min，平均 0.6 s/帧。V1–V4 全部 PASS，成片 54.033 s。
