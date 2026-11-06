<script setup lang="ts">
// Long-form sections after the film: the stage map, who decides what, how gates
// work, the two projects so far, and where to start.
import { withBase } from 'vitepress'
import StageFlow from '../components/StageFlow.vue'

const STATUSES = [
  { s: 'PASS', d: '全部检查满足冻结门限', act: '写阶段日志，进入下一阶段' },
  { s: 'FAIL', d: '至少一项不满足', act: '复盘根因，改设计或做法后重跑；失败记录保留' },
  { s: 'NOT_RUN', d: '缺产物，或这一阶段还没有检查', act: '补齐产物' },
  { s: 'BLOCKED', d: '外部条件不满足，比如缺 MuJoCo、ffprobe', act: '记录原因，修好环境' },
  { s: 'IDEALIZED', d: '靠理想化才过', act: '永远不算 PASS，必须标明' },
]

const CASES = [
  {
    href: '/cases/slice-01', img: '/img/slice/kf_00525.webp', kicker: '薄切片 01 · 1 个工艺步骤',
    title: '开培养箱取板，送到观察站',
    body: '只做一步，但从需求一路走到成片，用来测出每个阶段的真实成本。仿真阶段返工 14 次，由此催生了运动学预演。',
    stats: [['54.0 s', '连续仿真'], ['13 / 13', '门限 PASS'], ['14', '仿真返工']],
  },
  {
    href: '/cases/full-lab', img: '/img/full/overview.webp', kicker: '全流程实验室 · 14 个工艺步骤',
    title: '细胞传代黑灯实验室',
    body: '从培养箱取母板一直做到子板送回，分 4 期开发再接力连跑。全程由 agent 自主推进，审批点自审。',
    stats: [['911.9 s', '连续仿真'], ['20 / 20', '门限 PASS'], ['10 / 10', '负例抓到']],
  },
]

const PATHS = [
  { href: '/guide/', k: '想先理解流程', t: '一页看懂整个流程', d: '七个阶段怎么接力、你在哪两处出场、验证门怎样判定。大约 15 分钟。' },
  { href: '/skill/', k: '要开一个新项目', t: '开始一个项目', d: '对 Claude Code 说什么、每个阶段你会看到什么、审批时看哪几样。' },
  { href: '/physics/', k: '想搞懂物理那一半', t: '物理实验台', d: '在浏览器里直接跑 MuJoCo：穿透、摩擦、对中、伺服、weld、负例、状态接力。' },
]
</script>

<template>
  <section id="stages" class="pl-section" tabindex="-1">
    <p class="pl-eyebrow pl-rule"><span>七个阶段</span></p>
    <div class="pl-section-head">
      <h2><span class="nb">每个阶段都要过门，</span><span class="nb">才能交给下一个</span></h2>
      <p class="pl-section-lede">流程是一串固定的阶段。每个阶段有明确的输入和产物，结束时用一条命令判定。上一阶段的产物就是下一阶段的输入，所以哪一步出问题、问题有多大，都能单独看出来。点一个阶段看它的细节。</p>
    </div>
    <StageFlow :initial="0" />
  </section>

  <section class="pl-section">
    <p class="pl-eyebrow pl-rule"><span>谁决定什么</span></p>
    <div class="pl-section-head">
      <h2><span class="nb">你只在三处出场，</span><span class="nb">其余交给 agent</span></h2>
      <p class="pl-section-lede">你决定方向：做什么、不做什么、做到多真、看起来像什么。尺寸、夹具、布局、控制参数这类工程细节由 agent 自己查证、自己决定，写清理由和证据，不拿来问你。</p>
    </div>
    <ol class="moments">
      <li><span class="n mono">开工前</span><h3>确认三张清单</h3><p>场景有哪些区域和设备，流程分几步、每步在哪里由谁做，资产哪些复用、哪些新建。范围大时会有一页范围预览。</p></li>
      <li><span class="n mono">审批点 ①</span><h3>看方案预览</h3><p>布局、设备、工艺步骤、风险，以及运动学预演的结论。这里决定方案的方向对不对。</p></li>
      <li><span class="n mono">审批点 ②</span><h3>看 plan 和参考图</h3><p>门限有没有覆盖你在意的风险，每条关键门限有没有负例，参考图的风格对不对。之后全程自主推进。</p></li>
    </ol>
    <div class="agent-rules">
      <div><h3>卡住时的顺序</h3><p>先重新设计；不行就理想化并如实标注；实在不行标 BLOCKED 继续往下做。门限永不放宽。</p></div>
      <div><h3>只记实测</h3><p>不写时间预估。阶段日志记每个阶段的实测耗时、验证门失败、返工和人工介入。</p></div>
      <div><h3>每步都留档</h3><p>产物同步到 HuggingFace，流程代码和经验进 git。经验记录在项目收尾时写回 skill。</p></div>
    </div>
  </section>

  <section class="pl-section">
    <p class="pl-eyebrow pl-rule"><span>验证门</span></p>
    <div class="pl-section-head">
      <h2><span class="nb">只认事先冻结的数字，</span><span class="nb">不认「看起来没问题」</span></h2>
      <p class="pl-section-lede">验证门是一个脚本：读项目目录里的产物，对照 plan 阶段冻结在 <code>thresholds.json</code> 里的门限，给出五种结果之一，并把判定和证据写进 <code>gates/&lt;阶段&gt;.json</code>。退出码 0 只代表 PASS。</p>
    </div>
    <div class="gates">
      <div class="term wb-term" aria-label="wb gate 的输出示例">
        <div><span class="dim">$</span> uv run --extra sim wb gate cell-passaging-lab simulation</div>
        <div><span class="ok">✅ simulation: PASS</span></div>
        <div>  <span class="ok">✅</span> 名义流程 20 项门限（第 5 期）</div>
        <div>  <span class="ok">✅</span> 负例 N1 去托面 按预期判 FAIL</div>
        <div>  <span class="ok">✅</span> 负例 N2 过插 按预期判 FAIL</div>
        <div class="dim">  …</div>
        <div>  <span class="ok">✅</span> 负例 N10 子板缺位 按预期判 FAIL</div>
        <div>  <span class="ok">✅</span> 渲染用位姿记录</div>
      </div>
      <ul class="statuses">
        <li v-for="x in STATUSES" :key="x.s"><span class="wb-tag" :class="x.s">{{ x.s }}</span><div><b>{{ x.d }}</b><p>{{ x.act }}</p></div></li>
      </ul>
    </div>
    <p class="more"><a :href="withBase('/guide/concepts')">在「核心概念」里亲手试一次判定 →</a></p>
  </section>

  <section class="pl-section">
    <p class="pl-eyebrow pl-rule"><span>两个真实项目</span></p>
    <div class="pl-section-head">
      <h2><span class="nb">流程是从项目里</span><span class="nb">长出来的</span></h2>
      <p class="pl-section-lede">先用只有一步的薄切片把每个阶段走通、记下每处卡点，再提炼成 skill；然后用它做完整的 14 步实验室。教程里的每个数字都来自这两个项目的阶段日志和门限结果。</p>
    </div>
    <div class="cases">
      <a v-for="c in CASES" :key="c.href" class="case" :href="withBase(c.href)">
        <img :src="withBase(c.img)" :alt="c.title" loading="lazy" />
        <div class="cb">
          <p class="k mono">{{ c.kicker }}</p>
          <h3>{{ c.title }}</h3>
          <p class="d">{{ c.body }}</p>
          <dl><div v-for="[v, l] in c.stats" :key="l"><dt class="mono">{{ v }}</dt><dd>{{ l }}</dd></div></dl>
        </div>
      </a>
    </div>
  </section>

  <section class="pl-section last">
    <p class="pl-eyebrow pl-rule"><span>从这里开始</span></p>
    <div class="pl-section-head">
      <h2>按你的目的选一条路</h2>
    </div>
    <div class="paths">
      <a v-for="p in PATHS" :key="p.href" :href="withBase(p.href)"><span class="k mono">{{ p.k }}</span><h3>{{ p.t }}</h3><p>{{ p.d }}</p><span class="go">→</span></a>
    </div>
    <div class="start wb-term">
      <div class="dim"># 在 world-building 仓库里打开 Claude Code，然后说：</div>
      <div><span class="acc">你</span>  用 lab-scene-pipeline 新建一个项目：培养箱取板，送到显微镜拍照</div>
      <div class="dim"># 继续一个已有项目：</div>
      <div><span class="acc">你</span>  继续推进 cell-passaging-lab</div>
    </div>
  </section>
</template>

<style scoped>
.pl-section code { font-family: var(--font-mono); font-size: .88em; padding: 1px 6px; border-radius: 5px; background: var(--surface-2); border: 1px solid var(--line); }
.moments { list-style: none; margin: 48px 0 0; padding: 0; display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.moments li { position: relative; padding: 22px 20px; border: 1px solid var(--line); border-radius: 14px; background: color-mix(in srgb, var(--surface) 74%, transparent); box-shadow: var(--shadow-1); }
.moments li + li::before { content: ''; position: absolute; left: -15px; top: 40px; width: 16px; height: 1px; background: var(--line-2); }
.moments .n { font-size: 11px; color: var(--accent-ink); letter-spacing: .04em; }
.pl .moments h3 { margin-top: 10px; font-size: 22px; }
.moments p { margin-top: 10px; font-size: 14px; line-height: 1.8; color: var(--ink-2); }
.agent-rules { margin-top: 40px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 32px; }
.agent-rules > div { padding-top: 18px; border-top: 1px solid var(--line-2); }
.pl .agent-rules h3 { font-size: 19px; }
.agent-rules p { margin-top: 10px; font-size: 14.5px; line-height: 1.8; color: var(--ink-2); }
.gates { margin-top: 44px; display: grid; grid-template-columns: 1.05fr 1fr; gap: 24px; align-items: start; }
.term div { white-space: pre; }
.statuses { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; }
.statuses li { display: grid; grid-template-columns: 96px 1fr; gap: 14px; padding: 12px 0; border-top: 1px solid var(--line); align-items: start; }
.statuses .wb-tag { margin-top: 2px; justify-self: start; }
.statuses b { font-weight: 500; font-size: 14.5px; color: var(--ink); }
.statuses p { margin-top: 2px; font-size: 13.5px; color: var(--muted); line-height: 1.7; }
.more { margin-top: 18px; font-size: 14px; }
.more a { color: var(--accent-ink); font-weight: 500; }
.cases { margin-top: 44px; display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.case { display: flex; flex-direction: column; border: 1px solid var(--line); border-radius: 16px; overflow: hidden; background: var(--surface); box-shadow: var(--shadow-1); transition: transform .25s var(--ease), border-color .25s var(--ease); }
.case:hover { transform: translateY(-2px); border-color: var(--line-2); }
.case img { width: 100%; aspect-ratio: 16 / 8; object-fit: cover; display: block; background: #e7e5df; }
.cb { padding: 22px 24px 24px; }
.k { font-size: 11px; color: var(--faint); letter-spacing: .04em; }
.pl .case h3 { margin-top: 8px; font-size: 24px; }
.d { margin-top: 10px; font-size: 14.5px; line-height: 1.8; color: var(--ink-2); }
.case dl { margin: 18px 0 0; display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.case dt { font-size: 20px; color: var(--ink); }
.case dd { margin: 2px 0 0; font-size: 12px; color: var(--muted); }
.paths { margin-top: 40px; display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; }
.paths a { position: relative; padding: 22px 22px 46px; border: 1px solid var(--line); border-radius: 14px; background: color-mix(in srgb, var(--surface) 80%, transparent); box-shadow: var(--shadow-1); transition: border-color .25s var(--ease), transform .25s var(--ease); }
.paths a:hover { border-color: var(--accent); transform: translateY(-2px); }
.paths .k { color: var(--accent-ink); }
.pl .paths h3 { margin-top: 8px; font-size: 21px; }
.paths p { margin-top: 8px; font-size: 14px; line-height: 1.75; color: var(--ink-2); }
.go { position: absolute; left: 22px; bottom: 16px; color: var(--accent-ink); }
.start { margin-top: 20px; }
.start div { white-space: pre-wrap; }
.last { padding-bottom: 140px; }
@media (max-width: 1000px) {
  .moments, .agent-rules, .paths { grid-template-columns: 1fr; }
  .moments li + li::before { display: none; }
  .gates, .cases { grid-template-columns: 1fr; }
}
</style>
