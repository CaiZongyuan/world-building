<script setup lang="ts">
import { computed } from 'vue'
import { hudAt } from './story'

const props = defineProps<{ t: number }>()
const h = computed(() => hudAt(props.t))
</script>

<template>
  <div class="hud pl-panel">
    <div><span>阶段</span><b class="mono">{{ h.stage }} / 7</b></div>
    <div><span>验证门 PASS</span><b class="mono ok">{{ h.passed }}</b></div>
    <div><span>门失败</span><b class="mono" :class="{ bad: h.fails }">{{ h.fails }}</b></div>
    <div><span>返工</span><b class="mono">{{ h.reworks }}</b></div>
    <div><span>审批点</span><b class="mono acc">{{ h.approvals }} / 2</b></div>
  </div>
</template>

<style scoped>
.hud { display: flex; gap: 0; padding: 0; overflow: hidden; }
.hud > div { display: flex; flex-direction: column; gap: 2px; padding: 9px 16px; border-right: 1px solid var(--line); }
.hud > div:last-child { border-right: 0; }
span { font-size: 10.5px; color: var(--faint); font-family: var(--font-mono); letter-spacing: .04em; white-space: nowrap; }
b { font-size: 15px; font-weight: 500; color: var(--ink); }
b.ok { color: var(--ok); }
b.bad { color: var(--bad); }
b.acc { color: var(--accent-ink); }
.mono { font-family: var(--font-mono); font-variant-numeric: tabular-nums; }
</style>
