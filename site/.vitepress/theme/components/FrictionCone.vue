<script setup lang="ts">
import { computed, ref } from 'vue'

const mu = ref(0.6)
const ang = ref(25)
const half = computed(() => (Math.atan(mu.value) * 180) / Math.PI)
const ok = computed(() => ang.value <= half.value)
const cx = 150, cy = 190, L = 160
const p = (deg: number, len: number) => [cx + Math.sin((deg * Math.PI) / 180) * len, cy - Math.cos((deg * Math.PI) / 180) * len]
const l1 = computed(() => p(-half.value, L))
const l2 = computed(() => p(half.value, L))
const f = computed(() => p(ang.value, 130))
</script>

<template>
  <div class="fc vp-raw wb-panel">
    <div class="ctrl">
      <label>摩擦系数 μ <b class="wb-mono">{{ mu.toFixed(2) }}</b><input v-model.number="mu" type="range" min="0.05" max="2" step="0.05" /></label>
      <label>接触力偏离法向的角度 <b class="wb-mono">{{ ang }}°</b><input v-model.number="ang" type="range" min="0" max="80" step="1" /></label>
      <p class="verdict" :class="ok ? 'yes' : 'no'">{{ ok ? `力在锥内（${ang}° ≤ ${half.toFixed(1)}°）：不打滑` : `力在锥外（${ang}° > ${half.toFixed(1)}°）：会滑动` }}</p>
      <p class="note">锥的半角 = arctan μ。V 形夹块的斜面是 45°，arctan 1 = 45°，所以 μ ≥ 1 时推力落在锥里，管子被「卡」在斜面上推不动，这就是自锁。</p>
    </div>
    <svg viewBox="0 0 300 220" role="img" aria-label="摩擦锥示意">
      <rect x="20" y="190" width="260" height="22" fill="var(--solid)" stroke="var(--ink-2)" />
      <text x="150" y="206" text-anchor="middle" font-size="11" fill="var(--ink)">接触面</text>
      <path :d="`M${cx} ${cy} L${l1[0]} ${l1[1]} A ${L} ${L} 0 0 1 ${l2[0]} ${l2[1]} Z`" fill="var(--accent-soft)" stroke="var(--accent)" />
      <line :x1="cx" :y1="cy" :x2="cx" :y2="cy - L - 6" stroke="var(--muted)" stroke-dasharray="4 4" />
      <text :x="cx + 4" :y="cy - L - 10" font-size="11" fill="var(--muted)">法向</text>
      <line :x1="cx" :y1="cy" :x2="f[0]" :y2="f[1]" :stroke="ok ? 'var(--pass)' : 'var(--fail)'" stroke-width="4" stroke-linecap="round" />
      <circle :cx="f[0]" :cy="f[1]" r="6" :fill="ok ? 'var(--pass)' : 'var(--fail)'" />
      <text :x="l2[0] - 8" :y="l2[1] + 16" font-size="11" fill="var(--accent-ink)" text-anchor="end">半角 {{ half.toFixed(1) }}°</text>
    </svg>
  </div>
</template>

<style scoped>
.fc { margin: 22px 0; display: grid; grid-template-columns: 1fr 300px; gap: 20px; padding: 18px; align-items: center; }
.ctrl { display: flex; flex-direction: column; gap: 12px; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 13px; color: var(--muted); }
label b { color: var(--ink); }
input[type='range'] { accent-color: var(--accent); }
.verdict { margin: 0; padding: 9px 12px; border-radius: 8px; font-weight: 500; font-size: 14px; }
.verdict.yes { background: color-mix(in srgb, var(--ok) 12%, transparent); color: var(--ok); }
.verdict.no { background: color-mix(in srgb, var(--bad) 12%, transparent); color: var(--bad); }
.note { margin: 0; font-size: 13px; line-height: 1.7; color: var(--muted); }
svg { width: 100%; height: auto; overflow: visible; }
@media (max-width: 700px) { .fc { grid-template-columns: 1fr; } }
</style>
