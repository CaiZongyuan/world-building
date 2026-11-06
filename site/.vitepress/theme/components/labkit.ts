// Shared pieces of the physics labs: the MuJoCo WASM engine (loaded once, lazily),
// the precomputed replays (one file per lab), and the 2D canvas drawing of a scene.
// The lab definitions in site/labs/labs.json are shared with labs/runner.py and play.py.
import LABS_JSON from '../../../labs/labs.json'

export interface LabParam { id: string; label: string; default: number; options: { label: string; sub: Record<string, number | string> }[] }
export interface LabMetric { id: string; label: string; kind: string; unit: string; gate?: { op: string; v: number }; series?: boolean }
export interface LabDef { id: string; title: string; view: any; duration: number; params: LabParam[]; metrics: LabMetric[]; special?: string; base?: string; split?: number; xml?: string; control?: any[] }

export const LABS: LabDef[] = (LABS_JSON as any).labs

const REPLAYS = import.meta.glob('../../../labs/fallback/*.json', { query: '?url', import: 'default' }) as Record<string, () => Promise<string>>
const replayCache: Record<string, Promise<any>> = {}

export function loadReplay(id: string): Promise<any> {
  if (!replayCache[id]) {
    const key = Object.keys(REPLAYS).find((k) => k.endsWith(`/${id}.json`))
    replayCache[id] = key ? REPLAYS[key]().then((url) => fetch(url)).then((r) => r.json()) : Promise.resolve(null)
  }
  return replayCache[id]
}

// ---- Engine ------------------------------------------------------------------

export type EngineState = 'idle' | 'loading' | 'live' | 'replay'
let engine: Promise<any> | null = null
let state: EngineState = 'idle'
const listeners = new Set<(s: EngineState) => void>()
const set = (s: EngineState) => { state = s; listeners.forEach((f) => f(s)) }
export const engineState = () => state
export function onEngine(f: (s: EngineState) => void) { listeners.add(f); return () => listeners.delete(f) }

const CDN = 'https://cdn.jsdelivr.net/npm/@mujoco/mujoco@3.17.0/'

export function loadEngine(): Promise<any> {
  if (engine) return engine
  set('loading')
  engine = (async () => {
    try {
      const mod = await import(/* @vite-ignore */ CDN + 'mujoco.js')
      const r = await fetch(CDN + 'mujoco.wasm')
      if (!r.ok) throw new Error('wasm ' + r.status)
      const MJ = await mod.default({ wasmBinary: await r.arrayBuffer() })
      MJ.MjModel.from_xml_string("<mujoco><worldbody><geom type='sphere' size='.1'/></worldbody></mujoco>").delete()
      set('live')
      return MJ
    } catch (e) {
      console.warn('MuJoCo WASM unavailable, using replays', e)
      set('replay')
      return null
    }
  })()
  return engine
}

// ---- Drawing -----------------------------------------------------------------

export const css = (n: string) => getComputedStyle(document.documentElement).getPropertyValue(n).trim()
export const fmt = (v: number | null | undefined, u = '') => (v === null || v === undefined || Number.isNaN(v)) ? '—'
  : (Math.abs(v) >= 100 ? v.toFixed(0) : Math.abs(v) >= 10 ? v.toFixed(1) : Math.abs(v) >= 1 ? v.toFixed(2) : v.toFixed(3)) + (u ? ' ' + u : '')

export function quatToMat(w: number, x: number, y: number, z: number) {
  return [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w),
    2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w),
    2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]
}
const CIRC = Array.from({ length: 24 }, (_, i) => [Math.cos(i * Math.PI / 12), Math.sin(i * Math.PI / 12)])
function localPts(type: number, s: number[]) {
  const P: number[][] = []
  if (type === 6) { for (const a of [-1, 1]) for (const b of [-1, 1]) for (const c of [-1, 1]) P.push([a * s[0], b * s[1], c * s[2]]) }
  else if (type === 5) { for (const [c, d] of CIRC) for (const z of [-s[1], s[1]]) P.push([c * s[0], d * s[0], z]) }
  else if (type === 3) { for (const [c, d] of CIRC) for (const z of [-s[1], s[1]]) { P.push([c * s[0], d * s[0], z]); P.push([c * s[0], 0, z + d * s[0]]); P.push([0, c * s[0], z + d * s[0]]) } }
  else if (type === 2 || type === 4) { for (const [c, d] of CIRC) { P.push([c * s[0], d * s[0], 0]); P.push([c * s[0], 0, d * s[0]]); P.push([0, c * s[0], d * s[0]]) } }
  return P
}
function hull(pts: number[][]) {
  pts = pts.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1])
  const cr = (o: number[], a: number[], b: number[]) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
  const lo: number[][] = [], up: number[][] = []
  for (const p of pts) { while (lo.length >= 2 && cr(lo[lo.length - 2], lo[lo.length - 1], p) <= 0) lo.pop(); lo.push(p) }
  for (const p of pts.slice().reverse()) { while (up.length >= 2 && cr(up[up.length - 2], up[up.length - 1], p) <= 0) up.pop(); up.push(p) }
  return lo.slice(0, -1).concat(up.slice(0, -1))
}
const ROLE = (n: string) => n.startsWith('obj_') ? '--obj' : n.startsWith('sup_') ? '--sup' : n.startsWith('pad_') ? '--pad' : n.startsWith('tool_') ? '--tool' : '--solid'

export function fitCanvas(cv: HTMLCanvasElement) {
  const r = cv.getBoundingClientRect(), dpr = Math.min(2, window.devicePixelRatio || 1)
  const w = Math.max(10, Math.round(r.width * dpr)), h = Math.max(10, Math.round(r.height * dpr))
  if (cv.width !== w || cv.height !== h) { cv.width = w; cv.height = h }
  return dpr
}

export interface Geom { name: string; type: number; size: number[]; body: number; visible?: boolean; pose?: number[] }

export function drawScene(cv: HTMLCanvasElement, geoms: Geom[], poses: number[][], view: any, contacts: { pos: number[]; pen: number }[], opts: { label?: string } = {}) {
  const dpr = fitCanvas(cv), ctx = cv.getContext('2d')!, W = cv.width, H = cv.height
  ctx.fillStyle = css('--surface'); ctx.fillRect(0, 0, W, H)
  const span = view.span, sc = W / span, [ca, cb] = view.center
  const xy = view.plane === 'xy'
  const P = (p: number[]) => [W / 2 + (p[0] - ca) * sc, H / 2 - ((xy ? p[1] : p[2]) - cb) * sc]
  const step = [0.0001, 0.0005, 0.001, 0.005, 0.01, 0.05, 0.1].find((s) => s * sc > 26 * dpr) || 0.1
  ctx.strokeStyle = css('--grid'); ctx.lineWidth = 1
  ctx.beginPath()
  for (let x = Math.floor((ca - span) / step) * step; x < ca + span; x += step) { const X = W / 2 + (x - ca) * sc; ctx.moveTo(X, 0); ctx.lineTo(X, H) }
  for (let y = Math.floor((cb - span) / step) * step; y < cb + span; y += step) { const Y = H / 2 - (y - cb) * sc; ctx.moveTo(0, Y); ctx.lineTo(W, Y) }
  ctx.stroke()
  const items: { g: Geom; poly: number[][]; depth: number }[] = []
  geoms.forEach((g, i) => {
    if (g.visible === false || g.type === 0) return
    const p = poses[i]; if (!p) return
    const R = p.slice(3, 12)
    const pts = localPts(g.type, g.size).map(([a, b, c]) => [p[0] + R[0] * a + R[1] * b + R[2] * c, p[1] + R[3] * a + R[4] * b + R[5] * c, p[2] + R[6] * a + R[7] * b + R[8] * c])
    if (!pts.length) return
    items.push({ g, poly: hull(pts.map(P)), depth: xy ? p[2] : -p[1] })
  })
  items.sort((a, b) => a.depth - b.depth)
  for (const it of items) {
    ctx.beginPath(); it.poly.forEach(([x, y], k) => (k ? ctx.lineTo(x, y) : ctx.moveTo(x, y))); ctx.closePath()
    ctx.globalAlpha = it.g.name.startsWith('obj_') ? 0.85 : 0.7; ctx.fillStyle = css(ROLE(it.g.name)); ctx.fill()
    ctx.globalAlpha = 1; ctx.strokeStyle = css('--ink'); ctx.lineWidth = Math.max(1, dpr * 0.8); ctx.stroke()
  }
  if (view.mark) {
    const [mx, my] = P(xy ? [view.mark[0], view.mark[1], 0] : [view.mark[0], 0, view.mark[1]])
    ctx.strokeStyle = css('--fail'); ctx.lineWidth = 1.5 * dpr; ctx.beginPath(); ctx.moveTo(mx - 9 * dpr, my); ctx.lineTo(mx + 9 * dpr, my); ctx.moveTo(mx, my - 9 * dpr); ctx.lineTo(mx, my + 9 * dpr); ctx.stroke()
    for (const it of items) if (it.g.name.startsWith('obj_')) {
      const cx = it.poly.reduce((s, q) => s + q[0], 0) / it.poly.length, cy = it.poly.reduce((s, q) => s + q[1], 0) / it.poly.length
      ctx.beginPath(); ctx.arc(cx, cy, 3 * dpr, 0, Math.PI * 2); ctx.fillStyle = css('--ink'); ctx.fill()
    }
  }
  for (const c of contacts || []) {
    const [x, y] = P(c.pos); const pen = Math.max(0, c.pen)
    ctx.beginPath(); ctx.arc(x, y, (2.2 + Math.min(6, pen * 6)) * dpr, 0, Math.PI * 2)
    ctx.fillStyle = css('--contact'); ctx.globalAlpha = 0.9; ctx.fill(); ctx.globalAlpha = 1
  }
  const bar = [0.1, 0.05, 0.01, 0.005, 0.001, 0.0005, 0.0001].find((s) => s * sc <= 0.3 * W) || 0.0001
  ctx.strokeStyle = css('--ink'); ctx.lineWidth = 2 * dpr; ctx.beginPath(); ctx.moveTo(12 * dpr, H - 14 * dpr); ctx.lineTo(12 * dpr + bar * sc, H - 14 * dpr); ctx.stroke()
  ctx.fillStyle = css('--ink-2'); ctx.font = `${11 * dpr}px ${css('--font-mono')}`
  ctx.fillText(bar >= 0.01 ? `${bar * 100} cm` : bar >= 0.001 ? `${bar * 1000} mm` : `${(bar * 1000).toFixed(1)} mm`, 12 * dpr, H - 20 * dpr)
  if (opts.label) { ctx.fillStyle = css('--muted'); ctx.fillText(opts.label, W - ctx.measureText(opts.label).width - 10 * dpr, H - 10 * dpr) }
}

export function drawPlot(cv: HTMLCanvasElement, series: (number | null)[], dur: number, gate: { op: string; v: number } | undefined, unit: string, tNow: number | null, fps: number) {
  const dpr = fitCanvas(cv), ctx = cv.getContext('2d')!, W = cv.width, H = cv.height
  ctx.fillStyle = css('--surface'); ctx.fillRect(0, 0, W, H)
  const L = 46 * dpr, R = 10 * dpr, T = 12 * dpr, B = 24 * dpr
  const vals = series.filter((v): v is number => v !== null && Number.isFinite(v))
  let ymax = Math.max(gate ? gate.v * 1.6 : 0, ...vals.map(Math.abs), 1e-6)
  if (gate && vals.length && Math.max(...vals) > gate.v * 20) ymax = gate.v * 20
  const X = (t: number) => L + (t / dur) * (W - L - R), Y = (v: number) => H - B - (Math.min(v, ymax) / ymax) * (H - T - B)
  ctx.strokeStyle = css('--line'); ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(L, T); ctx.lineTo(L, H - B); ctx.lineTo(W - R, H - B); ctx.stroke()
  ctx.fillStyle = css('--muted'); ctx.font = `${10.5 * dpr}px ${css('--font-mono')}`
  for (const f of [0, 0.5, 1]) { const v = ymax * f; ctx.fillText(fmt(v), 4 * dpr, Y(v) + 4 * dpr) }
  for (const f of [0, 0.5, 1]) { const t = dur * f; ctx.fillText(t.toFixed(1) + ' s', X(t) - (f === 1 ? 30 * dpr : f ? 12 * dpr : 0), H - 6 * dpr) }
  if (gate) {
    ctx.setLineDash([5 * dpr, 4 * dpr]); ctx.strokeStyle = css('--fail'); ctx.beginPath(); ctx.moveTo(L, Y(gate.v)); ctx.lineTo(W - R, Y(gate.v)); ctx.stroke(); ctx.setLineDash([])
    ctx.fillStyle = css('--fail'); ctx.fillText(`门限 ${gate.op === '<=' ? '≤' : '≥'} ${gate.v} ${unit}`, L + 6 * dpr, Y(gate.v) - 5 * dpr)
  }
  ctx.strokeStyle = css('--accent'); ctx.lineWidth = 2 * dpr; ctx.beginPath(); let started = false
  series.forEach((v, i) => { if (v === null || !Number.isFinite(v)) { started = false; return } const x = X(i / fps), y = Y(v); if (!started) { ctx.moveTo(x, y); started = true } else ctx.lineTo(x, y) })
  ctx.stroke()
  if (tNow !== null) { ctx.strokeStyle = css('--ink-2'); ctx.lineWidth = 1; ctx.beginPath(); ctx.moveTo(X(tNow), T); ctx.lineTo(X(tNow), H - B); ctx.stroke() }
}
