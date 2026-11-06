<script setup lang="ts">
// Hover a concept on the left; the matching MJCF on the right lights up.
import { computed, ref } from 'vue'

const XML = `<mujoco model="place">
  <option timestep="0.0005"/>
  <worldbody>
    <geom name="sup_drawer" type="box" size="0.08 0.055 0.01" solref="0.004 1"/>
    <body name="plate" pos="0 0 0.06">
      <freejoint/>
      <geom name="obj_plate" type="box" size="0.064 0.043 0.01" mass="0.12"/>
    </body>
    <body name="fl" pos="-0.069 0 0" gravcomp="1">
      <joint name="jl" type="slide" axis="1 0 0"/>
      <geom name="pad_fl" type="box" size="0.004 0.012 0.006" friction="1 0.005 0.0001" solref="0.002 1"/>
    </body>
  </worldbody>
  <actuator>
    <position name="a_l" joint="jl" kp="3000" kv="30" forcerange="-8 8"/>
  </actuator>
  <equality>
    <weld name="w_hand" body1="hand" body2="tube" solref="0.005 1"/>
  </equality>
</mujoco>`
const ITEMS = [
  { k: 'body', t: 'body', d: '刚体，有自己的坐标系。子 body 挂在父 body 上，构成一棵树。', re: /<body[^>]*>|<\/body>/g },
  { k: 'joint', t: 'joint / freejoint', d: '自由度。freejoint 表示能自由运动的工件（板、管、盖）；hinge 是转轴，slide 是滑轨。', re: /<freejoint\/>|<joint[^>]*\/>/g },
  { k: 'geom', t: 'geom', d: '碰撞形状，也决定质量分布。接触只发生在 geom 之间。名字前缀 obj_ / sup_ / pad_ 标出它的角色。', re: /<geom[^>]*\/>/g },
  { k: 'solref', t: 'solref / friction', d: '接触的软硬和摩擦系数，写在 geom 上。下一页的实验专门讲。', re: /solref="[^"]*"|friction="[^"]*"/g },
  { k: 'actuator', t: 'actuator', d: '电机。位置执行器按「目标 − 实际」出力，有力的上限 forcerange。', re: /<position[^>]*\/>/g },
  { k: 'equality', t: 'equality（weld）', d: '约束，把两个 body 焊在一起。只在夹持小件时用，并受门限盯住。', re: /<weld[^>]*\/>/g },
]
const sel = ref('geom')
const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;')
const html = computed(() => {
  const it = ITEMS.find((i) => i.k === sel.value)!
  let out = '', last = 0
  const re = new RegExp(it.re.source, 'g')
  let m: RegExpExecArray | null
  while ((m = re.exec(XML))) { out += esc(XML.slice(last, m.index)) + `<mark>${esc(m[0])}</mark>`; last = m.index + m[0].length }
  return out + esc(XML.slice(last))
})
</script>

<template>
  <div class="an vp-raw">
    <ul>
      <li v-for="it in ITEMS" :key="it.k" :class="{ on: sel === it.k }" tabindex="0" @mouseenter="sel = it.k" @focus="sel = it.k" @click="sel = it.k">
        <b class="wb-mono">{{ it.t }}</b><span>{{ it.d }}</span>
      </li>
    </ul>
    <pre v-html="html" />
  </div>
</template>

<style scoped>
.an { margin: 22px 0; display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.25fr); gap: 16px; }
ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
li { padding: 10px 12px; border: 1px solid var(--line); border-radius: 10px; cursor: default; background: color-mix(in srgb, var(--surface) 80%, transparent); transition: border-color .2s var(--ease), background .2s var(--ease); }
li.on { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 7%, var(--surface)); }
li b { display: block; font-size: 12.5px; color: var(--accent-ink); font-weight: 400; }
li span { display: block; margin-top: 3px; font-size: 13px; line-height: 1.65; color: var(--ink-2); }
pre { margin: 0; padding: 14px 16px; border-radius: 12px; background: var(--term-bg); color: var(--term-ink); font-family: var(--font-mono); font-size: 11.5px; line-height: 1.7; overflow: auto; border: 1px solid var(--term-line); }
pre :deep(mark) { background: color-mix(in srgb, #9ca4ff 30%, transparent); color: #fff; border-radius: 3px; padding: 0 1px; }
@media (max-width: 800px) { .an { grid-template-columns: 1fr; } }
</style>
