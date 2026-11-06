---
title: 开始一个项目
description: 怎样用 lab-scene-pipeline skill 新建或继续一个场景项目：对 Claude Code 说什么、它会按什么顺序推进、每一步你会看到什么。
---

# 开始一个项目

流程沉淀成了一个 skill：`lab-scene-pipeline`，放在仓库的 `.agents/skills/lab-scene-pipeline/SKILL.md`。它告诉 agent 按什么顺序推进阶段、每个阶段固定做哪几件事、在哪里停下来等你。你不需要背下流程，只需要知道怎么启动它、在哪几处出场。

## 准备

- 在 `world-building` 仓库里打开 Claude Code（这样 skill、`wb` 命令、经验记录都在手边）。
- 本机需要：Python 3.12+ 和 [uv](https://docs.astral.sh/uv/)（`wb` 命令行和 MuJoCo 都通过 uv 运行）；Windows 侧的 Blender 5.4（建模和渲染）；项目产物目录 `D:\Projects\Robots\projects\`，同步到 HuggingFace 数据集需要登录 `hf`。
- 先跑一次测试，确认工具链可用：

```bash
uv run --extra sim pytest
```

## 一句话启动

新建项目：

```text
用 lab-scene-pipeline 新建一个项目：<一句话描述场景和要做的工艺步骤>
```

继续一个已有项目：

```text
继续推进 <项目名>
```

继续时，skill 会先读 `stage-log.md` 和 `gates/*.json`，从第一个没 PASS 的阶段接着做。不需要你告诉它上次做到哪里。

## 一次完整的对话是什么样

下面是一段示意对话，按两个真实项目的做法编写。逐条点开，注意黄色的说明：它们标出了你需要注意的地方。

<ChatReplay />

## skill 会按什么顺序推进

| 阶段 | 产物 | agent 做什么 | 你做什么 |
|---|---|---|---|
| [01 需求访谈](/stages/requirements) | `requirements.md` | 分轮提问（附推荐答案），实查资产，摊开三张清单 | 回答问题；确认三张清单 |
| [02 方案预览](/stages/proposal) | `02-proposal/index.html` | 运动学预演、写 8 节方案页、`wb publish` | **审批点①** |
| [03 plan](/stages/plan) | `plan.md`、`thresholds.json` | 冻结门限和负例，做危险探针 | 和参考图一起审 |
| [04 参考图](/stages/reference) | `04-reference/` | 生成参考图、尺寸表、载荷链，`wb review` | **审批点②** |
| [05 建模](/stages/modelling) | MJCF、GLB、映射表 | 自主推进 | — |
| [06 仿真](/stages/simulation) | `results/`、`states_30fps.npz` | 自主推进；FAIL 就复盘、改设计、重跑 | 想看进展就问 |
| [07 渲染](/stages/render) | `film.mp4`、关键帧 | 自主推进，默认 draft 画质 | — |
| 收尾 | 复盘、学习页 | 阶段排序，经验写回 lessons 和 skill | 看成片和复盘 |

每个阶段内部都是同样五步：阶段说明 → 产物 → `wb gate` 判 PASS → 阶段日志和经验记录 → 同步 HF 与 git。

## 怎样给出好的需求

需求访谈会帮你把需求问清楚，但一开始多说一点能少问几轮：

- **说清工艺步骤的起点和终点**：「从培养箱取板，送到显微镜拍照，再放回培养箱」比「做个拍照场景」好得多。
- **说清你在意什么**：是要看动作和干涉的工程审阅片，还是要展示片？要不要所有步骤都做真实物理？
- **说清不要什么**：不做液体、不做某台设备、不跑别的物理引擎……「不做什么」和「做什么」一样重要。
- **不用说尺寸、夹爪、布局**：这些 agent 会自己查证、自己决定，写进方案页的工程决策。

## 大项目和全程自主

工艺步骤很多时，plan 会把工艺切成几期，各期可以交给子代理并行开发，最后接力连跑，详见[分期的大项目](/stages/phased)。如果任务很长、你不想中途介入，可以在需求访谈时就把所有决定说清楚，授权全程自主：审批点改为 agent 自审、页面照常发布，结束时一次性交付成片、学习页和复盘。

## 接下来

- 审批时具体看什么：[审批时看什么](./review)
- 所有命令：[命令速查](./commands)
- 遇到问题：[症状速查](./troubleshooting)
- 检验自己是否理解了：[自测](./quiz)
