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
