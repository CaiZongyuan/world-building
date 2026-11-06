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
3. **参数化与 AI 3D 生成分工**：核心交互设备及大件规整箱体（冰箱、透明玻璃门试剂柜、实验台架）用 Blender 参数化建模（玻璃柜用参数化外壳+透射玻璃门，或冰箱用规整几何体+外部贴图）；非接触异形小件与柜内陈设（排风波纹管与集气罩、带盘绕电线的电源盒、墙面插座插头、柜内试剂瓶、废料桶）用 `colab-operator` 在 Colab L4 批量运行 Pixal3D 生成 `.glb`，经 Blender `2 mm` 空间容差去碎块与最小包围盒自动调平后作为 `VIS_` 合入。
4. 预览渲染只作为验证证据，不需要审批。图片一律用 WebP。

做法见 `docs/lessons/05-modelling.md` 与 `docs/lessons/09-pixal3d-colab-scene-dressing.md`。

### 6 仿真 → `06-simulation/`
1. 用 MjSpec 装配场景。
2. 先做运动学初筛，再跑动力学。
3. 跑名义流程和全部负例。

可达性、控制前馈、接触数值和 MjSpec 的几个坑，都在 `docs/lessons/06-simulation.md` 里，这是问题最多的阶段。

### 7 位姿绑定与渲染 → `07-render/`
1. 视觉根和 MuJoCo body 一一对应，逐帧写入位姿。
2. 成片默认用 `draft` 档位（720p、16 spp、降噪），够工程审阅看动作和干涉；`final` 档位只在用户要展示级画质时才用。
3. 先渲几张关键帧，测吞吐、调曝光和机位，再渲全片；渲完由收尾脚本编码成片并运行验证门。

成片不加速、不剪辑。做法见 `docs/lessons/07-pose-binding-render.md`。

## 分期的大项目（全流程实验室）

步骤多时把工艺切成几期，plan 里给每期冻结一组门限（`simulation.phase_gates`），负例也标上所属的期。
1. **并行开发**：各期可以交给子代理在项目副本里开发，先用合成的起点。子代理卡住时由协调者接手，不放宽门限。
2. **集成**：从上一期的真实终态重跑。所有期用同一个模型（各期用到的工件和约束都放进场景），期末用 `chain.py` 存完整的 mjData 状态，下一期原样接上。`run_full.py` 依次跑完各期，合并结果，加终点门限，并把位姿按 30 fps 网格重采样。
3. **进展汇报**：开发中途不渲成片。用 `render_shots.py` 在已装配的场景上换机位渲关键帧，再用 `progress/make_sheet.py` 拼成带说明的 WebP。
4. **成片放到最后统一渲染**：全程只装配一次。`set_camera_segments.py` 给每期设一个固定机位（某一期可以整期用近景），期与期之间硬切。全片渲完后，按期的边界切出各期成片（`render_full.sh`）。

集成时常见的问题见 `docs/lessons/06-simulation.md` 的"分期开发与集成"一节。

## 项目收尾

按阶段日志给各阶段排序，找出问题最大的阶段，写一份汇总复盘（参考 `docs/lessons/08-retro-slice01.md`），再把新得到的经验回写到本 skill 和对应的 lessons 文件里。流程本身变了（阶段、验证门、命令、规则），同步更新教程站点 `site/`，`pnpm build` 通过后再提交。
