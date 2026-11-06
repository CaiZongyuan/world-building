<script setup lang="ts">
// Scrub through keyframes of a rendered film. Every pose in these frames came from MuJoCo.
import { computed, ref } from 'vue'
import { withBase } from 'vitepress'

const SETS: Record<string, { src: string; t: number; cap: string }[]> = {
  slice: [
    { src: 'slice/kf_00000.webp', t: 0, cap: '初始：两扇门关着，Panda 在停靠位。' },
    { src: 'slice/kf_00150.webp', t: 5, cap: '外门由执行器打开（3–6 s），内玻璃门随后打开（5–7.5 s）。' },
    { src: 'slice/kf_00270.webp', t: 9, cap: '两扇门全开，观察站抽屉伸出 0.19 m（7.5–9.5 s）。' },
    { src: 'slice/kf_00525.webp', t: 17.5, cap: '偏置宽指水平伸进第 3 层，夹住板的两个短端（17–18.5 s 闭合）。' },
    { src: 'slice/kf_00750.webp', t: 25, cap: '抬起 12 mm，后退 0.37 m 退出箱体，再升高。' },
    { src: 'slice/kf_00930.webp', t: 31, cap: '绕底座竖轴圆弧搬运，手爪只绕竖直轴转，盖不倾斜（25.5–31.5 s）。' },
    { src: 'slice/kf_01080.webp', t: 36, cap: '板落进托槽，确认托住后才松爪。' },
    { src: 'slice/kf_01350.webp', t: 45, cap: 'Panda 回停靠位（39–44 s），抽屉开始收回。' },
    { src: 'slice/kf_01620.webp', t: 54, cap: '两扇门关好，板随抽屉进入观察站，结束。' },
  ],
  full: ['00000', '00268', '00536', '00804', '01072', '01340', '01608', '01876', '02144', '02412', '02680', '02948', '03216'].map((k) => ({ src: `kf/frame_${k}.webp`, t: Number(k) / 30, cap: '全流程实验室期 1（取母板 → 观察 → 送进工作站），draft 档位。' })),
}
const props = withDefaults(defineProps<{ set?: string }>(), { set: 'slice' })
const frames = SETS[props.set]
const i = ref(Math.min(3, frames.length - 1))
const f = computed(() => frames[i.value])
const total = frames[frames.length - 1].t
</script>

<template>
  <figure class="fs vp-raw">
    <div class="frame"><img v-for="(x, k) in frames" :key="x.src" :src="withBase('/img/' + x.src)" :style="{ opacity: k === i ? 1 : 0 }" :alt="x.cap" loading="lazy" /><span class="tc wb-mono">{{ f.t.toFixed(1) }} s / {{ total.toFixed(1) }} s</span></div>
    <input v-model.number="i" type="range" :min="0" :max="frames.length - 1" step="1" aria-label="拖动查看关键帧" />
    <figcaption>{{ f.cap }}</figcaption>
  </figure>
</template>

<style scoped>
.fs { margin: 22px 0; }
.frame { position: relative; aspect-ratio: 16 / 9; border-radius: 12px; overflow: hidden; border: 1px solid var(--line); background: var(--figure-ground); }
.frame img { position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; transition: opacity .2s linear; border: 0; border-radius: 0; }
.tc { position: absolute; right: 10px; top: 10px; font-size: 11px; padding: 3px 8px; border-radius: 6px; background: rgb(0 0 0 / 55%); color: #f0eee8; }
input { width: 100%; margin-top: 10px; accent-color: var(--accent); }
figcaption { margin-top: 4px; font-size: 13.5px; color: var(--ink-2); line-height: 1.7; }
</style>
