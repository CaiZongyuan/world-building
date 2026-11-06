<script setup lang="ts">
// Top of every stage page: where the stage sits in the pipeline, what goes in,
// what comes out, the command that closes it, and whether you are needed.
import { computed } from 'vue'
import { withBase } from 'vitepress'
import { STAGES } from '../data/stages'

const props = defineProps<{ stage: string }>()
const i = computed(() => STAGES.findIndex((s) => s.id === props.stage))
const s = computed(() => STAGES[i.value])
</script>

<template>
  <div class="sh vp-raw">
    <ol class="rail">
      <li v-for="(x, k) in STAGES" :key="x.id" :class="{ on: k === i, past: k < i }"><a :href="withBase(x.link)"><i /><span>{{ x.short }}<em v-if="x.approval">{{ x.approval === 1 ? '①' : '②' }}</em></span></a></li>
    </ol>
    <div class="card wb-panel">
      <div><span class="k">回答的问题</span><b>{{ s.question }}</b></div>
      <div><span class="k">输入</span><ul><li v-for="x in s.input" :key="x">{{ x }}</li></ul></div>
      <div><span class="k">产物 · {{ s.dir }}/</span><ul><li v-for="x in s.output" :key="x" class="wb-mono">{{ x }}</li></ul></div>
      <div><span class="k">完成判据</span><code>wb gate &lt;项目&gt; {{ s.id }}</code><span class="you" :class="{ ap: s.approval }">{{ s.approval ? `之后是审批点${s.approval === 1 ? '①' : '②'}：需要你点头` : '不需要你介入' }}</span></div>
    </div>
  </div>
</template>

<style scoped>
.sh { margin: 18px 0 28px; }
.rail { list-style: none; margin: 0 0 12px; padding: 0; display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
.rail a { display: flex; flex-direction: column; gap: 5px; font-size: 12px; color: var(--faint); text-decoration: none; }
.rail i { display: block; height: 3px; border-radius: 2px; background: var(--line-2); }
.rail li.past i { background: color-mix(in srgb, var(--accent) 40%, var(--line-2)); }
.rail li.on i { background: var(--accent); }
.rail li.on a { color: var(--ink); font-weight: 500; }
.rail em { font-style: normal; color: var(--accent-ink); margin-left: 3px; }
.card { display: grid; grid-template-columns: 1.1fr 1fr 1.2fr 1fr; gap: 0; padding: 0; overflow: hidden; }
.card > div { padding: 14px 16px; border-right: 1px solid var(--line); display: flex; flex-direction: column; gap: 6px; }
.card > div:last-child { border-right: 0; }
.k { font-family: var(--font-mono); font-size: 10.5px; letter-spacing: .06em; color: var(--faint); text-transform: uppercase; }
.card b { font-family: var(--font-display); font-size: 17px; font-weight: 600; line-height: 1.45; color: var(--ink); }
.card ul { margin: 0; padding: 0; list-style: none; }
.card li { font-size: 13px; line-height: 1.65; color: var(--ink-2); }
.card li.wb-mono { font-size: 12px; }
code { font-family: var(--font-mono); font-size: 12px; color: var(--accent-ink); }
.you { font-size: 12.5px; color: var(--muted); }
.you.ap { color: var(--accent-ink); font-weight: 500; }
@media (max-width: 900px) { .card { grid-template-columns: 1fr 1fr; } .card > div:nth-child(2) { border-right: 0; } .card > div:nth-child(-n+2) { border-bottom: 1px solid var(--line); } }
@media (max-width: 560px) { .card { grid-template-columns: 1fr; } .card > div { border-right: 0; border-bottom: 1px solid var(--line); } .rail span { font-size: 0; } .rail em { font-size: 11px; } }
</style>
