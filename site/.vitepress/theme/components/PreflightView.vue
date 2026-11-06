<script setup lang="ts">
// The real preflight of the full-lab project (layout v3): box proxies seen from
// above, every key pose, and what the 57 checks are. Click a pose to see where
// the IK put the carriage on the rail and which way the gripper goes in.
import { computed, ref } from 'vue'
import { MOVERS, POSES, STATIC } from '../landing/layout'
import PF from '../data/preflight_v3.json'

const S = 190
const X = (x: number) => (x + 0.35) * S
const Y = (y: number) => (1.5 - y) * S
const W = X(3.45), H = Y(-1.45)
const boxes = STATIC.filter((b) => b.pos[2] + b.size[2] > 0.3 || b.name === 'rail_beam').map((b) => ({ name: b.name, x: X(b.pos[0] - b.size[0]), y: Y(b.pos[1] + b.size[1]), w: 2 * b.size[0] * S, h: 2 * b.size[1] * S, dev: b.name.split('_')[0] }))
const sweeps = MOVERS.filter((m) => m.type === 'hinge' && m.axis[2] !== 0).map((m) => {
  const b = m.boxes[0]
  const r = Math.hypot(b.pos[0], b.pos[1]) + b.size[0]
  const a0 = Math.atan2(b.pos[1], b.pos[0])
  const a1 = a0 + Math.sign(m.axis[2]) * m.range[1]
  const p = (a: number) => [X(m.anchor[0] + r * Math.cos(a)), Y(m.anchor[1] + r * Math.sin(a))]
  const [x0, y0] = p(a0), [x1, y1] = p(a1)
  const large = m.range[1] > Math.PI ? 1 : 0
  const sweep = m.axis[2] < 0 ? 1 : 0
  return { name: m.name, d: `M${X(m.anchor[0])} ${Y(m.anchor[1])} L${x0} ${y0} A ${r * S} ${r * S} 0 ${large} ${sweep} ${x1} ${y1} Z` }
})
const poses = PF.poses.map((p: any) => ({ ...p, x: X(POSES[p.id][0]), y: Y(POSES[p.id][1]), z: POSES[p.id][2], via: p.id.startsWith('via_') || p.id === 'park' }))
const sel = ref('incubator_shelf3')
const cur = computed(() => poses.find((p: any) => p.id === sel.value)!)
const base = computed(() => ({ x: X(cur.value.rail), y: Y(0) }))
const arrow = computed(() => {
  const a = cur.value.approach || [0, 0, -1]
  const h = Math.hypot(a[0], a[1])
  if (h < 0.1) return null
  const len = 0.22 * S
  return { x1: cur.value.x - (a[0] / h) * len, y1: cur.value.y + (a[1] / h) * len, x2: cur.value.x, y2: cur.value.y }
})
const tab = ref<'map' | 'checks' | 'history'>('map')
const HISTORY = [
  { v: 'v1', f: '11 / 33', p: '培养箱外门扫过导轨和机器人；开盖器机身挡住偏置指；工作站里的离心管从正上方够不着；抽屉、离心机盖是依附关系却被判成碰撞；停靠位在工作站门的扫掠区里', c: '—' },
  { v: 'v2', f: '10 / 33', p: '废物箱投放方向写反；离心机后方孔位远了约 2 cm；外门下沿低于导轨梁顶；远距离过渡直接在关节空间插值，扫到门和台子', c: '培养箱挪到导轨末端、铰链放外侧；开盖器改细柱夹爪；管座改为台面前沿的细柱；标出依附关系；停靠位移到导轨南侧' },
  { v: 'v3', f: '0 / 57', p: '—', c: '离心台往导轨挪近 0.10 m；培养箱垫高 0.12 m；导轨梁缩短；每个工位加门口过渡点；按工艺顺序生成完整路线（27 段过渡）' },
]
const NAMES: Record<string, string> = { incubator: '培养箱', imager: '观察站', workstation: '工作站', centrifuge: '离心机', decapper: '开盖器', side: '侧架', waste: '废物托盘', rail: '导轨' }
</script>

<template>
  <div class="pv vp-raw wb-panel">
    <div class="top">
      <div class="wb-seg">
        <button type="button" :aria-pressed="tab === 'map'" @click="tab = 'map'">俯视图与位姿</button>
        <button type="button" :aria-pressed="tab === 'checks'" @click="tab = 'checks'">57 项检查</button>
        <button type="button" :aria-pressed="tab === 'history'" @click="tab = 'history'">v1 → v3</button>
      </div>
      <span class="src wb-mono">cell-passaging-lab · 02-proposal/analysis · 布局 v3</span>
    </div>

    <div v-if="tab === 'map'" class="map">
      <svg :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="全流程实验室布局俯视图">
        <g class="sweeps"><path v-for="s in sweeps" :key="s.name" :d="s.d" /></g>
        <rect v-for="b in boxes" :key="b.name" :x="b.x" :y="b.y" :width="b.w" :height="b.h" :class="['bx', b.dev]" />
        <text v-for="d in ['incubator', 'imager', 'workstation', 'centrifuge']" :key="d" class="dn" :x="d === 'incubator' ? X(2.85) : d === 'imager' ? X(1.75) : d === 'workstation' ? X(1.55) : X(0.55)" :y="d === 'workstation' ? Y(1.3) : Y(-1.28)" text-anchor="middle">{{ NAMES[d] }}</text>
        <circle class="reach" :cx="base.x" :cy="base.y" :r="0.855 * S" />
        <rect class="carriage" :x="base.x - 0.16 * S" :y="base.y - 0.15 * S" :width="0.32 * S" :height="0.3 * S" rx="6" />
        <line class="link" :x1="base.x" :y1="base.y" :x2="cur.x" :y2="cur.y" />
        <line v-if="arrow" class="appr" :x1="arrow.x1" :y1="arrow.y1" :x2="arrow.x2" :y2="arrow.y2" marker-end="url(#pv-arrow)" />
        <defs><marker id="pv-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0 0 10 5 0 10z" fill="var(--accent)" /></marker></defs>
        <g v-for="p in poses" :key="p.id" class="pose" :class="{ on: p.id === sel, via: p.via }" @click="sel = p.id">
          <circle :cx="p.x" :cy="p.y" :r="p.id === sel ? 9 : 6" />
        </g>
      </svg>
      <div class="info">
        <p class="wb-eyebrow">点地图上的圆点选一个位姿</p>
        <h4 class="wb-mono">{{ cur.id }}</h4>
        <dl>
          <div><dt>TCP 位置</dt><dd class="wb-mono">x {{ POSES[cur.id][0].toFixed(2) }} · y {{ POSES[cur.id][1].toFixed(2) }} · z {{ cur.z.toFixed(3) }} m</dd></div>
          <div><dt>导轨位置</dt><dd class="wb-mono">{{ cur.rail.toFixed(2) }} m（IK 把导轨也当一个自由度）</dd></div>
          <div><dt>进入方向</dt><dd>{{ cur.approach && Math.abs(cur.approach[2]) > 0.8 ? '从上往下' : cur.approach && Math.abs(cur.approach[2]) > 0.3 ? '斜向下（沿离心机 30° 孔轴）' : '水平伸入' }}</dd></div>
          <div><dt>无碰撞构型</dt><dd><b>{{ cur.configs }}</b> 组（每个位姿最多保留 6 组，供过渡段挑选）</dd></div>
        </dl>
        <p class="note">圆圈是 Panda 约 0.855 m 的臂展。手爪水平伸入取放板的位姿，都要落在同一条可解的高度带里（TCP 0.90–0.99 m）。这条约束是仿真阶段才发现、再写回布局的。</p>
        <div class="wb-seg small"><button v-for="p in poses.filter((x: any) => !x.via)" :key="p.id" type="button" :aria-pressed="p.id === sel" @click="sel = p.id">{{ p.id.replace(/_/g, ' ') }}</button></div>
      </div>
    </div>

    <div v-else-if="tab === 'checks'" class="checks">
      <div class="cat"><h4><b>G</b> 夹爪行程 · {{ PF.gripper.length }} 项</h4><p>开口范围 {{ PF.opening[0] }}–{{ PF.opening[1] }} m，两侧各留 5 mm 余量。</p><ul><li v-for="g in PF.gripper" :key="g.id">✓ {{ g.id.slice(2) }} <span class="wb-mono">{{ (g.w * 1000).toFixed(1) }} mm</span></li></ul></div>
      <div class="cat"><h4><b>P</b> 关键位姿 · {{ PF.poses.length }} 项</h4><p>多初值（默认 200 个）、带碰撞检查的 IK，含进出段；余量 {{ PF.clearance * 1000 }} mm，贴着支撑面的夹取位姿放宽到 1 mm。</p><ul><li v-for="p in PF.poses" :key="p.id">✓ {{ p.id }} <span class="wb-mono">{{ p.configs }} 组</span></li></ul></div>
      <div class="cat"><h4><b>D</b> 活动件扫掠 · {{ PF.movers.length }} 项</h4><p>门、抽屉、离心机盖从关到开整段扫过去，查它和静态环境、机器人的接触。</p><ul><li v-for="m in PF.movers" :key="m">✓ {{ m }}</li></ul></div>
      <div class="cat"><h4><b>T</b> 过渡 · {{ PF.transitions.length }} 项</h4><p>相邻位姿之间关节插值，逐点查碰撞；在两端所有可用构型的组合里找一条无接触的。</p><ul><li v-for="t in PF.transitions" :key="t.id">✓ {{ t.id }} <span class="wb-mono">试 {{ t.tried }}</span></li></ul></div>
    </div>

    <div v-else class="hist">
      <table>
        <thead><tr><th>版本</th><th>失败 / 总数</th><th>主要问题</th><th>改动</th></tr></thead>
        <tbody><tr v-for="h in HISTORY" :key="h.v"><td class="wb-mono">{{ h.v }}</td><td class="wb-mono" :class="h.v === 'v3' ? 'ok' : 'bad'">{{ h.f }}</td><td>{{ h.p }}</td><td>{{ h.c }}</td></tr></tbody>
      </table>
      <p class="note">每一版只要 40–63 s。这些问题如果留到仿真阶段，每一个都要跑一次约 2 min 的动力学才会暴露，而且更难定位。</p>
    </div>
  </div>
</template>

<style scoped>
.pv { margin: 22px 0; padding: 14px 16px 16px; container-type: inline-size; }
.top { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.src { font-size: 11px; color: var(--faint); }
.map { margin-top: 14px; display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(0, 1fr); gap: 16px; }
svg { width: 100%; height: auto; display: block; border: 1px solid var(--line); border-radius: 10px; background: var(--surface); }
.bx { fill: color-mix(in srgb, var(--m-body-2) 55%, transparent); stroke: var(--ink-2); stroke-width: 1; stroke-opacity: .55; }
.bx.rail { fill: color-mix(in srgb, var(--m-dark) 30%, transparent); }
.bx.workstation { fill: color-mix(in srgb, var(--m-glass) 22%, transparent); }
.sweeps path { fill: color-mix(in srgb, var(--accent) 10%, transparent); stroke: var(--accent); stroke-dasharray: 4 3; stroke-width: 1; }
.dn { font-size: 15px; fill: var(--muted); font-family: var(--font-ui); }
.reach { fill: color-mix(in srgb, var(--accent) 5%, transparent); stroke: var(--accent); stroke-opacity: .5; stroke-dasharray: 6 4; }
.carriage { fill: var(--ink-2); opacity: .8; }
.link { stroke: var(--accent); stroke-width: 1.5; stroke-dasharray: 3 3; }
.appr { stroke: var(--accent); stroke-width: 3; }
.pose { cursor: pointer; }
.pose circle { fill: var(--ok); stroke: var(--surface); stroke-width: 2; transition: r .2s var(--ease); }
.pose.via circle { fill: var(--ghost); }
.pose.on circle { fill: var(--accent); }
.info h4 { margin: 6px 0 8px; font-size: 16px; color: var(--ink); }
dl { margin: 0; }
dl div { display: grid; grid-template-columns: 76px 1fr; gap: 10px; padding: 6px 0; border-top: 1px solid var(--line); font-size: 13px; }
dt { color: var(--faint); }
dd { margin: 0; color: var(--ink-2); }
.note { margin: 10px 0; font-size: 12.5px; line-height: 1.7; color: var(--muted); }
.small button { font-size: 11.5px; padding: 4px 8px; }
.checks { margin-top: 14px; display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.cat { border: 1px solid var(--line); border-radius: 10px; padding: 12px 14px; max-height: 280px; overflow: auto; }
.cat h4 { margin: 0; font-size: 14px; color: var(--ink); }
.cat h4 b { font-family: var(--font-mono); color: var(--accent-ink); margin-right: 4px; }
.cat p { margin: 6px 0; font-size: 12.5px; line-height: 1.65; color: var(--muted); }
.cat ul { list-style: none; margin: 0; padding: 0; font-size: 12px; color: var(--ink-2); font-family: var(--font-mono); }
.cat li { line-height: 1.8; }
.cat li::first-letter { color: var(--ok); }
.cat li span { color: var(--faint); }
.hist { margin-top: 14px; overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); vertical-align: top; line-height: 1.65; color: var(--ink-2); }
th { font-weight: 500; color: var(--muted); font-size: 12px; white-space: nowrap; }
td.ok { color: var(--ok); white-space: nowrap; }
td.bad { color: var(--bad); white-space: nowrap; }
@container (max-width: 900px) { .map { grid-template-columns: 1fr; } }
@container (max-width: 560px) { .checks { grid-template-columns: 1fr; } }
</style>
