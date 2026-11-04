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

| 阶段 | 开始 | 结束 | 墙钟耗时 | agent 轮数 | 验证门失败次数 | 返工次数 | 人工介入次数 | 主要卡点 |
|---|---|---|---|---|---|---|---|---|
{rows}
"""


def new_project(root: Path, title: str) -> None:
    if root.exists() and any(root.iterdir()):
        raise FileExistsError(f"{root} 已存在且非空")
    root.mkdir(parents=True, exist_ok=True)
    for d in STAGES.values():
        (root / d).mkdir()
    (root / "gates").mkdir()
    rows = "\n".join(f"| {STAGE_TITLES[s]} |  |  |  |  |  |  |  |  |" for s in STAGES)
    (root / "stage-log.md").write_text(STAGE_LOG.format(rows=rows), encoding="utf-8")
    (root / "README.md").write_text(
        f"# {title}\n\n项目目录契约见 world-building 仓库 `docs/agents/project-layout.md`。\n",
        encoding="utf-8",
    )


# 发布到仓库时排除的文件（截图等过程产物，体积大且不需要版本化）
PUBLISH_EXCLUDE = ("preview_",)  # 前缀匹配：截图类过程产物


def publish_proposal(project: Path, repo: Path) -> Path:
    """方案预览进 GitHub 仓库（ADR-0002 修订）：整目录覆盖复制到 proposals/<项目名>/。"""
    import shutil

    src = project / STAGES["proposal"]
    if not (src / "index.html").is_file():
        raise FileNotFoundError(f"{src} 没有 index.html")
    dst = repo / "proposals" / project.name
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=lambda d, names: [n for n in names if n.startswith(PUBLISH_EXCLUDE)])
    return dst
