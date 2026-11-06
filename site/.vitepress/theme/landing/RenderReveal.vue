<script setup lang="ts">
// The render chapter swaps the proxy lab for real frames of the phase-1 film.
import { computed } from 'vue'
import { withBase } from 'vitepress'
import { KEYFRAMES, clamp, window01 } from './story'

const props = defineProps<{ t: number }>()
const o = computed(() => window01(props.t, 58.2, 64.2, 0.7))
const idx = computed(() => Math.min(KEYFRAMES.length - 1, Math.floor(clamp((props.t - 58.4) / 5.2) * KEYFRAMES.length)))
</script>

<template>
  <figure v-if="o > 0.01" class="rr" :style="{ opacity: o, transform: `translateY(${(1 - o) * 14}px)` }">
    <div class="frame">
      <img v-for="(k, i) in KEYFRAMES" :key="k" :src="withBase(`/img/kf/frame_${k}.webp`)" :style="{ opacity: i === idx ? 1 : 0 }" alt="" loading="lazy" />
      <span class="rec mono">● draft · 720p · 16 spp</span>
      <span class="tc mono">{{ (Number(KEYFRAMES[idx]) / 30).toFixed(1) }} s</span>
    </div>
    <figcaption>全流程实验室期 1 成片的真实画面：每一帧的位姿都来自 MuJoCo，Blender 只负责照抄和出图。</figcaption>
  </figure>
</template>

<style scoped>
.rr { margin: 0; width: min(560px, 42vw); }
.frame { position: relative; aspect-ratio: 16 / 9; border-radius: 12px; overflow: hidden; border: 1px solid var(--line-2); box-shadow: var(--shadow-2); background: var(--figure-ground); }
.frame img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; transition: opacity .25s linear; }
.rec, .tc { position: absolute; top: 10px; font-size: 10.5px; padding: 3px 8px; border-radius: 6px; background: rgb(0 0 0 / 55%); color: #f0eee8; }
.rec { left: 10px; }
.tc { right: 10px; }
figcaption { margin-top: 10px; font-size: 12.5px; line-height: 1.6; color: var(--muted); }
.mono { font-family: var(--font-mono); }
</style>
