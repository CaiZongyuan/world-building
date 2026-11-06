<script setup lang="ts">
import { ref } from 'vue'

const CELLS = [
  { r: '名义流程', c: 'PASS', good: true, h: '动作成立', d: '按设计正常跑，门限全部通过。这是我们要的结果。', ex: '全流程实验室：20 项门限全 PASS，最大穿透 0.219 mm。' },
  { r: '名义流程', c: 'FAIL', good: false, h: '设计有问题：改设计', d: '先复盘找根因，再改设计或做法后重跑。门限不动，失败记录保留。', ex: '配平管放回侧架 S3 = 2.04 mm → weld 改挂管身、杯壁间隙放到 3 mm → 0.20 mm。' },
  { r: '负例', c: 'PASS', good: false, h: '门限或负例无效', d: '故意做错了，门限却没抓到：要么测量写错了，要么这个「错」根本不危险。先做危险探针。', ex: 'N6 v1 分液偏 10 mm：孔半径 17.4 mm，吸头仍在孔里，S18 判 PASS。' },
  { r: '负例', c: 'FAIL', good: true, h: '抓到了', d: '门限确实能分辨对错。仿真验证门要求每个负例都落在这一格。', ex: 'N4 工作站门没开就伸手：S4 禁止接触判 FAIL。' },
]
const sel = ref(2)
</script>

<template>
  <div class="nm vp-raw">
    <div class="grid">
      <span />
      <span class="hd">门限判 PASS</span>
      <span class="hd">门限判 FAIL</span>
      <template v-for="row in ['名义流程', '负例']" :key="row">
        <span class="rh">{{ row }}</span>
        <button v-for="(c, i) in CELLS.filter((x) => x.r === row)" :key="c.c" type="button" class="cell" :class="{ good: c.good, bad: !c.good, on: CELLS.indexOf(c) === sel }" @click="sel = CELLS.indexOf(c)">
          <b>{{ c.good ? '✓' : '✗' }} {{ c.h }}</b>
        </button>
      </template>
    </div>
    <div class="det wb-panel">
      <p class="h">{{ CELLS[sel].r }} × 门限判 {{ CELLS[sel].c }}：{{ CELLS[sel].h }}</p>
      <p>{{ CELLS[sel].d }}</p>
      <p class="ex">项目里的例子：{{ CELLS[sel].ex }}</p>
    </div>
  </div>
</template>

<style scoped>
.nm { margin: 22px 0; display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 16px; align-items: stretch; }
.grid { display: grid; grid-template-columns: 76px 1fr 1fr; gap: 6px; align-items: stretch; }
.hd { font-size: 12px; color: var(--muted); text-align: center; align-self: end; }
.rh { font-size: 13px; color: var(--ink-2); align-self: center; }
.cell { min-height: 74px; padding: 10px; border-radius: 10px; border: 1px solid var(--line); cursor: pointer; text-align: left; font-family: var(--font-ui); transition: all .2s var(--ease); }
.cell b { font-size: 13.5px; font-weight: 500; }
.cell.good { background: color-mix(in srgb, var(--ok) 9%, transparent); color: var(--ok); }
.cell.bad { background: color-mix(in srgb, var(--bad) 8%, transparent); color: var(--bad); }
.cell.on { border-color: currentColor; box-shadow: 0 0 0 2px color-mix(in srgb, currentColor 20%, transparent); }
.det { padding: 14px 16px; }
.det p { margin: 0 0 8px; font-size: 13.5px; line-height: 1.75; color: var(--ink-2); }
.det .h { font-weight: 500; color: var(--ink); }
.det .ex { color: var(--muted); font-size: 13px; margin: 0; }
@media (max-width: 800px) { .nm { grid-template-columns: 1fr; } }
</style>
