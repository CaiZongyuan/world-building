"""运动学预演：用一份小场景检查四类判定（需要 Menagerie Panda 与 sim 依赖）。"""

import json
from pathlib import Path

import pytest

SPEC = Path(__file__).parent / "fixtures" / "preflight" / "basic.json"
PANDA = Path(json.loads(SPEC.read_text())["robot"]["mjcf"])
pytestmark = pytest.mark.skipif(not PANDA.is_file(), reason="缺少 Menagerie Panda")


@pytest.fixture(scope="module")
def rep(tmp_path_factory):
    pytest.importorskip("mujoco")
    from wb.preflight import run
    return run(SPEC, tmp_path_factory.mktemp("pf"))


def by_id(rep, sec):
    return {r["id"]: r for r in rep[sec]}


def test_gripper_stroke(rep):
    g = by_id(rep, "gripper")
    assert g["G:tube"]["ok"] and not g["G:plate"]["ok"]   # 板宽 85.5 mm 超出原装 80 mm 行程


def test_pose_reachable_and_collision(rep):
    p = by_id(rep, "poses")
    assert p["P:pick_table"]["ok"]
    assert not p["P:inside_table"]["ok"] and p["P:inside_table"]["reachable"]   # 够得到但手伸进了桌子
    assert not p["P:far"]["reachable"]


def test_mover_sweep_hits_table(rep):
    assert not by_id(rep, "movers")["D:door"]["ok"]


def test_outputs(rep, tmp_path):
    assert rep["status"] == "FAIL"
