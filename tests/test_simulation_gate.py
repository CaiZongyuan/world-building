"""仿真验证门：用合成的 results/*.json 检查判定逻辑（不跑物理）。"""

import json

from wb.gate import run_gate

ALL = {f"S{i}": "PASS" for i in range(1, 14)}


NEGATIVES = [
    {"id": "N1", "label": "去托面", "variant": "no_support", "expect_fail": ["S7"],
     "metric_gt": {"N1_plate_drop_after_release": 0.005}},
    {"id": "N2", "label": "过插", "variant": "overinsert", "expect_fail": ["S3"]},
    {"id": "N3", "label": "夹取高度偏高", "variant": "grasp_high", "expect_fail": ["S5", "S6"]},
]


def make(tmp_path, nominal=None, n3_gates=None, negatives=NEGATIVES):
    (tmp_path / "p" / "03-plan").mkdir(parents=True)
    (tmp_path / "p" / "03-plan" / "thresholds.json").write_text(json.dumps({"simulation": {"negatives": negatives}}))
    s = tmp_path / "p" / "06-simulation"
    (s / "results").mkdir(parents=True)
    (s / "states_30fps.npz").write_bytes(b"x")
    w = lambda n, g, m=None: (s / "results" / f"{n}.json").write_text(json.dumps({"gates": g, "metrics": m or {}}))  # noqa: E731
    w("nominal", nominal or ALL)
    w("no_support", {"S7": "FAIL"}, {"N1_plate_drop_after_release": 0.5})
    w("overinsert", {"S3": "FAIL"})
    w("grasp_high", n3_gates or {"S5": "FAIL", "S6": "PASS"})
    return tmp_path / "p"


def test_simulation_pass(tmp_path):
    assert run_gate(make(tmp_path), "simulation").status == "PASS"


def test_nominal_gate_fail_propagates(tmp_path):
    assert run_gate(make(tmp_path, nominal=ALL | {"S8": "FAIL"}), "simulation").status == "FAIL"


def test_negative_not_tripped_is_fail(tmp_path):
    r = run_gate(make(tmp_path, n3_gates={"S5": "PASS", "S6": "PASS"}), "simulation")
    assert r.status == "FAIL" and "负例 N3 夹取高度偏高 按预期判 FAIL" in {c.name for c in r.checks if c.status == "FAIL"}


def test_missing_negative_list_is_fail(tmp_path):
    r = run_gate(make(tmp_path, negatives=[]), "simulation")
    assert r.status == "FAIL" and "负例清单" in {c.name for c in r.checks if c.status == "FAIL"}


def test_negative_metric_condition(tmp_path):
    p = make(tmp_path)
    (p / "06-simulation" / "results" / "no_support.json").write_text(
        json.dumps({"gates": {"S7": "FAIL"}, "metrics": {"N1_plate_drop_after_release": 0.001}}))
    assert run_gate(p, "simulation").status == "FAIL"
