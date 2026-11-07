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
    assert "V2 绑定帧数 = 仿真时长 × 30（绑定不加速、不跳帧）" in {c.name for c in r.checks if c.status == "FAIL"}


def make_footage(tmp_path, have_all=True):
    """多机位素材流程：footage_plan.json 两个机位，按录制倍速应录 6 帧。"""
    p = make(tmp_path)
    f = p / "07-render" / "footage"
    plan = {"cameras": {"wide": {"windows": [[0, 30]], "strides": [[0, 15, 8], [16, 30, 4]]},
                        "ws": {"windows": [[10, 13]], "strides": [[10, 13, 2]]}}}
    f.mkdir(parents=True)
    (f / "footage_plan.json").write_text(json.dumps(plan))
    want = {"wide": [0, 8, 16, 20, 24, 28], "ws": [10, 12]}
    for cam, frames in want.items():
        (f / "draft" / cam).mkdir(parents=True)
        for fr in frames[: None if have_all else -1]:
            (f / "draft" / cam / f"f_{fr:05d}.webp").write_bytes(b"x")
    return p


def test_render_footage_complete_passes_v4a(tmp_path):
    r = run_gate(make_footage(tmp_path), "render")
    st = {c.name: c.status for c in r.checks}
    assert st["V4a 素材库完整（按录制倍速，帧号在仿真范围内）"] == "PASS"
    assert st["V4b 剪辑版可解码且帧数与剪辑表一致"] == "NOT_RUN"   # 还没剪辑版


def test_render_footage_missing_frame_fails(tmp_path):
    r = run_gate(make_footage(tmp_path, have_all=False), "render")
    assert "V4a 素材库完整（按录制倍速，帧号在仿真范围内）" in {c.name for c in r.checks if c.status == "FAIL"}
