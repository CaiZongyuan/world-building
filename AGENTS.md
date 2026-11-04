# World Building

把实验室/工作站需求变成可仿真、可渲染三维场景的流程。术语见 `GLOSSARY.md`，关键决策见 `docs/adr/`，阶段经验见 `docs/lessons/`。

- 正文用中文；代码、文件名、标识符用英文。
- 本仓库只放流程本身；项目产物放 HF `RickC1999/world-building-projects`，不进 git（ADR-0002）。
- 生成图片按 `docs/agents/image-generation.md`。
- 项目目录、验证门命令、外部工具调用见 `docs/agents/project-layout.md`；测试 `uv run --extra sim pytest`。
- 新建或推进场景项目：用 skill `lab-scene-pipeline`。

## Agent skills

### Issue tracker

Issues 和 spec 放在 GitHub Issues（`CaiZongyuan/world-building`，用 `gh`）。See `docs/agents/issue-tracker.md`.

### Triage labels

使用默认五个标签（needs-triage、needs-info、ready-for-agent、ready-for-human、wontfix）。See `docs/agents/triage-labels.md`.

### Domain docs

Single-context：根目录 `GLOSSARY.md` + `docs/adr/`。See `docs/agents/domain.md`.
