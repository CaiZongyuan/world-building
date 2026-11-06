<script setup lang="ts">
// Slice 01 retro: stages ranked by how much trouble they caused (stage-log.md).
const R = [
  { s: '仿真', wall: '约 1.5 h', fail: '名义流程 7 次 + 1 个负例失效', rework: 14, note: '几何、布局、控制、数值四类问题叠在一起' },
  { s: '建模', wall: '约 0.5 h', fail: '0', rework: 2, note: '仿真阶段又追加 3 次指具修订；设计问题到「干涉核查」时才暴露' },
  { s: '位姿绑定与渲染', wall: '0.3 h + 全片 16.3 min', fail: '0', rework: 4, note: '一开始用展示级档位，每帧约 13.5 s；改 draft 后约 0.55 s' },
  { s: '方案预览', wall: '约 0.2 h', fail: '1', rework: 0, note: '事实核查推翻了 2 个需求推荐（用户反馈 2 轮）' },
  { s: '需求 / plan / 参考图', wall: '各 0.1–0.5 h', fail: '0', rework: 0, note: '很顺利' },
]
</script>

<template>
  <div class="rb vp-raw">
    <div v-for="(r, i) in R" :key="r.s" class="row" :class="{ top: i === 0 }">
      <span class="n wb-mono">{{ i + 1 }}</span>
      <div class="main">
        <div class="h"><b>{{ r.s }}</b><span class="wb-mono">{{ r.wall }} · 门失败 {{ r.fail }}</span></div>
        <div class="bar"><i :style="{ width: Math.max(1.5, (r.rework / 14) * 100) + '%' }" /><span class="wb-mono">返工 {{ r.rework }}</span></div>
        <p>{{ r.note }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.rb { margin: 20px 0; display: flex; flex-direction: column; gap: 10px; }
.row { display: grid; grid-template-columns: 28px 1fr; gap: 12px; padding: 12px 14px; border: 1px solid var(--line); border-radius: 12px; background: color-mix(in srgb, var(--surface) 80%, transparent); }
.row.top { border-color: color-mix(in srgb, var(--bad) 45%, var(--line)); }
.n { font-size: 18px; color: var(--faint); }
.h { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; }
.h b { font-size: 15px; color: var(--ink); font-weight: 500; }
.h span { font-size: 12px; color: var(--muted); }
.bar { margin-top: 6px; display: flex; align-items: center; gap: 8px; }
.bar i { display: block; height: 8px; border-radius: 4px; background: var(--ghost); }
.top .bar i { background: var(--bad); }
.bar span { font-size: 12px; color: var(--ink-2); white-space: nowrap; }
p { margin: 6px 0 0; font-size: 13px; color: var(--muted); line-height: 1.65; }
</style>
