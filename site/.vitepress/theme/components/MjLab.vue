<script setup lang="ts">
// One physics lab: pick parameters, run MuJoCo in the browser, watch the gate.
// Falls back to a replay computed by labs/runner.py when WASM cannot load.
import { computed, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
// @ts-ignore plain ES module shared with the Node checks
import { instantiate, Run } from '../../../labs/engine.js'
import { LABS, drawPlot, drawScene, engineState, fmt, loadEngine, loadReplay, onEngine, quatToMat, type EngineState, type Geom } from './labkit'

const props = defineProps<{ id: string }>()
const lab = LABS.find((l) => l.id === props.id)!

const TRY: Record<string, string[]> = {
  drop: ['先保持默认（0.3 mm、0.004 s），按运行：穿透约 0.11 mm，PASS。', '把刚度换成 0.02 s（默认）：同样的松手高度，穿透 0.59 mm，FAIL。', '松手高度拉到 50 mm：任何刚度都过不了。这就是「不往下丢东西」。', '下方放大图里红点是接触点，看板角陷进台面的深度。'],
  grip: ['默认是 8 N、μ 1.0、软接触：提起来以后块一直往下溜，下滑约 8 mm，两项都 FAIL。', '换成加硬指垫：穿透降到 0.02 mm，但还会溜 1.3 mm（摩擦蠕变）。', '再加 noslip：下滑 0，两项都 PASS。', '把力降到 0.5 N：怎么设都夹不住；升到 60 N 配软指垫：穿透 3.8 mm。'],
  vjaw: ['默认是 V 形夹块、μ 0.2、严格摩擦：管心被推到轴线上，偏差接近 0，PASS。', '换成平夹块：x 方向推正了，y 方向的 1.6 mm 原样保留，FAIL。', 'V 形夹块配 μ 1.5：斜面自锁，推不动，FAIL。', '再把摩擦模型切到默认：μ 1.5 也「推正」了。这是软摩擦蠕变，不是真实物理。'],
  servo: ['默认（前馈关、重力补偿关）：跟踪误差约 4.5°，FAIL。', '只开前馈或只开重力补偿：都还剩 2° 多。', '两个都开：0.16°，PASS。', '把 biastype 切到 none：手臂直接甩到限位，误差约 90°。'],
  weld: ['默认是「手 → 盖 → 管」、快速转身、加硬 weld：管相对手倾斜 5.4°，FAIL。', '换成「手 → 管」：0.6°，PASS。', 'weld 刚度换回默认 0.02 s：两种挂法都偏到 7° 以上，说明默认 weld 本身就太软。'],
  place: ['先跑名义流程：S3、S7、S8 三项全 PASS。', '换成「离支撑面 20 mm 就松手」：S7 = 0（松爪前根本没托住），撞击穿透 0.88 mm，S3 也 FAIL。', '换成负例 N1：托面没有碰撞，板穿过去掉到地面，三项全 FAIL。这就是负例要证明的：门限确实能分辨对错。'],
}

const choice = ref<Record<string, number>>(Object.fromEntries(lab.params.map((p) => [p.id, p.default])))
const speed = ref(0.25)
const playing = ref(false)
const done = ref(false)
const t = ref(0)
const mode = ref<EngineState>(engineState())
const result = shallowRef<Record<string, { v: number; ok: boolean | null }> | null>(null)
const showXml = ref(false)
const copied = ref(false)

const root = ref<HTMLElement>()
const cv = ref<HTMLCanvasElement>()
const zv = ref<HTMLCanvasElement>()
const pv = ref<HTMLCanvasElement>()

let MJ: any = null
let run: any = null
let replay: any = null
let fb: any = null
let geoms: Geom[] = []
let poses: number[][] = []
let contacts: { pos: number[]; pen: number }[] = []
let idx = 0
let nextSample = 0
let last = 0
let raf = 0
let ro: ResizeObserver | null = null
let io: IntersectionObserver | null = null
let off: (() => void) | null = null

const inst = computed(() => instantiate(lab, choice.value))
const key = computed(() => lab.params.map((p) => choice.value[p.id]).join('|'))
const xml = computed(() => (inst.value.xml as string).replace(/></g, '>\n<'))
const cmd = computed(() => `uv run --extra sim python site/labs/play.py ${lab.id} ` + lab.params.map((p) => `${p.id}=${choice.value[p.id]}`).join(' '))
const modeText = computed(() => ({ idle: '引擎未加载', loading: '正在加载 MuJoCo 3.17…', live: '实时 MuJoCo（浏览器内）', replay: '预计算回放（本地 MuJoCo 3.17）' })[mode.value])
const zoomNote = computed(() => !lab.view.zoom ? '' : lab.view.zoom.mark ? `放大 ×${Math.round(lab.view.span / lab.view.zoom.span)}：红十字是旋盖头轴线，黑点是管心` : `接触处放大 ×${Math.round(lab.view.span / lab.view.zoom.span)}：红点是接触点，看陷进去多深`)

function setFrame(i: number) {
  const f = fb.frames[Math.min(i, fb.frames.length - 1)]
  const moving = geoms.map((g, k) => (g.body !== 0 ? k : -1)).filter((k) => k >= 0)
  poses = geoms.map((g) => { const p = g.pose!; return [p[0], p[1], p[2], ...quatToMat(p[3], p[4], p[5], p[6])] })
  moving.forEach((gi, j) => { const p = f.g[j]; if (p) poses[gi] = [p[0], p[1], p[2], ...quatToMat(p[3], p[4], p[5], p[6])] })
  contacts = f.c.map((c: number[]) => ({ pos: [c[0], c[1], c[2]], pen: c[3] }))
  t.value = f.t
}

function reset() {
  playing.value = false
  done.value = false
  result.value = null
  if (run) { run.dispose(); run = null }
  t.value = 0
  if (MJ) {
    run = new Run(MJ, inst.value)
    geoms = run.geoms(); poses = run.poses(); contacts = []; nextSample = 0
  } else if (replay) {
    fb = replay[key.value]
    if (fb) { geoms = fb.geoms; idx = 0; setFrame(0) }
  }
  draw()
}

function pick(pid: string, i: number) {
  choice.value = { ...choice.value, [pid]: i }
  reset()
}

function toggle() {
  if (done.value) reset()
  if (!MJ && !fb) return
  playing.value = !playing.value
  if (playing.value) { last = performance.now(); raf = requestAnimationFrame(tick) }
}

function finish() {
  playing.value = false
  done.value = true
  result.value = MJ ? run.result() : fb.result
}

function tick(ts: number) {
  if (!playing.value) return
  const dtw = Math.min(0.05, (ts - last) / 1000); last = ts
  const target = t.value + dtw * speed.value
  if (MJ) {
    let guard = 0
    while (run.d.time < target && guard++ < 6000) {
      if (!run.step()) { finish(); break }
      if (run.d.time >= nextSample - 1e-9) { run.sample(); nextSample += 1 / 60 }
    }
    t.value = run.d.time; poses = run.poses()
    contacts = run.contacts.filter((c: any) => c.dist < 0).map((c: any) => ({ pos: c.pos, pen: -c.dist * 1000 }))
    if (run.k >= run.n) finish()
  } else if (fb) {
    idx = Math.round(target * 60)
    if (idx >= fb.frames.length - 1) { idx = fb.frames.length - 1; setFrame(idx); finish() } else setFrame(idx)
  }
  draw()
  if (playing.value) raf = requestAnimationFrame(tick)
}

function draw() {
  if (!cv.value || !geoms.length) return
  drawScene(cv.value, geoms, poses, lab.view, contacts, { label: lab.view.plane === 'xy' ? '俯视' : '侧视' })
  if (zv.value && lab.view.zoom) drawScene(zv.value, geoms, poses, { plane: lab.view.plane, center: lab.view.zoom.center, span: lab.view.zoom.span, mark: lab.view.zoom.mark }, contacts)
  const mt = lab.metrics.find((m) => m.series) || lab.metrics[0]
  const started = playing.value || done.value || t.value > 0
  let s: (number | null)[] = []
  if (MJ && run && started) s = run.series[mt.id]
  else if (fb && started) s = fb.series[mt.id].slice(0, idx + 1)
  if (pv.value) drawPlot(pv.value, s, lab.duration, mt.gate, mt.unit, t.value, 60)
}

async function engineReady(s: EngineState) {
  mode.value = s
  if (s === 'live') MJ = await loadEngine()
  else if (s === 'replay') replay = await loadReplay(lab.id)
  if (s === 'live' || s === 'replay') reset()
}

async function copyXml() {
  try { await navigator.clipboard.writeText(inst.value.xml); copied.value = true; setTimeout(() => (copied.value = false), 1600) } catch { /* ignore */ }
}

onMounted(() => {
  off = onEngine(engineReady)
  if (engineState() === 'live' || engineState() === 'replay') engineReady(engineState())
  io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { loadEngine(); io?.disconnect() } }, { rootMargin: '400px 0px' })
  io.observe(root.value!)
  ro = new ResizeObserver(() => draw())
  ro.observe(cv.value!)
})

onBeforeUnmount(() => {
  playing.value = false
  cancelAnimationFrame(raf)
  off?.(); io?.disconnect(); ro?.disconnect()
  try { run?.dispose() } catch { /* ignore */ }
})
</script>

<template>
  <div ref="root" class="lab vp-raw">
    <div class="lh"><b>{{ lab.title }}</b><span class="mode" :class="mode">{{ modeText }}</span></div>
    <div class="ctl">
      <div v-for="p in lab.params" :key="p.id" class="p">
        <span>{{ p.label }}</span>
        <div class="wb-seg" role="group" :aria-label="p.label">
          <button v-for="(o, i) in p.options" :key="i" type="button" :aria-pressed="choice[p.id] === i" @click="pick(p.id, i)">{{ o.label }}</button>
        </div>
      </div>
    </div>
    <div class="body">
      <div class="view">
        <canvas ref="cv" class="main" :aria-label="lab.title + ' 的仿真画面'" />
        <div class="tbar">
          <button type="button" class="wb-btn wb-btn--primary" :disabled="mode === 'loading' || mode === 'idle'" @click="toggle">{{ playing ? '❚❚ 暂停' : done ? '▶ 再跑一次' : t > 0 ? '▶ 继续' : '▶ 运行' }}</button>
          <button type="button" class="wb-btn" @click="reset">↺ 回到起点</button>
          <div class="wb-seg" role="group" aria-label="播放速度">
            <button v-for="sp in [0.1, 0.25, 1]" :key="sp" type="button" :aria-pressed="speed === sp" @click="speed = sp">{{ sp }}×</button>
          </div>
          <span class="t">t = {{ t.toFixed(3) }} s</span>
        </div>
        <div class="legend"><span><i style="background:var(--obj)" />工件</span><span><i style="background:var(--pad)" />夹持面</span><span><i style="background:var(--tool)" />机构</span><span><i style="background:var(--sup)" />支撑面</span><span><i style="background:var(--solid)" />固定物</span><span><i class="dot" />接触点（越大越深）</span></div>
        <div v-if="lab.view.zoom" class="zoomwrap"><span>{{ zoomNote }}</span><canvas ref="zv" class="zoomc" /></div>
      </div>
      <div class="side">
        <canvas ref="pv" class="plot" aria-label="门限曲线" />
        <div class="res">
          <p v-if="!result" class="wait">{{ mode === 'loading' ? '引擎加载中…' : '按「运行」开始测量，跑完给出判定。' }}</p>
          <div v-for="mt in (result ? lab.metrics : [])" :key="mt.id" class="r">
            <span>{{ mt.label }}<small v-if="mt.gate">门限 {{ mt.gate.op === '<=' ? '≤' : '≥' }} {{ mt.gate.v }} {{ mt.unit }}</small></span>
            <span class="v">{{ fmt(result![mt.id].v, mt.unit) }}</span>
            <span class="wb-tag" :class="result![mt.id].ok ? 'PASS' : 'FAIL'">{{ result![mt.id].ok ? 'PASS' : 'FAIL' }}</span>
          </div>
        </div>
        <div class="try"><b>试试这样做</b><ul><li v-for="s in TRY[lab.id] || []" :key="s">{{ s }}</li></ul></div>
      </div>
    </div>
    <div class="xmlbar">
      <button type="button" class="link" @click="showXml = !showXml">{{ showXml ? '收起' : '看这个实验的 MJCF，或在本机 MuJoCo 里打开' }}</button>
    </div>
    <div v-if="showXml" class="xml">
      <p>本机运行（仓库根目录）：<code>{{ cmd }}</code> <button type="button" class="wb-btn" @click="copyXml">{{ copied ? '已复制' : '复制 XML' }}</button></p>
      <pre>{{ xml }}</pre>
    </div>
  </div>
</template>

<style scoped>
.lab { margin: 24px 0; border: 1px solid var(--line); border-radius: 14px; background: color-mix(in srgb, var(--surface) 94%, transparent); box-shadow: var(--shadow-1); overflow: hidden; }
.lh { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 13px 16px; border-bottom: 1px solid var(--line); background: var(--surface-2); flex-wrap: wrap; }
.lh b { font-family: var(--font-display); font-weight: 600; font-size: 16px; color: var(--ink); }
.mode { font-size: 12px; color: var(--muted); font-family: var(--font-mono); }
.mode.live { color: var(--ok); }
.mode.replay { color: var(--warn); }
.ctl { display: flex; flex-wrap: wrap; gap: 12px 22px; padding: 12px 16px; border-bottom: 1px solid var(--line); }
.p { display: flex; flex-direction: column; gap: 6px; }
.p > span { font-size: 12px; color: var(--muted); }
.body { display: grid; grid-template-columns: minmax(0, 1.55fr) minmax(0, 1fr); }
.view { border-right: 1px solid var(--line); }
.main { width: 100%; aspect-ratio: 16 / 10; display: block; }
.tbar { display: flex; align-items: center; gap: 8px; padding: 10px 14px; flex-wrap: wrap; border-top: 1px solid var(--line); }
.t { margin-left: auto; font-family: var(--font-mono); font-size: 12px; color: var(--muted); }
.legend { display: flex; flex-wrap: wrap; gap: 4px 12px; padding: 0 14px 10px; font-size: 11.5px; color: var(--muted); }
.legend span { display: inline-flex; align-items: center; gap: 5px; }
.legend i { width: 10px; height: 10px; border-radius: 2px; display: inline-block; }
.legend i.dot { background: var(--contact); border-radius: 50%; }
.zoomwrap { padding: 0 14px 14px; }
.zoomwrap span { display: block; font-size: 11.5px; color: var(--muted); margin-bottom: 6px; }
.zoomc { width: 100%; aspect-ratio: 16 / 7; display: block; border: 1px solid var(--line); border-radius: 8px; }
.side { padding: 14px; display: flex; flex-direction: column; gap: 12px; min-width: 0; }
.plot { width: 100%; aspect-ratio: 16 / 9; display: block; border: 1px solid var(--line); border-radius: 8px; }
.res { display: flex; flex-direction: column; gap: 6px; }
.wait { font-size: 13px; color: var(--muted); margin: 0; }
.r { display: grid; grid-template-columns: 1fr auto auto; gap: 10px; align-items: center; padding: 8px 10px; border: 1px solid var(--line); border-radius: 8px; font-size: 13px; color: var(--ink-2); }
.r small { display: block; font-size: 11px; color: var(--muted); }
.v { font-family: var(--font-mono); font-size: 13px; color: var(--ink); }
.try { font-size: 13px; color: var(--ink-2); }
.try b { font-size: 13px; color: var(--ink); }
.try ul { margin: 6px 0 0; padding-left: 18px; }
.try li { line-height: 1.65; margin: 3px 0; }
.xmlbar { border-top: 1px solid var(--line); padding: 8px 16px; }
.link { font-size: 12.5px; color: var(--accent-ink); cursor: pointer; background: none; border: 0; padding: 0; }
.xml { padding: 0 16px 14px; }
.xml p { font-size: 12.5px; color: var(--muted); display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 0 0 8px; }
.xml code { font-family: var(--font-mono); font-size: 11.5px; padding: 2px 6px; border-radius: 5px; background: var(--surface-2); border: 1px solid var(--line); overflow-wrap: anywhere; }
.xml pre { margin: 0; max-height: 280px; overflow: auto; font-family: var(--font-mono); font-size: 11.5px; line-height: 1.6; padding: 12px; border-radius: 8px; background: var(--term-bg); color: var(--term-ink); }
@media (max-width: 800px) {
  .body { grid-template-columns: 1fr; }
  .view { border-right: 0; border-bottom: 1px solid var(--line); }
}
</style>
