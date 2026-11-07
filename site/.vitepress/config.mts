import { defineConfig, type HeadConfig } from 'vitepress'
import { fileURLToPath } from 'node:url'
import { assertDisplayFontCovers } from './display-font'

const base = '/world-building/'
const origin = 'https://caizongyuan.github.io'
const repo = 'https://github.com/CaiZongyuan/world-building'

export default defineConfig({
  base,
  lang: 'zh-CN',
  title: '场景流程',
  description: '从一句需求，到一段经过物理验证的成片：world-building 场景流程与 lab-scene-pipeline skill 教程。',
  appearance: true,
  cleanUrls: true,
  lastUpdated: false,
  head: [
    ['link', { rel: 'icon', type: 'image/svg+xml', href: `${base}mark.svg` }],
    ['link', { rel: 'preload', href: `${base}fonts/noto-serif-sc-600.woff2`, as: 'font', type: 'font/woff2', crossorigin: '' }],
    ['meta', { name: 'theme-color', content: '#121211' }],
    ['meta', { property: 'og:site_name', content: '场景流程' }],
  ],
  transformHead({ pageData, title, description }): HeadConfig[] {
    const path = pageData.relativePath.replace(/(^|\/)index\.md$/, '$1').replace(/\.md$/, '')
    return [
      ['meta', { property: 'og:type', content: 'website' }],
      ['meta', { property: 'og:title', content: title }],
      ['meta', { property: 'og:description', content: description }],
      ['meta', { property: 'og:url', content: `${origin}${base}${path}` }],
      ['meta', { property: 'og:image', content: `${origin}${base}img/full/overview.webp` }],
    ]
  },
  buildEnd: (site) => assertDisplayFontCovers(site.srcDir),
  vite: {
    build: { chunkSizeWarningLimit: 700 },
    // The lab definitions live in site/labs and are shared with the local Python runner.
    server: { fs: { allow: [fileURLToPath(new URL('..', import.meta.url))] } },
  },
  themeConfig: {
    logo: '/mark.svg',
    siteTitle: '场景流程',
    nav: [
      { text: '入门', link: '/guide/', activeMatch: '/guide/' },
      { text: '七个阶段', link: '/stages/requirements', activeMatch: '/stages/' },
      { text: '物理实验台', link: '/physics/', activeMatch: '/physics/' },
      { text: '用好 skill', link: '/skill/', activeMatch: '/skill/' },
      { text: '案例', link: '/cases/slice-01', activeMatch: '/cases/' },
    ],
    sidebar: [
      {
        text: '入门',
        items: [
          { text: '一页看懂整个流程', link: '/guide/' },
          { text: '核心概念', link: '/guide/concepts' },
          { text: '谁决定什么', link: '/guide/roles' },
        ],
      },
      {
        text: '七个阶段',
        items: [
          { text: '01 需求访谈', link: '/stages/requirements' },
          { text: '02 方案预览', link: '/stages/proposal' },
          { text: '03 plan', link: '/stages/plan' },
          { text: '04 参考图', link: '/stages/reference' },
          { text: '05 建模', link: '/stages/modelling' },
          { text: '06 仿真', link: '/stages/simulation' },
          { text: '07 位姿绑定与渲染', link: '/stages/render' },
          { text: '07 续：录制与剪辑', link: '/stages/footage' },
          { text: '分期的大项目与收尾', link: '/stages/phased' },
        ],
      },
      {
        text: '物理实验台',
        items: [
          { text: '一个物体由什么组成', link: '/physics/' },
          { text: '接触、摩擦与对中', link: '/physics/contact' },
          { text: '执行器与约束', link: '/physics/actuators' },
          { text: '物理测试怎么做', link: '/physics/testing' },
        ],
      },
      {
        text: '用好 skill',
        items: [
          { text: '开始一个项目', link: '/skill/' },
          { text: '审批时看什么', link: '/skill/review' },
          { text: '命令速查', link: '/skill/commands' },
          { text: '症状速查', link: '/skill/troubleshooting' },
          { text: '自测', link: '/skill/quiz' },
        ],
      },
      {
        text: '案例',
        items: [
          { text: '薄切片 01：开箱取板', link: '/cases/slice-01' },
          { text: '全流程实验室：14 步传代', link: '/cases/full-lab' },
          { text: 'Colab 3D 生成与 Blender 修模', link: '/cases/pixal3d-dressing' },
        ],
      },
    ],
    socialLinks: [{ icon: 'github', link: repo }],
    outline: { level: [2, 3], label: '本页目录' },
    docFooter: { prev: '上一页', next: '下一页' },
    darkModeSwitchLabel: '外观',
    lightModeSwitchTitle: '切换到浅色',
    darkModeSwitchTitle: '切换到深色',
    sidebarMenuLabel: '菜单',
    returnToTopLabel: '回到顶部',
    externalLinkIcon: false,
    search: { provider: 'local', options: { translations: { button: { buttonText: '搜索', buttonAriaLabel: '搜索' }, modal: { noResultsText: '没有结果', resetButtonTitle: '清除', footer: { selectText: '选择', navigateText: '切换', closeText: '关闭' } } } } },
  },
})
