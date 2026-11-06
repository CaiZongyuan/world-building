<script setup lang="ts">
// The project folder as the agent fills it: one chip per stage directory, and the
// files of the stage being worked on right now.
import { computed } from 'vue'
import { treeAt } from './story'

const props = defineProps<{ t: number }>()
const rows = computed(() => treeAt(props.t))
const cur = computed(() => rows.value.find((r) => r.state === 'active' || r.state === 'fail') ?? [...rows.value].reverse().find((r) => r.state === 'pass') ?? rows.value[0])
const label = { todo: '待开始', active: '进行中', fail: 'FAIL', pass: 'PASS' }
</script>

<template>
  <div class="pt pl-panel">
    <div class="pl-panel-head"><span>项目目录</span><span class="nt">cell-passaging-lab/</span></div>
    <div class="pl-panel-body">
      <ol class="chips">
        <li v-for="r in rows" :key="r.dir" :class="r.state" :title="`${r.dir}/ · ${label[r.state]}`"><span class="mono">{{ r.dir.slice(0, 2) }}</span></li>
      </ol>
      <div class="cur">
        <div class="row"><span class="dir mono">{{ cur.dir }}/</span><span class="st" :class="cur.state">{{ label[cur.state] }}</span></div>
        <ul class="files"><li v-for="f in cur.files" :key="f.f" :class="{ fresh: f.fresh }" class="mono">{{ f.f }}</li></ul>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pt { flex-shrink: 0; }
.nt { text-transform: none; letter-spacing: 0; }
.chips { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; }
.chips li { height: 22px; display: grid; place-items: center; border-radius: 6px; border: 1px dashed var(--line-2); font-size: 10.5px; color: var(--faint); transition: all .3s var(--ease); }
.chips li.active { border-style: solid; border-color: var(--accent); color: var(--accent-ink); background: color-mix(in srgb, var(--accent) 10%, transparent); }
.chips li.fail { border-style: solid; border-color: var(--bad); color: var(--bad); background: color-mix(in srgb, var(--bad) 10%, transparent); }
.chips li.pass { border-style: solid; border-color: color-mix(in srgb, var(--ok) 50%, var(--line)); color: var(--ok); background: color-mix(in srgb, var(--ok) 9%, transparent); }
.cur { margin-top: 10px; }
.row { display: flex; justify-content: space-between; align-items: center; }
.dir { font-size: 11.5px; color: var(--ink); }
.st { font-family: var(--font-mono); font-size: 10px; letter-spacing: .05em; color: var(--faint); }
.st.active { color: var(--accent); }
.st.pass { color: var(--ok); }
.st.fail { color: var(--bad); }
.files { list-style: none; margin: 4px 0 0; padding: 0 0 0 12px; border-left: 1px solid var(--line-2); min-height: 18px; }
.files li { font-size: 11px; line-height: 1.7; color: var(--muted); transition: color .6s var(--ease); }
.files li.fresh { color: var(--accent-ink); }
.mono { font-family: var(--font-mono); }
</style>
