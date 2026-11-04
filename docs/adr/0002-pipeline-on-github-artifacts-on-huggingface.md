# 流程放 GitHub，项目产物放 HuggingFace

GitHub 仓库 `world-building`（private）只存流程本身：skills、经验记录、GLOSSARY、ADR、脚本、方案预览模板，不存任何二进制资产。每个项目的产物（.blend、MJCF、USD、参考图、渲染、方案预览 HTML、阶段日志、plan.md）存 HF private dataset `RickC1999/world-building-projects`，本地克隆在 `D:\Projects\Robots\projects\`。1103/1104 旧资产归档到 private `RickC1999/lumen-lab-archive`，因其含 CC BY-NC 与第三方许可文件，公开前需单独审查。

## 修订（2026-11-04）：方案预览进 GitHub

用户要求把方案预览这一系列 HTML 放进 GitHub 仓库，方便直接浏览和对比各版本。例外范围只限方案预览：`uv run wb publish <项目>` 会把 `02-proposal/` 复制到仓库的 `proposals/<项目名>/`，复制时排除 `preview_*` 截图，图片统一用 WebP，每个项目约 0.5 MB。项目目录里的那份仍然是源，验证门也只检查源。其余产物照旧只放 HF。
