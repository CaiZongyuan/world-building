import DefaultTheme from 'vitepress/theme-without-fonts'
import { withBase, type Theme } from 'vitepress'
import Landing from './landing/Landing.vue'
import StageFlow from './components/StageFlow.vue'
import StageHeader from './components/StageHeader.vue'
import GateSandbox from './components/GateSandbox.vue'
import NegMatrix from './components/NegMatrix.vue'
import ThresholdTable from './components/ThresholdTable.vue'
import PreflightView from './components/PreflightView.vue'
import HazardProbe from './components/HazardProbe.vue'
import ChatReplay from './components/ChatReplay.vue'
import Pitfalls from './components/Pitfalls.vue'
import Quiz from './components/Quiz.vue'
import MjLab from './components/MjLab.vue'
import ChainLab from './components/ChainLab.vue'
import FrictionCone from './components/FrictionCone.vue'
import ContactBits from './components/ContactBits.vue'
import Anatomy from './components/Anatomy.vue'
import FilmScrub from './components/FilmScrub.vue'
import TestLayers from './components/TestLayers.vue'
import ProjectTreeDoc from './components/ProjectTreeDoc.vue'
import DesignSplit from './components/DesignSplit.vue'
import RetroBars from './components/RetroBars.vue'
import './style.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    // Raw <img> tags in Markdown use $withBase so they work under the /world-building/ base.
    app.config.globalProperties.$withBase = withBase
    const all = { Landing, StageFlow, StageHeader, GateSandbox, NegMatrix, ThresholdTable, PreflightView, HazardProbe, ChatReplay, Pitfalls, Quiz, MjLab, ChainLab, FrictionCone, ContactBits, Anatomy, FilmScrub, TestLayers, ProjectTreeDoc, DesignSplit, RetroBars }
    for (const [name, c] of Object.entries(all)) app.component(name, c)
  },
} satisfies Theme
