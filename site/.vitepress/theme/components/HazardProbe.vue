<script setup lang="ts">
// N6: "dispense target offset". Is a 10 mm offset dangerous at all?
import { computed, ref } from 'vue'

const R = 17.4
const off = ref(10)
const margin = computed(() => R - off.value)
const pass = computed(() => margin.value >= 2)
const S = 4.6
const cx = 150, cy = 110
</script>

<template>
  <div class="hp vp-raw wb-panel">
    <svg viewBox="0 0 300 220" role="img" aria-label="六孔板一个孔的俯视图与吸头位置">
      <rect x="20" y="16" width="260" height="188" rx="10" class="plate" />
      <circle :cx="cx" :cy="cy" :r="R * S" class="well" />
      <circle :cx="cx" :cy="cy" :r="(R - 2) * S" class="safe" />
      <line :x1="cx" :y1="cy" :x2="cx + off * S" :y2="cy" class="offl" />
      <circle :cx="cx" :cy="cy" r="3" class="ctr" />
      <circle :cx="cx + off * S" :cy="cy" r="7" :class="pass ? 'tip ok' : 'tip bad'" />
      <text :x="cx" :y="cy - R * S - 6" text-anchor="middle" class="lb">孔半径 17.4 mm · 虚线内离边 ≥ 2 mm</text>
      <text :x="cx + off * S / 2" :y="cy + 18" text-anchor="middle" class="lb">偏 {{ off }} mm</text>
    </svg>
    <div class="side">
      <label>负例 N6：分液目标偏移 <b class="wb-mono">{{ off }} mm</b><input v-model.number="off" type="range" min="0" max="25" step="1" /></label>
      <div class="marks"><button type="button" class="wb-btn" @click="off = 10">v1：偏 10 mm</button><button type="button" class="wb-btn" @click="off = 20">v2：偏 20 mm</button></div>
      <p class="res"><span>S18 吸头在开口内、离边 ≥ 2 mm</span><span class="wb-tag" :class="pass ? 'PASS' : 'FAIL'">{{ pass ? 'PASS' : 'FAIL' }}</span></p>
      <p class="txt" v-if="pass">吸头离孔边还有 <b>{{ margin.toFixed(1) }} mm</b>。这个「错」在物理上并不危险，门限判 PASS 是对的，<b>是负例本身无效</b>。</p>
      <p class="txt" v-else>吸头落到孔外的板面上，S18 判 FAIL：负例有效，证明门限真能抓到这种错。</p>
      <p class="note">项目里的做法：门限 S18 不动，只把负例改成 v2（偏 20 mm），并在 thresholds.json 的 revisions 里写明原因。以后先用独立小模型扫一遍参数（危险探针），再把负例写进 plan。</p>
    </div>
  </div>
</template>

<style scoped>
.hp { margin: 22px 0; padding: 16px; display: grid; grid-template-columns: 300px 1fr; gap: 20px; align-items: center; }
svg { width: 100%; height: auto; }
.plate { fill: var(--surface-2); stroke: var(--line-2); }
.well { fill: color-mix(in srgb, var(--m-medium) 35%, transparent); stroke: var(--ink-2); stroke-width: 1.2; }
.safe { fill: none; stroke: var(--ok); stroke-dasharray: 4 3; }
.offl { stroke: var(--muted); stroke-dasharray: 3 3; }
.ctr { fill: var(--ink-2); }
.tip.ok { fill: var(--ok); }
.tip.bad { fill: var(--bad); }
.lb { font-size: 10.5px; fill: var(--muted); font-family: var(--font-ui); }
.side { display: flex; flex-direction: column; gap: 10px; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: var(--muted); }
label b { color: var(--ink); }
input { accent-color: var(--accent); }
.marks { display: flex; gap: 8px; flex-wrap: wrap; }
.res { margin: 0; display: flex; justify-content: space-between; align-items: center; gap: 10px; padding: 8px 10px; border: 1px solid var(--line); border-radius: 8px; font-size: 13px; color: var(--ink-2); }
.txt { margin: 0; font-size: 13.5px; line-height: 1.75; color: var(--ink-2); }
.note { margin: 0; font-size: 12.5px; line-height: 1.7; color: var(--muted); }
@media (max-width: 760px) { .hp { grid-template-columns: 1fr; } }
</style>
