<script setup lang="ts">
// The 20 frozen simulation thresholds of the full-lab project and the worst value
// measured over the whole 911.9 s run (06-simulation/full/res_full.json).
import { computed, ref } from 'vue'

const G: [string, string, string, string, string, number | null, string][] = [
  ['S1', '稳定', '预静置最后 1 s 所有自由体的速度', '< 1 mm/s', '≈ 1e-6 mm/s', 0, '开局没放稳，后面的测量全被污染'],
  ['S2', '稳定', '没被搬运的物体相对上次落定位置的漂移', '≤ 0.1 mm', '≈ 1e-9 mm', 0, '物体自己慢慢滑走'],
  ['S3', '接触', '任意接触对的最大穿透', '≤ 0.25 mm', '0.219 mm', 0.876, '力过大或接触过软，结果不可信'],
  ['S4', '接触', '机器人碰到设备、门、台面的次数', '0', '0', 0, '碰撞、轨迹错误'],
  ['S5', '工件', '搬运中盖相对板的水平位移', '≤ 2 mm', '0.024 mm', 0.012, '盖滑落'],
  ['S6', '工件', '搬运中盖相对板的竖直位移', '≤ 1 mm', '0.019 mm', 0.019, '盖被提走'],
  ['S7', '接触', '松爪前支撑力 ÷ 重量（持续 0.1 s）', '≥ 0.8', '最小 4.8 倍', null, '没放稳就松手'],
  ['S8', '工件', '放置后到目标点的距离', '≤ 3 mm', '2.70 mm', 0.9, '放偏，下一步取不到'],
  ['S9', '设备', '终态门和离心机盖的角度', '< 0.1°', '0.03°', 0.3, '门没关好'],
  ['S10', '设备', '终态抽屉位移', '< 3 mm', '0.5 mm', 0.167, '抽屉没收回'],
  ['S11', '诚实', '板和盖上的约束数、mocap 数', '0 / 0', '0 / 0', 0, '用约束偷偷托住大件'],
  ['S12', '稳定', 'MuJoCo 告警；NaN / Inf', '0 / 无', '0 / 无', 0, '数值爆炸'],
  ['S13', '稳定', '关节越限、执行器力饱和的步数', '0', '0', 0, '电机做不到的动作'],
  ['S14', '诚实', '挂约束时的对准误差', '≤ 1 mm / 3°', '竖直 0.41 mm', 0.41, '没对准就当成抓到了'],
  ['S15', '诚实', '挂约束那一刻的跳变', '≤ 0.1 mm', '0.070 mm', 0.7, '瞬移'],
  ['S16', '设备', '离心联锁：转动时盖角 / 开盖时转速', '< 0.5° / < 0.1 rad/s', '无违反', 0, '开盖离心'],
  ['S17', '设备', '两管孔位相差 180° 的偏差', '± 1°', '0.003°', 0.003, '离心不配平'],
  ['S18', '诚实', '吸排液时吸头在开口内且低于开口', '离边 ≥ 2 mm', '最小离边 7.1 mm', null, '吸到空处或板面'],
  ['S20', '诚实', '动作日志：每步有开始和结束，顺序正确', '完整', '14 步完整', null, '漏步、跳步'],
  ['S21', '设备', '完整运行终态（子板、废物、管、门）', '全部满足', '全部满足', null, '流程没真正走完'],
]
const CAT: Record<string, string> = { 稳定: '数值稳定', 接触: '接触真实', 工件: '工件安全', 诚实: '不作弊', 设备: '设备与工艺' }
const f = ref('all')
const rows = computed(() => G.filter((g) => f.value === 'all' || g[1] === f.value))
</script>

<template>
  <div class="tt vp-raw">
    <div class="wb-seg"><button type="button" :aria-pressed="f === 'all'" @click="f = 'all'">全部 20 项</button><button v-for="(l, k) in CAT" :key="k" type="button" :aria-pressed="f === k" @click="f = k">{{ l }}</button></div>
    <div class="wrap">
      <table>
        <thead><tr><th>编号</th><th>测什么</th><th>门限</th><th>全程最差实测</th><th>防什么</th></tr></thead>
        <tbody>
          <tr v-for="g in rows" :key="g[0]">
            <td class="id wb-mono">{{ g[0] }}</td>
            <td>{{ g[2] }}<small>{{ CAT[g[1]] }}</small></td>
            <td class="wb-mono nw">{{ g[3] }}</td>
            <td><span class="wb-mono">{{ g[4] }}</span>
              <span v-if="g[5] !== null" class="bar"><i :style="{ width: Math.max(2, g[5] * 100) + '%' }" :class="{ tight: g[5] > 0.8 }" /></span>
              <span v-else class="wb-tag PASS">PASS</span>
            </td>
            <td class="why">{{ g[6] }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="note">条形是实测值占门限的比例，越长越接近失败。余量最小的两项：S3 穿透（88%）和 S8 放置误差（90%）。plan 里没有编号 S19。</p>
  </div>
</template>

<style scoped>
.tt { margin: 20px 0; }
.wrap { margin-top: 10px; overflow-x: auto; border: 1px solid var(--line); border-radius: 12px; }
table { width: 100%; border-collapse: collapse; font-size: 13px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid var(--line); vertical-align: top; color: var(--ink-2); line-height: 1.6; }
th { font-weight: 500; font-size: 12px; color: var(--muted); background: var(--surface-2); white-space: nowrap; }
tr:last-child td { border-bottom: 0; }
.id { color: var(--accent-ink); font-weight: 500; }
small { display: block; color: var(--faint); font-size: 11px; }
.nw { white-space: nowrap; font-size: 12px; }
.bar { display: block; margin-top: 4px; width: 110px; height: 6px; border-radius: 3px; background: var(--grid); overflow: hidden; }
.bar i { display: block; height: 100%; background: var(--ok); }
.bar i.tight { background: var(--warn); }
.why { color: var(--muted); }
.note { margin: 8px 0 0; font-size: 12.5px; color: var(--muted); }
</style>
