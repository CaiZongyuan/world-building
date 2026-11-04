# 项目目录契约

每个项目对应流程的一次运行，在 `D:\Projects\Robots\projects\<项目名>\`（WSL：`/mnt/d/Projects/Robots/projects/<项目名>/`）下建一个目录。整个 `projects/` 目录是 HF private dataset `RickC1999/world-building-projects` 的本地镜像，每个项目对应其中一个子目录（ADR-0002）。

## 结构

```
<项目名>/
├── README.md            项目标题
├── stage-log.md         阶段日志（每个阶段一行，另附卡点小节）
├── gates/<阶段>.json     验证门最近一次的判定结果与证据
├── 01-requirements/     需求访谈 → requirements.md
├── 02-proposal/         方案预览 → index.html + img/
├── 03-plan/             plan → plan.md
├── 04-reference/        参考图
├── 05-modelling/        建模
├── 06-simulation/       仿真
└── 07-render/           位姿绑定与渲染
```

新建项目：`uv run wb new <项目目录> --title "<标题>"`。不要手工拼目录。

## 验证门

```bash
uv run wb gate <项目目录> <阶段>   # 阶段：requirements proposal plan reference modelling simulation render
```

- 输出：PASS / FAIL / NOT_RUN / BLOCKED / IDEALIZED，并写入 `gates/<阶段>.json`。退出码 0 只代表 PASS。
- 阶段目录不存在，或该阶段还没有实现检查 → NOT_RUN。
- IDEALIZED 永远不算 PASS。
- 每个阶段的检查都要同时有正例夹具和负例夹具，放在 `tests/fixtures/`，用 `uv run pytest` 运行。

## 发布方案预览到仓库

`uv run wb publish <项目目录>`：把 `02-proposal/` 复制到仓库的 `proposals/<项目名>/`（ADR-0002 修订）。方案预览每改一次都要重新发布一次，再提交。

方案预览的样式：把仓库里的 `templates/proposal/assets/` 复制到 `02-proposal/assets/`，页面用 `<link rel="stylesheet" href="assets/theme.css">` 引用。主题沿用 spatial-sync 站点，支持浅色和深色两套，URL 加 `?theme=light|dark` 可强制切换。图片一律用 WebP（验证门会检查）。

## 同步

```bash
cd /mnt/d/Projects/Robots/projects
uvx --from huggingface_hub hf upload RickC1999/world-building-projects <项目名> <项目名> --repo-type dataset --commit-message "..."
uvx --from huggingface_hub hf download RickC1999/world-building-projects --repo-type dataset --include "<项目名>/*" --local-dir .
```

HF 不保存空目录。所以刚拉下来的项目缺少某个阶段目录很正常，对应阶段的验证门会判 NOT_RUN。

## 外部工具（从 WSL 调用）

- **Blender 5.4**：`/mnt/d/Environment/blender-5.4.0/blender.exe -b --factory-startup --python <脚本>`。路径参数必须先用 `wslpath -w` 转成 Windows 路径。每次启动约 7 秒，多个操作应合并到一个脚本里执行。
- **MuJoCo**：`uv run --extra sim python ...`，CPU 运行。
- **imagegen**：见 `image-generation.md`。

## 运动学预演（`wb preflight`）

方案预览阶段用它检查布局和夹具的运动学可行性：`uv run --extra sim wb preflight <preflight.json> [--out 目录]`，输出 `preflight_report.json` 和俯视图 `preflight_top.svg`。只做运动学，不跑动力学，一次几秒到几十秒。

`preflight.json` 的字段（单位 m、rad；盒子的 `size` 是半尺寸）：

- `robot`：`mjcf`（Menagerie Panda）、`base`、`yaw`；可选 `rail`（`axis`、`range`，导轨也作为 IK 的一个自由度）；`tool`：`tcp_in_hand`、`opening_range`，可选 `finger_boxes`（挂在左右手指上，右指自动镜像 x）、`hand_boxes`。
- `static`：静态方盒代理，`name`、`pos`、`size`，可选 `yaw`。**尺寸取自真实资产**，代理过大会产生误报。
- `movers`：门、抽屉等活动件：`joint`（`type` 为 hinge 或 slide，`anchor`、`axis`、`range`），`boxes`（相对锚点），可选 `rest`、`sweep_others`（扫掠时其他活动件的状态）、`attached_to`。
- `workpieces`：`name`、`grip_width`，用来核对夹爪行程（两侧各留 `grip_margin`，默认 5 mm）。
- `poses`：关键位姿，按顺序求解，后一个位姿优先选与前一个连续的构型。字段有 `pos`、`approach`（手爪进入方向）、`opening_axis`（手指张合方向）、`standoff`（沿进入方向的进出距离）、`movers`（此时各活动件的状态）、`finger_q`、`ignore`、`clearance`（贴着支撑面的夹取位姿可以放宽到 1 mm）；也可以直接给 `q` 关节角。两指夹爪默认对称（绕进入方向转 180° 视为同一个抓取）。
- `transitions`：`[[起点, 终点], …]`。关节插值逐点检查碰撞，并在两端所有可用构型（每个位姿最多 6 组）的组合里找一条无接触的。
- `clearance`：机器人与环境的安全余量，默认 5 mm。

四类结果：`G` 夹爪行程、`P` 关键位姿（含进出段）、`D` 活动件扫掠、`T` 过渡。
