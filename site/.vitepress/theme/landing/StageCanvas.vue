<script setup lang="ts">
// Mounts one LabStage and renders it from the `t` prop while it is on screen.
import { onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'
import { withBase } from 'vitepress'
import type { LabStage } from './stage'
import { labelsAt, type LabelSpec } from './story'

const props = withDefaults(defineProps<{ t: number; offsetX?: number; offsetY?: number; reduced?: boolean }>(), { offsetX: 0, offsetY: 0, reduced: false })
const emit = defineEmits<{ ready: [] }>()

const host = ref<HTMLDivElement>()
const canvas = ref<HTMLCanvasElement>()
const items = shallowRef<(LabelSpec & { x: number; y: number })[]>([])
const failed = ref(false)
let stage: LabStage | null = null
let raf = 0
let visible = false
let disposed = false
let ro: ResizeObserver | null = null
let io: IntersectionObserver | null = null
let mo: MutationObserver | null = null

async function create() {
  try {
    // three.js stays out of the entry chunk.
    const { LabStage } = await import('./stage')
    if (disposed || !canvas.value || !host.value) return
    stage = new LabStage(canvas.value, props.reduced)
  } catch (e) {
    console.warn('3D stage unavailable', e)
    failed.value = true
    return
  }
  const r = host.value.getBoundingClientRect()
  stage.resize(r.width, r.height)
  frame()
  emit('ready')
  loop()
}

function frame() {
  if (!stage) return
  stage.setOffset(props.offsetX, props.offsetY)
  stage.update(props.t, performance.now() / 1000)
  stage.render()
  const out: (LabelSpec & { x: number; y: number })[] = []
  const narrow = (host.value?.clientWidth ?? 1000) < 600
  for (const l of labelsAt(props.t)) {
    if (narrow && l.id.startsWith('l-') && !['l-inc', 'l-ws', 'l-rail'].includes(l.id)) continue
    const p = stage.project(l.anchor)
    if (p.visible) out.push({ ...l, x: p.x, y: p.y })
  }
  items.value = out
}

function loop() {
  const tick = () => {
    if (visible && !document.hidden) frame()
    raf = requestAnimationFrame(tick)
  }
  raf = requestAnimationFrame(tick)
}

onMounted(() => {
  ro = new ResizeObserver(([e]) => {
    stage?.resize(e.contentRect.width, e.contentRect.height)
    frame()
  })
  ro.observe(host.value!)
  io = new IntersectionObserver(([e]) => { visible = e.isIntersecting })
  io.observe(host.value!)
  mo = new MutationObserver(() => { stage?.applyTheme(); frame() })
  mo.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
  create()
})

onBeforeUnmount(() => {
  disposed = true
  cancelAnimationFrame(raf)
  ro?.disconnect(); io?.disconnect(); mo?.disconnect()
  stage?.dispose()
  stage = null
})
</script>

<template>
  <div ref="host" class="pl-stage">
    <canvas ref="canvas" class="pl-stage-canvas" />
    <img v-if="failed" class="pl-stage-fallback" :src="withBase('/img/full/overview.webp')" alt="全流程实验室的渲染画面" />
    <div class="pl-labels" aria-hidden="true">
      <div v-for="l in items" :key="l.id" class="pl-label" :class="l.tone" :style="{ transform: `translate(${l.x}px, ${l.y}px) translate(-50%, -100%)`, opacity: l.o }">
        <span>{{ l.text }}</span><b /><em />
      </div>
    </div>
  </div>
</template>

<style scoped>
.pl-stage { position: relative; }
.pl-stage-canvas { position: absolute; inset: 0; width: 100%; height: 100%; display: block; }
.pl-stage-fallback { position: absolute; inset: 10% 6% 14% 34%; width: 60%; object-fit: cover; border-radius: 14px; opacity: .7; }
</style>
