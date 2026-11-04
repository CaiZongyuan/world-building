"""验证门：只测外部行为（项目目录 + 阶段 → 状态）。"""

import shutil
from pathlib import Path

import pytest

from wb.gate import run_gate
from wb.project import new_project

FIX = Path(__file__).parent / "fixtures"


@pytest.fixture
def project(tmp_path):
    def copy(name):
        dst = tmp_path / name
        shutil.copytree(FIX / name, dst)
        return dst
    return copy


def test_missing_stage_is_not_run(project):
    assert run_gate(project("empty-project"), "requirements").status == "NOT_RUN"


def test_unimplemented_stage_is_not_run(project):
    p = project("req-pass")
    (p / "06-simulation").mkdir()
    assert run_gate(p, "simulation").status == "NOT_RUN"


def test_requirements_pass_with_evidence(project):
    p = project("req-pass")
    r = run_gate(p, "requirements")
    assert r.status == "PASS"
    assert all(c.evidence for c in r.checks)
    assert (p / "gates" / "requirements.json").is_file()


@pytest.mark.parametrize("name", ["req-missing-section", "req-empty-section"])
def test_requirements_negative_fails(project, name):
    r = run_gate(project(name), "requirements")
    assert r.status == "FAIL"
    failed = {c.name for c in r.checks if c.status == "FAIL"}
    assert failed == {"必填节：算力预算"} if name == "req-missing-section" else failed == {"必填节：目标"}


def test_new_project_follows_contract(tmp_path):
    p = tmp_path / "demo"
    new_project(p, "演示")
    assert (p / "stage-log.md").is_file()
    assert run_gate(p, "requirements").status == "FAIL"  # 目录在但没有需求记录
    with pytest.raises(FileExistsError):
        new_project(p, "again")
