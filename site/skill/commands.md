---
title: 命令速查
description: wb 命令行（new、gate、preflight、publish、review）、大项目脚本、渲染、同步，以及外部工具的调用方式。
---

# 命令速查

所有命令都在 `world-building` 仓库根目录运行。`<项目>` 指项目目录，例如 `/mnt/d/Projects/Robots/projects/cell-passaging-lab`。

## wb 命令行

```bash
# 新建项目（按项目目录契约生成骨架，不要手工拼目录）
uv run wb new /mnt/d/Projects/Robots/projects/<项目> --title "标题"

# 跑验证门：requirements proposal plan reference modelling simulation render
uv run --extra sim wb gate <项目> <阶段>

# 方案预览：运动学预演（输出 preflight_report.json 和俯视图）
uv run --extra sim wb preflight <preflight.json> --out <目录>

# 方案预览：发布到仓库 proposals/<项目名>/
uv run wb publish <项目>

# 参考图：生成审批点②页面 04-reference/index.html
uv run wb review <项目>
```

`wb gate` 输出 PASS / FAIL / NOT_RUN / BLOCKED / IDEALIZED，写入 `gates/<阶段>.json`，退出码 0 只代表 PASS。建模门要用 MuJoCo 编译模型、跑静置测试，不带 `--extra sim` 时判 BLOCKED；skill 里统一带上它。

## 测试

```bash
uv run --extra sim pytest          # 每道门都有正例和负例夹具（tests/fixtures/）
```

## 大项目

```bash
# 四期接力连跑（每期接上一期的完整状态），可从第 k 期续跑
python 06-simulation/run_full.py [k]

# 渲染：装配、陈设、look-dev、量夹持间隙（V5）、规划机位与录制倍速、渲素材、拼剪辑版并跑门（可分步，已存在的帧会跳过）
bash 07-render/render_full.sh [build|enrich|lookdev|grasp|plan|render|finish]
# 改了手部这类局部外观后，只删看得到该部位的素材帧再续渲
python 07-render/footage/finger_visibility.py --delete
# 只渲一轮素材任务（pass1 = 剪辑要用的帧，pass2 = 全部素材）
bash 07-render/footage/render_pass.sh jobs_pass1.json draft
# 按剪辑表拼片 → 07-render/videos/<name>_draft.mp4
python 07-render/edits/make_edit.py 07-render/edits/main_v1.json draft

# 进展截图、修复前后对比：在渲染场景上换一个临时机位渲几帧（渲染设置与素材相同），再拼成带说明的 WebP
blender -b 07-render/render_scene_lookdev.blend --python 07-render/render_shots.py -- <输出目录> <帧列表> '<相机 JSON>'
python progress/make_sheet.py ...
```

这些脚本在项目目录里，随项目一起保存在 HF 上，不在仓库里。

## 同步

```bash
cd /mnt/d/Projects/Robots/projects
uvx --from huggingface_hub hf upload RickC1999/world-building-projects <项目> <项目> --repo-type dataset --commit-message "..."
uvx --from huggingface_hub hf download RickC1999/world-building-projects --repo-type dataset --include "<项目>/*" --local-dir .
```

HF 不保存空目录，所以刚拉下来的项目缺某个阶段目录很正常，对应阶段的验证门判 NOT_RUN。

## 外部工具（从 WSL 调用）

| 工具 | 调用方式 | 注意 |
|---|---|---|
| Blender 5.4 | `cd /mnt/d/... && /mnt/d/Environment/blender-5.4.0/blender.exe -b --factory-startup --python <脚本> -- <参数> < /dev/null` | 路径参数先用 `wslpath -w` 转成 Windows 绝对路径；在 `/mnt/d` 下启动并加 `< /dev/null` 防止 WSL2 管道阻塞；每次启动约 7 秒，操作合并到一个脚本里 |
| Colab GPU | `colab exec -s <name> ...`（`colab-operator` skill） | 开机前打包全部 `.webp` 与脚本并设 `trap 'colab stop ...' EXIT`；开机后 `uv venv` 与 `HF_HUB_ENABLE_HF_TRANSFER=1` 双轨并行初始化（`~65 s`）；单进程批处理后下载 `outputs.tar.gz`，本地 `< 0.1 s` 校验 GLB 二进制头通过后**立即 `colab stop` 并用 `colab sessions` 确认清零**，再跑本地 Blender |
| MuJoCo | `uv run --extra sim python ...` | CPU 运行 |
| imagegen | 见仓库 `docs/agents/image-generation.md` | 生成后立即转 WebP |

## 物理实验台

```bash
uv run --extra sim python site/labs/play.py --list               # 列出全部实验和参数
uv run --extra sim python site/labs/play.py drop h=4 tc=2         # 在本机 MuJoCo 窗口里播放
uv run --extra sim python site/labs/runner.py [实验 ...]          # 重新生成网页用的预计算回放
```

## 本教程站点

```bash
cd site
pnpm install
pnpm dev        # 本地预览 http://127.0.0.1:5292/world-building/
pnpm build      # 构建；新增中文字符时先跑 pnpm font 重新切字体子集
```

推送到 `main` 后，GitHub Actions 会自动构建并发布到 GitHub Pages。
