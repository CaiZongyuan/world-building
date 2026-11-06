<script setup lang="ts">
import { computed, reactive } from 'vue'

const st = reactive({ A: { ct: 1, ca: 1 }, B: { ct: 1, ca: 1 } })
type G = 'A' | 'B'
type F = 'ct' | 'ca'
function flip(g: G, f: F, b: number) { st[g][f] ^= 1 << b }
const ab = computed(() => st.A.ct & st.B.ca)
const ba = computed(() => st.B.ct & st.A.ca)
const hit = computed(() => (ab.value | ba.value) !== 0)
</script>

<template>
  <div class="cb vp-raw">
    <div class="cards">
      <div v-for="g in (['A', 'B'] as G[])" :key="g" class="wb-panel card">
        <b>geom {{ g }}</b><span class="eg">{{ g === 'A' ? '例如被夹的管' : '例如手指' }}</span>
        <div v-for="f in (['ct', 'ca'] as F[])" :key="f" class="row">
          <span class="wb-mono">{{ f === 'ct' ? 'contype' : 'conaffinity' }}</span>
          <label v-for="b in [0, 1, 2]" :key="b"><input type="checkbox" :checked="!!(st[g][f] >> b & 1)" @change="flip(g, f, b)" />位{{ b }}</label>
          <span class="wb-mono val">= {{ st[g][f] }}</span>
        </div>
      </div>
    </div>
    <p class="verdict" :class="hit ? 'yes' : 'no'">{{ hit ? `会检测接触：A.contype & B.conaffinity = ${ab}，B.contype & A.conaffinity = ${ba}` : '不检测接触：两个方向的按位与都是 0。项目里让被夹工件和手指互不接触，就是这样设的。' }}</p>
  </div>
</template>

<style scoped>
.cb { margin: 20px 0; }
.cards { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.card { padding: 12px 14px; }
.card b { font-size: 14px; color: var(--ink); }
.eg { margin-left: 8px; font-size: 12px; color: var(--muted); }
.row { display: flex; align-items: center; gap: 10px; margin-top: 8px; font-size: 13px; color: var(--ink-2); flex-wrap: wrap; }
.row > .wb-mono:first-child { width: 92px; font-size: 12px; }
label { display: inline-flex; align-items: center; gap: 3px; }
input { accent-color: var(--accent); }
.val { color: var(--muted); font-size: 12px; }
.verdict { margin: 10px 0 0; padding: 9px 12px; border-radius: 8px; font-size: 13.5px; }
.verdict.yes { background: color-mix(in srgb, var(--ok) 12%, transparent); color: var(--ok); }
.verdict.no { background: color-mix(in srgb, var(--warn) 12%, transparent); color: var(--warn); }
@media (max-width: 700px) { .cards { grid-template-columns: 1fr; } }
</style>
