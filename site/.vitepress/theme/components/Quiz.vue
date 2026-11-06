<script setup lang="ts">
import { computed, ref } from 'vue'

const Q: [string, string[], number, string][] = [
  ['用户在整个流程里必须出场的两个审批点是？', ['需求访谈后、仿真后', '方案预览后、参考图（连同 plan）后', '建模后、渲染后', '每个阶段之后'], 1, '另外开工前要确认三张清单。审批点②之后，建模、仿真、渲染由 agent 自主推进。'],
  ['「这个工作站台面该多高」应该由谁决定？', ['用户在审批点决定', 'agent 查证后自己决定，写清理由和证据', '等仿真失败了再说', '照搬旧项目'], 1, '尺寸、夹具、布局这类工程细节是 agent 的事，写进方案页的「工程决策」。'],
  ['一个阶段怎样才算完成？', ['agent 觉得没问题', '产物齐了', 'wb gate 判 PASS，并写好阶段日志和经验记录', '用户说好'], 2, '四件事：阶段说明、产物、验证门 PASS、阶段日志与经验记录。'],
  ['门限判 FAIL 后，正确的做法是？', ['把门限放宽到刚好通过', '改设计或做法后重跑', '删掉这条门限', '标成 IDEALIZED 当作通过'], 1, '门限冻结后只改设计；IDEALIZED 永远不算 PASS；失败记录保留。'],
  ['负例跑出来判 PASS，说明什么？', ['设计很好', '门限或负例无效，要做危险探针', '仿真出错了，忽略即可', '应该把门限收紧'], 1, '负例必须判 FAIL。N6 v1 就是危险不存在，改负例而不改门限。'],
  ['薄切片 01 仿真阶段 14 次返工里，9 次本可以在哪里发现？', ['渲染阶段', '用很便宜的运动学检查，在建模之前', '需求访谈', '永远发现不了'], 1, '于是在方案预览里加了运动学预演（wb preflight）。'],
  ['板放到托面上，S3 测到 0.6 mm。最可能的原因是？', ['板太重', '从高处松手或接触太软', '摩擦系数太小', '时间步长太小'], 1, '软接触在撞击瞬间必然陷入；默认 solref 0.02 时，即使只从 0.3 mm 高松手也会到 0.59 mm。'],
  ['为什么板和盖不允许用 weld 搬运？', ['weld 太慢', '那样就证明不了夹持在物理上成立', 'MuJoCo 不支持', '会影响渲染'], 1, 'S11 规定大件只能靠接触和摩擦；weld 只给几克重的小件，并且受 S14、S15 约束。'],
  ['分期仿真时，只存 qpos 和 qvel 有什么风险？', ['没有风险', '漏掉执行器指令、约束参数等，接起来和一次跑完不等价', '文件太大', '渲染会出错'], 1, '项目里出过龙门不在零位、约束名缺失、被动设备指令回零三个问题。'],
  ['成片默认用什么画质？', ['1080p、128 spp 展示级', 'draft：720p、16 spp、降噪', 'EEVEE', '随便'], 1, '成片是给工程审阅看动作和干涉的。展示级只在用户明确要求时用。'],
  ['项目中断了，第二天怎么接着做？', ['重新开一个项目', '对 Claude Code 说「继续推进 <项目>」', '手动改 stage-log', '删掉 gates/'], 1, 'skill 会先读 stage-log.md 和 gates/*.json，从第一个没 PASS 的阶段接着做。'],
]
const ans = ref<(number | null)[]>(Q.map(() => null))
const done = computed(() => ans.value.filter((a) => a !== null).length)
const right = computed(() => ans.value.filter((a, i) => a === Q[i][2]).length)
function pick(i: number, j: number) { if (ans.value[i] === null) ans.value[i] = j }
</script>

<template>
  <div class="qz vp-raw">
    <p class="score">{{ done ? `已答 ${done} / ${Q.length}，答对 ${right}` : `共 ${Q.length} 题，点选项作答，答完立即显示解析。` }}</p>
    <div v-for="(q, i) in Q" :key="i" class="q wb-panel">
      <p class="t">{{ i + 1 }}. {{ q[0] }}</p>
      <div class="opts"><button v-for="(o, j) in q[1]" :key="j" type="button" :class="{ right: ans[i] !== null && j === q[2], wrong: ans[i] === j && j !== q[2] }" :disabled="ans[i] !== null" @click="pick(i, j)">{{ o }}</button></div>
      <p v-if="ans[i] !== null" class="why">{{ ans[i] === q[2] ? '✓ ' : '✗ ' }}{{ q[3] }}</p>
    </div>
  </div>
</template>

<style scoped>
.qz { margin: 20px 0; display: flex; flex-direction: column; gap: 10px; }
.score { margin: 0; font-size: 14px; color: var(--muted); }
.q { padding: 14px 16px; }
.t { margin: 0 0 10px; font-size: 14.5px; color: var(--ink); font-weight: 500; }
.opts { display: grid; grid-template-columns: 1fr 1fr; gap: 6px; }
.opts button { text-align: left; padding: 8px 12px; border-radius: 8px; border: 1px solid var(--line-2); background: var(--surface); color: var(--ink-2); font-size: 13.5px; cursor: pointer; font-family: var(--font-ui); line-height: 1.5; }
.opts button:hover:not(:disabled) { border-color: var(--accent); }
.opts button:disabled { cursor: default; }
.opts button.right { border-color: var(--ok); background: color-mix(in srgb, var(--ok) 12%, transparent); color: var(--ok); }
.opts button.wrong { border-color: var(--bad); background: color-mix(in srgb, var(--bad) 10%, transparent); color: var(--bad); }
.why { margin: 10px 0 0; font-size: 13.5px; line-height: 1.7; color: var(--ink-2); }
@media (max-width: 640px) { .opts { grid-template-columns: 1fr; } }
</style>
