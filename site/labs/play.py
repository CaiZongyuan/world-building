"""在本机 MuJoCo 窗口里播放一个交互实验（与网页同一份 labs.json、同样的控制时间表）。
用法（仓库根目录）：
  uv run --extra sim python site/labs/play.py drop             # 默认参数
  uv run --extra sim python site/labs/play.py drop h=4 tc=2    # 参数取选项序号（从 0 开始），和网页按钮顺序一致
  uv run --extra sim python site/labs/play.py --list           # 列出全部实验和参数
窗口里按空格暂停，双击物体后 Ctrl+右键拖动可以施加外力；看完关窗即可。结束时在终端打印本次的门限判定。"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mujoco  # noqa: E402
import runner  # noqa: E402


def main(argv):
    labs = {l["id"]: l for l in runner.SPEC["labs"] if not l.get("special")}
    if not argv or argv[0] == "--list":
        for l in labs.values():
            print(f"{l['id']:7s} {l['title']}")
            for p in l["params"]:
                print(f"    {p['id']}=" + " | ".join(f"{i}:{o['label']}" for i, o in enumerate(p["options"])) + f"   （默认 {p['default']}）")
        return
    lab = labs[argv[0]]
    choice = {p["id"]: p["default"] for p in lab["params"]}
    for a in argv[1:]:
        if "=" in a:
            k, v = a.split("="); choice[k] = int(v)
    inst = runner.instantiate(lab, choice)
    if "--dry" in argv:   # 只检查能否编译并跑完（无窗口环境用）
        print(runner.run(inst)["result"]); return
    import mujoco.viewer
    m = mujoco.MjModel.from_xml_string(inst["xml"]); d = mujoco.MjData(m)
    for jn, v in inst.get("init_qpos", {}).items():
        d.qpos[m.jnt_qposadr[m.joint(jn).id]] = v
    mujoco.mj_forward(m, d)
    chans = [(m.actuator(c["act"]).id, c) for c in inst.get("control", [])]
    with mujoco.viewer.launch_passive(m, d) as v:
        while v.is_running():
            t0 = time.time()
            if d.time < inst["duration"]:
                for a, ch in chans:
                    d.ctrl[a] = runner.ctrl_value(ch, d.time)
                mujoco.mj_step(m, d)
            v.sync()
            time.sleep(max(0.0, m.opt.timestep - (time.time() - t0)))
    print(runner.run(inst)["result"])


if __name__ == "__main__":
    main(sys.argv[1:])
