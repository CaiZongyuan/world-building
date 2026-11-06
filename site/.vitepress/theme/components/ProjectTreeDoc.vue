<script setup lang="ts">
import { ref } from 'vue'

const ROWS: [string, number, string][] = [
  ['<项目>/', 0, '一个项目 = 流程的一次运行。本地在 projects/<项目>/，整个 projects/ 镜像到 HF 数据集 RickC1999/world-building-projects。'],
  ['README.md', 1, '项目标题。由 wb new 生成。'],
  ['stage-log.md', 1, '阶段日志：每个阶段一行（耗时、轮数、门失败、返工、人工介入、主要卡点），下面是卡点小节。项目收尾时用它给阶段排序。'],
  ['gates/<阶段>.json', 1, '验证门最近一次的判定和证据。继续一个项目时，agent 先读这里，从第一个没 PASS 的阶段接着做。'],
  ['01-requirements/', 1, 'requirements.md（六节），范围大时还有 preview/index.html 范围预览。'],
  ['02-proposal/', 1, 'index.html（8 节方案页）、img/、analysis/（preflight.json、预演报告、俯视图）。wb publish 会把它复制到仓库的 proposals/。'],
  ['03-plan/', 1, 'plan.md 和 thresholds.json。后面所有验证门只读 thresholds.json。'],
  ['04-reference/', 1, 'board/*.webp、prompts/、reference.json、dimensions.md、load_path.svg，以及 wb review 生成的审批页 index.html。'],
  ['05-modelling/', 1, 'design.py → design.json → build_blender.py / build_mjcf.py；GLB、MJCF、mapping.json、preview/。'],
  ['06-simulation/', 1, 'scene.py、plan_motion.py、run_*.py、results/*.json、states_30fps.npz。大项目还有 chain.py、run_full.py。'],
  ['07-render/', 1, 'build_render_scene.py、render_frames.py、finish.sh；frames/、film.mp4、keyframes/。'],
]
const sel = ref(2)
</script>

<template>
  <div class="ptd vp-raw">
    <ul class="tree wb-mono">
      <li v-for="(r, i) in ROWS" :key="r[0]" :class="{ on: i === sel }" :style="{ paddingLeft: 12 + r[1] * 18 + 'px' }" tabindex="0" @mouseenter="sel = i" @focus="sel = i" @click="sel = i">{{ r[1] ? '├── ' : '' }}{{ r[0] }}</li>
    </ul>
    <div class="det wb-panel"><p class="wb-mono">{{ ROWS[sel][0] }}</p><p>{{ ROWS[sel][2] }}</p></div>
  </div>
</template>

<style scoped>
.ptd { margin: 20px 0; display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.1fr); gap: 16px; align-items: start; }
.tree { list-style: none; margin: 0; padding: 10px 0; border-radius: 12px; background: var(--term-bg); color: var(--term-ink); border: 1px solid var(--term-line); font-size: 12.5px; }
.tree li { padding-top: 3px; padding-bottom: 3px; cursor: default; white-space: pre; }
.tree li.on { background: color-mix(in srgb, #9ca4ff 20%, transparent); color: #fff; }
.det { padding: 14px 16px; position: sticky; top: 80px; }
.det p { margin: 0; font-size: 14px; line-height: 1.75; color: var(--ink-2); }
.det p.wb-mono { font-size: 13px; color: var(--accent-ink); margin-bottom: 6px; }
@media (max-width: 760px) { .ptd { grid-template-columns: 1fr; } }
</style>
