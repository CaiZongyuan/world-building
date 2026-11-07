---
name: lab-scene-pipeline
description: 场景流程：把实验室或工作站的需求一路做到可仿真、可渲染的三维场景，依次经过需求访谈、方案预览、plan、参考图、建模、仿真、渲染。适用于新建实验室/工作站场景项目、设计黑灯实验室的某个工艺步骤，或继续推进一个已有的场景项目。
---

# 场景流程

给第一次接触流程的人（包括用户）：先看教程站点 https://caizongyuan.github.io/world-building/（源码 `site/`），物理部分有可在浏览器里运行 MuJoCo 的实验台。

把一个**项目**按固定的**阶段**推进。每个阶段都要满足四件事才算完成：先写阶段说明，做出产物，**验证门**判 PASS，并写好**阶段日志**和**经验记录**。术语以 `GLOSSARY.md` 为准；项目目录结构、验证门命令和外部工具的用法见 `docs/agents/project-layout.md`。

用户只在两个**审批点**出场：方案预览之后、参考图（连同 plan）之后。其余时间由 agent 自主推进。尺寸、夹具、布局、层位这类工程细节由 agent 自己决定，写清理由和证据即可，不交给用户确认。全程不写时间预估，阶段日志只记实测数据。

## 每个阶段的固定动作

1. **阶段说明**：用几句话告诉用户这一阶段的输入、要做什么、用什么工具、怎么算完成、最可能出什么问题。
2. 做出产物，并放在 `<项目>/<阶段目录>/` 下。
3. `uv run --extra sim wb gate <项目> <阶段>` 判 PASS。判 FAIL 时先复盘，调整做法后再跑；只有完全卡死才停下来报告。门限一旦冻结就不再放宽，失败记录也全部保留。
4. 在 `stage-log.md` 里填好这一阶段的一行和卡点小节，并更新 `docs/lessons/` 中对应的文件。
5. 同步：`hf upload` 上传项目目录；如果改了流程代码或文档，用 git 提交并推送。

## 阶段

### 1 需求访谈 → `01-requirements/requirements.md`
用 grilling 的方式分轮提问，只问会改变方案的决定（范围、执行者、保真度、预算），能查到的事实先由子代理查清。需求记录必须包含六节：目标、不做什么、工艺步骤、设备、保真度、算力预算。

写需求记录之前，先把**场景、流程、资产三张清单**摊开给用户确认。资产要实查（能不能编译、缺不缺文件），不能只看说明文档。范围大时，做一页范围预览 `01-requirements/preview/index.html`。做法见 `docs/lessons/01-requirements-grilling.md`。

### 2 方案预览 → `02-proposal/index.html`（审批点①）
1. 用 `uv run wb new` 建好项目；把 `templates/proposal/assets/` 复制到 `02-proposal/assets/`。
2. **运动学预演**（`uv run --extra sim wb preflight <preflight.json>`，格式见 `docs/agents/project-layout.md`）：设备、工件、夹具全部用方盒代理，尺寸取自真实资产，做三件事：
   - 核对夹爪行程是否覆盖工件尺寸；
   - 用多初值、带碰撞检查的 IK 解出取、放两个关键位姿，写明进出方向和张合轴；
   - 做两类扫掠检查：机器人对环境，门和抽屉对静态环境。

   预演的结论写进"工程决策"一节。
3. 页面共 8 节；图片一律用 WebP，外部素材只引用不嵌入，并逐条标明许可。生成图片的方法见 `docs/agents/image-generation.md`。
4. 用 `uv run wb publish <项目>` 把页面发布到仓库的 `proposals/`，然后请用户审批。

做法见 `docs/lessons/02-proposal-preview.md`。

### 3 plan → `03-plan/plan.md` + `thresholds.json`
按阶段列出可勾选的任务。冻结带编号的门限（S/M/R/V）和负例（N），并同时写进 `thresholds.json`，验证门只读这个文件。负例清单写进 `thresholds.json` 的 `simulation.negatives`。每个负例都要先做一次危险探针（用独立小模型扫参数），确认它针对的危险在操作范围内确实会发生。做法见 `docs/lessons/03-plan.md`。

### 4 参考图 → `04-reference/`（审批点②，连同 plan 一起审）
参考图只冻结外观风格；尺寸以 `dimensions.md` 为准，每项都标明来源类别。另画一张载荷链 `load_path.svg`。用 `uv run wb review <项目>` 生成审批页。做法见 `docs/lessons/04-reference-images.md`。

### 5 建模 → `05-modelling/`
1. `design.py` 是唯一的参数源，Blender 构建和 MJCF 构建都从它读取。
2. 命名约定：`ROOT_` / `VIS_` / `COL_`；导出 GLB 时按白名单只选视觉对象，导出后再读回检查。
3. **参数化与 AI 3D 生成分工及 Colab 五阶段零浪费流程**：
   - **分工**：核心交互设备及大件规整箱体（冰箱、透明玻璃门试剂柜、实验台架）用 Blender 参数化建模（玻璃柜用参数化外壳+透射玻璃门，内部小件逐个生成后摆入；或冰箱用规整几何体+外部贴图）；非接触异形小件与柜内陈设（排风波纹管与集气罩、带盘绕电线的电源盒、墙面插座插头、柜内试剂瓶、废料桶）用 `colab-operator` 在 Colab L4 批量运行 Pixal3D 生成 `.glb`。
   - **Colab 五阶段 SOP**：① **开机前（0 CU）**：筛好物件、备齐 `.webp` 净图、跑 `colab sessions` 查孤儿实例、将输入与脚本打成单包 `colab_payload.tar.gz`，挂载 `trap 'colab stop ...' EXIT`；② **开机与双轨并行初始化（~65 s）**：申请 L4 并单次上传，前台 `uv venv --python 3.10` 装预编译 CUDA wheels + 打补丁（`~52 s`），后台同时用 `HF_HUB_ENABLE_HF_TRANSFER=1` 8 线程并发预取 16.7 GB 权重（`~60 s`）；③ **单进程四步批量生成（~129 s/个）**：批量 `BiRefNet` 抠图即卸 $\rightarrow$ 批量 `MoGe-2` 估外参即卸 $\rightarrow$ 共享 `DINOv3+NAF` 跑 `1024_cascade` 扩散 $\rightarrow$ 子进程 `export_glb_worker.py` 烘焙打包；④ **Gate A 秒级校验与立即关机（~5 s）**：单包下载 `outputs.tar.gz`，本地 `< 0.1 s` 校验 glTF 2.0 魔数头与面数，**通过后立即 `colab stop` 并确认 `No active sessions.`**（绝不挂着 GPU 等本地 Blender）；⑤ **Gate B 本地修模与合入（0 CU）**：Blender `2 mm` 空间容差去碎块与最小包围盒自动调平后作为 `VIS_` 合入。
4. 预览渲染只作为验证证据，不需要审批。图片一律用 WebP。

做法见 `docs/lessons/05-modelling.md` 与 `docs/lessons/09-pixal3d-colab-scene-dressing.md`。

### 6 仿真 → `06-simulation/`
1. 用 MjSpec 装配场景。
2. 先做运动学初筛，再跑动力学。
3. 跑名义流程和全部负例。

可达性、控制前馈、接触数值和 MjSpec 的几个坑，都在 `docs/lessons/06-simulation.md` 里，这是问题最多的阶段。

### 7 位姿绑定与渲染 → `07-render/`
按顺序做，每步做到判据为止。机位、运镜、倍速和成本的完整说明见教程 `site/stages/footage.md`；踩坑与实测数据见 `docs/lessons/07-pose-binding-render.md`。
1. **位姿绑定**：视觉根和 MuJoCo body 一一对应，逐帧写入位姿（插值 `CONSTANT`）。挂在 body 上的视觉件（夹爪指垫、治具）与碰撞件从同一份设计参数现建，不从旧 `.blend` 拷。判据：`binding_report.json` 中 V1、V3 通过；在最终渲染用的场景上跑 `check_grasp.py`，每次搬运两根手指到被夹物都 ≤ 1 mm（V5）。仿真夹住了、画面却隔空，就是视觉件和碰撞件对不上。
2. **look-dev（要逼真时）**：用亮度统计（均值、p50/p95、削顶、饱和度、冷暖）对照参考图校准。依次处理以下几项：
   - 反照率回到真实范围：白漆约 0.72；
   - 天花板加面板灯阵列；
   - Bevel 倒角、粗糙度噪声、颗粒地面、T 槽型材；
   - 门窗玻璃和透明耗材都用零折射薄层，降噪用 OIDN；
   - 隔断后的背景纵深；
   - 设备和机械臂贴标签贴花（射线落点 + Shrinkwrap 贴曲面）。
   - 被夹的透明件（孔板）加颜色提示：板底改彩色底托、侧面贴条码，否则夹在指垫里看着像夹了个空。

   墙用 `visible_camera` 隐藏。凡是改场景的脚本（装配、陈设、look-dev）都写进 `render_full.sh` 的步骤，从零重建要能复现成品。判据：统计对齐参考图，刚体位姿差 = 0；重建后 look-dev 报告的材质数、分段数和上一版一致。
3. **机位规划**：`footage/plan_footage.py` 按"哪个工位在动"给 7 类固定机位（一个全景，加上每个工位一个近景，关键工位再加一个角度）算时间窗。每一帧按"在发生什么"定**录制倍速**：关键动作 1×、工位操作 2×、搬运 4×、空闲 8×（全景放慢一档）。判据：每个机位都在自己的活动时段渲过测试帧，主体没被导轨上的机械臂挡住，曝光合适。
4. **剪辑表**：每个用途写一张 `edits/<名字>.json`，每段写机位、源时间段、剪辑倍速和备注。规则：
   - 关键动作 1–2×，工位操作 3–8×，搬运和等待 10–24×；
   - 剪辑倍速取录制倍速的整数倍；
   - 换工位时切机位，画面里不放字幕。
5. **渲染**：默认 `draft` 档位（720p、16 spp、OIDN）。`final` 档位只在用户要展示级画质时才用。先 `make_jobs.py`，再 `render_pass.sh jobs_pass1.json`（剪辑要用的帧，先出片），然后 `render_pass.sh jobs_pass2.json`（全部素材）。已存在的帧会被跳过，所以换了外观要先删旧素材；只改了机械臂手部这类局部，用 `footage/finger_visibility.py --delete` 只删看得到该部位的帧。判据：`wb gate` 的 V4a（素材完整）和 V4b（剪辑版帧数对得上）通过。

## 分期的大项目（全流程实验室）

步骤多时把工艺切成几期，plan 里给每期冻结一组门限（`simulation.phase_gates`），负例也标上所属的期。
1. **并行开发**：各期可以交给子代理在项目副本里开发，先用合成的起点。子代理卡住时由协调者接手，不放宽门限。
2. **集成**：从上一期的真实终态重跑。所有期用同一个模型（各期用到的工件和约束都放进场景），期末用 `chain.py` 存完整的 mjData 状态，下一期原样接上。`run_full.py` 依次跑完各期，合并结果，加终点门限，并把位姿按 30 fps 网格重采样。
3. **进展汇报**：开发中途不渲视频素材。用 `render_shots.py` 在已装配的场景上换机位渲关键帧，再用 `progress/make_sheet.py` 拼成带说明的 WebP。
4. **素材放到最后统一渲染**：全程只装配一次，按第 7 阶段第 3 条渲多机位素材，再按用途写剪辑表出片（全流程概览、单期、单工位都从同一批素材剪）。`render_full.sh` 依次跑 build → enrich（陈设）→ lookdev → grasp（V5）→ plan → render → finish。

集成时常见的问题见 `docs/lessons/06-simulation.md` 的"分期开发与集成"一节。

## 项目收尾

按阶段日志给各阶段排序，找出问题最大的阶段，写一份汇总复盘（参考 `docs/lessons/08-retro-slice01.md`），再把新得到的经验回写到本 skill 和对应的 lessons 文件里。流程本身变了（阶段、验证门、命令、规则），同步更新教程站点 `site/`，`pnpm build` 通过后再提交。
