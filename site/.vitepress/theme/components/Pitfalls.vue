<script setup lang="ts">
// Symptom → cause → fix, from both projects' stage logs and lessons.
import { computed, ref } from 'vue'

const P: [string, string, string, string][] = [
  ['需求', '开工后才发现漏了设备或步骤', '只问了原则，没把三张清单摊开确认', '先确认场景、流程、资产三张清单；范围大时做范围预览页'],
  ['需求', '「复用」的资产其实用不了', '只读了资产自带的说明文档', '实查：能不能编译、缺不缺网格；缺的按 SHA 从归档补回'],
  ['方案', '夹爪夹不住工件', '原装夹爪行程 80 mm < 六孔板 85.5 mm', '需求和预演阶段就核对夹爪行程与工件尺寸（G 检查）'],
  ['方案', '预演说可达，实际是手掌在板下面', '偏置指不对称，绕进入方向转 180° 不是同一个抓取', '偏置指位姿标 symmetric: false'],
  ['方案', '门扫掠误报一大片', '方盒代理尺寸是估的，偏大', '代理尺寸一律取自真实资产'],
  ['plan', '负例判 PASS', '危险本身不存在（N3 v1、N6 v1）', '先做危险探针；改负例，不改门限'],
  ['建模', '摆臂塌下', 'MjSpec 铰链范围默认是度，design 写的是弧度', '按 spec.compiler.degree 换算'],
  ['建模', '管子站不稳、会倒', '圆柱对圆柱只有一个接触点', '管底加方垫、座面为方块、周围浅杯壁'],
  ['建模', '物体穿过台面掉下去', '碰撞体太多，默认 arena 不够，接触失效', 'memory 设到 256 MB'],
  ['建模', 'Blender 材质被清掉', '先建材质后调用 read_factory_settings', '重置放在脚本最开头'],
  ['仿真', '某一段高度 IK 无解', 'Panda 手爪水平朝外时 j6 在 TCP 高出基座 0.18–0.34 m 顶到限位', '布局让所有取放高度落在同一条可解的高度带'],
  ['仿真', '搬运中盖滑落', '关节插值让手爪倾斜', '只允许绕竖直轴转：底座竖轴圆弧 + 偏航插值'],
  ['仿真', '板在指垫间慢慢滑走', '软接触的摩擦蠕变', 'noslip_iterations、指垫 solref 0.002'],
  ['仿真', '夹持穿透超标', '夹持力太大、接触太软', '夹持力和接触刚度一起调；18 N 配加硬指垫，穿透 0.09 mm'],
  ['仿真', '丢进箱子必然穿透超标', '撞击瞬间软接触必然陷入几毫米', '重件压上 0.5 mm 再松手，轻件在上方 0.3 mm 松手'],
  ['仿真', '小件被压进孔壁', '几克的件用默认 solref 0.02 太软', '小件统一 solref 0.004'],
  ['仿真', '实时因子从 0.2 掉到 0.02', '接触数暴涨（444 个）', '碰撞代理只留功能面；能排除的接触就排除'],
  ['仿真', '平夹块对不准管', '只能在一个方向推正', 'V 形夹块 + 低摩擦衬面 + 能滑的座面'],
  ['仿真', '机械臂跟踪滞后约 0.07 rad', '位置执行器有阻尼、没有前馈', 'ctrl = q_ref + (kv/kp)·q̇_ref'],
  ['仿真', '执行器一开局就撞到挡块', 'general 执行器漏设 biastype=affine', '自建位置执行器一律 affine'],
  ['仿真', '抽屉收回差约 2 mm', '复用设备 kp 偏小', '核对稳态误差，kp、kv 放大'],
  ['仿真', '门卡在 51.7°', 'attach_body 不带入源文件的 exclude', '在场景里显式补上接触排除'],
  ['仿真', '板跟着设备转了 90°', '子 body 继承 frame 的旋转', '反向偏航抵消'],
  ['仿真', '挂约束时物体跳走', 'weld data 默认 anchor (0,1,0)、relquat 全 0', '写全 12 个数，或运行时按实际位姿写入 eq_data'],
  ['仿真', '被抓的管相对手偏 2°', '最轻的件夹在 weld 链中间', '手直接约束最重的件'],
  ['仿真', '适配器漂了 24 mm', '压装件用了自由体 + weld，和转子较劲', '几何直接复制进父 body'],
  ['仿真', '托盘挡边挂住搬运中的板', '运动学初筛不统计被夹工件', '初筛把被夹工件也算上，或靠动力学发现'],
  ['仿真', '放板后 S7 = 0', '板的支撑点在孔底不在板裙，悬空 1.1 mm 就松爪', '按板的实际静止高度放置'],
  ['仿真', '下一期装吸头偏 190 mm', '上一期龙门不在零位', '存完整状态，计划从实际位置起步'],
  ['仿真', '转子被拉回 0°', '被动设备的执行器指令回零', '按名字接上全部关节和执行器指令'],
  ['仿真', '等待后台进程永远等不完', 'pgrep -f 匹配到等待循环自己', '按进程名检查'],
  ['渲染', '成片帧数对不上', '各期接缝处多出重复帧', '按 30 fps 网格重采样'],
  ['渲染', '相机在两个机位间渐变', 'Blender 5 分层动作没有 action.fcurves', '经 layers → strips → channelbags 取 fcurve'],
  ['渲染', '渲完找不到帧', '相对路径被 Windows 版 Blender 解析到 C:\\', '输出目录用绝对路径'],
  ['渲染', 'Blender 读不到中间文件', 'Windows 版 Blender 读不到 WSL 的 /tmp', '脚本和中间文件放在 /mnt/d 下'],
  ['渲染', '全片要渲 6 小时', '一开始用了展示级画质', '审阅用 draft，先测几帧吞吐'],
  ['渲染', '画面严重过曝', '沿用了建模预览的灯光，场景几乎全白', '灯光降到约三分之一，曝光 −0.5'],
]
const STAGES = ['全部', '需求', '方案', 'plan', '建模', '仿真', '渲染']
const q = ref('')
const st = ref('全部')
const rows = computed(() => P.filter((r) => (st.value === '全部' || r[0] === st.value) && (!q.value.trim() || r.join(' ').toLowerCase().includes(q.value.trim().toLowerCase()))))
</script>

<template>
  <div class="pf vp-raw">
    <div class="bar">
      <input v-model="q" type="search" placeholder="输入关键词：穿透、IK、weld、帧数…" aria-label="搜索症状" />
      <div class="wb-seg"><button v-for="s in STAGES" :key="s" type="button" :aria-pressed="st === s" @click="st = s">{{ s }}</button></div>
    </div>
    <div class="wrap">
      <table>
        <thead><tr><th>阶段</th><th>症状</th><th>原因</th><th>做法</th></tr></thead>
        <tbody><tr v-for="r in rows" :key="r[1]"><td class="s">{{ r[0] }}</td><td class="sym">{{ r[1] }}</td><td>{{ r[2] }}</td><td>{{ r[3] }}</td></tr></tbody>
      </table>
      <p v-if="!rows.length" class="empty">没有匹配的条目。</p>
    </div>
    <p class="cnt">{{ rows.length }} / {{ P.length }} 条</p>
  </div>
</template>

<style scoped>
.pf { margin: 20px 0; }
.bar { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
input { flex: 1; min-width: 220px; height: 36px; padding: 0 12px; border-radius: 9px; border: 1px solid var(--line-2); background: var(--surface); color: var(--ink); font-size: 14px; font-family: var(--font-ui); }
input:focus { outline: 2px solid color-mix(in srgb, var(--accent) 40%, transparent); }
.wrap { margin-top: 12px; overflow-x: auto; border: 1px solid var(--line); border-radius: 12px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); vertical-align: top; color: var(--ink-2); line-height: 1.6; }
th { font-weight: 500; font-size: 12px; color: var(--muted); background: var(--surface-2); }
.s { white-space: nowrap; color: var(--accent-ink); font-size: 12px; }
.sym { color: var(--ink); font-weight: 500; }
.empty { padding: 14px; color: var(--muted); font-size: 13px; margin: 0; }
.cnt { margin: 6px 0 0; font-size: 12px; color: var(--faint); }
</style>
