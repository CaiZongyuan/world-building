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


def copy_tree_plain(src: Path, dst: Path, skip=lambda rel: False) -> None:
    """只复制文件内容，不复制权限和时间戳（/mnt/d 等 Windows 盘上 copystat 会被拒绝）。"""
    import shutil

    for p in sorted(src.rglob("*")):
        rel = p.relative_to(src)
        if skip(rel):
            continue
        if p.is_dir():
            (dst / rel).mkdir(parents=True, exist_ok=True)
        else:
            (dst / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, dst / rel)


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
    copy_tree_plain(src, dst, skip=lambda rel: rel.name.startswith(PUBLISH_EXCLUDE))
    review = project / STAGES["reference"] / "index.html"
    if review.is_file():  # 审批点②页面一并发布到 review/
        keep = {"index.html", "assets", "board", "load_path.svg"}
        copy_tree_plain(review.parent, dst / "review", skip=lambda rel: rel.parts[0] not in keep)
    return dst
