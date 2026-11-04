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


def test_proposal_pass(project):
    assert run_gate(project("proposal-pass"), "proposal").status == "PASS"


@pytest.mark.parametrize("name,failed_check", [
    ("proposal-ref-no-license", "外部素材：来源 / 许可 / 用途"),
    ("proposal-hotlink", "图片本地化（无外链）"),
    ("proposal-device-no-level", "设备：状态 / 难度等级 / 许可"),
    ("proposal-png", "图片格式为 WebP"),
])
def test_proposal_negative_fails(project, name, failed_check):
    r = run_gate(project(name), "proposal")
    assert r.status == "FAIL"
    assert failed_check in {c.name for c in r.checks if c.status == "FAIL"}


def test_publish_copies_proposal(project, tmp_path):
    from wb.project import publish_proposal
    p = project("proposal-pass")
    (p / "02-proposal" / "preview_full.png").write_bytes(b"x")
    dst = publish_proposal(p, tmp_path / "repo")
    assert (dst / "index.html").is_file() and (dst / "img" / "a.webp").is_file()
    assert not (dst / "preview_full.png").exists()
