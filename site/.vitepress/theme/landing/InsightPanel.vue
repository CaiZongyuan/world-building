<script setup lang="ts">
// One instrument per chapter: what the agent is looking at right now.
import { computed } from 'vue'
import { withBase } from 'vitepress'
import { DIMS, GATES_SHOWN, KEYFRAMES, MCHECKS, NEGATIVES, REFS, RETRO, SCOPE, chapterAt, clamp, penAt, preflightAt, ramp } from './story'

const props = defineProps<{ t: number }>()
const ch = computed(() => chapterAt(props.t).id)
const pf = computed(() => preflightAt(props.t))
const frozen = computed(() => props.t >= 25.4)

// S3 penetration trace over the simulation chapter.
const TRACE_T0 = 43.6
const TRACE_T1 = 55.6
const trace = computed(() => {
  const t = props.t
  if (t < TRACE_T0) return ''
  const pts: string[] = []
  for (let s = TRACE_T0; s <= Math.min(t, TRACE_T1); s += 0.08) {
    const x = ((s - TRACE_T0) / (TRACE_T1 - TRACE_T0)) * 280
    const y = 70 - Math.min(penAt(s), 2.4) / 2.4 * 64
    pts.push(`${x.toFixed(1)},${y.toFixed(1)}`)
  }
  return pts.join(' ')
})
const pen = computed(() => penAt(props.t))
const gateY = 70 - 0.25 / 2.4 * 64
const negLit = computed(() => Math.floor(clamp((props.t - 52.6) / 1.6) * 10))
const mDone = computed(() => Math.floor(clamp((props.t - 38.9) / 1.8) * MCHECKS.length))
const frame = computed(() => KEYFRAMES[Math.min(KEYFRAMES.length - 1, Math.floor(clamp((props.t - 58.4) / 5.2) * KEYFRAMES.length))])
const vDone = computed(() => Math.floor(clamp((props.t - 60.6) / 1.8) * 4))
const retroOn = computed(() => ramp(props.t, 64.4, 66.0))
</script>

<template>
  <div class="ip pl-panel">
    <template v-if="ch === 'req'">
      <div class="pl-panel-head"><span>三张清单</span><span>待你确认</span></div>
      <div class="pl-panel-body">
        <p class="k">场景 · {{ SCOPE.scene.length }} 项</p>
        <div class="chips"><span v-for="(s, i) in SCOPE.scene" :key="s" :style="{ opacity: ramp(t, 5.8 + i * 0.12, 6.2 + i * 0.12) }">{{ s }}</span></div>
        <p class="k">流程 · 14 步</p>
        <div class="chips"><span v-for="(s, i) in SCOPE.flow" :key="s" :style="{ opacity: ramp(t, 6.4 + i * 0.08, 6.8 + i * 0.08) }">{{ s }}</span><span class="more">…</span></div>
        <p class="k">资产 · 16 项，逐项实查</p>
        <dl class="assets"><div v-for="([a, b], i) in SCOPE.assets" :key="a" :style="{ opacity: ramp(t, 7.0 + i * 0.15, 7.4 + i * 0.15) }"><dt>{{ a }}</dt><dd>{{ b }}</dd></div></dl>
      </div>
    </template>

    <template v-else-if="ch === 'proposal'">
      <div class="pl-panel-head"><span>运动学预演</span><span>{{ pf.show ? pf.v : '准备中' }}</span></div>
      <div class="pl-panel-body">
        <div class="big">
          <b :class="pf.failed ? 'bad' : 'ok'">{{ pf.show ? pf.failed : '—' }}</b><span>/ {{ pf.total }} 项失败</span>
        </div>
        <div class="bar"><i :style="{ width: (pf.show ? (1 - pf.failed / pf.total) * 100 : 0) + '%' }" /></div>
        <ul class="cats">
          <li><b>G</b>夹爪行程覆盖工件</li>
          <li><b>P</b>取放位姿：多初值 IK + 碰撞检查</li>
          <li><b>D</b>门、抽屉扫掠对静态环境</li>
          <li><b>T</b>位姿之间的过渡</li>
        </ul>
        <p class="note">{{ pf.note }}</p>
      </div>
    </template>

    <template v-else-if="ch === 'plan'">
      <div class="pl-panel-head"><span>thresholds.json</span><span :class="{ lock: frozen }">{{ frozen ? '已冻结' : '编写中' }}</span></div>
      <div class="pl-panel-body">
        <ul class="gates">
          <li v-for="g in GATES_SHOWN" :key="g.id" :style="{ opacity: ramp(t, g.at, g.at + 0.4) }"><b class="mono">{{ g.id }}</b><span>{{ g.what }}</span><em class="mono">{{ g.v }}</em></li>
        </ul>
        <p class="k">负例：故意做错，门限必须判 FAIL</p>
        <div class="chips neg"><span v-for="(n, i) in NEGATIVES" :key="n" :style="{ opacity: ramp(t, 22.4 + i * 0.12, 22.8 + i * 0.12) }">{{ n }}</span></div>
      </div>
    </template>

    <template v-else-if="ch === 'reference'">
      <div class="pl-panel-head"><span>参考图</span><span>只冻结风格</span></div>
      <div class="pl-panel-body">
        <div class="refs"><figure v-for="(r, i) in REFS" :key="r.src" :style="{ opacity: ramp(t, 28.8 + i * 0.3, 29.4 + i * 0.3) }"><img :src="withBase('/' + r.src)" :alt="r.cap + '参考图'" /><figcaption>{{ r.cap }}</figcaption></figure></div>
        <dl class="assets dims"><div v-for="([a, b], i) in DIMS" :key="a" :style="{ opacity: ramp(t, 30.0 + i * 0.2, 30.4 + i * 0.2) }"><dt>{{ a }}</dt><dd><span class="src">{{ b }}</span></dd></div></dl>
      </div>
    </template>

    <template v-else-if="ch === 'modelling'">
      <div class="pl-panel-head"><span>建模</span><span>唯一参数源</span></div>
      <div class="pl-panel-body">
        <div class="split">
          <span class="src mono">design.py</span>
          <svg viewBox="0 0 200 36" aria-hidden="true"><path d="M100 0v10M100 10H40v18M100 10h60v18" /></svg>
          <div class="two"><span class="mono">build_blender.py<small>VIS_ → GLB</small></span><span class="mono">build_mjcf.py<small>COL_ → MJCF</small></span></div>
        </div>
        <ul class="checks"><li v-for="(m, i) in MCHECKS" :key="m" :class="{ on: i < mDone }"><i />{{ m }}</li></ul>
      </div>
    </template>

    <template v-else-if="ch === 'simulation'">
      <div class="pl-panel-head"><span>S3 最大穿透（mm）</span><span class="mono" :class="pen > 0.25 ? 'badt' : ''">{{ pen.toFixed(2) }}</span></div>
      <div class="pl-panel-body">
        <svg class="trace" viewBox="0 0 280 74" preserveAspectRatio="none" aria-hidden="true">
          <line x1="0" :y1="gateY" x2="280" :y2="gateY" class="gate" />
          <text x="276" :y="gateY - 4" text-anchor="end">门限 0.25</text>
          <polyline :points="trace" />
        </svg>
        <p class="k">负例 N1–N10：每一个都必须判 FAIL</p>
        <div class="negs"><span v-for="(n, i) in NEGATIVES" :key="n" :class="{ on: i < negLit }" :title="n">{{ n.split(' ')[0] }}</span></div>
      </div>
    </template>

    <template v-else-if="ch === 'render'">
      <div class="pl-panel-head"><span>渲染 · draft</span><span class="mono">帧 {{ Number(frame) }} / 3226</span></div>
      <div class="pl-panel-body">
        <ul class="checks"><li v-for="(v, i) in ['V1 场景里没有碰撞代理', 'V2 帧数 = 仿真时长 × 30', 'V3 抽检位姿与仿真一致', 'V4 成片可解码、时长一致']" :key="v" :class="{ on: i < vDone }"><i />{{ v }}</li></ul>
      </div>
    </template>

    <template v-else>
      <div class="pl-panel-head"><span>复盘 · 薄切片 01</span><span>按返工排序</span></div>
      <div class="pl-panel-body">
        <ul class="retro">
          <li v-for="(r, i) in RETRO" :key="r.stage"><span>{{ r.stage }}</span><i :style="{ width: (r.rework / 14) * 100 * retroOn + '%' }" :class="{ top: i === 0 }" /><b class="mono">{{ r.rework }}</b></li>
        </ul>
        <p class="note">仿真阶段 14 次返工里，9 次只要摆出位姿就能发现。于是方案预览里加了运动学预演。</p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.ip { flex-shrink: 1; min-height: 0; overflow: hidden; }
.k { margin: 10px 0 6px; font-size: 11.5px; color: var(--faint); }
.k:first-child { margin-top: 0; }
.chips { display: flex; flex-wrap: wrap; gap: 5px; }
.chips span { font-size: 11.5px; padding: 2px 8px; border-radius: 6px; background: var(--surface-2); border: 1px solid var(--line); color: var(--ink-2); }
.chips .more { background: none; border: 0; color: var(--faint); }
.chips.neg span { font-family: var(--font-mono); font-size: 10.5px; }
.assets { margin: 0; display: flex; flex-direction: column; }
.assets div { display: flex; justify-content: space-between; gap: 10px; padding: 4px 0; border-top: 1px solid var(--line); font-size: 12px; }
.assets dt { color: var(--ink-2); }
.assets dd { margin: 0; color: var(--muted); text-align: right; }
.src { font-family: var(--font-mono); font-size: 10.5px; padding: 1px 6px; border-radius: 5px; border: 1px solid color-mix(in srgb, var(--accent) 40%, var(--line-2)); color: var(--accent-ink); }
.big { display: flex; align-items: baseline; gap: 8px; }
.big b { font-family: var(--font-mono); font-size: 34px; font-weight: 500; line-height: 1.1; }
.big b.bad { color: var(--bad); }
.big b.ok { color: var(--ok); }
.big span { font-size: 13px; color: var(--muted); }
.bar { margin: 8px 0 10px; height: 5px; border-radius: 3px; background: color-mix(in srgb, var(--bad) 30%, var(--line)); overflow: hidden; }
.bar i { display: block; height: 100%; background: var(--ok); transition: width .5s var(--ease); }
.cats { list-style: none; margin: 0; padding: 0; display: grid; gap: 3px; }
.cats li { font-size: 12px; color: var(--ink-2); display: flex; gap: 8px; }
.cats b { font-family: var(--font-mono); font-size: 11px; color: var(--accent-ink); width: 12px; }
.note { margin-top: 10px; font-size: 12px; line-height: 1.6; color: var(--muted); }
.gates { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 4px; }
.gates li { display: grid; grid-template-columns: 34px 1fr auto; gap: 8px; font-size: 12px; align-items: baseline; color: var(--ink-2); }
.gates b { color: var(--accent-ink); font-weight: 500; font-size: 11.5px; }
.gates em { font-style: normal; font-size: 11px; color: var(--ink); }
.lock { color: var(--accent-ink); }
.refs { display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px; margin-bottom: 8px; }
.refs figure { margin: 0; }
.refs img { width: 100%; aspect-ratio: 1; object-fit: cover; border-radius: 7px; border: 1px solid var(--line); background: #e9e7e1; display: block; }
.refs figcaption { font-size: 11px; color: var(--muted); text-align: center; margin-top: 3px; }
.dims dd { text-align: right; }
.split { display: flex; flex-direction: column; align-items: center; }
.split > .src { font-size: 11.5px; padding: 3px 10px; }
.split svg { width: 100%; height: 30px; fill: none; stroke: var(--line-2); stroke-width: 1.2; }
.two { width: 100%; display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.two span { font-size: 11px; text-align: center; padding: 6px 4px; border-radius: 8px; border: 1px solid var(--line); background: var(--surface-2); color: var(--ink-2); }
.two small { display: block; color: var(--muted); font-size: 10.5px; margin-top: 2px; }
.checks { list-style: none; margin: 10px 0 0; padding: 0; display: grid; gap: 4px; }
.checks li { font-size: 12px; color: var(--faint); display: flex; align-items: center; gap: 8px; transition: color .3s var(--ease); }
.checks i { width: 12px; height: 12px; border-radius: 50%; border: 1px solid var(--line-2); flex-shrink: 0; transition: all .3s var(--ease); }
.checks li.on { color: var(--ink-2); }
.checks li.on i { background: var(--ok); border-color: var(--ok); }
.trace { width: 100%; height: 76px; display: block; overflow: visible; }
.trace polyline { fill: none; stroke: var(--accent); stroke-width: 1.6; vector-effect: non-scaling-stroke; }
.trace .gate { stroke: var(--bad); stroke-dasharray: 4 3; stroke-width: 1; vector-effect: non-scaling-stroke; }
.trace text { font-size: 9px; fill: var(--bad); font-family: var(--font-mono); }
.badt { color: var(--bad); }
.negs { display: grid; grid-template-columns: repeat(5, 1fr); gap: 4px; }
.negs span { font-family: var(--font-mono); font-size: 10.5px; text-align: center; padding: 3px 0; border-radius: 5px; border: 1px dashed var(--line-2); color: var(--faint); transition: all .25s var(--ease); }
.negs span.on { border-style: solid; border-color: color-mix(in srgb, var(--bad) 50%, var(--line)); color: var(--bad); background: color-mix(in srgb, var(--bad) 8%, transparent); }
.retro { list-style: none; margin: 0; padding: 0; display: grid; gap: 6px; }
.retro li { display: grid; grid-template-columns: 112px 1fr 22px; gap: 8px; align-items: center; font-size: 12px; color: var(--ink-2); }
.retro i { display: block; height: 8px; border-radius: 4px; background: var(--ghost); min-width: 2px; }
.retro i.top { background: var(--bad); }
.retro b { font-weight: 500; text-align: right; }
.mono { font-family: var(--font-mono); }
</style>
