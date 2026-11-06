// The seven stages, as the skill and `wb gate` define them. Shared by the stage map,
// the stage page headers and the home page.

export interface StageInfo {
  n: number
  id: string
  dir: string
  name: string
  short: string
  approval?: 1 | 2
  question: string
  input: string[]
  output: string[]
  tools: string[]
  gate: string[]
  pitfall: string
  link: string
  lesson: string
}

export const STAGES: StageInfo[] = [
  {
    n: 1, id: 'requirements', dir: '01-requirements', name: '需求访谈', short: '需求',
    question: '要做什么、不做什么、做到多真？',
    input: ['你的一句需求', '已有资产（实查能否编译、缺不缺文件）'],
    output: ['requirements.md（六节）', 'preview/index.html 范围预览（范围大时）'],
    tools: ['grilling 式分轮提问，每问附推荐答案', '子代理先查清能查到的事实'],
    gate: ['六节齐全且不为空：目标、不做什么、工艺步骤、设备、保真度、算力预算'],
    pitfall: '只问原则就开工，没把场景、流程、资产三张清单摊开给你确认。',
    link: '/stages/requirements', lesson: 'docs/lessons/01-requirements-grilling.md',
  },
  {
    n: 2, id: 'proposal', dir: '02-proposal', name: '方案预览', short: '方案', approval: 1,
    question: '这个方案在物理上摆得下、够得着吗？',
    input: ['requirements.md', '复用资产的 MJCF 和真实尺寸'],
    output: ['index.html（8 节方案页）', 'analysis/preflight_report.json + 俯视图', '概念图（WebP）'],
    tools: ['wb preflight 运动学预演', 'imagegen 生成概念图', 'wb publish 发布到仓库'],
    gate: ['8 节齐全', '图片本地、存在、为 WebP', '设备有状态 / 难度 / 许可；步骤有难度 / 保真度；外部素材有来源 / 许可 / 用途'],
    pitfall: '只查点位能不能到，不查工具几何、进出方向和门的扫掠。',
    link: '/stages/proposal', lesson: 'docs/lessons/02-proposal-preview.md',
  },
  {
    n: 3, id: 'plan', dir: '03-plan', name: 'plan', short: 'plan',
    question: '怎样才算「做成了」？',
    input: ['通过审批的方案预览（含风险表）', '历史门限与负例'],
    output: ['plan.md（问题、方案、任务、验收门限、范围外）', 'thresholds.json（门限、负例、分期）'],
    tools: ['危险探针：用独立小模型扫参数，确认负例针对的危险真会发生'],
    gate: ['五节齐全', '任务是可勾选清单', '门限有编号行并写明冻结日期', '不含时间预估'],
    pitfall: '负例针对的危险根本不存在，跑出来判 PASS，证明不了任何事。',
    link: '/stages/plan', lesson: 'docs/lessons/03-plan.md',
  },
  {
    n: 4, id: 'reference', dir: '04-reference', name: '参考图', short: '参考图', approval: 2,
    question: '新建的东西长什么样、多大、怎么受力？',
    input: ['方案里的工程决策', '复用资产的实测几何、外部标准'],
    output: ['board/*.webp + reference.json', 'dimensions.md（每项标来源类别）', 'load_path.svg 载荷链', 'index.html 审批页（wb review 生成）'],
    tools: ['imagegen 并行出图', 'wb review'],
    gate: ['R1 参考图为 WebP 且已查看', 'R2 尺寸表每项有来源类别', 'R3 有载荷链图'],
    pitfall: '生成图和设计不一致却不注明；把参考图当工程图用。',
    link: '/stages/reference', lesson: 'docs/lessons/04-reference-images.md',
  },
  {
    n: 5, id: 'modelling', dir: '05-modelling', name: '建模', short: '建模',
    question: '视觉模型和物理模型怎样保持一致？',
    input: ['dimensions.md、load_path.svg、参考图', 'thresholds.json 的 modelling 段'],
    output: ['design.py → design.json（唯一参数源）', 'Blender 视觉模型 + GLB', 'MJCF 物理模型', 'mapping.json、预览图'],
    tools: ['Blender 5.4 headless', 'MuJoCo MjSpec'],
    gate: ['M1 MJCF 可编译、关节范围正确', 'M2 支撑面高度', 'M3 GLB 无碰撞代理', 'M4 映射表完整', 'M5 静置 1 s', 'M6 夹具开口', 'M7 执行器齐全'],
    pitfall: '铰链范围单位（MjSpec 默认是度）、圆柱压圆柱只有一个接触点、导出后不读回检查。',
    link: '/stages/modelling', lesson: 'docs/lessons/05-modelling.md',
  },
  {
    n: 6, id: 'simulation', dir: '06-simulation', name: '仿真', short: '仿真',
    question: '动作在物理上成立吗？门限能抓到错吗？',
    input: ['MJCF、design.json', 'thresholds.json（门限与负例）'],
    output: ['scene.py、run_*.py', 'results/*.json（名义流程与每个负例）', 'states_30fps.npz（渲染用位姿）'],
    tools: ['MuJoCo（Python，CPU）', '运动学初筛 → 动力学'],
    gate: ['名义流程全部门限 PASS', '每个负例按预期判 FAIL', '渲染用位姿记录存在'],
    pitfall: '问题最多的阶段：可达性、接触数值、执行器、约束、分期接力。',
    link: '/stages/simulation', lesson: 'docs/lessons/06-simulation.md',
  },
  {
    n: 7, id: 'render', dir: '07-render', name: '位姿绑定与渲染', short: '渲染',
    question: '画面是不是只照抄了仿真？',
    input: ['states_30fps.npz', '视觉资产（.blend / GLB）'],
    output: ['render_scene.blend、binding_report.json', 'frames/ → film.mp4、关键帧 WebP'],
    tools: ['Blender Cycles（draft 档位）', 'ffmpeg + 字幕'],
    gate: ['V1 场景无碰撞代理', 'V2 帧数 = 仿真时长 × 30', 'V3 抽检位姿与仿真一致', 'V4 成片可解码、时长一致'],
    pitfall: '一开始就用展示级画质；传给 Windows 版 Blender 的路径不是绝对路径。',
    link: '/stages/render', lesson: 'docs/lessons/07-pose-binding-render.md',
  },
]
