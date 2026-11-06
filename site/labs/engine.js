// 交互实验的实时引擎（MuJoCo WASM）。与 runner.py 逻辑一一对应：同一份 labs.json、同样的控制与测量。
// 网页里内联使用；Node 里 import 用来和 Python 结果对齐。

export function instantiate(lab, choice) {
  let text = JSON.stringify(lab);
  for (const p of lab.params || []) {
    const sub = p.options[choice[p.id]].sub;
    for (const [k, v] of Object.entries(sub)) text = text.split("{{" + k + "}}").join(String(v).replace(/"/g, '\\"'));
  }
  return JSON.parse(text);
}

export function ctrlValue(ch, t) {
  if (ch.kind === "pwl") {
    const pts = ch.pts.map(([a, b]) => [parseFloat(a), parseFloat(b)]);
    if (t <= pts[0][0]) return pts[0][1];
    for (let i = 0; i + 1 < pts.length; i++) {
      const [t0, v0] = pts[i], [t1, v1] = pts[i + 1];
      if (t <= t1) { let s = (t - t0) / (t1 - t0); s = s * s * (3 - 2 * s); return v0 + (v1 - v0) * s; }
    }
    return pts[pts.length - 1][1];
  }
  if (ch.kind === "sine") {
    const ramp = Math.min(1, t / (ch.ramp ?? 0.5));
    const q = ch.c + ramp * ch.A * Math.sin(ch.w * t), qd = ramp * ch.A * ch.w * Math.cos(ch.w * t);
    return q + parseFloat(ch.ff ?? 0) * qd;
  }
  throw new Error(ch.kind);
}

export function refValue(ch, t) {
  const ramp = Math.min(1, t / (ch.ramp ?? 0.5));
  return ch.c + ramp * ch.A * Math.sin(ch.w * t);
}

const name = (m, kind, i) => { const a = m[kind](i); const n = a.name; return n; };

// 一次实时运行：sim = new Run(mj, inst)；sim.step() 推进一个时间步；sim.frame() 取当前绘制数据
export class Run {
  constructor(mj, inst) {
    this.mj = mj; this.inst = inst;
    const m = this.m = mj.MjModel.from_xml_string(inst.xml);
    const d = this.d = new mj.MjData(m);
    for (const [jn, v] of Object.entries(inst.init_qpos || {})) d.qpos[m.jnt_qposadr[m.jnt(jn).id]] = v;
    mj.mj_forward(m, d);
    this.dt = m.opt.timestep;
    this.n = Math.round(inst.duration / this.dt);
    this.k = 0;
    this.chans = (inst.control || []).map(c => [m.actuator(c.act).id, c]);
    this.gname = []; for (let i = 0; i < m.ngeom; i++) this.gname.push(name(m, "geom", i) || "");
    this.moving = []; for (let i = 0; i < m.ngeom; i++) if (m.geom_bodyid[i] !== 0) this.moving.push(i);
    const set = prefixes => { const s = new Set(); this.gname.forEach((g, i) => { if ((prefixes || [""]).some(p => g.startsWith(p))) s.add(i); }); return s; };
    this.metrics = inst.metrics.map(mt => ({ mt, A: set(mt.geoms), B: set(mt.geoms2), acc: null, win: null, s0: null }));
    this.series = Object.fromEntries(inst.metrics.map(mt => [mt.id, []]));
    this.f6 = new mj.DoubleBuffer(6);
    this.contacts = [];
    this.measure();
  }
  body(n) { return this.m.body(n).id; }
  readContacts() {
    const d = this.d, out = [], cv = d.contact;
    for (let k = 0; k < d.ncon; k++) { const c = cv.get(k); out.push({ g1: c.geom1, g2: c.geom2, dist: c.dist, pos: Array.from(c.pos), j: k }); c.delete?.(); }
    cv.delete?.();
    this.contacts = out; return out;
  }
  measure() {
    const { m, d, mj } = this, t = d.time;
    const cons = this.readContacts();
    for (const M of this.metrics) {
      const mt = M.mt;
      if (t < (mt.t0 ?? 0) || t > (mt.t1 ?? 1e9)) continue;
      let v;
      if (mt.kind === "maxpen") {
        v = 0; for (const c of cons) if ((M.A.has(c.g1) && M.B.has(c.g2)) || (M.A.has(c.g2) && M.B.has(c.g1))) v = Math.max(v, -c.dist);
        v *= 1000; M.acc = Math.max(M.acc ?? 0, v); M.win = Math.max(M.win ?? 0, v);
      } else if (mt.kind === "slip") {
        const bz = d.xpos[3 * this.body(mt.body) + 2] - d.xpos[3 * this.body(mt.ref) + 2];
        if (M.s0 === null) M.s0 = bz; v = (M.s0 - bz) * 1000; M.acc = Math.max(M.acc ?? 0, v); M.win = v;
      } else if (mt.kind === "xyerr" || mt.kind === "poserr") {
        const b = 3 * this.body(mt.body), p = [d.xpos[b], d.xpos[b + 1], d.xpos[b + 2]];
        v = mt.kind === "xyerr" ? Math.hypot(p[0] - mt.target[0], p[1] - mt.target[1]) * 1000
          : Math.hypot(p[0] - mt.target[0], p[1] - mt.target[1], p[2] - mt.target[2]) * 1000;
        M.acc = v; M.win = v;
      } else if (mt.kind === "track") {
        const ch = this.chans.find(([, c]) => c.act === mt.act)[1];
        const q = d.qpos[m.jnt_qposadr[m.jnt(mt.joint).id]];
        v = Math.abs((q - refValue(ch, t)) * 180 / Math.PI); M.acc = Math.max(M.acc ?? 0, v); M.win = v;
      } else if (mt.kind === "reltilt") {
        const a = 9 * this.body(mt.body), b = 9 * this.body(mt.ref);
        const dot = d.xmat[a + 2] * d.xmat[b + 2] + d.xmat[a + 5] * d.xmat[b + 5] + d.xmat[a + 8] * d.xmat[b + 8];
        v = Math.acos(Math.max(-1, Math.min(1, dot))) * 180 / Math.PI; M.acc = Math.max(M.acc ?? 0, v); M.win = v;
      } else if (mt.kind === "support") {
        let fz = 0;
        for (const c of cons) if ((M.A.has(c.g1) && M.B.has(c.g2)) || (M.A.has(c.g2) && M.B.has(c.g1))) {
          mj.mj_contactForce(m, d, c.j, this.f6); fz += this.f6.GetView()[0];
        }
        const w = m.body_subtreemass[this.body(mt.body)] * 9.81;
        v = fz / w; M.acc = M.acc === null ? v : Math.min(M.acc, v); M.win = v;
      }
    }
  }
  step() {
    const { m, d, mj } = this;
    if (this.k >= this.n) return false;
    for (const [a, ch] of this.chans) d.ctrl[a] = ctrlValue(ch, d.time);
    mj.mj_step(m, d); this.k++;
    this.measure();
    return true;
  }
  sample() {   // 每帧记录一次曲线点（与 runner.py 的 60 fps 采样同义：maxpen 取窗口最大值）
    for (const M of this.metrics) {
      this.series[M.mt.id].push(M.win === null ? null : M.win);
      if (M.mt.kind === "maxpen") M.win = this.d.time < (M.mt.t0 ?? 0) ? null : 0;
    }
  }
  result() {
    const out = {};
    for (const M of this.metrics) {
      const v = M.acc ?? 0, g = M.mt.gate;
      out[M.mt.id] = { v, ok: g ? (g.op === "<=" ? v <= g.v : v >= g.v) : null };
    }
    return out;
  }
  geoms() {   // 静态几何表（类型、尺寸、名字）
    const { m } = this, out = [];
    for (let i = 0; i < m.ngeom; i++) out.push({ name: this.gname[i], type: m.geom_type[i], size: [m.geom_size[3 * i], m.geom_size[3 * i + 1], m.geom_size[3 * i + 2]], body: m.geom_bodyid[i], visible: m.geom_rgba[4 * i + 3] > 0 });
    return out;
  }
  poses() {   // 所有几何当前位姿：[x,y,z, 9 个旋转矩阵元素]
    const { d, m } = this, out = [];
    for (let i = 0; i < m.ngeom; i++) out.push([d.geom_xpos[3 * i], d.geom_xpos[3 * i + 1], d.geom_xpos[3 * i + 2], ...Array.from(d.geom_xmat.subarray(9 * i, 9 * i + 9))]);
    return out;
  }
  dispose() { try { this.f6.delete(); this.d.delete(); this.m.delete(); } catch (e) { } }
}
