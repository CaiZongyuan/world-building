<script setup lang="ts">
// The home page. A sticky 3D lab plays one real project through all seven
// stages as the reader scrolls, or by itself on autoplay; one click skips it.
// Long-form sections follow: the stage map, who decides what, the gates,
// the two projects so far and where to start.
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import StageCanvas from './StageCanvas.vue'
import AgentConsole from './AgentConsole.vue'
import ProjectTree from './ProjectTree.vue'
import InsightPanel from './InsightPanel.vue'
import HudStrip from './HudStrip.vue'
import GateToast from './GateToast.vue'
import RenderReveal from './RenderReveal.vue'
import HomeSections from './HomeSections.vue'
import { CHAPTERS, DURATION, HERO, chapterAt, chapterIndex, clamp, lerp, smooth, window01 } from './story'
import './landing.css'

const HERO_SCREENS = 0.75
const PER_SECOND = 0.14
const END_SCREENS = 0.6
const HERO_SPEED = 4
const SCROLL_KEYS = new Set(['ArrowUp', 'ArrowDown', 'PageUp', 'PageDown', 'Home', 'End', ' '])

const track = ref<HTMLElement>()
const ctl = ref<HTMLButtonElement>()
const vh = ref(900)
const vw = ref(1440)
const t = ref(0)
const heroP = ref(0)
const reduced = ref(false)
const playing = ref(false)
let target = 0
let playT = 0
let focusControls = false
let raf = 0
let last = 0

const trackH = computed(() => vh.value * (1 + HERO_SCREENS + DURATION * PER_SECOND + END_SCREENS))
const chapter = computed(() => chapterAt(t.value))
const ci = computed(() => chapterIndex(t.value))
const heroO = computed(() => 1 - smooth(heroP.value))
const narrow = computed(() => vw.value < 980)
const offsetX = computed(() => (narrow.value ? 0 : lerp(0.03, 0.1, heroO.value)))
const offsetY = computed(() => (narrow.value ? lerp(-0.08, -0.16, heroO.value) : 0))
const local = computed(() => clamp((t.value - chapter.value.start) / (chapter.value.end - chapter.value.start)))
const ended = computed(() => t.value >= DURATION - 0.05)
const renderOn = computed(() => window01(t.value, 58.2, 64.2, 0.7))

function measure() {
  vh.value = window.innerHeight
  vw.value = window.innerWidth
}

function read() {
  if (!track.value) return
  const y = -track.value.getBoundingClientRect().top
  heroP.value = clamp(y / (HERO_SCREENS * vh.value))
  const tt = clamp((y - HERO_SCREENS * vh.value) / (PER_SECOND * vh.value), 0, DURATION)
  target = reduced.value ? chapterAt(tt).key : tt
}

function onResize() {
  measure()
  read()
}

const filmTop = () => track.value!.getBoundingClientRect().top + window.scrollY
const scrollFor = (time: number) => filmTop() + (HERO_SCREENS + time * PER_SECOND) * vh.value

function jump(i: number) {
  if (!track.value) return
  const time = i === 0 ? 0 : CHAPTERS[i].start + 0.2
  if (playing.value) playT = time
  else window.scrollTo({ top: scrollFor(time), behavior: reduced.value ? 'auto' : 'smooth' })
}

function play() {
  if (!track.value) return
  const now = (window.scrollY - filmTop()) / (PER_SECOND * vh.value) - HERO_SCREENS / PER_SECOND
  playT = now >= DURATION - 0.05 ? 0 : Math.max(now, -HERO_SCREENS / PER_SECOND)
  playing.value = true
  focusControls = Boolean(document.activeElement?.closest('.hero'))
}

function toggle() {
  if (playing.value) playing.value = false
  else play()
}

function skip() {
  playing.value = false
  const el = document.getElementById('stages')
  if (!el) return
  window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - 40, behavior: reduced.value ? 'auto' : 'smooth' })
  el.focus({ preventScroll: true })
}

function interrupt(e: Event) {
  if (!playing.value || (e.target as Element | null)?.closest?.('[data-film-control]')) return
  if (e instanceof KeyboardEvent && !SCROLL_KEYS.has(e.key)) return
  playing.value = false
}

onMounted(() => {
  reduced.value = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  measure()
  read()
  t.value = target
  window.addEventListener('scroll', read, { passive: true })
  window.addEventListener('resize', onResize)
  for (const type of ['wheel', 'touchstart', 'pointerdown', 'keydown']) window.addEventListener(type, interrupt, { passive: true })
  last = performance.now()
  const tick = (now: number) => {
    const dt = Math.min(0.1, (now - last) / 1000)
    last = now
    if (playing.value) {
      playT = Math.min(DURATION, playT + dt * (playT < 0 ? HERO_SPEED : 1))
      window.scrollTo(0, scrollFor(playT))
      if (playT >= DURATION) playing.value = false
    }
    if (focusControls && heroO.value < 0.5) {
      focusControls = false
      ctl.value?.focus({ preventScroll: true })
    }
    const k = reduced.value ? 1 : 1 - Math.exp(-dt * 6)
    t.value += (target - t.value) * k
    if (Math.abs(target - t.value) < 0.0005) t.value = target
    raf = requestAnimationFrame(tick)
  }
  raf = requestAnimationFrame(tick)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(raf)
  window.removeEventListener('scroll', read)
  window.removeEventListener('resize', onResize)
  for (const type of ['wheel', 'touchstart', 'pointerdown', 'keydown']) window.removeEventListener(type, interrupt)
})
</script>

<template>
  <div class="pl">
    <section ref="track" class="film" :style="{ height: trackH + 'px' }">
      <div class="sticky">
        <StageCanvas class="stage" :t="t" :offset-x="offsetX" :offset-y="offsetY" :reduced="reduced" :style="{ opacity: 1 - 0.75 * renderOn }" />
        <div class="veil" :style="{ opacity: 0.8 + 0.2 * heroO }" />

        <header class="hero" :inert="heroO <= 0.5 || undefined" :style="{ opacity: heroO, transform: `translateY(${-28 * (1 - heroO)}px)`, pointerEvents: heroO > 0.5 ? 'auto' : 'none' }">
          <p class="pl-eyebrow">{{ HERO.eyebrow }}</p>
          <h1><span v-for="s in HERO.title" :key="s" class="nb">{{ s }}</span></h1>
          <p class="lede">{{ HERO.lede }}</p>
          <div class="actions" data-film-control>
            <button class="pl-btn pl-btn--primary" @click="play"><svg viewBox="0 0 16 16"><path d="M5 3.2v9.6L12.6 8z" fill="currentColor" /></svg>自动播放（约 70 秒）</button>
            <button class="pl-btn" @click="skip">跳过动画<svg viewBox="0 0 16 16"><path d="M8 3v10m0 0 4-4m-4 4L4 9" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" /></svg></button>
          </div>
          <p class="note">也可以向下滚动，按自己的节奏看。场景是全流程实验室项目的真实布局。</p>
        </header>

        <div class="copy" :style="{ opacity: 1 - heroO }">
          <Transition name="swap" mode="out-in">
            <div :key="chapter.id">
              <p class="kicker"><span class="mono">阶段 {{ chapter.n }}</span><span>{{ chapter.kicker }}</span></p>
              <h2>{{ chapter.title }}</h2>
              <p class="body">{{ chapter.body }}</p>
            </div>
          </Transition>
          <div class="local"><i :style="{ transform: `scaleX(${local})` }" /></div>
        </div>

        <div v-if="!narrow" class="reveal" :style="{ pointerEvents: 'none' }"><RenderReveal :t="t" /></div>

        <aside class="instruments" :style="{ opacity: 1 - heroO }">
          <AgentConsole :t="t" :limit="narrow ? 3 : 6" />
          <template v-if="!narrow">
            <ProjectTree :t="t" />
            <InsightPanel :t="t" />
          </template>
        </aside>

        <div class="gate"><GateToast :t="t" /></div>

        <HudStrip v-if="!narrow" class="hud" :t="t" :style="{ opacity: 1 - heroO }" />

        <div class="controls" data-film-control :inert="heroO >= 0.5 || undefined" :style="{ opacity: 1 - heroO, pointerEvents: heroO < 0.5 ? 'auto' : 'none' }">
          <button ref="ctl" class="ctl" :aria-label="playing ? '暂停' : '自动播放'" :aria-pressed="playing" @click="toggle">
            <template v-if="playing"><svg viewBox="0 0 16 16"><path d="M5 3.5v9M11 3.5v9" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" /></svg></template><template v-else><svg viewBox="0 0 16 16"><path d="M5 3.2v9.6L12.6 8z" fill="currentColor" /></svg></template>
          </button>
          <nav class="rail" aria-label="阶段">
            <button v-for="(c, i) in CHAPTERS" :key="c.id" :class="{ on: i === ci, past: i < ci }" :style="{ flexGrow: c.end - c.start }" :aria-label="`${c.n} ${c.kicker}`" :aria-current="i === ci ? 'step' : undefined" @click="jump(i)">
              <i /><span>{{ c.kicker }}</span>
            </button>
          </nav>
          <button class="skip" @click="skip">{{ ended ? '继续阅读' : '跳过动画' }}<svg viewBox="0 0 16 16"><path d="M8 3v10m0 0 4-4m-4 4L4 9" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" /></svg></button>
        </div>

        <div class="cue" :style="{ opacity: heroO }"><span>向下滚动</span><i /></div>
      </div>
    </section>

    <HomeSections />
  </div>
</template>

<style scoped>
.film { position: relative; }
.sticky { position: sticky; top: 0; height: 100vh; height: 100svh; overflow: hidden; background: var(--ground); }
.stage { position: absolute; inset: 0; transition: opacity .2s linear; }
.veil { position: absolute; inset: 0; pointer-events: none; background:
  radial-gradient(ellipse 44% 80% at 0% 50%, color-mix(in srgb, var(--ground) 94%, transparent), color-mix(in srgb, var(--ground) 55%, transparent) 55%, transparent 100%),
  linear-gradient(180deg, color-mix(in srgb, var(--ground) 70%, transparent), transparent 18%, transparent 82%, color-mix(in srgb, var(--ground) 80%, transparent)); }

.hero { position: absolute; left: max(32px, 6vw); top: 50%; translate: 0 -50%; max-width: 620px; z-index: 2; }
.hero h1 { margin-top: 18px; font-size: clamp(40px, 5.6vw, 76px); line-height: 1.12; }
.lede { margin-top: 22px; font-size: 16.5px; line-height: 1.8; color: var(--ink-2); max-width: 540px; }
.actions { margin-top: 30px; display: flex; gap: 10px; flex-wrap: wrap; }
.note { margin-top: 18px; font-size: 12.5px; color: var(--faint); }

.copy { position: absolute; left: max(32px, 4.4vw); top: 50%; translate: 0 -54%; width: min(370px, 28vw); z-index: 2; }
.kicker { display: flex; align-items: center; gap: 10px; font-size: 13px; color: var(--muted); }
.kicker .mono { color: var(--accent-ink); font-size: 11.5px; letter-spacing: .04em; }
.copy h2 { margin-top: 14px; font-size: clamp(26px, 2.7vw, 38px); line-height: 1.24; }
.body { margin-top: 16px; font-size: 14.5px; line-height: 1.85; color: var(--ink-2); }
.local { margin-top: 26px; height: 2px; background: var(--line); border-radius: 1px; overflow: hidden; }
.local i { display: block; height: 100%; background: var(--accent); transform-origin: left; }
.swap-enter-active, .swap-leave-active { transition: opacity .35s var(--ease), transform .35s var(--ease); }
.swap-enter-from { opacity: 0; transform: translateY(10px); }
.swap-leave-to { opacity: 0; transform: translateY(-8px); }

.reveal { position: absolute; left: calc(max(32px, 4.4vw) + min(370px, 28vw) + 48px); top: 50%; translate: 0 -54%; z-index: 2; }
.instruments { position: absolute; right: 20px; top: 76px; bottom: 96px; width: 330px; display: flex; flex-direction: column; gap: 10px; overflow: hidden; z-index: 2; }
.gate { position: absolute; left: 50%; top: 84px; translate: -50% 0; z-index: 3; }
.hud { position: absolute; left: 50%; bottom: 84px; translate: -50% 0; z-index: 2; }

.controls { position: absolute; left: 24px; right: 24px; bottom: 20px; display: flex; align-items: center; gap: 14px; z-index: 3; }
.ctl { flex-shrink: 0; display: grid; place-items: center; width: 40px; height: 40px; border-radius: 50%; border: 1px solid var(--line-2); background: color-mix(in srgb, var(--surface) 86%, transparent); color: var(--ink); cursor: pointer; backdrop-filter: blur(10px); }
.ctl:hover { border-color: var(--ghost); }
.ctl svg { width: 15px; height: 15px; }
.rail { flex: 1; display: flex; gap: 4px; min-width: 0; }
.rail button { flex-basis: 0; min-width: 0; display: flex; flex-direction: column; gap: 6px; padding: 6px 0 0; background: none; border: 0; cursor: pointer; text-align: left; }
.rail i { display: block; height: 3px; border-radius: 2px; background: var(--line-2); transition: background .3s var(--ease); }
.rail button.past i { background: color-mix(in srgb, var(--accent) 45%, var(--line-2)); }
.rail button.on i { background: var(--accent); }
.rail span { font-size: 11.5px; color: var(--faint); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; transition: color .3s var(--ease); }
.rail button.on span { color: var(--ink); }
.rail button:hover span { color: var(--ink-2); }
.skip { flex-shrink: 0; display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 14px; border-radius: 8px; border: 1px solid var(--line-2); background: color-mix(in srgb, var(--surface) 86%, transparent); color: var(--ink-2); font-size: 13px; cursor: pointer; backdrop-filter: blur(10px); }
.skip svg { width: 13px; height: 13px; }

.cue { position: absolute; left: 50%; bottom: 28px; translate: -50% 0; display: flex; flex-direction: column; align-items: center; gap: 8px; font-size: 11.5px; color: var(--faint); pointer-events: none; }
.cue i { width: 1px; height: 28px; background: linear-gradient(var(--faint), transparent); }

@media (max-width: 1240px) {
  .instruments { width: 300px; }
  .reveal { display: none; }
}
@media (max-width: 980px) {
  .hero { left: 20px; right: 20px; top: auto; bottom: 120px; translate: 0 0; }
  .hero h1 { font-size: 40px; }
  .lede { font-size: 15px; }
  .copy { left: 20px; right: 20px; width: auto; top: auto; bottom: 86px; translate: 0 0; padding: 14px 16px; border-radius: 12px; background: color-mix(in srgb, var(--surface) 88%, transparent); border: 1px solid var(--line); backdrop-filter: blur(12px); }
  .copy h2 { font-size: 22px; margin-top: 8px; white-space: normal; }
  .body { font-size: 13.5px; margin-top: 8px; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }
  .local { margin-top: 12px; }
  .instruments { top: 70px; left: 16px; right: 16px; width: auto; bottom: auto; }
  .gate { top: auto; bottom: 330px; }
  .rail span { display: none; }
  .controls { left: 16px; right: 16px; bottom: 16px; }
}
</style>
