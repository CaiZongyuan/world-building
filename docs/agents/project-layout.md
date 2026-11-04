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
