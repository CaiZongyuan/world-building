<p align="center">
  <img src="site/public/mark.svg" width="56" alt="World Building 标志" />
</p>

# World Building · 场景流程

**一条会持续更新的构建流程：把实验室需求做成经过物理验证的三维场景。**

给它一句「做一个细胞传代黑灯实验室」，它交出 MuJoCo 里跑出来的仿真，记录下来的刚体位姿逐帧驱动 Blender 渲染。动作是**算出来的**，不是手 K 的；脚本对照开工前冻结的门限判定每一步是否做完。

<p align="center">
  <a href="https://github.com/CaiZongyuan/world-building/actions/workflows/site.yml"><img src="https://github.com/CaiZongyuan/world-building/actions/workflows/site.yml/badge.svg" alt="站点构建" /></a>
  <a href="https://caizongyuan.github.io/world-building/"><img src="https://img.shields.io/badge/文档-GitHub%20Pages-9ca4ff?style=flat-square" alt="文档" /></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.12%2B-3776ab?style=flat-square&logo=python&logoColor=white" alt="Python 3.12+" /></a>
  <a href="https://mujoco.readthedocs.io/"><img src="https://img.shields.io/badge/MuJoCo-3.3%2B-ff8c00?style=flat-square" alt="MuJoCo 3.3+" /></a>
  <a href="https://www.blender.org/"><img src="https://img.shields.io/badge/Blender-5.4-e87d0d?style=flat-square&logo=blender&logoColor=white" alt="Blender 5.4" /></a>
</p>

<p align="center">
  <strong>简体中文</strong> · <a href="README.md">English</a> · <a href="https://caizongyuan.github.io/world-building/"><strong>介绍与教程 ↗</strong></a>
</p>

---

> **介绍网址 → [caizongyuan.github.io/world-building](https://caizongyuan.github.io/world-building/)**
> 教程都在这个站点里，不写在 README 里：流程怎么跑、可在浏览器里运行的 MuJoCo 物理实验台、命令速查、审批时看什么，以及两个案例页（成片关键帧可拖动查看）。站点为中文，推送 `main` 时从 `site/` 自动重建发布。

![方案预览阶段生成的实验室场景参考图](site/public/img/slice/proposal_scene.webp)

*上图是概念参考图。最终的动作由 MuJoCo 仿真产生，渲染逐帧照抄记录的位姿，没有手调动画。*

## 这个仓库就是流程本身，而流程会一直改

这里放的是**流程**，不是场景：驱动项目的 [`lab-scene-pipeline` skill](.agents/skills/lab-scene-pipeline/SKILL.md)、`wb` 命令行与验证门、受控术语表、决策记录、每次跑完写下的经验记录、方案页模板与已发布的方案页，以及教程站点。

这套流程没有「最终版」。每个项目都会留下阶段日志和复盘，学到的东西回写进 [`docs/lessons/`](docs/lessons/)、skill、验证门和站点。规则是被真实项目改出来的——薄切片发现仿真返工大多是本该更早发现的可达性问题，于是流程里加了运动学预演。这个仓库的提交历史，就是流程本身的修订记录。

有两件事不要混为一谈：

- **门限在单个项目内冻结。** plan 一旦把带编号的门限定下来，验证门就绝不放宽它来把 FAIL 变成 PASS。这是为了让一次交付的结果可核查。
- **流程本身从不冻结。** 阶段怎么划、检查什么、命令怎么叫、文档怎么写，都可以改，而且预期会一直改。

场景产物（`.blend`、MJCF、GLB、参考图、仿真结果、成片、阶段日志）不进 git，放在 Hugging Face 数据集 [`RickC1999/world-building-projects`](https://huggingface.co/datasets/RickC1999/world-building-projects)。这个划分是刻意的，见 [ADR-0002](docs/adr/0002-pipeline-on-github-artifacts-on-huggingface.md)；先物理后渲染、skill 如何从薄切片长出来等决策记在 [`docs/adr/`](docs/adr/)。

## 快速开始

环境：Python 3.12+、[`uv`](https://docs.astral.sh/uv/)；`sim` extra 安装 MuJoCo 3.3+。Blender 5.4 是渲染阶段调用的外部工具。

```bash
git clone https://github.com/CaiZongyuan/world-building.git
cd world-building

uv sync --extra sim
uv run --extra sim pytest          # 每道门都有正例和负例夹具
```

`wb` 命令行（[`src/wb/`](src/wb/)）负责项目目录契约和验证门：

```bash
uv run wb new <项目> --title "我的实验室"                    # 按契约建项目骨架
uv run --extra sim wb gate <项目> <阶段>                    # PASS / FAIL / NOT_RUN / BLOCKED / IDEALIZED
uv run --extra sim wb preflight <preflight.json> --out <目录> # 运动学可行性检查
uv run wb publish <项目>                                    # 发布方案预览页
uv run wb review <项目>                                     # 生成审批页面
```

输入格式和项目目录契约见 [`docs/agents/project-layout.md`](docs/agents/project-layout.md)。流程改了，教程站要跟着改：推送前先在 `site/` 里跑 `pnpm build`。

## 仓库里有什么

| 路径 | 内容 |
|---|---|
| [`.agents/skills/lab-scene-pipeline/`](.agents/skills/lab-scene-pipeline/) | 调度项目的 skill |
| [`docs/lessons/`](docs/lessons/) | 每次跑完沉淀的经验：做什么、为什么、踩过的坑（附证据） |
| [`docs/adr/`](docs/adr/) | 决策记录；可以修订，不是不可动的规定 |
| [`GLOSSARY.md`](GLOSSARY.md)、[`AGENTS.md`](AGENTS.md) | 受控术语与工作约定 |
| [`src/wb/`](src/wb/)、[`tests/`](tests/) | `wb` 命令行与验证门夹具 |
| [`proposals/`](proposals/)、[`templates/proposal/`](templates/proposal/) | 已发布的方案页及其 HTML/CSS 主题 |
| [`site/`](site/) | 教程站点、交互式物理实验台、案例页 |

## 真实项目

这套流程已经在真活上跑过，也正是这些项目在不断改写它：[薄切片 01](https://caizongyuan.github.io/world-building/cases/slice-01)（连续仿真 54.0 s、最大穿透 0.09 mm、1,621 帧成片）和[全流程黑灯实验室](https://caizongyuan.github.io/world-building/cases/full-lab)（14 个工艺步骤、911.9 s 接力连跑、20/20 门限通过、10/10 负例按预期判 FAIL）。两个案例页把失败、理想化处理和尚未解决的问题也都公开——这些正是下一次修订的原料。

## 技术栈

| 层 | 工具 |
|---|---|
| 调度 | Agent Skills（`SKILL.md`） |
| 物理 | MuJoCo 3.3+、`MjSpec`、MJCF、Menagerie Panda、CPU |
| 视觉 | Blender 5.4（Cycles/OptiX）、GLB、生成参考图 → WebP |
| 工具链 | Python 3.12+、`uv`、`wb` 命令行、pytest |
| 文档 | VitePress 1.6、pnpm、自定义 Vue 组件、MuJoCo WASM 实验台 |
| 产物 | Hugging Face 数据集、GitHub Pages |

## 状态

- 设计上就是进行中：流程、验证门和文档都会继续变动。仓库正文用中文，代码、文件名、标识符用英文。本 README 与 [英文版](README.md) 是这扇双语门。
- 不是打包好的库或开箱即用产品。目前尚未声明许可证，复用资产前请联系维护者；生成的参考图与第三方素材各有其许可条款。

---

<p align="center">
  <a href="https://caizongyuan.github.io/world-building/">介绍与教程</a> · <a href="README.md">English</a>
</p>
