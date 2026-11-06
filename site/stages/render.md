---
title: 07 位姿绑定与渲染
description: 把 MuJoCo 记录的刚体位姿逐帧写进 Blender 的视觉根对象，用 draft 档位渲出与仿真等长的成片。
---

# 07 位姿绑定与渲染

<StageHeader stage="render" />

渲染阶段把 MuJoCo 记录下来的刚体位姿逐帧写进 Blender 的视觉根对象，再用 Cycles 渲出**与仿真等长**的成片：不加速，不剪辑。画面里的每一个动作都必须来自物理仿真，不允许手动打关键帧。

## 拖一下看看

下面是薄切片 01 成片的关键帧。每一帧里板、门、抽屉、机械臂的位置，都是 MuJoCo 算出来、再原样写进 Blender 的：

<FilmScrub set="slice" />

## 位姿绑定：一个视觉根对应一个 body

```
states_30fps.npz → 每个视觉根 = 一个 MuJoCo body → 逐帧写世界位姿（插值 CONSTANT）→ Cycles draft 渲帧 → ffmpeg + 字幕 → 验证门 V1–V4
```

1. **只按白名单导入。** 名字带 `COL_` 或 collision 的对象直接排除，而不是导入后隐藏；复用资产里的灯光、相机、展示台也不导入。
2. **视觉根和 body 一一对应。** 每个根对象不设父级，直接写入该帧仿真的世界位置和四元数，关键帧插值用 CONSTANT；全程不动的 body 不打关键帧。
3. **复用资产的视觉不在 body 原点时**，父对象按下式取位姿：`对象世界 = S_body(t) · R_body_rest⁻¹ · StationT · E_rest`。其中 `S_body(t)` 是仿真里这个 body 的当前世界位姿，`R_body_rest` 是原始模型零位下它的世界位姿，`StationT` 是工位的摆放变换，`E_rest` 是父空物体在资产文件里的矩阵。
4. **仿真里改过的几何，视觉模型要同步改**（例如托槽开槽用布尔 DIFFERENCE 做出来）。
5. **绑定之后马上自检**：V1 场景里不能有碰撞代理；V3 抽查若干帧，Blender 世界位姿要和仿真记录一致。比较四元数时要记住 q 和 −q 是同一个旋转。

## 画质：默认 draft

成片是给工程审阅看动作和干涉的，不是展示片。`render_frames.py` 有三个档位，只改采样和分辨率，不动机位、灯光、材质：

| 档位 | 设置 | 实测吞吐 | 什么时候用 |
|---|---|---|---|
| `draft`（默认） | Cycles OptiX 720p、16 spp、自适应采样 + OptiX 降噪 | 约 0.55–1 s / 帧 | 工程审阅 |
| `final` | 1080p、128 spp | 约 13.5 s / 帧 | 你明确要展示级画质时 |
| `eevee` | 最快 | — | 玻璃门会渲成不透明、挡住箱内动作，这类场景不用 |

<div class="wb-grid2">
<figure class="wb-figure"><img :src="$withBase('/img/slice/cmp_hq450.webp')" alt="final 档位局部" /><figcaption><b>final</b>，第 450 帧局部：玻璃门干净。</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/slice/cmp_draft450.webp')" alt="draft 档位局部" /><figcaption><b>draft</b>，同一帧同一位置：玻璃门上多一点颗粒，其他几乎一样。</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/slice/cmp_draft1080.webp')" alt="draft 全帧" /><figcaption><b>draft</b>，第 1080 帧：能看清箱内、机械臂和抽屉。</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/slice/cmp_eevee.webp')" alt="eevee 全帧" /><figcaption><b>eevee</b>，同一帧：玻璃门不透明，箱内的动作看不到了。</figcaption></figure>
</div>

::: warning 教训：一开始就用了展示级画质
薄切片 01 一开始用 1080p、128 spp，每帧 13–15 s，全片 1621 帧要约 6 h。渲到第 490 帧时用户指出没必要，改成 draft 后每帧约 0.55 s，快了约 25 倍，全片 16.3 min。现在的规则：**先问清成片给谁看，审阅用途一律 draft**；正式开渲前先渲 3–6 帧，测吞吐、调曝光和机位。
:::

## 收尾和验证门

逐帧写盘，已经存在的帧会跳过，中断后可以接着渲。渲完由收尾脚本编码成片（ffmpeg，libass 叠 ASS 字幕：当前步骤、教学等待的倒计时、计数结果标「模拟数据」），然后跑验证门：

```bash
uv run --extra sim wb gate <项目> render
```

| 编号 | 检查 |
|---|---|
| V1 | 场景中没有碰撞代理对象 |
| V2 | 帧数 = 仿真时长 × 30（不加速、不跳帧） |
| V3 | 抽检帧中各刚体的 Blender 世界位姿与仿真记录一致 |
| V4 | 成片能正常解码，时长与仿真一致（缺 ffprobe 时判 BLOCKED） |

## 踩过的坑

- **Windows 版 Blender 读不到 WSL 的 `/tmp`。** 脚本和中间文件都放在 `/mnt/d` 下。
- **传给 Windows 版 Blender 的输出目录要用绝对路径。** `wslpath -w` 对相对路径原样返回，Blender 的工作目录是 `C:\`，帧就写到了 `C:\<目录名>`。
- **Blender 5 的分层动作没有 `action.fcurves`**，要经 `action.layers → strips → channelbags → fcurves` 取；用 `getattr(action, "fcurves", [])` 会静默拿到空列表，插值没改成 CONSTANT，相机分段就在两个机位之间渐变。
- **收尾脚本死等**：用 `pgrep -f render_frames.py` 判断渲染是否结束，会匹配到父 shell 自己的命令行，永远等不完。按进程名 `blender.exe` 检查。
- **第一版灯光严重过曝**：沿用了建模预览的灯光，而场景几乎全是白色材质。降到约三分之一、曝光 −0.5 才正常。
- **机位**：从右前方平视时观察站正好挡在前景。改成右前方高位俯视后，培养箱内部、机械臂和抽屉都能看到。

## 两个项目里的实测

薄切片 01：构建与绑定约 0.3 h，返工 4 次（含画质档位）；全片 1621 帧 draft 档位共 16.3 min，平均 0.6 s / 帧；V1–V4 全部 PASS，成片 54.033 s。全流程实验室期 1：3226 帧、107.5 s，V3 位姿误差为 0。

经验记录原文：`docs/lessons/07-pose-binding-render.md`。
