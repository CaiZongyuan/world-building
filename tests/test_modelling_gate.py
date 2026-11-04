"""建模验证门：用最小项目目录（tmp_path 里现造）跑正例与负例。"""

import json
import struct

import pytest

mujoco = pytest.importorskip("mujoco")
from wb.gate import run_gate  # noqa: E402

XML = """<mujoco><compiler angle="radian"/><worldbody>
<body name="incubator__cabinet"><geom name="incubator__col_shelf_1" type="box" pos="0 0 {z}" size=".2 .2 .0015"/></body>
<body name="incubator__outer_door"><joint name="incubator__outer_door_hinge" type="hinge" axis="0 0 1" range="0 2.0071"/>
<geom type="box" size=".01 .01 .01" pos="1 1 1" mass="1" contype="0" conaffinity="0"/></body>
</worldbody></mujoco>"""


def glb(names):
    js = json.dumps({"asset": {"version": "2.0"}, "nodes": [{"name": n} for n in names]}).encode()
    js += b" " * (-len(js) % 4)
    return struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js)) + struct.pack("<II", len(js), 0x4E4F534A) + js


def make(tmp_path, shelf_z=0.3135, nodes=("VIS_cabinet__shelf_1",)):
    p = tmp_path / "proj"
    (p / "03-plan").mkdir(parents=True)
    m = p / "05-modelling"
    (m / "preview").mkdir(parents=True)
    (m / "preview" / "a.webp").write_bytes(b"RIFF")
    (m / "incubator.xml").write_text(XML.format(z=shelf_z))
    (m / "incubator_visual.glb").write_bytes(glb(list(nodes)))
    (m / "design.json").write_text(json.dumps({"bodies": {"cabinet": {"parts": [{"name": "shelf_1", "collision": True}]}},
                                               "offset_finger": {"opening_range": [0.11, 0.19]}}))
    (m / "mapping.json").write_text(json.dumps([{"body": "cabinet", "part": "shelf_1", "visual": "VIS_cabinet__shelf_1",
                                                 "collision": "COL_cabinet__shelf_1", "physics_root": "ROOT_cabinet"}]))
    (p / "03-plan" / "thresholds.json").write_text(json.dumps({"modelling": {
        "mjcf": "05-modelling/incubator.xml", "glb": "05-modelling/incubator_visual.glb",
        "M1_joint_range_deg": {"incubator__outer_door_hinge": [0, 115]},
        "M2_shelf_tops": {"incubator__col_shelf_1": 0.315}, "M2_tol": 0.001,
        "M5_max_penetration": 0.00025, "M5_door_hold_deg": 0.1, "M6_opening_range": [0.11, 0.19]}}))
    return p


def test_modelling_pass(tmp_path):
    assert run_gate(make(tmp_path), "modelling").status == "PASS"


def test_modelling_glb_with_collision_proxy_fails(tmp_path):
    r = run_gate(make(tmp_path, nodes=("VIS_cabinet__shelf_1", "COL_cabinet__shelf_1")), "modelling")
    assert r.status == "FAIL" and "M3 GLB 无碰撞代理" in {c.name for c in r.checks if c.status == "FAIL"}


def test_modelling_wrong_shelf_height_fails(tmp_path):
    r = run_gate(make(tmp_path, shelf_z=0.32), "modelling")
    assert r.status == "FAIL" and "M2 关键支撑面高度" in {c.name for c in r.checks if c.status == "FAIL"}
