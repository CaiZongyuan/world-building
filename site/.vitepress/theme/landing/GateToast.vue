<script setup lang="ts">
import { computed } from 'vue'
import { toastAt } from './story'

const props = defineProps<{ t: number }>()
const g = computed(() => toastAt(props.t))
</script>

<template>
  <div v-if="g && g.o > 0.01" class="gt pl-panel" :class="g.kind" :style="{ opacity: g.o, transform: `translateY(${(1 - g.o) * 10}px) scale(${0.98 + 0.02 * g.o})` }" role="status">
    <div class="pl-panel-head">
      <span v-if="g.kind === 'approve'" class="who"><svg viewBox="0 0 16 16"><path d="M8 1.8 13 3.6v4c0 3.1-2.1 5.4-5 6.6-2.9-1.2-5-3.5-5-6.6v-4z" /></svg>审批点 {{ g.n === 1 ? '①' : '②' }} · 你出场</span>
      <span v-else class="who">验证门</span>
      <span v-if="g.kind === 'approve'">{{ g.pressed ? '已批准' : '待审批' }}</span>
      <span v-else class="verdict">{{ g.kind === 'pass' ? 'PASS' : 'FAIL' }}</span>
    </div>
    <div class="pl-panel-body">
      <p class="title">{{ g.title }}</p>
      <p class="meta">{{ g.meta }}</p>
      <div v-if="g.kind === 'approve'" class="actions">
        <span class="b">提意见</span>
        <span class="b primary" :class="{ pressed: g.pressed }">{{ g.pressed ? '已批准' : '批准' }}<svg v-if="g.pressed" viewBox="0 0 12 12"><path d="M2.5 6.2 5 8.6l4.6-5" /></svg></span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.gt { width: 330px; }
.gt.approve { border-color: color-mix(in srgb, var(--accent) 45%, var(--line)); }
.gt.pass { border-color: color-mix(in srgb, var(--ok) 40%, var(--line)); }
.gt.fail { border-color: color-mix(in srgb, var(--bad) 45%, var(--line)); }
.who { display: inline-flex; align-items: center; gap: 6px; color: var(--accent-ink); }
.who svg { width: 13px; height: 13px; fill: none; stroke: currentColor; stroke-width: 1.4; }
.pass .who, .pass .verdict { color: var(--ok); }
.fail .who, .fail .verdict { color: var(--bad); }
.title { font-size: 14px; color: var(--ink); font-weight: 500; font-family: var(--font-mono); }
.approve .title { font-family: var(--font-ui); }
.meta { margin-top: 4px; font-size: 12px; line-height: 1.6; color: var(--muted); }
.actions { display: flex; justify-content: flex-end; gap: 8px; margin-top: 12px; }
.b { display: inline-flex; align-items: center; gap: 6px; height: 28px; padding: 0 12px; border-radius: 7px; border: 1px solid var(--line-2); font-size: 12.5px; color: var(--muted); }
.b.primary { background: var(--ink); border-color: var(--ink); color: var(--ground); transition: transform .15s var(--ease), background .2s var(--ease); }
.b.primary.pressed { background: var(--ok); border-color: var(--ok); color: var(--ground); transform: scale(.97); }
.b svg { width: 11px; height: 11px; fill: none; stroke: currentColor; stroke-width: 1.8; stroke-linecap: round; }
</style>
