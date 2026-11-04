"""渲染验证门：合成 binding_report 的正例与负例（不跑 Blender）。"""

import json

from wb.gate import run_gate


def make(tmp_path, **over):
    r = tmp_path / "p" / "07-render"
    (r / "frames").mkdir(parents=True)
    rep = dict(frames=31, sim_duration_s=1.0, fps=30, v1_collision_objects_in_scene=[], v3_max_pos_err_m=0.0,
               v3_max_rot_err_rad=0.0) | over
    (r / "binding_report.json").write_text(json.dumps(rep))
    return tmp_path / "p"


def test_render_without_film_is_not_run(tmp_path):
    r = run_gate(make(tmp_path), "render")
    assert r.status == "NOT_RUN"


def test_render_collision_proxy_fails(tmp_path):
    r = run_gate(make(tmp_path, v1_collision_objects_in_scene=["COL_x"]), "render")
    assert r.status == "FAIL"


def test_render_speedup_fails(tmp_path):
    r = run_gate(make(tmp_path, frames=16), "render")   # 半数帧 = 加速
    assert "V2 帧数 = 仿真时长 × 30（不加速、不跳帧）" in {c.name for c in r.checks if c.status == "FAIL"}
