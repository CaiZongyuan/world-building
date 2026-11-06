<script setup lang="ts">
// Lab 7: save the state mid-run, resume in a fresh MjData, compare with one straight run.
import { onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
// @ts-ignore plain ES module
import { ctrlValue, instantiate } from '../../../labs/engine.js'
import { LABS, css, fitCanvas, loadEngine, loadReplay, onEngine, engineState } from './labkit'

const lab = LABS.find((l) => l.id === 'chain')!
const MODES: [string, string][] = [['full', '完整积分状态 mjSTATE_INTEGRATION'], ['qpos_qvel', '只存 qpos + qvel'], ['qpos_only', '只存 qpos（漏了速度）'], ['ctrl_zero', '完整状态，但手指指令回零']]
const sel = ref('ctrl_zero')
const data = shallowRef<any>(null)
const src = ref('加载中…')
const live = ref(engineState() === 'live')
const busy = ref(false)
const cv = ref<HTMLCanvasElement>()
let ro: ResizeObserver | null = null
let off: (() => void) | null = null

function chainLive(MJ: any) {
  const base = LABS.find((l) => l.id === lab.base)!
  const inst = instantiate(base, Object.fromEntries(base.params.map((p) => [p.id, p.default])))
  const m = MJ.MjModel.from_xml_string(inst.xml), chans = inst.control.map((c: any) => [m.actuator(c.act).id, c])
  const plate = m.body('plate').id, dt = m.opt.timestep, n = Math.round(inst.duration / dt), ks = Math.round(lab.split! / dt), every = Math.round(1 / (60 * dt))
  const fresh = () => { const d = new MJ.MjData(m); for (const [j, v] of Object.entries(inst.init_qpos || {})) d.qpos[m.jnt_qposadr[m.jnt(j).id]] = v; MJ.mj_forward(m, d); return d }
  const step = (d: any, skip: string[]) => { for (const [a, c] of chans) if (!skip.includes(c.act)) d.ctrl[a] = ctrlValue(c, d.time); MJ.mj_step(m, d) }
  const ref0 = fresh(), traj: number[][] = []
  for (let k = 0; k < n; k++) { step(ref0, []); traj.push([ref0.xpos[3 * plate], ref0.xpos[3 * plate + 1], ref0.xpos[3 * plate + 2]]) }
  const out: any = { ref_z: traj.filter((_, k) => k % every === 0).map((p) => p[2] * 1000), split: lab.split, fps: 60 }
  const SPEC = MJ.mjtState.mjSTATE_INTEGRATION.value, nst = MJ.mj_stateSize(m, SPEC)
  for (const [mode] of MODES) {
    const d = fresh(); for (let k = 0; k < ks; k++) step(d, [])
    const d2 = new MJ.MjData(m)
    if (mode === 'full' || mode === 'ctrl_zero') { const b = new MJ.DoubleBuffer(nst); MJ.mj_getState(m, d, b, SPEC); MJ.mj_setState(m, d2, Array.from(b.GetView()), SPEC); b.delete(); if (mode === 'ctrl_zero') d2.ctrl.fill(0) }
    else { d2.qpos.set(d.qpos); if (mode === 'qpos_qvel') d2.qvel.set(d.qvel); d2.time = d.time }
    MJ.mj_forward(m, d2)
    const skip = mode === 'ctrl_zero' ? ['a_l', 'a_r'] : []; let dev = 0; const zs: number[] = []
    for (let k = ks; k < n; k++) { step(d2, skip); const p = [d2.xpos[3 * plate], d2.xpos[3 * plate + 1], d2.xpos[3 * plate + 2]]; dev = Math.max(dev, Math.hypot(p[0] - traj[k][0], p[1] - traj[k][1], p[2] - traj[k][2])); if (k % every === 0) zs.push(p[2] * 1000) }
    out[mode] = { max_dev_m: dev, z: zs }
    d.delete(); d2.delete()
  }
  ref0.delete(); m.delete()
  return out
}

async function recompute() {
  const MJ = await loadEngine()
  if (!MJ) return
  busy.value = true
  setTimeout(() => { data.value = chainLive(MJ); src.value = '浏览器内 MuJoCo 刚刚算出'; busy.value = false; draw() }, 30)
}

const lg = (v: number) => (v <= 0 ? 0 : Math.max(0, (Math.log10(v) + 15) / 14))
const devText = (v: number) => (v === 0 ? '0（逐位相同）' : v < 1e-6 ? v.toExponential(1) + ' m' : (v * 1000).toFixed(2) + ' mm')

function draw() {
  const D = data.value, c = cv.value
  if (!D || !c) return
  const dpr = fitCanvas(c), ctx = c.getContext('2d')!, W = c.width, H = c.height
  ctx.fillStyle = css('--surface'); ctx.fillRect(0, 0, W, H)
  const ref0: number[] = D.ref_z, s: number[] = D[sel.value].z, n = ref0.length, L = 44 * dpr, R = 10 * dpr, T = 12 * dpr, B = 24 * dpr
  const all = ref0.concat(s), lo = Math.min(...all) - 2, hi = Math.max(...all) + 2
  const X = (i: number) => L + (i / (n - 1)) * (W - L - R), Y = (z: number) => H - B - ((z - lo) / (hi - lo)) * (H - T - B)
  ctx.strokeStyle = css('--line'); ctx.beginPath(); ctx.moveTo(L, T); ctx.lineTo(L, H - B); ctx.lineTo(W - R, H - B); ctx.stroke()
  ctx.fillStyle = css('--muted'); ctx.font = `${10.5 * dpr}px ${css('--font-mono')}`
  ctx.fillText(`${hi.toFixed(0)} mm`, 2 * dpr, T + 8 * dpr); ctx.fillText(`${lo.toFixed(0)} mm`, 2 * dpr, H - B)
  ctx.fillText('板中心高度', L + 6 * dpr, T + 10 * dpr); ctx.fillText(`${(n / 60).toFixed(1)} s`, W - 34 * dpr, H - 6 * dpr)
  ctx.strokeStyle = css('--ink-2'); ctx.lineWidth = 2 * dpr; ctx.beginPath(); ref0.forEach((z, i) => (i ? ctx.lineTo(X(i), Y(z)) : ctx.moveTo(X(i), Y(z)))); ctx.stroke()
  const i0 = n - s.length; ctx.strokeStyle = css('--accent'); ctx.setLineDash([6 * dpr, 4 * dpr]); ctx.beginPath(); s.forEach((z, j) => (j ? ctx.lineTo(X(i0 + j), Y(z)) : ctx.moveTo(X(i0 + j), Y(z)))); ctx.stroke(); ctx.setLineDash([])
  ctx.strokeStyle = css('--fail'); ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(X(i0), T); ctx.lineTo(X(i0), H - B); ctx.stroke()
}

function pick(k: string) { sel.value = k; draw() }

onMounted(async () => {
  off = onEngine((s) => { live.value = s === 'live' })
  loadEngine()
  data.value = await loadReplay('chain')
  src.value = '预计算（本地 MuJoCo 3.17）'
  ro = new ResizeObserver(draw)
  ro.observe(cv.value!)
  draw()
})
onBeforeUnmount(() => { off?.(); ro?.disconnect() })
</script>

<template>
  <div class="lab vp-raw">
    <div class="lh"><b>{{ lab.title }}</b><span class="mode">{{ src }}</span></div>
    <div class="ctl">
      <div class="p"><span>在 t = {{ lab.split }} s 存档的方式</span>
        <div class="wb-seg" role="group" aria-label="存档方式"><button v-for="[k, l] in MODES" :key="k" type="button" :aria-pressed="k === sel" @click="pick(k)">{{ l }}</button></div>
      </div>
      <div class="p"><span>&nbsp;</span><button type="button" class="wb-btn wb-btn--primary" :disabled="!live || busy" @click="recompute">{{ busy ? '计算中…' : '▶ 在浏览器里重算' }}</button></div>
    </div>
    <div class="body">
      <div class="view">
        <canvas ref="cv" class="plot" aria-label="板高度随时间" />
        <div class="legend"><span><i style="background:var(--ink-2)" />一次跑完（参照）</span><span><i style="background:var(--accent)" />存档后接着跑</span><span><i style="background:var(--fail)" />存档时刻</span></div>
      </div>
      <div class="side">
        <b class="h">接上以后，板的轨迹与一次跑完的最大偏差</b>
        <div v-if="data" class="bars">
          <div v-for="[k, l] in MODES" :key="k" class="r" :class="{ on: k === sel }"><span>{{ l }}</span><span class="bar"><i :style="{ width: lg(data[k].max_dev_m) * 100 + '%' }" /></span><span class="v">{{ devText(data[k].max_dev_m) }}</span></div>
          <small>条形按对数刻度：从 1e-15 m 到 10 cm。</small>
        </div>
        <div class="try"><b>怎么读</b><ul><li>完整状态：偏差恰好为 0，逐位相同。</li><li>只存 qpos + qvel：约 1e-13 m，这个场景里热启动的影响可以忽略，但它不是 0。</li><li>漏了速度：搬运中的板「停了一下」，偏差约 0.18 mm。</li><li>指令回零：手指松开，板提前掉落 27.6 mm。终点一样，过程完全不同，S3、S7 会抓到。</li></ul></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.lab { margin: 24px 0; border: 1px solid var(--line); border-radius: 14px; background: color-mix(in srgb, var(--surface) 94%, transparent); box-shadow: var(--shadow-1); overflow: hidden; }
.lh { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 13px 16px; border-bottom: 1px solid var(--line); background: var(--surface-2); flex-wrap: wrap; }
.lh b { font-family: var(--font-display); font-weight: 600; font-size: 16px; color: var(--ink); }
.mode { font-size: 12px; color: var(--muted); font-family: var(--font-mono); }
.ctl { display: flex; flex-wrap: wrap; gap: 12px 22px; padding: 12px 16px; border-bottom: 1px solid var(--line); }
.p { display: flex; flex-direction: column; gap: 6px; }
.p > span { font-size: 12px; color: var(--muted); }
.body { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr); }
.view { padding: 12px 14px; border-right: 1px solid var(--line); }
.plot { width: 100%; aspect-ratio: 16 / 9; display: block; }
.legend { display: flex; flex-wrap: wrap; gap: 4px 12px; margin-top: 8px; font-size: 11.5px; color: var(--muted); }
.legend span { display: inline-flex; align-items: center; gap: 5px; }
.legend i { width: 12px; height: 3px; display: inline-block; }
.side { padding: 14px; display: flex; flex-direction: column; gap: 10px; }
.h { font-size: 14px; color: var(--ink); }
.bars { display: flex; flex-direction: column; gap: 6px; }
.r { display: grid; grid-template-columns: 1fr; gap: 3px; padding: 7px 10px; border: 1px solid var(--line); border-radius: 8px; font-size: 12.5px; color: var(--ink-2); }
.r.on { border-color: var(--accent); }
.bar { height: 6px; border-radius: 3px; background: var(--grid); overflow: hidden; }
.bar i { display: block; height: 100%; background: var(--accent); }
.v { font-family: var(--font-mono); font-size: 12px; color: var(--ink); }
small { font-size: 11.5px; color: var(--muted); }
.try { font-size: 13px; color: var(--ink-2); }
.try ul { margin: 6px 0 0; padding-left: 18px; }
.try li { line-height: 1.65; margin: 3px 0; }
@media (max-width: 800px) { .body { grid-template-columns: 1fr; } .view { border-right: 0; } }
</style>
