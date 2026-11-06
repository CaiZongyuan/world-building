"""交互实验的离线运行器：读 labs.json（与网页共用同一份定义），按参数组合跑 MuJoCo，输出回放数据 fallback/<实验>.json。
网页里的实时模式（MuJoCo WASM）用同一份定义、同样的控制与测量逻辑；本脚本的结果就是网页在无法加载引擎时播放的预计算回放。
用法：python runner.py [lab_id ...]   （不带参数跑全部）"""
import itertools
import json
import math
import sys
from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
SPEC = json.loads((HERE / "labs.json").read_text(encoding="utf-8"))
FPS = 60


def instantiate(lab, choice):
    """choice: {param_id: option_index} → 替换 {{KEY}} 后的 lab 定义"""
    text = json.dumps(lab, ensure_ascii=False)
    for p in lab["params"]:
        for k, v in p["options"][choice[p["id"]]]["sub"].items():
            text = text.replace("{{" + k + "}}", str(v))
    return json.loads(text)


def ctrl_value(ch, t):
    if ch["kind"] == "pwl":
        pts = [(float(a), float(b)) for a, b in ch["pts"]]
        if t <= pts[0][0]:
            return pts[0][1]
        for (t0, v0), (t1, v1) in zip(pts, pts[1:]):
            if t <= t1:
                s = (t - t0) / (t1 - t0); s = s * s * (3 - 2 * s)   # smoothstep，避免阶跃
                return v0 + (v1 - v0) * s
        return pts[-1][1]
    if ch["kind"] == "sine":   # q_ref = c + A sin(wt)，可选前馈 (kv/kp)·q̇_ref
        ramp = min(1.0, t / ch.get("ramp", 0.5))
        q = ch["c"] + ramp * ch["A"] * math.sin(ch["w"] * t)
        qd = ramp * ch["A"] * ch["w"] * math.cos(ch["w"] * t)
        return q + float(ch.get("ff", 0)) * qd
    raise ValueError(ch["kind"])


def ref_value(ch, t):
    ramp = min(1.0, t / ch.get("ramp", 0.5))
    return ch["c"] + ramp * ch["A"] * math.sin(ch["w"] * t)


def geom_ids(m, prefixes):
    return {i for i in range(m.ngeom) if any((m.geom(i).name or "").startswith(p) for p in prefixes)}


def run(lab):
    m = mujoco.MjModel.from_xml_string(lab["xml"])
    d = mujoco.MjData(m)
    if "init_qpos" in lab:
        for jn, v in lab["init_qpos"].items():
            d.qpos[m.jnt_qposadr[m.joint(jn).id]] = v
    mujoco.mj_forward(m, d)
    chans = [(m.actuator(c["act"]).id, c) for c in lab.get("control", [])]
    dt = m.opt.timestep
    n = int(round(lab["duration"] / dt))
    every = max(1, int(round(1 / (FPS * dt))))
    moving = [i for i in range(m.ngeom) if m.geom_bodyid[i] != 0]
    frames, series = [], {mt["id"]: [] for mt in lab["metrics"]}
    acc = {mt["id"]: None for mt in lab["metrics"]}
    win = {mt["id"]: -1e9 for mt in lab["metrics"]}
    gsets = {mt["id"]: (geom_ids(m, mt.get("geoms", [""])), geom_ids(m, mt.get("geoms2", [""]))) for mt in lab["metrics"]}
    state0 = {}
    f6 = np.zeros(6)
    for k in range(n + 1):
        t = d.time
        for a, ch in chans:
            d.ctrl[a] = ctrl_value(ch, t)
        for ev in lab.get("events", []):
            if abs(t - ev["t"]) < dt / 2:
                d.eq_active[m.equality(ev["eq"]).id] = ev["on"]
        # ---- 测量
        for mt in lab["metrics"]:
            kind, i = mt["kind"], mt["id"]
            if t < mt.get("t0", 0) or t > mt.get("t1", 1e9):
                continue
            if kind == "maxpen":
                A, B = gsets[i]; v = 0.0
                for c in d.contact[:d.ncon]:
                    if (c.geom1 in A and c.geom2 in B) or (c.geom2 in A and c.geom1 in B):
                        v = max(v, -c.dist)
                v *= 1000
                acc[i] = max(acc[i] or 0.0, v); win[i] = max(win[i], v)
            elif kind == "slip":   # body 相对参考 body 的竖直下滑量（mm），以 t0 时刻为零
                bz = d.xpos[m.body(mt["body"]).id][2] - d.xpos[m.body(mt["ref"]).id][2]
                state0.setdefault(i, bz); v = (state0[i] - bz) * 1000
                acc[i] = max(acc[i] or 0.0, v); win[i] = v
            elif kind == "xyerr":   # body 到目标点的水平距离（mm），取末值
                p = d.xpos[m.body(mt["body"]).id]; v = math.hypot(p[0] - mt["target"][0], p[1] - mt["target"][1]) * 1000
                acc[i] = float(v); win[i] = float(v)
            elif kind == "poserr":   # body 到目标点的三维距离（mm），取末值
                p = d.xpos[m.body(mt["body"]).id]; v = float(np.linalg.norm(p - np.array(mt["target"]))) * 1000
                acc[i] = float(v); win[i] = float(v)
            elif kind == "track":   # 关节跟踪误差（°），取最大
                ch = next(c for _, c in chans if c["act"] == mt["act"])
                q = d.qpos[m.jnt_qposadr[m.joint(mt["joint"]).id]]; v = abs(math.degrees(q - ref_value(ch, t)))
                acc[i] = max(acc[i] or 0.0, v); win[i] = v
            elif kind == "reltilt":   # body z 轴相对参考 body z 轴的夹角（°），取最大
                za = d.xmat[m.body(mt["body"]).id].reshape(3, 3)[:, 2]; zb = d.xmat[m.body(mt["ref"]).id].reshape(3, 3)[:, 2]
                v = math.degrees(math.acos(max(-1.0, min(1.0, float(za @ zb)))))
                acc[i] = max(acc[i] or 0.0, v); win[i] = v
            elif kind == "support":   # 支撑面法向力合计 ÷ 重量，取窗口内最小
                A, B = gsets[i]; fz = 0.0
                for j, c in enumerate(d.contact[:d.ncon]):
                    if (c.geom1 in A and c.geom2 in B) or (c.geom2 in A and c.geom1 in B):
                        mujoco.mj_contactForce(m, d, j, f6); fz += f6[0]
                w = m.body_subtreemass[m.body(mt["body"]).id] * 9.81
                v = fz / w; acc[i] = v if acc[i] is None else min(acc[i], v); win[i] = v
        if k % every == 0:
            fr = []
            for g in moving:
                q = np.zeros(4); mujoco.mju_mat2Quat(q, d.geom_xmat[g])
                fr.append([round(float(x), 6) for x in (*d.geom_xpos[g], *q)])
            cp = [[round(float(x), 5) for x in c.pos] + [round(-float(c.dist) * 1000, 4)] for c in d.contact[:d.ncon] if c.dist < 0]
            frames.append(dict(t=round(t, 4), g=fr, c=cp[:12]))
            for mt in lab["metrics"]:
                series[mt["id"]].append(None if win[mt["id"]] == -1e9 else round(win[mt["id"]], 5))
                if mt["kind"] == "maxpen":
                    win[mt["id"]] = -1e9 if t < mt.get("t0", 0) else 0.0
        if k < n:
            mujoco.mj_step(m, d)
    res = {}
    for mt in lab["metrics"]:
        v = float(acc[mt["id"]]) if acc[mt["id"]] is not None else 0.0
        g = mt.get("gate")
        ok = None if not g else (v <= g["v"] if g["op"] == "<=" else v >= g["v"])
        res[mt["id"]] = dict(v=round(v, 5), ok=ok)
    return dict(frames=frames, series=series, result=res, moving=moving)


def static_geoms(lab):
    m = mujoco.MjModel.from_xml_string(lab["xml"]); d = mujoco.MjData(m); mujoco.mj_forward(m, d)
    out = []
    for g in range(m.ngeom):
        q = np.zeros(4); mujoco.mju_mat2Quat(q, d.geom_xmat[g])
        out.append(dict(name=m.geom(g).name, type=int(m.geom_type[g]), size=[round(float(x), 6) for x in m.geom_size[g]],
                        body=int(m.geom_bodyid[g]), pose=[round(float(x), 6) for x in (*d.geom_xpos[g], *q)],
                        visible=bool(m.geom_rgba[g][3] > 0)))
    return out


def run_chain(lab):
    """状态接力：一次跑完 vs 中途存档再接着跑（完整积分状态 / 只存 qpos+qvel）。比较板的轨迹差。"""
    base = next(l for l in SPEC["labs"] if l["id"] == lab["base"])
    inst = instantiate(base, {p["id"]: p["default"] for p in base["params"]})
    m = mujoco.MjModel.from_xml_string(inst["xml"])
    chans = [(m.actuator(c["act"]).id, c) for c in inst["control"]]
    plate = m.body("plate").id
    dt = m.opt.timestep; n = int(round(inst["duration"] / dt)); ks = int(round(lab["split"] / dt))

    def fresh():
        d = mujoco.MjData(m)
        for jn, v in inst.get("init_qpos", {}).items():
            d.qpos[m.jnt_qposadr[m.joint(jn).id]] = v
        mujoco.mj_forward(m, d); return d

    def step(d, skip=()):
        for a, ch in chans:
            if ch["act"] not in skip:
                d.ctrl[a] = ctrl_value(ch, d.time)
        mujoco.mj_step(m, d)

    ref = fresh(); traj = []
    every = max(1, int(round(1 / (FPS * dt))))
    for k in range(n):
        step(ref); traj.append(ref.xpos[plate].copy())
    out = {"ref_z": [round(float(x[2]) * 1000, 4) for x in traj[::every]], "split": lab["split"], "fps": FPS}
    for mode in ("full", "qpos_qvel", "qpos_only", "ctrl_zero"):
        d = fresh()
        for k in range(ks):
            step(d)
        d2 = mujoco.MjData(m)
        if mode == "full":
            spec = mujoco.mjtState.mjSTATE_INTEGRATION
            st = np.zeros(mujoco.mj_stateSize(m, spec)); mujoco.mj_getState(m, d, st, spec); mujoco.mj_setState(m, d2, st, spec)
        elif mode == "qpos_qvel":
            d2.qpos[:] = d.qpos; d2.qvel[:] = d.qvel; d2.time = d.time
        elif mode == "qpos_only":
            d2.qpos[:] = d.qpos; d2.time = d.time
        else:   # 完整状态，但下一段不再驱动手指：手指的执行器指令停在 0（就是集成时"被动设备指令回零"）
            spec = mujoco.mjtState.mjSTATE_INTEGRATION
            st = np.zeros(mujoco.mj_stateSize(m, spec)); mujoco.mj_getState(m, d, st, spec); mujoco.mj_setState(m, d2, st, spec)
            d2.ctrl[:] = 0
        mujoco.mj_forward(m, d2)
        skip = ("a_l", "a_r") if mode == "ctrl_zero" else ()
        dev = 0.0; zs = []
        for k in range(ks, n):
            step(d2, skip); dev = max(dev, float(np.linalg.norm(d2.xpos[plate] - traj[k])))
            if k % every == 0:
                zs.append(round(float(d2.xpos[plate][2]) * 1000, 4))
        out[mode] = dict(max_dev_m=dev, end_dev_m=float(np.linalg.norm(d2.xpos[plate] - traj[-1])), z=zs)
        print("chain", mode, out[mode]["max_dev_m"], flush=True)
    return out


def main(ids):
    out_dir = HERE / "fallback"
    out_dir.mkdir(exist_ok=True)
    for lab in SPEC["labs"]:
        if ids and lab["id"] not in ids:
            continue
        if lab.get("special") == "chain":
            data = run_chain(lab)
        else:
            data = {}
            ranges = [range(len(p["options"])) for p in lab["params"]]
            for combo in itertools.product(*ranges):
                choice = {p["id"]: c for p, c in zip(lab["params"], combo)}
                inst = instantiate(lab, choice)
                r = run(inst)
                key = "|".join(map(str, combo))
                data[key] = dict(frames=r["frames"], series=r["series"], result=r["result"], geoms=static_geoms(inst))
                print(lab["id"], key, json.dumps(r["result"], ensure_ascii=False), flush=True)
        out_f = out_dir / f"{lab['id']}.json"
        out_f.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
        print(out_f.name, out_f.stat().st_size // 1024, "KB")


if __name__ == "__main__":
    main(sys.argv[1:])
