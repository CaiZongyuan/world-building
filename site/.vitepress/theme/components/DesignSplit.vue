<script setup lang="ts">
import { ref } from 'vue'

const NODES = {
  design: { t: 'design.py → design.json', d: '唯一的参数源：每个部件的尺寸、位置、关节、质量，以及它是 visual、collision 还是 physics-root。改尺寸只改这一处。' },
  blender: { t: 'build_blender.py', d: 'Blender 5.4 headless 读 design.json 建视觉模型。命名：ROOT_<body> 放在关节轴上，VIS_<body>__<part> 是视觉，COL_<body>__<part> 是碰撞代理（hide_render，单独的 collection）。' },
  mjcf: { t: 'build_mjcf.py', d: 'MuJoCo MjSpec 读同一份 design.json 建物理模型。碰撞几何只取 collision=True 的部件；视觉几何放 group 2，不参与碰撞。' },
  glb: { t: 'lab_visual.glb', d: '导出时按白名单只选 VIS_ 和 ROOT_，不依赖隐藏状态。验证门直接解析 GLB 的 JSON 块读节点名（M3）。' },
  xml: { t: 'lab_assets.xml', d: 'M1 要能编译、关节范围与 thresholds.json 一致；M5 静置 1 s 不能有超过 0.25 mm 的穿透。' },
  map: { t: 'mapping.json', d: '每个 body 对应哪些视觉对象。渲染阶段靠它把仿真位姿一一写给视觉根（M4 检查覆盖完整）。' },
}
type K = keyof typeof NODES
const sel = ref<K>('design')
</script>

<template>
  <div class="ds vp-raw">
    <svg viewBox="0 0 640 230" role="img" aria-label="design.py 分出视觉和物理两份模型">
      <defs><marker id="ds-a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 10 5 0 10z" fill="var(--ghost)" /></marker></defs>
      <path d="M320 52 V76 H150 V100 M320 76 H490 V100 M150 140 V164 M490 140 V164 M150 120 H490" class="ln" />
      <path d="M150 164 V172 M490 164 V172" class="ln" marker-end="url(#ds-a)" />
      <g v-for="(n, k) in { design: [320, 32], blender: [150, 120], mjcf: [490, 120], glb: [150, 196], xml: [490, 196], map: [320, 120] }" :key="k" :class="['nd', { on: sel === k }]" tabindex="0" @click="sel = k as K" @mouseenter="sel = k as K" @focus="sel = k as K">
        <rect :x="n[0] - 92" :y="n[1] - 18" width="184" height="36" rx="9" />
        <text :x="n[0]" :y="n[1] + 4.5" text-anchor="middle">{{ NODES[k as K].t }}</text>
      </g>
      <text x="40" y="226" class="cap">视觉：给渲染（可以精细）</text>
      <text x="600" y="226" class="cap" text-anchor="end">物理：给仿真（只留功能面）</text>
    </svg>
    <div class="det wb-panel"><p class="wb-mono">{{ NODES[sel].t }}</p><p>{{ NODES[sel].d }}</p></div>
  </div>
</template>

<style scoped>
.ds { margin: 22px 0; display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr); gap: 16px; align-items: center; }
svg { width: 100%; height: auto; }
.ln { fill: none; stroke: var(--ghost); stroke-width: 1.4; }
.nd { cursor: pointer; }
.nd rect { fill: var(--surface); stroke: var(--line-2); transition: all .2s var(--ease); }
.nd text { font-family: var(--font-mono); font-size: 12px; fill: var(--ink-2); }
.nd.on rect { stroke: var(--accent); fill: color-mix(in srgb, var(--accent) 10%, var(--surface)); }
.nd.on text { fill: var(--accent-ink); }
.cap { font-size: 11.5px; fill: var(--faint); font-family: var(--font-ui); }
.det { padding: 14px 16px; }
.det p { margin: 0; font-size: 13.5px; line-height: 1.75; color: var(--ink-2); }
.det p.wb-mono { font-size: 13px; color: var(--accent-ink); margin-bottom: 6px; }
@media (max-width: 760px) { .ds { grid-template-columns: 1fr; } }
</style>
