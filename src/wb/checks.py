"""各阶段的验证门检查。每个检查只看阶段目录里的文件。"""

from __future__ import annotations

import re
from pathlib import Path

from wb.gate import BLOCKED, FAIL, NOT_RUN, PASS, Check, stage_check

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


# ---------------------------------------------------------------- 建模
def _glb_node_names(path: Path) -> list[str]:
    """不依赖 Blender，直接解析 GLB 的 JSON 块读节点名：验证导出字节本身。"""
    import json
    import struct

    b = path.read_bytes()
    n = struct.unpack_from("<I", b, 12)[0]
    gltf = json.loads(b[20:20 + n])
    return [x.get("name", "") for x in gltf.get("nodes", [])] + [x.get("name", "") for x in gltf.get("meshes", [])]


def _thresholds(stage_dir: Path) -> dict:
    import json

    f = stage_dir.parent / "03-plan" / "thresholds.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


@stage_check("modelling")
def check_modelling(stage_dir: Path) -> list[Check]:
    import json
    import math

    th = _thresholds(stage_dir).get("modelling")
    if not th:
        return [Check("冻结门限", BLOCKED, "缺少 03-plan/thresholds.json 的 modelling 段")]
    proj = stage_dir.parent
    checks: list[Check] = []
    try:
        import mujoco
    except ImportError:
        return [Check("MuJoCo 可用", BLOCKED, "需 `uv run --extra sim`")]

    xml = proj / th["mjcf"]
    try:
        m = mujoco.MjModel.from_xml_path(str(xml))
    except Exception as e:  # noqa: BLE001
        return [Check("M1 MJCF 可编译", FAIL, str(e)[:200], [th["mjcf"]])]
    bad = []
    for j, (lo, hi) in th["M1_joint_range_deg"].items():
        r = [math.degrees(v) for v in m.jnt_range[m.joint(j).id]]
        if abs(r[0] - lo) > 0.01 or abs(r[1] - hi) > 0.01:
            bad.append(f"{j} {r[0]:.2f}…{r[1]:.2f}")
    checks.append(Check("M1 MJCF 可编译且门范围正确", FAIL if bad else PASS, "; ".join(bad), [th["mjcf"]]))

    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    bad = []
    for g, z in th["M2_shelf_tops"].items():
        gid = m.geom(g).id
        top = d.geom_xpos[gid][2] + m.geom_size[gid][2]
        if abs(top - z) > th["M2_tol"]:
            bad.append(f"{g} 顶面 {top:.4f} ≠ {z}")
    checks.append(Check("M2 隔板高度", FAIL if bad else PASS, "; ".join(bad), [th["mjcf"]]))

    names = _glb_node_names(proj / th["glb"])
    col = [n for n in names if n.startswith("COL_") or "collision" in n.lower()]
    checks.append(Check("M3 GLB 无碰撞代理", FAIL if col or not names else PASS,
                        f"{len(names)} 个节点/网格" + (f"；含 {col[:5]}" if col else ""), [th["glb"]]))

    design = json.loads((stage_dir / "design.json").read_text(encoding="utf-8"))
    mapping = json.loads((stage_dir / "mapping.json").read_text(encoding="utf-8"))
    idx = {(r["body"], r["part"]): r for r in mapping}
    bad = []
    for bname, b in design["bodies"].items():
        for p in b["parts"]:
            r = idx.get((bname, p["name"]))
            if not r or not r.get("visual") or not r.get("physics_root") or bool(r.get("collision")) != p["collision"]:
                bad.append(f"{bname}/{p['name']}")
    checks.append(Check("M4 映射表完整一致", FAIL if bad else PASS, "问题：" + ", ".join(bad[:8]) if bad else
                        f"{len(mapping)} 行", ["05-modelling/mapping.json"]))

    mujoco.mj_resetData(m, d)
    maxpen, maxdoor = 0.0, 0.0
    for _ in range(int(1.0 / m.opt.timestep)):
        mujoco.mj_step(m, d)
        for c in d.contact[: d.ncon]:
            maxpen = max(maxpen, -c.dist)
        maxdoor = max(maxdoor, *(abs(math.degrees(d.qpos[m.joint(j).qposadr[0]])) for j in th["M1_joint_range_deg"]))
    ok = maxpen <= th["M5_max_penetration"] and maxdoor <= th["M5_door_hold_deg"]
    checks.append(Check("M5 静置 1 s", PASS if ok else FAIL, f"最大穿透 {maxpen*1000:.3f} mm，门最大偏转 {maxdoor:.4f}°",
                        [th["mjcf"]]))

    lo, hi = design["offset_finger"]["opening_range"]
    need = th["M6_opening_range"]
    ok = lo <= need[0] + 1e-9 and hi >= need[1] - 1e-9
    checks.append(Check("M6 偏置宽指开口范围", PASS if ok else FAIL, f"{lo:.3f}…{hi:.3f} m", ["05-modelling/design.json"]))

    prev = sorted((stage_dir / "preview").glob("*.webp"))
    checks.append(Check("预览渲染（证据）", PASS if prev else FAIL, f"{len(prev)} 张", [f"05-modelling/preview/{p.name}" for p in prev]))
    return checks


# ---------------------------------------------------------------- 仿真
# 负例清单写在各项目的 03-plan/thresholds.json → simulation.negatives，每项：
#   {"id": "N1", "label": "去托面", "variant": "no_support", "expect_fail": ["S7"],
#    "metric_gt": {"N1_plate_drop_after_release": 0.005}}   # metric_gt 可省略
# 名义流程要检查的门限编号写在 simulation.nominal_gates；缺省为 S1–S13。


@stage_check("simulation")
def check_simulation(stage_dir: Path) -> list[Check]:
    import json

    res = stage_dir / "results"
    checks: list[Check] = []
    nom = res / "nominal.json"
    if not nom.is_file():
        return [Check("名义流程结果", NOT_RUN, "缺少 results/nominal.json")]
    r = json.loads(nom.read_text(encoding="utf-8"))
    sim_th = _thresholds(stage_dir).get("simulation", {})
    bad = [k for k, v in r["gates"].items() if v != "PASS"]
    expected = set(sim_th.get("nominal_gates") or [f"S{i}" for i in range(1, 14)])
    missing = sorted(expected - set(r["gates"]))
    checks.append(Check(f"名义流程 {len(expected)} 项门限", FAIL if bad or missing else PASS,
                        ("FAIL：" + ", ".join(bad) if bad else "") + (" 缺：" + ", ".join(missing) if missing else ""),
                        [f"06-simulation/results/nominal.json"]))
    negatives = sim_th.get("negatives") or []
    if not negatives:
        checks.append(Check("负例清单", FAIL, "thresholds.json 的 simulation.negatives 为空"))
    for neg in negatives:
        name, label, gates = neg["variant"], f"{neg['id']} {neg['label']}", neg["expect_fail"]
        f = res / f"{name}.json"
        if not f.is_file():
            checks.append(Check(f"负例 {label}", NOT_RUN, f"缺少 results/{name}.json"))
            continue
        n = json.loads(f.read_text(encoding="utf-8"))
        tripped = any(n["gates"].get(g) == "FAIL" for g in gates) and all(
            (n["metrics"].get(k) or 0) > v for k, v in (neg.get("metric_gt") or {}).items())
        checks.append(Check(f"负例 {label} 按预期判 FAIL", PASS if tripped else FAIL,
                            "" if tripped else f"未触发：{', '.join(f'{g}={n['gates'].get(g)}' for g in gates)}",
                            [f"06-simulation/results/{name}.json"]))
    st = stage_dir / "states_30fps.npz"
    checks.append(Check("渲染用位姿记录", PASS if st.is_file() else FAIL, "" if st.is_file() else "缺少 states_30fps.npz",
                        ["06-simulation/states_30fps.npz"] if st.is_file() else []))
    return checks


# ---------------------------------------------------------------- 渲染
@stage_check("render")
def check_render(stage_dir: Path) -> list[Check]:
    import json
    import shutil
    import subprocess

    th = _thresholds(stage_dir).get("render", {"V2_fps": 30, "V3_pose_tol": 1e-5})
    rep_f = stage_dir / "binding_report.json"
    if not rep_f.is_file():
        return [Check("位姿绑定报告", NOT_RUN, "缺少 binding_report.json")]
    rep = json.loads(rep_f.read_text(encoding="utf-8"))
    ev = ["07-render/binding_report.json"]
    checks = [Check("V1 场景无碰撞代理", FAIL if rep["v1_collision_objects_in_scene"] else PASS,
                    ", ".join(rep["v1_collision_objects_in_scene"][:5]), ev)]
    expect = round(rep["sim_duration_s"] * th["V2_fps"]) + 1
    frames = sorted((stage_dir / "frames").glob("frame_*.png")) + sorted((stage_dir / "frames").glob("frame_*.webp"))
    ok = rep["frames"] == expect and rep["fps"] == th["V2_fps"]
    checks.append(Check("V2 帧数 = 仿真时长 × 30（不加速、不跳帧）", PASS if ok else FAIL,
                        f"绑定 {rep['frames']} 帧，期望 {expect}；已渲染 {len(frames)} 帧", ev))
    ok = rep["v3_max_pos_err_m"] <= th["V3_pose_tol"] and rep["v3_max_rot_err_rad"] <= 1e-4
    checks.append(Check("V3 抽检位姿与仿真一致", PASS if ok else FAIL,
                        f"位置 {rep['v3_max_pos_err_m']:.2e} m，姿态 {rep['v3_max_rot_err_rad']:.2e} rad", ev))
    mp4 = stage_dir / "film.mp4"
    if not mp4.is_file():
        checks.append(Check("V4 成片可解码且时长一致", NOT_RUN, "缺少 film.mp4"))
    elif not shutil.which("ffprobe"):
        checks.append(Check("V4 成片可解码且时长一致", BLOCKED, "ffprobe 不可用"))
    else:
        out = subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                              "stream=nb_read_frames,r_frame_rate", "-of", "json", str(mp4)], capture_output=True, text=True)
        s = json.loads(out.stdout or "{}").get("streams", [{}])[0]
        n = int(s.get("nb_read_frames", 0))
        num, den = map(int, s.get("r_frame_rate", "0/1").split("/"))
        dur = n / (num / den) if num else 0
        ok = out.returncode == 0 and n == expect and abs(dur - expect / th["V2_fps"]) <= 1 / th["V2_fps"]
        checks.append(Check("V4 成片可解码且时长一致", PASS if ok else FAIL, f"{n} 帧，{dur:.3f} s",
                            ["07-render/film.mp4"]))
    return checks
