"""项目目录契约（见 docs/agents/project-layout.md）。"""

from __future__ import annotations

from pathlib import Path

from wb.gate import STAGES

STAGE_TITLES = {
    "requirements": "需求访谈",
    "proposal": "方案预览",
    "plan": "plan",
    "reference": "参考图",
    "modelling": "建模",
    "simulation": "仿真",
    "render": "位姿绑定与渲染",
}

STAGE_LOG = """# 阶段日志

每个阶段结束时填一行；“主要卡点”写一句话，细节写在下方同名小节。阶段复盘按此表排序。

| 阶段 | 开始 | 结束 | 墙钟耗时 | agent 轮数 | 验证门失败次数 | 返工次数 | 人工介入次数 | 时间上限 | 主要卡点 |
|---|---|---|---|---|---|---|---|---|---|
{rows}
"""


def new_project(root: Path, title: str) -> None:
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"{root} 已存在且非空")
    root.mkdir(parents=True, exist_ok=True)
    for d in STAGES.values():
        (root / d).mkdir()
    (root / "gates").mkdir()
    rows = "\n".join(f"| {STAGE_TITLES[s]} |  |  |  |  |  |  |  |  |  |" for s in STAGES)
    (root / "stage-log.md").write_text(STAGE_LOG.format(rows=rows), encoding="utf-8")
    (root / "README.md").write_text(
        f"# {title}\n\n项目目录契约见 world-building 仓库 `docs/agents/project-layout.md`。\n",
        encoding="utf-8",
    )
