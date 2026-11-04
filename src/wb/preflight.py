"""运动学预演：在建模之前，用方盒代理检查取放可行性。

输入一份 preflight.json（格式见 docs/agents/project-layout.md 的"运动学预演"一节），做四类检查：
  G 夹爪行程：每个工件的夹持宽度落在夹具开口范围内（两侧各留余量）
  P 关键位姿：多初值、带碰撞检查的 IK（导轨也是一个自由度），连同沿进出方向的预位姿和直线进出段
  D 设备扫掠：门、抽屉等活动件在行程内与静态环境、其他活动件的接触
  T 过渡：相邻关键位姿之间关节插值，逐点检查机器人与环境的接触
输出 preflight_report.json 与俯视图 preflight_top.svg。只看运动学，不跑动力学。
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import mujoco
import numpy as np

NATURAL = np.array([0, -0.3, 0, -2.2, 0, 2.0, 0.785])
ARM = [f"panda__joint{i}" for i in range(1, 8)]


def _yaw_quat(yaw: float) -> list[float]:
    return [math.cos(yaw / 2), 0, 0, math.sin(yaw / 2)]


def tool_R(approach, opening) -> np.ndarray:
    """手爪姿态：z 轴 = 进入方向（approach），y 轴 = 手指张合方向（opening）。"""
    z = np.asarray(approach, float); z /= np.linalg.norm(z)
    y = np.asarray(opening, float); y = y - z * (y @ z); y /= np.linalg.norm(y)
    return np.column_stack([np.cross(y, z), y, z])


# ------------------------------------------------------------------ 场景
def build(spec_d: dict) -> tuple[mujoco.MjSpec, mujoco.MjModel]:
    r = spec_d["robot"]
    spec = mujoco.MjSpec()
    spec.option.timestep = 0.002
    wb = spec.worldbody
    for b in spec_d.get("static", []):
        wb.add_geom(name=f"static__{b['name']}", type=mujoco.mjtGeom.mjGEOM_BOX, pos=b["pos"], size=b["size"],
                    quat=_yaw_quat(b.get("yaw", 0.0)), rgba=[.6, .6, .6, 1])
    for mv in spec_d.get("movers", []):
        j = mv["joint"]
        body = wb.add_body(name=f"mover__{mv['name']}", pos=j["anchor"])
        jt = mujoco.mjtJoint.mjJNT_HINGE if j["type"] == "hinge" else mujoco.mjtJoint.mjJNT_SLIDE
        body.add_joint(name=f"mover__{mv['name']}", type=jt, axis=j["axis"], range=j["range"])
        for k, g in enumerate(mv["boxes"]):   # 盒子位置相对铰链/滑轨锚点
            body.add_geom(name=f"mover__{mv['name']}__{k}", type=mujoco.mjtGeom.mjGEOM_BOX, pos=g["pos"], size=g["size"],
                          quat=_yaw_quat(g.get("yaw", 0.0)), rgba=[.3, .5, .8, 1])

    pd = mujoco.MjSpec.from_file(str(r["mjcf"]))
    tool = r.get("tool", {})
    for fb, sx in (("left_finger", 1), ("right_finger", -1)):   # Menagerie right_finger 自带绕 z 180°，局部 x 取反
        for g in tool.get("finger_boxes", []):
            pd.body(fb).add_geom(name=f"{fb}_{g['name']}", type=mujoco.mjtGeom.mjGEOM_BOX,
                                 pos=[sx * g["pos"][0], g["pos"][1], g["pos"][2]], size=g["size"], mass=0.01)
    for g in tool.get("hand_boxes", []):
        pd.body("hand").add_geom(name=f"hand_{g['name']}", type=mujoco.mjtGeom.mjGEOM_BOX, pos=g["pos"], size=g["size"], mass=0.01)
    pd.body("hand").add_site(name="tcp", pos=tool.get("tcp_in_hand", [0, 0, 0.1034]), size=[0.004] * 3)

    rail = r.get("rail")
    if rail:
        car = wb.add_body(name="rail_carriage", pos=r["base"])
        car.add_joint(name="rail", type=mujoco.mjtJoint.mjJNT_SLIDE, axis=rail["axis"], range=rail["range"])
        car.add_geom(name="rail_carriage_geom", type=mujoco.mjtGeom.mjGEOM_BOX, size=[0.1, 0.1, 0.005], pos=[0, 0, -0.006],
                     contype=0, conaffinity=0, rgba=[.2, .2, .2, 1])
        f = car.add_frame(quat=_yaw_quat(r.get("yaw", 0.0)))
    else:
        f = wb.add_frame(pos=r["base"], quat=_yaw_quat(r.get("yaw", 0.0)))
    f.attach_body(pd.body("link0"), "panda__", "")
    m = spec.compile()
    return spec, m


@dataclass
class Robot:
    m: mujoco.MjModel

    def __post_init__(self):
        m = self.m
        self.d = mujoco.MjData(m)
        names = (["rail"] if any(m.joint(i).name == "rail" for i in range(m.njnt)) else []) + ARM
        jid = [m.joint(n).id for n in names]
        self.names = names
        self.qadr = np.array([m.jnt_qposadr[j] for j in jid])
        self.dadr = np.array([m.jnt_dofadr[j] for j in jid])
        self.lo, self.hi = m.jnt_range[jid].T.copy()
        self.site = m.site("panda__tcp").id
        self.fingers = [m.jnt_qposadr[m.joint(n).id] for n in ("panda__finger_joint1", "panda__finger_joint2")]
        self.robot_geoms = {g for g in range(m.ngeom) if m.body(m.geom_bodyid[g]).name.startswith("panda__")}
        self.has_rail = names[0] == "rail"

    def posture(self, q):
        p = q.copy(); p[-7:] = NATURAL
        return p

    def fk(self, q):
        self.d.qpos[self.qadr] = q
        mujoco.mj_kinematics(self.m, self.d)
        mujoco.mj_comPos(self.m, self.d)
        return self.d.site_xpos[self.site].copy(), self.d.site_xmat[self.site].reshape(3, 3).copy()

    def solve(self, p, R, q0, iters=300):
        q = np.array(q0, float)
        n = len(q)
        polish = max(30, iters // 4)   # 最后一段不加姿态拉力，只消除位姿误差（拉力会和远离舒适姿态的解较劲）
        for it in range(iters):
            x, Rc = self.fk(q)
            e = np.concatenate([p - x, 0.5 * sum(np.cross(Rc[:, i], R[:, i]) for i in range(3))])
            if np.linalg.norm(e[:3]) < 1e-5 and np.linalg.norm(e[3:]) < 1e-4:
                break
            Jp, Jr = np.zeros((3, self.m.nv)), np.zeros((3, self.m.nv))
            mujoco.mj_jacSite(self.m, self.d, Jp, Jr, self.site)
            J = np.vstack([Jp, Jr])[:, self.dadr]
            JJ = J @ J.T + 1e-6 * np.eye(6)
            dq = J.T @ np.linalg.solve(JJ, e)
            if it < iters - polish:
                N = np.eye(n) - J.T @ np.linalg.solve(JJ, J)
                dq += N @ (0.02 * (self.posture(q) - q))
            q = np.clip(q + dq, self.lo + 1e-4, self.hi - 1e-4)
        x, Rc = self.fk(q)
        return q, (float(np.linalg.norm(p - x)), float(np.linalg.norm(0.5 * sum(np.cross(Rc[:, i], R[:, i]) for i in range(3)))))

    def set_state(self, q, opening, movers: dict[str, float]):
        d, m = self.d, self.m
        d.qpos[:] = 0
        d.qpos[self.qadr] = q
        d.qpos[self.fingers] = min(0.04, max(0.0, opening))
        for name, v in movers.items():
            d.qpos[m.jnt_qposadr[m.joint(f"mover__{name}").id]] = v
        mujoco.mj_forward(m, d)

    def env_hits(self, clearance, ignore=()) -> list[tuple[str, str, float]]:
        m, d = self.m, self.d
        out = []
        for c in d.contact[: d.ncon]:
            g1, g2 = c.geom
            r1, r2 = g1 in self.robot_geoms, g2 in self.robot_geoms
            if r1 == r2 or c.dist >= clearance:
                continue
            rg, og = (g1, g2) if r1 else (g2, g1)
            on = m.geom(og).name
            if any(on.startswith(f"static__{i}") or on.startswith(f"mover__{i}") for i in ignore):
                continue
            out.append((m.geom(rg).name or m.body(m.geom_bodyid[rg]).name, on, round(float(c.dist) * 1000, 2)))
        return out


# ------------------------------------------------------------------ 检查
def _mover_defaults(spec_d):
    return {mv["name"]: mv.get("rest", mv["joint"]["range"][0]) for mv in spec_d.get("movers", [])}


def check_gripper(spec_d) -> list[dict]:
    lo, hi = spec_d["robot"]["tool"]["opening_range"]
    margin = spec_d.get("grip_margin", 0.005)
    out = []
    for w in spec_d.get("workpieces", []):
        ok = lo <= w["grip_width"] and w["grip_width"] + 2 * margin <= hi
        out.append(dict(id=f"G:{w['name']}", ok=bool(ok), grip_width=w["grip_width"], opening_range=[lo, hi],
                        detail="" if ok else f"夹持宽度 {w['grip_width']*1000:.1f} mm 不在开口 {lo*1000:.0f}–{hi*1000:.0f} mm（两侧余量 {margin*1000:.0f} mm）内"))
    return out


def _site_target(pose, R, spec_d):
    """位姿给的是工具点 pose.tcp_in_hand（缺省为夹具 TCP）的位置；换算成 TCP site 应到达的位置。"""
    p = np.asarray(pose["pos"], float)
    if "tcp_in_hand" not in pose:
        return p
    tool = np.asarray(spec_d["robot"]["tool"].get("tcp_in_hand", [0, 0, 0.1034]), float)
    return p + R @ (tool - np.asarray(pose["tcp_in_hand"], float))


def solve_pose(rb: Robot, pose, spec_d, seeds=200, clearance=0.005, ref_q=None, keep=6):
    """多初值 IK。返回 (候选列表, 信息)；候选按（接触数, 离参考构型距离）排序，无碰撞且彼此不同的构型最多保留 keep 组。"""
    clearance = pose.get("clearance", clearance)
    movers = _mover_defaults(spec_d) | pose.get("movers", {})
    ign = pose.get("ignore", [])
    opening = pose.get("finger_q", 0.04)
    if "q" in pose:   # 直接给定关节角（如已有项目的停靠位）：只做碰撞检查
        q = np.asarray(pose["q"], float)
        rb.set_state(q, opening, movers)
        hits = rb.env_hits(clearance, ign)
        return [(q, None)], dict(reachable=True, hits=hits[:5], n_hits=len(hits))
    p = np.asarray(pose["pos"], float)
    R0 = tool_R(pose["approach"], pose["opening_axis"])
    # 两指夹爪对称：绕进入方向转 180° 是同一个抓取，两种朝向都试（pose.symmetric=false 可关闭）
    Rs = [R0] + ([R0 @ np.diag([-1.0, -1.0, 1.0])] if pose.get("symmetric", True) else [])
    rng = np.random.default_rng(0)
    mid = (rb.lo + rb.hi) / 2
    target = NATURAL if ref_q is None else np.asarray(ref_q, float)[-7:]
    found = []
    for k in range(seeds):
        seed = mid.copy()
        seed[-7:] = NATURAL if k == 0 else rb.lo[-7:] + (rb.hi[-7:] - rb.lo[-7:]) * rng.random(7)
        if k == 1 and ref_q is not None:   # 以上一个位姿的解为初值，保持构型连续
            seed = np.array(ref_q, float)
        if rb.has_rail:
            ax = np.asarray(spec_d["robot"]["rail"]["axis"], float)
            proj = float((p - np.asarray(spec_d["robot"]["base"])) @ ax)
            seed[0] = np.clip(proj + (0 if k < seeds // 2 else rng.normal(0, 0.25)), rb.lo[0], rb.hi[0])
        R = Rs[k % len(Rs)]
        q, err = rb.solve(_site_target(pose, R, spec_d), R, seed)
        if err[0] > 1e-4 or err[1] > 1e-3:
            continue
        rb.set_state(q, opening, movers)
        hits = rb.env_hits(clearance, ign)
        found.append(((len(hits), float(np.linalg.norm(q[-7:] - target))), q, hits, R))
    if not found:
        return [], dict(reachable=False, hits=[], n_hits=None)
    found.sort(key=lambda f: f[0])
    best = found[0]
    cands = []
    for sc, q, _, R in found:
        if sc[0] == 0 and all(np.linalg.norm(q - c[0]) > 0.3 for c in cands):
            cands.append((q, R))
        if len(cands) >= keep:
            break
    return (cands or [(best[1], best[3])]), dict(reachable=True, hits=best[2][:5], n_hits=best[0][0], posture_dist=round(best[0][1], 3))


def _approach(rb: Robot, pose, spec_d, q, R, clearance):
    """从目标位姿沿进入方向反向退出到预位姿，返回 (预位姿关节角, 最大跟踪误差, 接触)。"""
    a = np.asarray(pose["approach"], float); a /= np.linalg.norm(a)
    movers = _mover_defaults(spec_d) | pose.get("movers", {})
    p1 = _site_target(pose, R, spec_d); p0 = p1 - a * pose["standoff"]
    pc = pose.get("clearance", clearance)
    qk, worst, seg_hits = q.copy(), 0.0, []
    for s in np.linspace(0, 1, 11)[1:]:
        qk, err = rb.solve(p1 + (p0 - p1) * s, R, qk, iters=150)
        worst = max(worst, err[0])
        rb.set_state(qk, pose.get("finger_q", 0.04), movers)
        seg_hits += rb.env_hits(pc, pose.get("ignore", []))
    return qk, worst, seg_hits


def check_poses(rb: Robot, spec_d, clearance) -> tuple[list[dict], dict]:
    """sols[位姿名] = 可用构型列表；有 standoff 时为预位姿关节角（过渡检查从预位姿进出）。"""
    out, sols = [], {}
    prev = None
    for pose in spec_d.get("poses", []):   # 按列出的顺序求解，后一个位姿优先选与前一个连续的构型
        cands, info = solve_pose(rb, pose, spec_d, clearance=clearance, ref_q=prev)
        rec = dict(id=f"P:{pose['name']}", **info)
        ok = info["reachable"] and info["n_hits"] == 0
        usable, first_fail = [], None
        if ok:
            for q, R in cands:
                if pose.get("standoff"):
                    qk, worst, seg_hits = _approach(rb, pose, spec_d, q, R, clearance)
                    if worst < 1e-3 and not seg_hits:
                        usable.append((q, qk))
                    elif first_fail is None:
                        first_fail = (worst, seg_hits)
                else:
                    usable.append((q, q))
            ok = bool(usable)
        if usable:
            prev = usable[0][0]
            rec["q"] = [round(float(v), 4) for v in usable[0][0]]
            rec["configurations"] = len(usable)
        sols[pose["name"]] = [u[1] for u in usable]
        rec["ok"] = bool(ok)
        if not ok:
            why = []
            if not info["reachable"]:
                why.append("IK 无解（够不着或姿态不可达）")
            elif info["n_hits"]:
                why.append(f"最佳解仍有 {info['n_hits']} 处接触，例：{info['hits'][0][0]} × {info['hits'][0][1]}")
            elif first_fail:
                worst, seg_hits = first_fail
                if seg_hits:
                    why.append(f"进出段接触：{seg_hits[0][0]} × {seg_hits[0][1]}")
                if worst >= 1e-3:
                    why.append(f"进出段跟踪误差 {worst*1000:.1f} mm")
            rec["detail"] = "；".join(why)
        out.append(rec)
    return out, sols


def check_movers(rb: Robot, spec_d, park_q) -> list[dict]:
    m, d = rb.m, rb.d
    out = []
    mover_bodies = {mv["name"]: m.body(f"mover__{mv['name']}").id for mv in spec_d.get("movers", [])}
    for mv in spec_d.get("movers", []):
        lo, hi = mv["joint"]["range"]
        hits = {}
        bid = mover_bodies[mv["name"]]
        for v in np.linspace(lo, hi, 25):
            st = _mover_defaults(spec_d) | mv.get("sweep_others", {}) | {mv["name"]: v}
            rb.set_state(park_q, 0.04, st)
            for c in d.contact[: d.ncon]:
                b1, b2 = (m.geom_bodyid[g] for g in c.geom)
                if (b1 == bid) == (b2 == bid) or c.dist >= 0:
                    continue
                other = c.geom[1] if b1 == bid else c.geom[0]
                on = m.geom(other).name or m.body(m.geom_bodyid[other]).name
                if on.startswith(tuple(f"static__{n}" for n in mv.get("attached_to", []))):
                    continue
                hits.setdefault(on, []).append(round(float(v), 3))
        out.append(dict(id=f"D:{mv['name']}", ok=not hits,
                        hits={k: [v[0], v[-1]] for k, v in hits.items()},
                        detail="" if not hits else "扫掠接触：" + "、".join(f"{k}（{v[0]}–{v[-1]}）" for k, v in list(hits.items())[:3])))
    return out


def check_transitions(rb: Robot, spec_d, sols, clearance) -> list[dict]:
    """相邻关键位姿之间关节插值；在两端所有可用构型的组合里找一条无接触的。"""
    out = []
    poses = {p["name"]: p for p in spec_d.get("poses", [])}
    for a, b in spec_d.get("transitions", []):
        A, B = sols.get(a) or [], sols.get(b) or []
        if not A or not B:
            out.append(dict(id=f"T:{a}→{b}", ok=False, detail="端点位姿无解"))
            continue
        movers = _mover_defaults(spec_d) | poses.get(b, {}).get("movers", {})
        ign = poses.get(b, {}).get("ignore", []) + poses.get(a, {}).get("ignore", [])
        best = None
        for i, qa in enumerate(A):
            for j, qb in enumerate(B):
                hits = []
                for s in np.linspace(0, 1, 41):
                    rb.set_state(qa + (qb - qa) * s, 0.04, movers)
                    hits += [(round(float(s), 3),) + h for h in rb.env_hits(clearance, ign)]
                if best is None or len(hits) < len(best[2]):
                    best = (i, j, hits)
                if not hits:
                    break
            if best and not best[2]:
                break
        i, j, hits = best
        out.append(dict(id=f"T:{a}→{b}", ok=not hits, configurations=[i, j], tried=len(A) * len(B), hits=hits[:5],
                        detail="" if not hits else f"{len(A)}×{len(B)} 组构型组合都有接触，最少的一组 {len(hits)} 处，例 s={hits[0][0]}：{hits[0][1]} × {hits[0][2]}"))
    return out


# ------------------------------------------------------------------ 俯视图
def top_svg(spec_d, rb: Robot, sols, report) -> str:
    boxes = []
    for b in spec_d.get("static", []):
        boxes.append((b["name"], np.array(b["pos"][:2]), np.array(b["size"][:2]), b.get("yaw", 0.0), "s"))
    for mv in spec_d.get("movers", []):
        for g in mv["boxes"]:
            boxes.append((mv["name"], np.array(mv["joint"]["anchor"][:2]) + np.array(g["pos"][:2]), np.array(g["size"][:2]), g.get("yaw", 0.0), "m"))
    pts = np.concatenate([np.array([c - s for _, c, s, _, _ in boxes] + [c + s for _, c, s, _, _ in boxes])]) if boxes else np.zeros((1, 2))
    pts = np.vstack([pts, np.asarray(spec_d["robot"]["base"][:2])[None]])
    lo, hi = pts.min(0) - 0.25, pts.max(0) + 0.25
    W = 760
    sc = W / (hi[0] - lo[0])
    H = int((hi[1] - lo[1]) * sc)
    X = lambda x: (x - lo[0]) * sc  # noqa: E731
    Y = lambda y: H - (y - lo[1]) * sc  # noqa: E731
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="sans-serif" font-size="11">',
           '<style>.s{fill:#e8e6e0;stroke:#555}.m{fill:#dbe4f5;stroke:#4c50c4;stroke-dasharray:3 2}.t{fill:#333}.ok{fill:#2f7b4f}.bad{fill:#c63d2f}</style>']
    for name, c, s, yaw, k in boxes:
        corners = [np.array([sx * s[0], sy * s[1]]) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        R = np.array([[math.cos(yaw), -math.sin(yaw)], [math.sin(yaw), math.cos(yaw)]])
        pp = " ".join(f"{X((c + R @ v)[0]):.1f},{Y((c + R @ v)[1]):.1f}" for v in corners)
        svg.append(f'<polygon class="{k}" points="{pp}"/>')
        if k == "s":
            svg.append(f'<text class="t" x="{X(c[0]):.1f}" y="{Y(c[1]):.1f}" text-anchor="middle">{name}</text>')
    r = spec_d["robot"]
    b0 = np.asarray(r["base"][:2], float)
    if r.get("rail"):
        ax = np.asarray(r["rail"]["axis"][:2], float)
        a0, a1 = b0 + ax * r["rail"]["range"][0], b0 + ax * r["rail"]["range"][1]
        svg.append(f'<line x1="{X(a0[0]):.1f}" y1="{Y(a0[1]):.1f}" x2="{X(a1[0]):.1f}" y2="{Y(a1[1]):.1f}" stroke="#222" stroke-width="5" stroke-linecap="round"/>')
    svg.append(f'<circle cx="{X(b0[0]):.1f}" cy="{Y(b0[1]):.1f}" r="6" fill="#222"/>')
    status = {rec["id"][2:]: rec["ok"] for rec in report["poses"]}
    for pose in spec_d.get("poses", []):
        p = pose["pos"]
        cls = "ok" if status.get(pose["name"]) else "bad"
        svg.append(f'<circle class="{cls}" cx="{X(p[0]):.1f}" cy="{Y(p[1]):.1f}" r="5"/>'
                   f'<text class="t" x="{X(p[0]) + 7:.1f}" y="{Y(p[1]) - 6:.1f}">{pose["name"]}</text>')
    svg.append("</svg>")
    return "\n".join(svg)


# ------------------------------------------------------------------ 入口
def run(spec_path: Path, out_dir: Path | None = None) -> dict:
    spec_path = Path(spec_path)
    spec_d = json.loads(spec_path.read_text(encoding="utf-8"))
    out_dir = Path(out_dir or spec_path.parent)
    clearance = spec_d.get("clearance", 0.005)
    _, m = build(spec_d)
    m.geom_margin[:] = 0
    rb = Robot(m)
    m.geom_margin[list(rb.robot_geoms)] = clearance
    report: dict = dict(spec=spec_path.name, clearance_m=clearance, mujoco=mujoco.__version__)
    report["gripper"] = check_gripper(spec_d)
    report["poses"], sols = check_poses(rb, spec_d, clearance)
    park = (sols.get(spec_d.get("park_pose", "")) or [None])[0]
    if park is None:
        park = rb.posture((rb.lo + rb.hi) / 2)
    m.geom_margin[:] = 0
    report["movers"] = check_movers(rb, spec_d, park)
    m.geom_margin[list(rb.robot_geoms)] = clearance
    report["transitions"] = check_transitions(rb, spec_d, sols, clearance)
    allrec = report["gripper"] + report["poses"] + report["movers"] + report["transitions"]
    report["summary"] = dict(total=len(allrec), failed=[r["id"] for r in allrec if not r["ok"]])
    report["status"] = "PASS" if not report["summary"]["failed"] else "FAIL"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "preflight_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    (out_dir / "preflight_top.svg").write_text(top_svg(spec_d, rb, sols, report), encoding="utf-8")
    return report
