<script setup lang="ts">
// A worked conversation with the skill, message by message. It is an illustration
// written from what the two real projects did; every behaviour shown is in SKILL.md.
import { computed, ref } from 'vue'

interface Msg { who: 'you' | 'agent' | 'tool'; text: string; stage?: string; note?: string }
const SCRIPT: Msg[] = [
  { stage: '开场', who: 'you', text: '用 lab-scene-pipeline 新建一个项目：培养箱取板，送到显微镜拍照，再放回培养箱。', note: '一句话就够。不用先想尺寸、夹爪、布局，那些是 agent 的事。' },
  { who: 'tool', text: 'uv run wb new projects/plate-imaging --title "培养箱取板拍照"' },
  { stage: '01 需求访谈', who: 'agent', text: '阶段 1 需求访谈。输入是你这句话和现有资产；我分轮提问，只问会改变方案的决定；完成判据是 requirements.md 六节齐全、wb gate requirements 判 PASS。最可能的问题：资产说明和实际不符。', note: '每个阶段开始前，agent 都会先给一段这样的「阶段说明」。' },
  { who: 'agent', text: '我先让子代理实查了资产：培养箱、六孔板、Panda 能编译；显微镜没有现成资产，要新建。\nQ1 范围只做取板 → 拍照 → 放回三步？推荐：是。\nQ2 显微镜载物台由执行器驱动，不让机械臂去推？推荐：是，这样去掉一整类接触难点。\nQ3 全部真实物理，不做液体？推荐：是。\nQ4 成片不加速、不剪辑，draft 画质？推荐：是。', note: '每问都带推荐答案，回「按推荐」就等于全部接受。能查到的事实，它不会来问你。' },
  { who: 'you', text: '都按推荐。' },
  { who: 'agent', text: '开工前请确认三张清单：\n场景：培养箱、显微镜、导轨机械臂，共 3 个区域；\n流程：开门取板 → 送显微镜 → 拍照 → 取回 → 放回 → 关门，每步写明在哪、谁做、搬什么；\n资产：复用 4 项（附实查结果），新建 1 项（显微镜）。', note: '这是你第一次需要认真看的地方：范围对不对、有没有漏掉的设备或步骤。' },
  { who: 'you', text: '确认。' },
  { who: 'tool', text: 'wb gate plate-imaging requirements  →  ✅ PASS' },
  { stage: '02 方案预览', who: 'agent', text: '运动学预演 v1：9 项里 2 项失败。显微镜载物台太高，取放位姿 IK 无解；外门扫到导轨。把台面降低、培养箱挪到导轨末端后，v2 全部通过。结论写进方案页的「工程决策」。', note: '尺寸、台高、夹具这类工程决定 agent 自己做，写清理由和证据，不拿来问你。' },
  { who: 'tool', text: 'wb publish plate-imaging  →  proposals/plate-imaging/index.html' },
  { who: 'agent', text: '方案预览已发布，请审批（审批点①）。重点看：布局、预演结论、每台设备复用还是新建、风险表。' },
  { who: 'you', text: '批准。', note: '审批点①。有意见就直接说，agent 改完重新发布。' },
  { stage: '03 plan + 04 参考图', who: 'agent', text: 'plan 已写好：门限 S1–S13 冻结在 thresholds.json；负例 N1 去托面、N2 过插、N3 夹取高度偏高，每个都先做过危险探针。显微镜参考图 4 张，与设计不一致的两处已逐张注明。审批页由 wb review 生成，请一起审（审批点②）。' },
  { who: 'you', text: '批准。之后不用再问我了。', note: '审批点②是你最后一次必须出场。之后 agent 全程自主推进。' },
  { stage: '05–07 自主推进', who: 'agent', text: '收到。建模、仿真、渲染自主推进。卡住时按「改设计 → 理想化并标注 → 标 BLOCKED 继续」的顺序处理，门限不放宽。' },
  { who: 'tool', text: 'wb gate plate-imaging modelling  →  ✅ PASS（M1–M6）' },
  { who: 'agent', text: '仿真第 1 次：S7 FAIL，松爪前支撑力为 0。板的支撑点在孔底不在板裙，我按板裙高度放，板悬在托面上方 1.1 mm 就松了爪。改成按板的实际静止高度放置后重跑：S1–S13 全部 PASS，N1–N3 都按预期判 FAIL。', note: 'FAIL 是常态。你会在阶段日志里看到每次失败、根因和改法。' },
  { who: 'you', text: '现在进展到哪了？给我看看。', note: '中途随时可以问。大项目开发中不渲成片，只渲关键帧拼成进展图。' },
  { who: 'agent', text: '仿真已 PASS，正在渲染：draft 档位（720p、16 spp），先渲了 4 帧确认曝光和机位。进展图：progress/phase1.webp。' },
  { who: 'tool', text: 'wb gate plate-imaging render  →  ✅ PASS（V1–V4）' },
  { stage: '收尾', who: 'agent', text: '交付：成片、学习页、阶段日志。按日志排序，问题最大的是仿真阶段（返工 3 次，都是放置高度）。经验已写回 docs/lessons/06-simulation.md 和 SKILL.md。', note: '每个项目结束，流程本身都会更新一点。' },
  { stage: '另一天', who: 'you', text: '继续推进 plate-imaging', note: '项目中断后，用这句话接着做。' },
  { who: 'agent', text: '已读 stage-log.md 和 gates/*.json：前 5 个阶段 PASS，仿真最近一次 FAIL（S3）。从仿真阶段接着做。' },
]

const n = ref(4)
const shown = computed(() => SCRIPT.slice(0, n.value))
const done = computed(() => n.value >= SCRIPT.length)
function next() { if (!done.value) n.value++ }
function all() { n.value = SCRIPT.length }
function restart() { n.value = 1 }
</script>

<template>
  <div class="cr vp-raw wb-panel">
    <div class="head"><span class="wb-eyebrow">示意对话 · 按两个真实项目的做法编写</span><span class="wb-mono cnt">{{ n }} / {{ SCRIPT.length }}</span></div>
    <TransitionGroup name="cr" tag="ol" class="msgs">
      <li v-for="(m, i) in shown" :key="i" :class="m.who">
        <p v-if="m.stage" class="stage"><span>{{ m.stage }}</span></p>
        <div class="row">
          <span class="who">{{ m.who === 'you' ? '你' : m.who === 'agent' ? '◆' : '$' }}</span>
          <div class="bubble">{{ m.text }}</div>
        </div>
        <p v-if="m.note" class="note">{{ m.note }}</p>
      </li>
    </TransitionGroup>
    <div class="ctl">
      <button type="button" class="wb-btn wb-btn--primary" :disabled="done" @click="next">下一条 ↓</button>
      <button type="button" class="wb-btn" :disabled="done" @click="all">全部展开</button>
      <button type="button" class="wb-btn" @click="restart">从头看</button>
    </div>
  </div>
</template>

<style scoped>
.cr { margin: 22px 0; padding: 14px 16px 16px; }
.head { display: flex; justify-content: space-between; align-items: center; }
.cnt { font-size: 11.5px; color: var(--faint); }
.msgs { list-style: none; margin: 12px 0 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
.stage { margin: 8px 0 6px; display: flex; align-items: center; gap: 10px; font-size: 11.5px; color: var(--accent-ink); font-family: var(--font-mono); }
.stage::after { content: ''; flex: 1; height: 1px; background: var(--line); }
.row { display: grid; grid-template-columns: 24px 1fr; gap: 10px; align-items: start; }
.who { display: grid; place-items: center; width: 22px; height: 22px; border-radius: 6px; font-size: 11px; font-family: var(--font-mono); background: var(--surface-2); color: var(--accent); border: 1px solid var(--line); }
.you .who { background: var(--ink); color: var(--ground); border-color: var(--ink); }
.bubble { white-space: pre-line; font-size: 14px; line-height: 1.75; color: var(--ink-2); padding: 8px 12px; border-radius: 10px; background: color-mix(in srgb, var(--surface-2) 70%, transparent); border: 1px solid var(--line); }
.you .bubble { background: color-mix(in srgb, var(--accent) 8%, var(--surface)); border-color: color-mix(in srgb, var(--accent) 25%, var(--line)); color: var(--ink); font-weight: 500; }
.tool .bubble { font-family: var(--font-mono); font-size: 12px; background: var(--term-bg); color: var(--term-ink); border-color: var(--term-line); padding: 6px 12px; }
.note { margin: 4px 0 0 34px; font-size: 12.5px; color: var(--warn); line-height: 1.6; }
.note::before { content: '↳ '; }
.ctl { margin-top: 14px; display: flex; gap: 8px; flex-wrap: wrap; }
.cr-enter-active { transition: opacity .35s var(--ease), transform .35s var(--ease); }
.cr-enter-from { opacity: 0; transform: translateY(8px); }
</style>
