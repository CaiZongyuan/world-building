---
title: 04 参考图
description: 为新建部件冻结外观风格；尺寸写进尺寸表并逐项标来源；画出载荷链。和 plan 一起交给审批点②。
---

# 04 参考图

<StageHeader stage="reference" />

参考图阶段为需要新建的部件冻结**外观风格**，同时把**尺寸**和**载荷链**单独确定下来。参考图不是工程图：它只回答「长什么样」；「多大、怎么受力」由尺寸表和载荷链回答。

## 三样产物，各管一件事

| 产物 | 回答什么 | 要求 |
|---|---|---|
| `board/*.webp` + `reference.json` | 长什么样 | 每张图记录模型、请求尺寸与实际像素尺寸、是否已查看、与设计的差异 |
| `dimensions.md` | 多大 | 每一项都标来源类别：**标准锚点**（外部标准或规格书）/ **设计假设**（本项目自定）/ **实测**（从复用资产或计算中测得） |
| `load_path.svg` | 怎么受力 | 从工件一直画到地面；门单独画一条链 |

<div class="wb-grid2">
<figure class="wb-figure"><img :src="$withBase('/img/slice/ref_incubator.webp')" alt="培养箱参考图" /><figcaption>薄切片 01 新建的培养箱参考板。门的铰链朝向、隔板层数要和已有效果图、复用资产保持一致，并写进提示词。</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/slice/ref_fingers.webp')" alt="偏置宽指概念图" /><figcaption>偏置宽指的概念图：装在 Panda 手指上，夹住六孔板的两个短端。它的开口范围（110–190 mm）写在尺寸表里，不从图上量。</figcaption></figure>
</div>

## 尺寸表：每一项都说清楚从哪来

下面是薄切片 01 尺寸表的一部分。注意「来源类别」和「依据」两列：「实测」项尽量取自复用资产的几何数据，这样新旧资产可以直接对比。

| 项 | 值（m） | 来源类别 | 依据 |
|---|---|---|---|
| 外形 宽 × 深 × 高 | 0.70 × 0.70 × 0.95 | 设计假设 | 与旧培养箱 P1-B 同一量级，便于对照 |
| 内腔 宽（x） | −0.25 … +0.25 | 实测 | P1-B 碰撞几何：内壁 x = ±0.25 |
| 外门 转角 | 0 … 115° | 实测 | P1-B / P3 |
| 内玻璃门 铰链轴 | x = −0.262，**左铰链** | 设计假设 | 仿真阶段修订：右铰链开门后会横在机器人一侧 |
| 隔板 顶面高度 z | 0.315 / 0.435 / 0.555 / 0.675 | 设计假设 | 层间距 0.12；第 3 层 0.555 落在可达范围中段 |

最后一行说明了一件事：尺寸表不是一次写死的。夹爪伸入深度、接收位开槽这类问题，要到建模阶段做干涉核查时才会暴露；修订要回写到尺寸表，并在阶段日志里记为返工。

![薄切片 01 的载荷链草图](/img/slice/load_path.svg)

## 怎么生成、怎么审

- **imagegen 后台并行出图。** 所有提示词共用一段风格前缀（材质、配色、底色、「无文字、无 logo」），后面接各自的视角和状态。生成的 PNG 立即转成 WebP 再删掉 PNG。
- **拼成联系表一次看完**，逐张记录与设计的差异。
- **差异不必重新生成，只要注明。** 生成图常会自作主张，例如画出 5 层隔板。图只冻结风格，尺寸以尺寸表为准。全流程实验室的开盖器夹爪、管座杯口两张图和设计不一致，都是逐张注明、不重新生成。
- **审批页由命令生成，不手写**：

```bash
uv run wb review <项目>     # 生成 04-reference/index.html
```

plan 和参考图一起交给你审批（审批点②）。点头之后，建模、仿真、渲染都由 agent 自主推进。

<div class="wb-grid3">
<figure class="wb-figure"><img :src="$withBase('/img/ref/decapper.webp')" alt="开盖器参考图" /><figcaption>开盖器</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/ref/tube_holders.webp')" alt="管座参考图" /><figcaption>管座</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/ref/waste_bin.webp')" alt="废物托盘参考图" /><figcaption>废物托盘</figcaption></figure>
</div>

## 验证门查什么

```bash
uv run wb gate <项目> reference
```

- **R1** 参考图存在且为 WebP，并且已被查看过（实际尺寸记录在 `reference.json`）；
- **R2** 尺寸表每一项都标了来源类别，而且只标一种（全流程实验室有一行写了两种，门判了一次 FAIL）；
- **R3** 载荷链图存在。

## 两个项目里的实测

薄切片 01：约 0.2 h，生成 5 张图，没有返工，两处差异逐张注明。全流程实验室：6 张并行生成约 1 min，验证门失败 1 次（就是上面那行两种来源类别）。

经验记录原文：`docs/lessons/04-reference-images.md`。
