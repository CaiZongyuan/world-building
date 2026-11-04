"""命令行：`wb gate <项目目录> <阶段>`、`wb new <项目目录>`。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from wb.gate import STAGES, run_gate
from wb.project import new_project, publish_proposal

ICON = {"PASS": "✅", "FAIL": "❌", "NOT_RUN": "⏸", "BLOCKED": "⛔", "IDEALIZED": "🟡"}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="wb")
    sub = p.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("gate", help="运行某阶段的验证门")
    g.add_argument("project", type=Path)
    g.add_argument("stage", choices=list(STAGES))
    n = sub.add_parser("new", help="按项目目录契约新建项目")
    n.add_argument("project", type=Path)
    n.add_argument("--title", required=True)
    pub = sub.add_parser("publish", help="把项目的方案预览复制到仓库 proposals/<项目名>/")
    pub.add_argument("project", type=Path)
    pub.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    rv = sub.add_parser("review", help="生成审批点②页面 04-reference/index.html")
    rv.add_argument("project", type=Path)
    a = p.parse_args(argv)

    if a.cmd == "review":
        from wb.review import build_review_page
        print(f"已生成 {build_review_page(a.project)}")
        return 0

    if a.cmd == "publish":
        dst = publish_proposal(a.project, a.repo)
        print(f"已发布到 {dst}")
        return 0

    if a.cmd == "new":
        new_project(a.project, a.title)
        print(f"已新建项目 {a.project}")
        return 0

    r = run_gate(a.project, a.stage)
    print(f"{ICON[r.status]} {r.stage}: {r.status}")
    for c in r.checks:
        extra = f" — {c.detail}" if c.detail else ""
        print(f"  {ICON[c.status]} {c.name}{extra}")
    return 0 if r.status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
