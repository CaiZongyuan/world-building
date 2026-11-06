<script setup lang="ts">
// Try a gate verdict by hand: set each check's status and watch the aggregate,
// the CLI output and the exit code. The rule is the one in src/wb/gate.py.
import { computed, ref } from 'vue'

type S = 'PASS' | 'FAIL' | 'NOT_RUN' | 'BLOCKED' | 'IDEALIZED'
const ORDER: S[] = ['PASS', 'FAIL', 'NOT_RUN', 'BLOCKED', 'IDEALIZED']
const ICON: Record<S, string> = { PASS: '✅', FAIL: '❌', NOT_RUN: '⏸', BLOCKED: '⛔', IDEALIZED: '🟡' }
const PRESETS: Record<string, { label: string; checks: [string, S, string?][] }> = {
  requirements: { label: '需求访谈', checks: [['需求记录存在', 'PASS'], ['必填节：目标', 'PASS'], ['必填节：不做什么', 'FAIL', '该节为空'], ['必填节：工艺步骤', 'PASS'], ['必填节：设备', 'PASS'], ['必填节：保真度', 'PASS'], ['必填节：算力预算', 'PASS']] },
  simulation: { label: '仿真', checks: [['名义流程 20 项门限（第 5 期）', 'PASS'], ['负例 N3 夹取高度偏高 按预期判 FAIL', 'PASS'], ['负例 N6 分液目标偏移 按预期判 FAIL', 'FAIL', '负例跑出来 S18 判 PASS：危险不存在'], ['渲染用位姿记录', 'PASS']] },
  render: { label: '渲染', checks: [['V1 场景无碰撞代理', 'PASS'], ['V2 帧数 = 仿真时长 × 30（不加速、不跳帧）', 'PASS'], ['V3 抽检位姿与仿真一致', 'PASS'], ['V4 成片可解码且时长一致', 'BLOCKED', 'ffprobe 不可用']] },
}
const stage = ref<keyof typeof PRESETS>('requirements')
const checks = ref(PRESETS.requirements.checks.map(([n, s, d]) => ({ n, s, d: d ?? '' })))

function load(k: keyof typeof PRESETS) {
  stage.value = k
  checks.value = PRESETS[k].checks.map(([n, s, d]) => ({ n, s, d: d ?? '' }))
}
function cycle(i: number) {
  const c = checks.value[i]
  c.s = ORDER[(ORDER.indexOf(c.s) + 1) % ORDER.length]
  c.d = c.s === 'PASS' ? '' : c.d
}
const aggregate = computed<S>(() => {
  const s = checks.value.map((c) => c.s)
  if (!s.length) return 'NOT_RUN'
  if (s.includes('FAIL')) return 'FAIL'
  if (s.includes('BLOCKED')) return 'BLOCKED'
  if (s.every((x) => x === 'NOT_RUN')) return 'NOT_RUN'
  if (s.includes('NOT_RUN')) return 'NOT_RUN'
  if (s.includes('IDEALIZED')) return 'IDEALIZED'
  return 'PASS'
})
const WHY: Record<S, string> = {
  PASS: '全部检查通过。写阶段日志，进入下一阶段。',
  FAIL: '有一项 FAIL，整道门就是 FAIL，哪怕其余都过了。先复盘根因，改设计或做法再跑；门限不放宽。',
  BLOCKED: '没有 FAIL，但有外部条件不满足。修好环境再跑，不能当作通过。',
  NOT_RUN: '有检查没跑（缺产物或没实现）。部分没跑也不能算整体 PASS。',
  IDEALIZED: '靠理想化才过的检查，永远不算 PASS，必须在报告和成片里标明。',
}
</script>

<template>
  <div class="gs vp-raw wb-panel">
    <div class="top">
      <span class="lbl">选一个阶段</span>
      <div class="wb-seg"><button v-for="(p, k) in PRESETS" :key="k" type="button" :aria-pressed="stage === k" @click="load(k)">{{ p.label }}</button></div>
      <span class="hint">点每一项的状态切换它，看整道门怎么判。</span>
    </div>
    <div class="cols">
      <ul class="checks">
        <li v-for="(c, i) in checks" :key="c.n"><button type="button" class="wb-tag" :class="c.s" @click="cycle(i)">{{ c.s }}</button><span>{{ c.n }}</span></li>
      </ul>
      <div class="out">
        <div class="wb-term">
          <div><span class="dim">$</span> uv run --extra sim wb gate my-project {{ stage }}</div>
          <div :class="aggregate === 'PASS' ? 'ok' : aggregate === 'FAIL' ? 'bad' : 'warn'">{{ ICON[aggregate] }} {{ stage }}: {{ aggregate }}</div>
          <div v-for="c in checks" :key="c.n">  {{ ICON[c.s] }} {{ c.n }}<span v-if="c.d" class="dim"> — {{ c.d }}</span></div>
          <div class="dim">$ echo $?</div>
          <div :class="aggregate === 'PASS' ? 'ok' : 'bad'">{{ aggregate === 'PASS' ? 0 : 1 }}</div>
        </div>
        <p class="why"><span class="wb-tag" :class="aggregate">{{ aggregate }}</span>{{ WHY[aggregate] }}</p>
      </div>
    </div>
    <p class="rule">合并规则：FAIL &gt; BLOCKED &gt; NOT_RUN &gt; IDEALIZED &gt; PASS。判定和证据同时写进 <code>gates/{{ stage }}.json</code>。</p>
  </div>
</template>

<style scoped>
.gs { margin: 22px 0; padding: 16px 18px; }
.top { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.lbl { font-size: 13px; color: var(--muted); }
.hint { font-size: 12.5px; color: var(--faint); }
.cols { margin-top: 14px; display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr); gap: 16px; }
.checks { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.checks li { display: flex; align-items: center; gap: 10px; font-size: 13.5px; color: var(--ink-2); }
.checks .wb-tag { cursor: pointer; background: none; min-width: 84px; justify-content: center; }
.wb-term div { white-space: pre-wrap; }
.why { margin: 10px 0 0; font-size: 13.5px; line-height: 1.7; color: var(--ink-2); display: flex; gap: 10px; align-items: flex-start; }
.why .wb-tag { flex-shrink: 0; margin-top: 2px; }
.rule { margin: 12px 0 0; font-size: 12.5px; color: var(--muted); }
.rule code { font-family: var(--font-mono); font-size: 11.5px; }
@media (max-width: 800px) { .cols { grid-template-columns: 1fr; } }
</style>
