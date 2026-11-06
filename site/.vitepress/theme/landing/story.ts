// The landing storyboard. One project (the 14-step cell-passaging lab) runs the
// whole pipeline on one clock `t` in seconds. Every overlay and every 3D pose is a
// pure function of `t`, so scrolling either way, jumping to a chapter and
// autoplay all agree. Numbers come from the project's stage-log and gates.

export interface Chapter {
  id: string
  n: string
  kicker: string
  title: string
  body: string
  start: number
  end: number
  key: number
  stage: number
}

export const CHAPTERS: Chapter[] = [
  { id: 'req', n: '01', stage: 1, kicker: '需求访谈', title: '先把需求问到\n没有隐含假设', body: '你只说一句话。agent 分轮追问会改变方案的决定：范围、执行者、保真度、算力预算，每问都附推荐答案。然后把场景、流程、资产三张清单摊开给你确认。', start: 0, end: 9, key: 7.8 },
  { id: 'proposal', n: '02', stage: 2, kicker: '方案预览', title: '开工之前，\n先用方盒摆一遍', body: '设备、工件、夹具全部换成方盒代理，尺寸取自真实资产。多初值 IK 解出每个取放位姿，再扫一遍门和机械臂的运动范围。第一版布局 33 项里 11 项失败，改两轮后 57 项全部通过，然后交给你审批。', start: 9, end: 20, key: 18.4 },
  { id: 'plan', n: '03', stage: 3, kicker: 'plan', title: '把「成立」写成数字，\n然后冻结', body: '每条风险对应一条带编号的门限：穿透 ≤ 0.25 mm、放置误差 ≤ 3 mm、机器人碰到设备 0 次……每条关键门限再配一个故意做错的负例。写进 thresholds.json 以后，只改设计，不改门限。', start: 20, end: 28, key: 26.6 },
  { id: 'reference', n: '04', stage: 4, kicker: '参考图', title: '参考图只定风格，\n尺寸另有来源', body: '新建的部件先生成参考图，冻结外观；尺寸写进尺寸表，每一项标明来自标准锚点、设计假设还是实测；再画一条从工件到地面的载荷链。plan 和参考图一起交给你审批。', start: 28, end: 34, key: 32.8 },
  { id: 'modelling', n: '05', stage: 5, kicker: '建模', title: '一个参数源，\n两份模型', body: 'design.py 是唯一的参数源：Blender 读它建视觉模型，MJCF 读它建物理模型。视觉可以精细，碰撞只留方盒、圆柱这类基本形状和功能面，靠 VIS_ / COL_ 命名分开。', start: 34, end: 42, key: 37.6 },
  { id: 'simulation', n: '06', stage: 6, kicker: '仿真', title: '让物理引擎\n来证明动作成立', body: '控制器只给电机下目标，板、盖、管怎么动，全由 MuJoCo 按重力、接触、摩擦算出来。名义流程的门限必须全部 PASS，每个负例必须判 FAIL。这是问题最多的阶段。', start: 42, end: 56, key: 46.4 },
  { id: 'render', n: '07', stage: 7, kicker: '渲染', title: '画面只照抄仿真，\n不加一帧手调', body: 'MuJoCo 记下每个刚体每一帧的位姿，Blender 里的视觉模型逐帧照抄。成片默认 draft 画质，不加速、不剪辑，帧数必须等于仿真时长 × 30。', start: 56, end: 64, key: 61.6 },
  { id: 'retro', n: '08', stage: 8, kicker: '复盘', title: '每个项目，\n都让流程本身更好', body: '阶段日志只记实测：耗时、验证门失败、返工。项目收尾时按它给阶段排序，找出问题最大的一段，经验写回 docs/lessons 和 skill。下一个项目从更好的流程开始。', start: 64, end: 72, key: 69.5 },
]

export const DURATION = 72

export const HERO = {
  eyebrow: 'World Building · lab-scene-pipeline',
  title: ['从一句需求，', '到一段经过', '物理验证的成片'],
  lede: '这是一条把实验室场景从需求做到可仿真、可渲染三维场景的固定流程。下面用一个真实项目，带你把七个阶段从头走一遍：每一步做什么、产出什么、怎样判定做完了，以及你需要在哪两处出场。',
}

export function chapterAt(t: number): Chapter {
  for (const c of CHAPTERS) if (t < c.end) return c
  return CHAPTERS[CHAPTERS.length - 1]
}

export function chapterIndex(t: number): number {
  return CHAPTERS.indexOf(chapterAt(t))
}

export const clamp = (v: number, a = 0, b = 1) => Math.min(b, Math.max(a, v))
export const lerp = (a: number, b: number, s: number) => a + (b - a) * s
export const smooth = (s: number) => { s = clamp(s); return s * s * (3 - 2 * s) }
export const ramp = (t: number, a: number, b: number) => smooth((t - a) / (b - a))
/** 0 → 1 over [a, a + fade], holds, 1 → 0 over [b - fade, b]. */
export const window01 = (t: number, a: number, b: number, fade = 0.4) =>
  Math.min(ramp(t, a, a + fade), 1 - ramp(t, b - fade, b))

// ---- Console -----------------------------------------------------------------

export type LineKind = 'human' | 'agent' | 'cmd' | 'out' | 'alert' | 'gate' | 'good' | 'bad'

export interface Line { t: number; kind: LineKind; text: string; type?: number }

export const CONSOLE: Line[] = [
  { t: 0.8, kind: 'human', text: '用 lab-scene-pipeline 新建项目：细胞传代黑灯实验室，14 步全部做进一个场景', type: 2.4 },
  { t: 3.5, kind: 'cmd', text: 'uv run wb new projects/cell-passaging-lab --title "细胞传代黑灯实验室"' },
  { t: 4.2, kind: 'agent', text: 'Q3 小件（吸头、管、盖）怎么夹？推荐：weld 理想化，由门限盯住' },
  { t: 5.1, kind: 'human', text: '按推荐', type: 0.5 },
  { t: 5.8, kind: 'agent', text: '三张清单：场景 5 区 · 流程 14 步 · 资产 16 项（逐项实查能否编译）' },
  { t: 7.0, kind: 'cmd', text: 'wb gate cell-passaging-lab requirements' },
  { t: 7.5, kind: 'good', text: 'requirements: PASS · 六节齐全' },
  { t: 9.6, kind: 'agent', text: '设备换成方盒代理，尺寸取自真实资产' },
  { t: 10.6, kind: 'cmd', text: 'wb preflight 02-proposal/analysis/preflight.json' },
  { t: 12.0, kind: 'bad', text: 'v1：11 / 33 失败 · 培养箱外门扫过导轨' },
  { t: 13.6, kind: 'agent', text: '改布局：培养箱挪到导轨末端、外门往外侧开；离心台挪近 0.10 m' },
  { t: 16.2, kind: 'good', text: 'v3：57 / 57 通过' },
  { t: 17.0, kind: 'cmd', text: 'wb publish cell-passaging-lab' },
  { t: 18.2, kind: 'gate', text: '审批点①：方案预览已批准' },
  { t: 20.6, kind: 'agent', text: '每条风险对应一条门限，每条关键门限配一个负例' },
  { t: 22.2, kind: 'out', text: 'thresholds.json · 门限 S1–S21 · 负例 N1–N10' },
  { t: 23.8, kind: 'agent', text: 'N6 v1 偏 10 mm 吸头仍在孔里，危险不存在：改成偏 20 mm' },
  { t: 26.0, kind: 'good', text: 'plan: PASS · 门限已冻结' },
  { t: 28.6, kind: 'cmd', text: 'imagegen × 6（并行）→ 04-reference/board/*.webp' },
  { t: 30.0, kind: 'out', text: 'dimensions.md：每项标来源 · 标准锚点 / 设计假设 / 实测' },
  { t: 31.4, kind: 'cmd', text: 'wb review cell-passaging-lab' },
  { t: 32.6, kind: 'gate', text: '审批点②：plan + 参考图已批准' },
  { t: 34.6, kind: 'cmd', text: 'python 05-modelling/design.py' },
  { t: 35.6, kind: 'cmd', text: 'blender -b --python build_blender.py   # ROOT_ / VIS_ / COL_' },
  { t: 36.8, kind: 'cmd', text: 'python build_mjcf.py' },
  { t: 38.6, kind: 'alert', text: 'M5 静置：圆柱管压圆柱座只有一个接触点，管会倒 → 改方垫 + 杯壁' },
  { t: 40.8, kind: 'good', text: 'modelling: PASS · M1–M7' },
  { t: 42.6, kind: 'agent', text: '先做运动学初筛，再跑动力学' },
  { t: 43.6, kind: 'cmd', text: 'python 06-simulation/run_full.py' },
  { t: 47.6, kind: 'bad', text: 'S3 = 2.04 mm  FAIL · 配平管放回侧架时撞上杯壁' },
  { t: 49.0, kind: 'agent', text: '根因：weld 链里最轻的盖偏得最多 → 手直接约束管身' },
  { t: 51.0, kind: 'good', text: '名义流程 20 / 20 PASS · 连续仿真 911.9 s' },
  { t: 52.4, kind: 'cmd', text: 'run 负例 N1–N10' },
  { t: 54.2, kind: 'good', text: '10 / 10 按预期判 FAIL：门限真能抓到错' },
  { t: 55.2, kind: 'good', text: 'simulation: PASS' },
  { t: 56.6, kind: 'cmd', text: 'build_render_scene.py   # 每个视觉根 = 一个 body' },
  { t: 57.8, kind: 'cmd', text: 'render_frames.py --quality draft   # 720p · 16 spp' },
  { t: 60.4, kind: 'out', text: '期 1 成片：3 226 帧 = 107.5 s × 30，V3 位姿误差 0' },
  { t: 62.4, kind: 'good', text: 'render: PASS · V1–V4' },
  { t: 64.6, kind: 'agent', text: '按阶段日志排序：仿真返工最多' },
  { t: 66.2, kind: 'cmd', text: '写回 docs/lessons/06-simulation.md 与 SKILL.md' },
  { t: 68.4, kind: 'good', text: '下一个项目，从更好的流程开始' },
]

export interface VisibleLine extends Line { shown: string; age: number; typing: boolean }

export function consoleAt(t: number, limit = 7): VisibleLine[] {
  const out: VisibleLine[] = []
  for (const l of CONSOLE) {
    if (l.t > t) break
    const age = t - l.t
    let shown = l.text
    let typing = false
    if (l.type) {
      const n = Math.floor(clamp(age / l.type) * l.text.length)
      shown = l.text.slice(0, n)
      typing = n < l.text.length
    }
    out.push({ ...l, shown, age, typing })
  }
  return out.slice(-limit)
}

// ---- Project tree --------------------------------------------------------------

export const STAGE_DIRS = [
  { dir: '01-requirements', name: '需求访谈', files: [['preview/index.html', 6.0], ['requirements.md', 6.6]] },
  { dir: '02-proposal', name: '方案预览', files: [['analysis/preflight.json', 10.6], ['analysis/preflight_report.json', 16.2], ['index.html', 17.0]] },
  { dir: '03-plan', name: 'plan', files: [['plan.md', 21.4], ['thresholds.json', 22.2]] },
  { dir: '04-reference', name: '参考图', files: [['board/*.webp', 29.0], ['dimensions.md', 30.0], ['load_path.svg', 30.8], ['index.html', 31.4]] },
  { dir: '05-modelling', name: '建模', files: [['design.py', 34.6], ['lab_visual.glb', 35.8], ['lab_assets.xml', 36.8], ['mapping.json', 37.2]] },
  { dir: '06-simulation', name: '仿真', files: [['run_full.py', 43.6], ['results/*.json', 51.0], ['states_30fps.npz', 55.0]] },
  { dir: '07-render', name: '渲染', files: [['render_scene.blend', 56.6], ['frames/', 57.8], ['film.mp4', 62.0]] },
] as const

/** Gate verdict times per stage index (0-based). */
export const GATE_PASS = [7.5, 16.6, 26.0, 31.8, 40.8, 55.2, 62.4]

export type StageState = 'todo' | 'active' | 'fail' | 'pass'

export function treeAt(t: number) {
  return STAGE_DIRS.map((s, i) => {
    const start = CHAPTERS[i].start
    let state: StageState = 'todo'
    if (t >= GATE_PASS[i]) state = 'pass'
    else if (t >= start + 0.2) state = 'active'
    if (i === 5 && t >= 47.6 && t < 51.0) state = 'fail'
    const files = s.files.filter(([, at]) => t >= at).map(([f, at]) => ({ f, fresh: t - at < 1.4 }))
    return { ...s, i, state, files }
  })
}

// ---- Gate toasts -----------------------------------------------------------------

export interface Toast { a: number; b: number; kind: 'pass' | 'fail' | 'approve'; title: string; meta: string; press?: number; n?: number }

export const TOASTS: Toast[] = [
  { a: 7.4, b: 9.0, kind: 'pass', title: 'wb gate requirements', meta: '需求记录六节齐全：目标、不做什么、工艺步骤、设备、保真度、算力预算' },
  { a: 17.4, b: 19.8, kind: 'approve', n: 1, press: 18.2, title: '方案预览 · 02-proposal/index.html', meta: '8 节 · 预演 57/57 通过 · 工程决策附理由与证据' },
  { a: 25.9, b: 27.6, kind: 'pass', title: 'wb gate plan', meta: '任务可勾选 · 门限编号并冻结 · 没有时间预估' },
  { a: 31.8, b: 34.0, kind: 'approve', n: 2, press: 32.6, title: 'plan + 参考图 · 04-reference/index.html', meta: '20 项门限 · 10 个负例 · 6 张参考图逐张注明差异' },
  { a: 40.7, b: 42.2, kind: 'pass', title: 'wb gate modelling', meta: 'M1–M7：编译、支撑面高度、GLB 无碰撞代理、静置 1 s…' },
  { a: 47.5, b: 50.0, kind: 'fail', title: 'S3 最大穿透 2.04 mm > 0.25 mm', meta: '先复盘、改设计，再重跑；门限不放宽，失败记录保留' },
  { a: 55.1, b: 56.8, kind: 'pass', title: 'wb gate simulation', meta: '名义流程 20 项门限 PASS · 负例 N1–N10 全部按预期 FAIL' },
  { a: 62.3, b: 63.9, kind: 'pass', title: 'wb gate render', meta: 'V1 无碰撞代理 · V2 帧数 · V3 位姿一致 · V4 成片可解码' },
]

export function toastAt(t: number) {
  const k = TOASTS.find((g) => t > g.a - 0.05 && t < g.b + 0.05)
  if (!k) return null
  return { ...k, o: window01(t, k.a, k.b, 0.25), pressed: k.press !== undefined && t >= k.press }
}

// ---- HUD ---------------------------------------------------------------------------

export function hudAt(t: number) {
  const passed = GATE_PASS.filter((g) => t >= g).length
  const approvals = (t >= 18.2 ? 1 : 0) + (t >= 32.6 ? 1 : 0)
  const reworks = [[13.6, 1], [15.0, 2], [24.0, 3], [38.6, 4], [49.0, 5]].filter(([at]) => t >= at).length
  const fails = t >= 47.6 ? 1 : 0
  return { stage: Math.min(7, chapterAt(t).stage), passed, approvals, reworks, fails }
}

// ---- Insight panels -----------------------------------------------------------------

export const SCOPE = {
  scene: ['培养箱', '观察站', '移液工作站', '离心机', '开盖器', '废物托盘', '导轨机械臂'],
  flow: ['取母板', '观察', '送工作站', '去旧液', '加解离液', '收集到管', '离心', '开盖', '重悬', '计数', '接种', '送回培养箱'],
  assets: [['培养箱', '复用 · 实查可编译'], ['离心机', '复用 · 网格按 SHA 补回'], ['导轨', '新建 · 原设想不存在'], ['开盖器', '新建']],
}

/** Preflight versions from 02-proposal/analysis/preflight_log.md. */
export const PREFLIGHT = [
  { v: 'v1', at: 10.8, total: 33, failed: 11, note: '外门扫过导轨 · 管从正上方够不着 · 开盖器挡住偏置指' },
  { v: 'v2', at: 13.8, total: 33, failed: 10, note: '废物箱投放方向写反 · 离心机远 2 cm · 远距离过渡扫到门' },
  { v: 'v3', at: 16.2, total: 57, failed: 0, note: '12 个取放位姿 · 9 个门口过渡点 · 27 段过渡' },
]

export function preflightAt(t: number) {
  let cur = PREFLIGHT[0]
  for (const p of PREFLIGHT) if (t >= p.at) cur = p
  const running = t >= 10.6 && t < 10.8 + 0.6
  return { ...cur, running, show: t >= 10.6 }
}

export const GATES_SHOWN = [
  { id: 'S3', what: '任意接触的最大穿透', v: '≤ 0.25 mm', anchor: 'imager', at: 21.0 },
  { id: 'S4', what: '机器人碰到设备、门、台面', v: '0 次', anchor: 'wsDoor', at: 21.6 },
  { id: 'S8', what: '放置后到目标点的距离', v: '≤ 3 mm', anchor: 'incubator', at: 22.2 },
  { id: 'S14', what: '挂约束前的对准误差', v: '≤ 1 mm', anchor: 'decapper', at: 22.8 },
  { id: 'S16', what: '离心联锁：转动时盖必须关', v: '< 0.5°', anchor: 'centrifuge', at: 23.4 },
  { id: 'S18', what: '吸排液时吸头在开口内', v: '离边 ≥ 2 mm', anchor: 'wsDeck', at: 24.0 },
]

export const NEGATIVES = ['N1 去托面', 'N2 过插', 'N3 夹高 11 mm', 'N4 门没开', 'N5 吸头偏 3 mm', 'N6 分液偏 20 mm', 'N7 夹管偏 5 mm', 'N8 开盖离心', 'N9 配平错孔', 'N10 子板缺位']

export const REFS = [
  { src: 'img/ref/decapper.webp', cap: '开盖器' },
  { src: 'img/ref/tube_holders.webp', cap: '管座' },
  { src: 'img/ref/waste_bin.webp', cap: '废物托盘' },
]

export const DIMS = [
  ['六孔板 127.8 × 85.5 mm', '标准锚点'],
  ['管座杯壁间隙 1 mm', '设计假设'],
  ['工作站 Z 行程 75 mm', '实测'],
]

export const MCHECKS = ['M1 MJCF 能编译，关节范围一致', 'M2 支撑面高度误差 ≤ 1 mm', 'M3 GLB 读回无碰撞代理', 'M4 映射表覆盖全部部件', 'M5 静置 1 s 无穿透', 'M6 夹具开口覆盖工件', 'M7 执行器清单齐全']

/** Live S3 penetration (mm) in the simulation chapter, for the gauge. */
export function penAt(t: number) {
  if (t < 43.6) return 0
  const base = 0.05 + 0.08 * Math.abs(Math.sin(t * 2.3)) + (t > 45.8 && t < 46.4 ? 0.1 : 0)
  if (t >= 47.2 && t < 47.9) return lerp(base, 2.04, ramp(t, 47.2, 47.6))
  if (t >= 47.9 && t < 50.2) return 2.04
  if (t >= 50.2 && t < 50.6) return lerp(2.04, 0.2, ramp(t, 50.2, 50.6))
  return Math.min(base, 0.219)
}

export const KEYFRAMES = ['00000', '00268', '00536', '00804', '01072', '01340', '01608', '01876', '02144', '02412', '02680', '02948', '03216']

export const RETRO = [
  { stage: '仿真', rework: 14, note: '名义流程连续 7 次 FAIL' },
  { stage: '渲染', rework: 4, note: '画质档位、路径、曝光' },
  { stage: '建模', rework: 2, note: '+ 仿真阶段 3 次指具修订' },
  { stage: '方案预览', rework: 0, note: '验证门失败 1 次' },
  { stage: '需求 / plan / 参考图', rework: 0, note: '' },
]

// ---- Scene labels ------------------------------------------------------------------

export type Tone = 'plain' | 'accent' | 'warn' | 'bad' | 'good'

export interface LabelSpec { id: string; anchor: string; text: string; tone: Tone; o: number }

export function labelsAt(t: number): LabelSpec[] {
  const L: LabelSpec[] = []
  const push = (id: string, anchor: string, text: string, tone: Tone, o: number) => {
    if (o > 0.01) L.push({ id, anchor, text, tone, o })
  }
  // Chapter 1: the scene list, one footprint at a time.
  const scene = (at: number) => window01(t, at, 9.4, 0.4)
  push('l-inc', 'incubator', '培养箱 · 4 层隔板', 'plain', scene(5.9))
  push('l-img', 'imager', '观察站 · 抽屉 190 mm', 'plain', scene(6.2))
  push('l-ws', 'workstation', '移液工作站 · 龙门 + 双门', 'plain', scene(6.5))
  push('l-cf', 'centrifuge', '离心机 · 30° 固定角转子', 'plain', scene(6.8))
  push('l-rail', 'rail', '导轨 2.95 m + 机械臂', 'plain', scene(7.1))
  push('l-dec', 'decapper', '开盖器', 'plain', scene(7.4))
  // Chapter 2: preflight.
  push('p-door', 'incDoor', '外门扫过导轨', 'bad', window01(t, 11.0, 14.8, 0.3))
  push('p-ws', 'wsTube', '管从正上方够不着', 'bad', window01(t, 11.4, 14.4, 0.3))
  push('p-ok', 'incubator', '挪到导轨末端 · 外门往外侧开', 'good', window01(t, 15.2, 19.6, 0.3))
  // Chapter 3: frozen thresholds pinned where they bite.
  for (const g of GATES_SHOWN) push('g-' + g.id, g.anchor, `${g.id} ${g.what} ${g.v}`, 'accent', window01(t, g.at, 27.8, 0.35))
  // Chapter 5: the two models.
  push('m-vis', 'visTag', 'VIS_ 视觉模型 · 给渲染', 'plain', window01(t, 35.6, 40.4))
  push('m-col', 'colTag', 'COL_ 碰撞代理 · 只留功能面', 'accent', window01(t, 35.9, 40.4))
  // Chapter 6: simulation.
  push('s-pick', 'plateAt', '板靠指垫摩擦夹住，不挂约束', 'plain', window01(t, 44.2, 46.2, 0.3))
  push('s-place', 'imager', 'S7 支撑力 ≥ 0.8 × 重量后才松爪', 'good', window01(t, 46.1, 47.4, 0.3))
  push('s-fail', 'sideRack', 'S3 = 2.04 mm · 管撞上杯壁', 'bad', window01(t, 47.6, 50.4, 0.3))
  push('s-fix', 'sideRack', 'S3 = 0.20 mm · 手直接约束管身', 'good', window01(t, 50.6, 52.2, 0.3))
  push('s-neg', 'wsDoor', '负例 N4：门没开 → S4 判 FAIL ✓', 'warn', window01(t, 52.8, 55.0, 0.3))
  return L
}
