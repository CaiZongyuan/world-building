<script setup lang="ts">
import { ref } from 'vue'

const L = [
  { n: '①', t: '运动学预演', when: '方案预览阶段', cost: '40–63 s / 一版布局', how: '设备、工件、夹具全部用方盒代理，多初值带碰撞检查的 IK 解出取放位姿；扫一遍门、抽屉；查相邻位姿间的过渡。', catches: '夹爪行程不够、位姿够不着、门扫到导轨、进出方向撞隔板、过渡走不通。', blind: '不算力：接触、摩擦、控制滞后都看不到。' },
  { n: '②', t: '运动学初筛', when: '仿真阶段，跑动力学之前', cost: '约 8 s / 一条轨迹', how: '沿参考轨迹逐帧摆关节姿态，查机器人与环境、门和抽屉扫掠与静态环境的接触；手指开度按夹持状态设置。', catches: '轨迹途中的擦碰、关门时扫到手臂、抽屉面板扫过下降中的手指。', blind: '被夹着的工件不在检查范围里（托盘挡边挂住板就是这样漏掉的）。' },
  { n: '③', t: '动力学 + 门限', when: '仿真阶段', cost: '约 2 min（54 s 仿真）到数十分钟', how: '真正的物理：接触、摩擦、执行器、约束。测量全部冻结门限，跑全部负例。', catches: '穿透、滑移、支撑不足、执行器饱和、约束跳变……一切需要「算力」才能看到的问题。', blind: '慢，出了问题也更难定位。所以前两层能发现的，绝不留到这里。' },
]
const sel = ref(0)
</script>

<template>
  <div class="tl vp-raw">
    <div class="stack">
      <button v-for="(l, i) in L" :key="l.t" type="button" :class="{ on: i === sel }" :style="{ width: 70 + i * 15 + '%' }" @click="sel = i"><b>{{ l.n }} {{ l.t }}</b><span class="wb-mono">{{ l.cost }}</span></button>
      <p class="axis">越往下越贵，越往上越早做</p>
    </div>
    <div class="det wb-panel">
      <p class="wb-eyebrow">{{ L[sel].when }}</p>
      <h4>{{ L[sel].n }} {{ L[sel].t }}</h4>
      <dl>
        <div><dt>怎么做</dt><dd>{{ L[sel].how }}</dd></div>
        <div><dt>能抓到</dt><dd>{{ L[sel].catches }}</dd></div>
        <div><dt>盲区</dt><dd>{{ L[sel].blind }}</dd></div>
      </dl>
    </div>
  </div>
</template>

<style scoped>
.tl { margin: 22px 0; display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.2fr); gap: 18px; align-items: center; }
.stack { display: flex; flex-direction: column; align-items: center; gap: 6px; }
.stack button { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 12px 10px; border-radius: 10px; border: 1px solid var(--line); background: color-mix(in srgb, var(--surface) 80%, transparent); cursor: pointer; transition: all .2s var(--ease); font-family: var(--font-ui); }
.stack button.on { border-color: var(--accent); background: color-mix(in srgb, var(--accent) 9%, var(--surface)); }
.stack b { font-size: 14.5px; font-weight: 500; color: var(--ink); }
.stack span { font-size: 11.5px; color: var(--muted); }
.axis { margin: 4px 0 0; font-size: 12px; color: var(--faint); }
.det { padding: 16px 18px; }
.det h4 { margin: 4px 0 8px; font-family: var(--font-display); font-size: 19px; color: var(--ink); }
dl { margin: 0; }
dl div { display: grid; grid-template-columns: 56px 1fr; gap: 10px; padding: 7px 0; border-top: 1px solid var(--line); font-size: 13.5px; line-height: 1.7; }
dt { color: var(--faint); }
dd { margin: 0; color: var(--ink-2); }
@media (max-width: 760px) { .tl { grid-template-columns: 1fr; } }
</style>
