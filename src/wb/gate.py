"""验证门：输入项目目录 + 阶段，输出状态与证据清单。

这是本流程唯一的测试接缝（见 issue #1 Testing Decisions）。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

PASS, FAIL, NOT_RUN, BLOCKED, IDEALIZED = "PASS", "FAIL", "NOT_RUN", "BLOCKED", "IDEALIZED"

# 阶段名 → 项目目录下的阶段子目录
STAGES: dict[str, str] = {
    "requirements": "01-requirements",
    "proposal": "02-proposal",
    "plan": "03-plan",
    "reference": "04-reference",
    "modelling": "05-modelling",
    "simulation": "06-simulation",
    "render": "07-render",
}


@dataclass
class Check:
    name: str
    status: str
    detail: str = ""
    evidence: list[str] = field(default_factory=list)


@dataclass
class GateResult:
    stage: str
    status: str
    checks: list[Check]
    checked_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


def aggregate(checks: list[Check]) -> str:
    """FAIL > BLOCKED > NOT_RUN（全部未跑）> PASS。IDEALIZED 永不计为 PASS。"""
    statuses = [c.status for c in checks]
    if not statuses:
        return NOT_RUN
    if FAIL in statuses:
        return FAIL
    if BLOCKED in statuses:
        return BLOCKED
    if all(s == NOT_RUN for s in statuses):
        return NOT_RUN
    if NOT_RUN in statuses or IDEALIZED in statuses:
        # 部分未跑或含理想化：不能算整体 PASS
        return NOT_RUN if NOT_RUN in statuses else IDEALIZED
    return PASS


StageCheck = Callable[[Path], list[Check]]
_REGISTRY: dict[str, StageCheck] = {}


def stage_check(stage: str) -> Callable[[StageCheck], StageCheck]:
    def deco(fn: StageCheck) -> StageCheck:
        _REGISTRY[stage] = fn
        return fn

    return deco


def run_gate(project: Path, stage: str, write: bool = True) -> GateResult:
    if stage not in STAGES:
        raise ValueError(f"未知阶段 {stage!r}，可选：{', '.join(STAGES)}")
    stage_dir = project / STAGES[stage]
    if not stage_dir.is_dir():
        checks = [Check("阶段目录存在", NOT_RUN, f"{STAGES[stage]}/ 不存在")]
    elif stage not in _REGISTRY:
        checks = [Check("阶段检查已实现", NOT_RUN, f"阶段 {stage} 尚无验证门检查")]
    else:
        checks = _REGISTRY[stage](stage_dir)
    result = GateResult(stage, aggregate(checks), checks)
    if write:
        out = project / "gates" / f"{stage}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result.to_json() + "\n", encoding="utf-8")
    return result


# 注册各阶段检查
from wb import checks as _checks  # noqa: E402,F401
