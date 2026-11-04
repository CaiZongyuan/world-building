"""审批点②页面：把参考图、尺寸表、载荷链、plan 汇成一页 HTML（04-reference/index.html）。

样式复用方案预览主题（templates/proposal/assets）；页面只读项目文件，不手写内容。
"""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

from wb.checks import markdown_sections
from wb.project import copy_tree_plain

THEME = Path(__file__).resolve().parents[2] / "templates" / "proposal" / "assets"


def _inline(md: str) -> str:
    s = html.escape(md)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", s)


def md_tables_and_lists(md: str) -> str:
    """足够渲染本项目 Markdown 的子集：### 标题、表格、- / - [ ] 列表、段落。"""
    out, rows, items = [], [], []

    def flush():
        nonlocal rows, items
        if rows:
            head, *body = rows
            out.append('<div class="table-wrap"><table><tr>' + "".join(f"<th>{_inline(c)}</th>" for c in head) + "</tr>"
                       + "".join("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in r) + "</tr>" for r in body)
                       + "</table></div>")
        if items:
            out.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
        rows, items = [], []

    for line in md.splitlines():
        if line.startswith("|"):
            if items:
                flush()
            if not re.match(r"^\|[\s|:-]+\|$", line):
                rows.append([c.strip() for c in line.strip().strip("|").split("|")])
        elif m := re.match(r"^- \[([ x])\] (.*)", line):
            if rows:
                flush()
            items.append(("☑ " if m.group(1) == "x" else "☐ ") + _inline(m.group(2)))
        elif m := re.match(r"^- (.*)", line):
            if rows:
                flush()
            items.append(_inline(m.group(1)))
        elif m := re.match(r"^###+ (.*)", line):
            flush()
            out.append(f"<h3>{_inline(m.group(1))}</h3>")
        elif line.strip():
            flush()
            out.append(f'<p class="small">{_inline(line)}</p>')
        else:
            flush()
    flush()
    return "\n".join(out)


def build_review_page(project: Path) -> Path:
    ref = project / "04-reference"
    plan = (project / "03-plan" / "plan.md").read_text(encoding="utf-8")
    secs = markdown_sections(plan)
    images = json.loads((ref / "reference.json").read_text(encoding="utf-8"))["images"]
    dims_md = (ref / "dimensions.md").read_text(encoding="utf-8")
    dims_body = dims_md.split("\n", 1)[1]  # 去掉一级标题
    dims_body = re.sub(r"^## (.*)$", r"### \1", dims_body, flags=re.M)
    title = (project / "README.md").read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()

    figs = "\n".join(
        f'<figure><img src="{i["file"]}" alt=""><figcaption>{html.escape(i["note"])} '
        f'<span class="mute">· {i["model"]} · 实得 {i["actual_size"][0]}×{i["actual_size"][1]}</span></figcaption></figure>'
        for i in images)

    page = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>审批点② 参考图与 plan</title><link rel="stylesheet" href="assets/theme.css">
<script>try{{const q=new URLSearchParams(location.search).get('theme');const t=q||localStorage.getItem('wb-theme');if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<style>.board{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px}}</style>
</head><body>
<button class="theme-btn" id="theme-btn" type="button">外观</button>
<main>
<header>
<div class="eyebrow">World Building · 审批点② · {html.escape(project.name)}</div>
<h1>参考图与 plan</h1>
<p class="lede">{html.escape(title)}。这一页通过之后，建模、仿真、渲染都由 agent 自主推进。</p>
<nav class="toc"><a href="#board"><span class="n">01</span>参考板</a><a href="#dims"><span class="n">02</span>尺寸表</a><a href="#load"><span class="n">03</span>载荷链</a><a href="#plan"><span class="n">04</span>plan 任务</a><a href="#gates"><span class="n">05</span>冻结门限</a></nav>
</header>
<section id="board"><h2><span class="n">01</span>参考板</h2><p class="sub">参考图只用来冻结外观风格，尺寸一律以第 02 节为准。</p><div class="board">{figs}</div></section>
<section id="dims"><h2><span class="n">02</span>尺寸表</h2><p class="sub">来源类别分三种：标准锚点、设计假设、实测。</p>{md_tables_and_lists(dims_body)}</section>
<section id="load"><h2><span class="n">03</span>载荷链</h2><div class="card"><img src="load_path.svg" alt="载荷链" style="width:100%;border:0;background:none"></div></section>
<section id="plan"><h2><span class="n">04</span>plan 任务</h2><p class="sub">{_inline(secs.get("方案", "").strip().splitlines()[0] if secs.get("方案") else "")}</p>{md_tables_and_lists(secs.get("任务", ""))}</section>
<section id="gates"><h2><span class="n">05</span>冻结门限</h2>{md_tables_and_lists(secs.get("验收门限（冻结）", ""))}</section>
<footer>由 <code>wb review</code> 从项目文件生成：reference.json、dimensions.md、load_path.svg、03-plan/plan.md</footer>
<script>document.getElementById('theme-btn').onclick=()=>{{const r=document.documentElement,d=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;r.dataset.theme=d?'light':'dark';try{{localStorage.setItem('wb-theme',r.dataset.theme)}}catch(e){{}}}};</script>
</main></body></html>
"""
    if (ref / "assets").exists():
        shutil.rmtree(ref / "assets")
    copy_tree_plain(THEME, ref / "assets")
    out = ref / "index.html"
    out.write_text(page, encoding="utf-8")
    return out
