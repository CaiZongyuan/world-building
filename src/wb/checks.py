"""各阶段的验证门检查。每个检查只看阶段目录里的文件。"""

from __future__ import annotations

import re
from pathlib import Path

from wb.gate import FAIL, PASS, Check, stage_check

REQUIREMENT_SECTIONS = ["目标", "不做什么", "工艺步骤", "设备", "保真度", "算力预算"]


def markdown_sections(text: str) -> dict[str, str]:
    """按二级标题切分 Markdown，返回 {标题: 正文}。"""
    sections: dict[str, str] = {}
    current = None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            current = m.group(1)
            sections[current] = ""
        elif current is not None:
            sections[current] += line + "\n"
    return sections


@stage_check("requirements")
def check_requirements(stage_dir: Path) -> list[Check]:
    doc = stage_dir / "requirements.md"
    if not doc.is_file():
        return [Check("需求记录存在", FAIL, "缺少 requirements.md")]
    rel = f"{stage_dir.name}/requirements.md"
    sections = markdown_sections(doc.read_text(encoding="utf-8"))
    checks = [Check("需求记录存在", PASS, evidence=[rel])]
    for name in REQUIREMENT_SECTIONS:
        body = next((v for k, v in sections.items() if k.split("（")[0].strip() == name), None)
        if body is None:
            checks.append(Check(f"必填节：{name}", FAIL, "缺少该节", [rel]))
        elif not body.strip():
            checks.append(Check(f"必填节：{name}", FAIL, "该节为空", [rel]))
        else:
            checks.append(Check(f"必填节：{name}", PASS, evidence=[rel]))
    return checks


# ---------------------------------------------------------------- 方案预览
PROPOSAL_SECTIONS = ["goal", "renders", "layout", "devices", "steps", "stages", "risks", "references"]
STATUSES = {"PASS", "FAIL", "NOT_RUN", "BLOCKED", "IDEALIZED"}
LEVELS = {"L1", "L2", "L3", "L4", "L5"}
FIDELITY = {"物理", "理想化", "符号化"}
USAGE = {"仅参考", "可作资产"}


def _proposal_data(html: str):
    import json

    m = re.search(r'<script[^>]*id="proposal-data"[^>]*>(.*?)</script>', html, re.S)
    return json.loads(m.group(1)) if m else None


@stage_check("proposal")
def check_proposal(stage_dir: Path) -> list[Check]:
    page = stage_dir / "index.html"
    rel = f"{stage_dir.name}/index.html"
    if not page.is_file():
        return [Check("方案预览存在", FAIL, "缺少 index.html")]
    html = page.read_text(encoding="utf-8")
    checks = [Check("方案预览存在", PASS, evidence=[rel])]

    missing = [s for s in PROPOSAL_SECTIONS if f'id="{s}"' not in html]
    checks.append(Check("八节齐全", FAIL if missing else PASS, f"缺：{', '.join(missing)}" if missing else "", [rel]))

    srcs = [s for s in re.findall(r"<img[^>]+src=\"([^\"]+)\"", html) if "${" not in s]  # 跳过 JS 模板占位符
    remote = [s for s in srcs if re.match(r"^(https?:)?//", s)]
    absent = [s for s in srcs if s not in remote and not s.startswith("data:") and not (stage_dir / s).is_file()]
    checks.append(Check("图片本地化（无外链）", FAIL if remote else PASS, "外链：" + ", ".join(remote) if remote else "", [rel]))
    not_webp = [x for x in srcs if not x.startswith("data:") and not x.lower().endswith((".webp", ".svg"))]
    checks.append(Check("图片格式为 WebP", FAIL if not_webp else PASS, "非 WebP：" + ", ".join(not_webp) if not_webp else "", [rel]))
    checks.append(Check("图片文件存在", FAIL if absent else PASS, "缺：" + ", ".join(absent) if absent else "", [rel]))

    try:
        data = _proposal_data(html)
    except ValueError as e:
        data, err = None, str(e)
    else:
        err = "缺少 <script id=\"proposal-data\">"
    if data is None:
        checks.append(Check("结构化数据", FAIL, err, [rel]))
        return checks

    thumbs = [d["thumb"] for d in data.get("devices", []) if d.get("thumb")]
    bad_thumbs = [t for t in thumbs if re.match(r"^(https?:)?//", t) or not (stage_dir / t).is_file()
                  or not t.lower().endswith((".webp", ".svg"))]
    checks.append(Check("设备缩略图本地存在且为 WebP", FAIL if bad_thumbs else PASS,
                        "问题：" + ", ".join(bad_thumbs) if bad_thumbs else "", [rel]))

    bad_dev = [d.get("name", "?") for d in data.get("devices", [])
               if d.get("status") not in STATUSES or d.get("difficulty") not in LEVELS or not d.get("license")]
    checks.append(Check("设备：状态 / 难度等级 / 许可", FAIL if bad_dev or not data.get("devices") else PASS,
                        "不完整：" + ", ".join(bad_dev) if bad_dev else "", [rel]))

    bad_step = [s.get("name", "?") for s in data.get("steps", [])
                if s.get("difficulty") not in LEVELS or s.get("fidelity") not in FIDELITY]
    checks.append(Check("工艺步骤：难度等级 / 保真度", FAIL if bad_step or not data.get("steps") else PASS,
                        "不完整：" + ", ".join(bad_step) if bad_step else "", [rel]))

    bad_ref = [r.get("title", "?") for r in data.get("references", [])
               if not re.match(r"^https?://", r.get("url", "")) or not r.get("license") or r.get("usage") not in USAGE]
    checks.append(Check("外部素材：来源 / 许可 / 用途", FAIL if bad_ref else PASS,
                        "不完整：" + ", ".join(bad_ref) if bad_ref else "", [rel]))
    return checks


# ---------------------------------------------------------------- plan
PLAN_SECTIONS = ["问题", "方案", "任务", "验收门限（冻结）", "范围外"]


@stage_check("plan")
def check_plan(stage_dir: Path) -> list[Check]:
    doc = stage_dir / "plan.md"
    rel = f"{stage_dir.name}/plan.md"
    if not doc.is_file():
        return [Check("plan 存在", FAIL, "缺少 plan.md")]
    text = doc.read_text(encoding="utf-8")
    secs = markdown_sections(text)
    checks = [Check("plan 存在", PASS, evidence=[rel])]
    for name in PLAN_SECTIONS:
        ok = name in secs and secs[name].strip()
        checks.append(Check(f"必填节：{name}", PASS if ok else FAIL, "" if ok else "缺少或为空", [rel]))
    tasks = re.findall(r"^- \[[ x]\] ", text, re.M)
    checks.append(Check("任务为可勾选清单", PASS if tasks else FAIL, f"{len(tasks)} 条", [rel]))
    frozen = re.search(r"冻结于 \d{4}-\d{2}-\d{2}", secs.get("验收门限（冻结）", ""))
    checks.append(Check("门限带冻结日期", PASS if frozen else FAIL, "" if frozen else "缺少“冻结于 YYYY-MM-DD”", [rel]))
    rows = re.findall(r"^\| [SMRVN]\d+ \|", secs.get("验收门限（冻结）", ""), re.M)
    checks.append(Check("门限有编号行", PASS if rows else FAIL, f"{len(rows)} 行", [rel]))
    estimate = re.search(r"(预计|预估|上限)\s*\d+(\.\d+)?\s*(h|小时|天)", text)
    checks.append(Check("不含时间预估", FAIL if estimate else PASS, estimate.group(0) if estimate else "", [rel]))
    return checks


# ---------------------------------------------------------------- 参考图
DIM_CATEGORIES = {"标准锚点", "设计假设", "实测"}


@stage_check("reference")
def check_reference(stage_dir: Path) -> list[Check]:
    import json

    checks: list[Check] = []
    idx = stage_dir / "reference.json"
    if not idx.is_file():
        checks.append(Check("参考图清单", FAIL, "缺少 reference.json"))
    else:
        items = json.loads(idx.read_text(encoding="utf-8")).get("images", [])
        bad = [i.get("file", "?") for i in items
               if not str(i.get("file", "")).lower().endswith(".webp") or not (stage_dir / i.get("file", "")).is_file()]
        unseen = [i.get("file", "?") for i in items if not i.get("viewed") or not i.get("actual_size")]
        checks.append(Check("参考图存在且为 WebP (R1)", FAIL if bad or not items else PASS,
                            "问题：" + ", ".join(bad) if bad else f"{len(items)} 张", [idx.name]))
        checks.append(Check("参考图已查看并记录实际尺寸 (R1)", FAIL if unseen else PASS,
                            "未查看：" + ", ".join(unseen) if unseen else "", [idx.name]))

    dims = stage_dir / "dimensions.md"
    if not dims.is_file():
        checks.append(Check("尺寸表来源类别 (R2)", FAIL, "缺少 dimensions.md"))
    else:
        rows = [r for r in dims.read_text(encoding="utf-8").splitlines()
                if r.startswith("|") and not re.match(r"^\|\s*(项|-)", r)]
        cells = [[c.strip() for c in r.strip("|").split("|")] for r in rows]
        bad = [c[0] for c in cells if len(c) < 3 or c[2] not in DIM_CATEGORIES]
        checks.append(Check("尺寸表来源类别 (R2)", FAIL if bad or not cells else PASS,
                            "未分类：" + ", ".join(bad) if bad else f"{len(cells)} 项", [dims.name]))

    lp = stage_dir / "load_path.svg"
    checks.append(Check("载荷链草图 (R3)", PASS if lp.is_file() else FAIL, "" if lp.is_file() else "缺少 load_path.svg",
                        [lp.name] if lp.is_file() else []))
    return checks
