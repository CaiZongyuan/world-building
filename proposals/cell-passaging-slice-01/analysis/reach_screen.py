"""可达性初筛：Panda（Menagerie）放在 P3 底座位置，测关键 TCP 位姿能否 IK 求解。
只做运动学，不含碰撞与动力学；结论只用于方案预览的风险判断。"""
import json, sys
import numpy as np, mujoco

PANDA = "/mnt/d/Projects/Robots/assets/third_party/menagerie_franka_emika_panda/panda.xml"
spec = mujoco.MjSpec.from_file(PANDA)
base = spec.worldbody.first_body()
base.pos = [0.25, -1.05, 0.5]
hand = spec.body("hand")
TCP_OFFSET = float(sys.argv[1]) if len(sys.argv) > 1 else 0.1034  # 手掌到指尖中心
hand.add_site(name="tcp", pos=[0, 0, TCP_OFFSET])
m = spec.compile(); d = mujoco.MjData(m)
sid = m.site("tcp").id
lo, hi = m.jnt_range[:7, 0], m.jnt_range[:7, 1]

def rot(z, x):
    z = np.array(z, float); x = np.array(x, float); y = np.cross(z, x)
    return np.column_stack([x, y, z])

def ik(p, R, iters=400):
    best = None
    for seed in range(12):
        rng = np.random.default_rng(seed)
        d.qpos[:7] = lo + (hi - lo) * (0.5 if seed == 0 else rng.random(7))
        for _ in range(iters):
            mujoco.mj_kinematics(m, d); mujoco.mj_comPos(m, d)
            ep = p - d.site_xpos[sid]
            Rc = d.site_xmat[sid].reshape(3, 3)
            er = 0.5 * sum(np.cross(Rc[:, i], R[:, i]) for i in range(3))
            e = np.concatenate([ep, er])
            Jp = np.zeros((3, m.nv)); Jr = np.zeros((3, m.nv))
            mujoco.mj_jacSite(m, d, Jp, Jr, sid)
            J = np.vstack([Jp, Jr])[:, :7]
            dq = J.T @ np.linalg.solve(J @ J.T + 1e-4 * np.eye(6), e)
            d.qpos[:7] = np.clip(d.qpos[:7] + dq, lo, hi)
        pe, re = np.linalg.norm(ep), np.linalg.norm(er)
        if best is None or pe + re < best[0] + best[1]:
            best = (pe, re, d.qpos[:7].copy())
        if pe < 1e-3 and re < 1e-2:
            break
    return best

front = rot([0, 1, 0], [1, 0, 0])      # 从 -Y 侧水平伸入，指向 +Y，手指沿 X 张合
down = rot([0, 0, -1], [1, 0, 0])      # 自上而下，手指沿 X 张合
targets = {}
for i, z in enumerate([0.315, 0.435, 0.555, 0.675], 1):
    for y in (-0.18, -0.065):
        targets[f"隔板{i} 板心 y={y}"] = ([0, y, z + 0.010], front)
targets["培养箱门外预备位"] = ([0, -0.50, 0.45], front)
targets["观察站抽屉伸出位（板心上方）"] = ([0.6, -1.2 + 0.055 + 0.19, 0.6 + 0.08], down)
out = {}
for k, (p, R) in targets.items():
    pe, re, q = ik(np.array(p), R)
    out[k] = {"pos_err_mm": round(pe * 1000, 2), "rot_err": round(re, 4), "reachable": bool(pe < 1e-3 and re < 1e-2)}
    print(f"{'✅' if out[k]['reachable'] else '❌'} {k}: 位置误差 {pe*1000:.1f} mm, 姿态误差 {re:.3f}")
json.dump({"tcp_offset_m": TCP_OFFSET, "base": [0.25, -1.05, 0.5], "results": out},
          open(__file__.replace(".py", f"_tcp{TCP_OFFSET:.3f}.json"), "w"), ensure_ascii=False, indent=1)
