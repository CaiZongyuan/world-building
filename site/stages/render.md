---
title: 07 位姿绑定与渲染
description: 把 MuJoCo 记录的刚体位姿逐帧写进 Blender 的视觉根对象，经过 Look-Dev 与 Blender 侧真实感校准，渲出多机位原始素材，再按剪辑表剪出可加速、可切机位的视频。
---

# 07 位姿绑定与渲染

<StageHeader stage="render" />

渲染阶段做三件事：
1. **刚体位姿严格绑定**：把 MuJoCo 记录下来的刚体位姿（`states_30fps.npz`）逐帧写进 Blender 的视觉根对象（`ROOT_*`），画面里的每一个动作都来自物理仿真；
2. **场景 Look-Dev（真实质感、非接触陈设、工业标识、光照与镜头）**：在不改动任何一根刚体动画曲线（保持 `V3` 位姿误差为 0）且不引入任何碰撞体（保持 `V1` 通过）的前提下，把服务于物理求解的“仿真白盒”升级为具有真实洁净室材质、合理机电走线、克制工业丝印与通透光影的自动化实验室场景；
3. **多机位素材 + 剪辑**：在多个固定机位上按录制倍速渲出无字幕的原始素材（关键动作每帧都录，空闲时段隔 8 帧录 1 帧），再用剪辑表剪出不同长度的视频，可以加速、可以切机位。

## 拖一下看看

下面是薄切片 01 成片的关键帧。每一帧里板、门、抽屉、机械臂的位置，都是 MuJoCo 算出来、再原样写进 Blender 的：

<FilmScrub set="slice" />

---

## 一、 位姿绑定：一个视觉根对应一个 body

```
states_30fps.npz → 每个视觉根 = 一个 MuJoCo body → 逐帧写世界位姿（插值 CONSTANT）→ Look-Dev 质感与机电增补 → 多机位素材（按录制倍速，Cycles）→ 剪辑表拼片 → 验证门 V1–V4
```

1. **只按白名单导入。** 名字带 `COL_` 或 `collision` 的对象直接排除，而不是导入后隐藏；复用资产里的灯光、相机、展示台也不导入。
2. **视觉根和 body 一一对应。** 每个根对象不设父级，直接写入该帧仿真的世界位置和四元数，关键帧插值用 `CONSTANT`；全程不动的 body 不打关键帧。
3. **复用资产的视觉不在 body 原点时**，父对象按下式取位姿：`对象世界 = S_body(t) · R_body_rest⁻¹ · StationT · E_rest`。其中 `S_body(t)` 是仿真里这个 body 的当前世界位姿，`R_body_rest` 是原始模型零位下它的世界位姿，`StationT` 是工位的摆放变换，`E_rest` 是父空物体在资产文件里的矩阵。
4. **仿真里改过的几何，视觉模型要同步改**（例如托槽开槽用布尔 `DIFFERENCE` 做出来；偏置宽指挂到 Panda 手指根对象下）。
5. **绑定之后马上自检**：`V1` 场景里不能有碰撞代理；`V3` 抽查若干帧，Blender 世界位姿要和仿真记录一致（注意四元数 $q$ 与 $-q$ 表示同一旋转）。

---

## 二、 从“仿真白盒”到“真实感实验室”：六步 Look-Dev 流程

物理仿真阶段遵循「只建接触与运动学必需几何」的极简原则，因此刚完成位姿绑定的 `render_scene.blend` 往往是缺乏环境细节的“白盒实验室”（左后方冰箱与试剂柜为白色占位块、台面无理化板质感、墙面无供电插座与线槽、透明门存在折射重影）。我们在 `07-render` 阶段通过以下 **六步 Look-Dev 流程** 完成真实感升级：

### 三机位演进对比（仿真白盒 $\rightarrow$ 2D 风格锚定图 $\rightarrow$ Blender Cycles 最终渲染）

#### 1. 全景机位（`01_overview`，13 mm 超广角俯视）
<div class="wb-grid2">
<figure class="wb-figure"><img :src="$withBase('/img/pixal3d/overview_before.webp')" alt="全景：白盒底图" /><figcaption><b>① 仿真白盒底图</b>：冰箱与试剂柜为纯白方块，铝型材与台面缺乏金属/理化板质感，工作站透明前门因厚板折射出现双像重影。</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/pixal3d/overview_real.webp')" alt="全景：2D 真实感风格锚定图" /><figcaption><b>② 2D 真实感锚定图（Real 系列）</b>：锁死 Blender 结构底图透视，用生图模型生成目标工业洁净室质感，明确深灰理化板、4040 铝型材护栏、顶部蓝波纹集气罩与玻璃试剂柜的视觉标准。</figcaption></figure>
</div>
<figure class="wb-figure"><img :src="$withBase('/img/pixal3d/overview_after.webp')" alt="全景：Blender Cycles 最终渲染" /><figcaption><b>③ Blender 5.4 Cycles 最终渲染（01_overview_pixal3d）</b>：合入透明玻璃门试剂柜（内摆 16 个 Pixal3D 试剂瓶）、4°C 实验冰箱、同轴蓝色排风波纹管、右侧 4040 铝型材安全护栏、深灰理化板台面、零重影薄壁玻璃与低调的 <code>LUMEN TECH / LAB WORLD</code> 品牌标识。</figcaption></figure>

#### 2. 移液工作站近景（`02_workstation`，22 mm 标准近景）
<div class="wb-grid2">
<figure class="wb-figure"><img :src="$withBase('/img/pixal3d/workstation_before.webp')" alt="工作站：白盒底图" /><figcaption><b>① 仿真白盒底图</b>：前门 `Alpha=0.28 + Transmission=0.96 (IOR=1.06)` 导致直穿光线与折射光线叠加，箱内移液头、孔板与立柱出现严重横向重影，且门外机械臂倒映在玻璃门上。</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/pixal3d/workstation_real.webp')" alt="工作站：2D 真实感风格锚定图" /><figcaption><b>② 2D 真实感锚定图（Real 系列）</b>：目标为高通透无重影聚碳酸酯前门、深灰耐酸碱理化板台面、阳极氧化铝门框、箱内顶置补光以及移液头黄绿状态贴标。</figcaption></figure>
</div>
<figure class="wb-figure"><img :src="$withBase('/img/pixal3d/workstation_after.webp')" alt="工作站：Blender Cycles 最终渲染" /><figcaption><b>③ Blender 5.4 Cycles 最终渲染（02_workstation_pixal3d）</b>：改用零折射薄壁建筑玻璃 Shader（97% Transparent + 3% Glossy）彻底根除双像重影与机械臂倒影；补充箱内 45 W 顶置 LED 补光、隐藏烘焙静态吸头 <code>v03_tip_200ul</code>，并在深灰台面与眉板加入克制的激光镭雕与丝印。</figcaption></figure>

#### 3. 离心机与开盖器近景（`03_centrifuge`，22 mm 朝南近景）
<div class="wb-grid2">
<figure class="wb-figure"><img :src="$withBase('/img/pixal3d/centrifuge_before.webp')" alt="离心机：白盒底图" /><figcaption><b>① 仿真白盒底图</b>：南墙与台下完全空白，缺少供电线槽、插座、插头、设备连接线、台下 UPS 电源盒与废料桶。</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/pixal3d/centrifuge_real.webp')" alt="离心机：2D 真实感风格锚定图" /><figcaption><b>② 2D 真实感锚定图（Real 系列）</b>：明确南墙水平 PVC 线槽、双联插座、自然垂落的黑色橡胶电缆、台下 230V UPS 电源盒与右侧不锈钢内胆废料桶的工业细节。</figcaption></figure>
</div>
<figure class="wb-figure"><img :src="$withBase('/img/pixal3d/centrifuge_after.webp')" alt="离心机：Blender Cycles 最终渲染" /><figcaption><b>③ Blender 5.4 Cycles 最终渲染（03_centrifuge_pixal3d）</b>：切除插座 GLB 底部烘焙的断头残线，补齐 3D 模压黑插头护套与设备后壁防水接头，让 4 阶 NURBS 悬链线从插头连续延伸深入离心机、开盖器与观察站机壳内部。</figcaption></figure>

---

### Step 1：结构底图导出 + 2D AI 概念图锚定质感（Style Lock）

不要在没有视觉锚点的情况下盲目调 Blender 材质节点。标准做法是：
1. 先按分期镜头（全景、工作站近景、离心机近景）从 Blender 导出 3 张白盒结构图；
2. 将白盒结构图作为几何约束输入生图模型，在**严格锁死设备位置、机身比例与相机透视**的前提下生成照片级工业洁净室参考图（`*_real.webp`）；
3. 对照 `*_real.webp` 列出四张可执行清单：**① 基底 PBR 材质表**、**② 非接触 3D 陈设小件表**、**③ 机电走线与工业贴标表**、**④ 局部补光与色调映射参数**。

### Step 2：参数化硬表面 + AI 3D 生成资产（Pixal3D）混合布景

遵循「规整大箱体与透明门用 Blender 参数化建模，异形机电小件与柜内瓶罐用 Colab `Pixal3D` 生成」的分工原则（完整五阶段零浪费 SOP 与修模算法见 **[Colab 3D 生成与 Blender 修模](/cases/pixal3d-dressing)**）：
- **双门透明玻璃试剂柜**：用 Blender 参数化构建笔直白烤漆柜壳、三层隔板与透明玻璃门，内部将修模后的 `clean_reagent_bottle_clean.glb` 通过 `bottle_proto.copy()`（共享网格与 2K 贴图，零额外显存）实例化 16 瓶摆上隔板；
- **非接触机电小件**：4°C 实验冰箱、台下 230V UPS 电源盒、不锈钢废料桶、顶部集气罩与墙面双联插座经 `2 mm` 空间容差去碎块和最小包围盒体积（Min-Volume OBB）自动调平后，按真实米制尺寸归一并命名为 `VIS_pixal3d__*` 放入独立的 `pixal3d_dressing` Collection，**不打刚体关键帧、不带 `COL_` 前缀**，确保 `V1` 与 `V3` 验证门零冲突。

### Step 3：工业级 PBR 材质体系与「零重影薄壁建筑玻璃 Shader」

#### 1. 工业洁净室四大核心材质配方
| 材质名称 | 适用对象 | 核心 Principled BSDF / 节点参数 | 视觉作用 |
|---|---|---|---|
| **深灰耐酸碱理化板** (`MAT_PHENOLIC`) | 工作站内台面、离心机台面、观察站台面、护栏内台面 | `Base Color=(0.16, 0.17, 0.18)`，`Roughness=0.28`，`Coat Weight=0.25`，`Coat Roughness=0.18` | 压暗台面明度，与白色机械臂、透明孔板和银色铝型材拉开清晰层次 |
| **6063 阳极氧化铝型材** (`MAT_ALU_4040`) | 实验台腿与横梁、工作站外框架、右侧 4040 安全护栏 | `Base Color=(0.78, 0.80, 0.83)`，`Metallic=0.88`，`Roughness=0.26` | 还原工业铝型材的柔和拉丝金属光泽，配合哑光黑角码形成真实装配感 |
| **哑光黑压铸铝/工业橡胶** (`MAT_GUSSET_BLK`) | 4040 角码、地脚、门把手、合页、拖链、插头与电源线 | `Base Color=(0.04, 0.04, 0.045)`，`Metallic=0.15`，`Roughness=0.42` | 提供高对比度结构锚点，避免全白/全银场景发飘 |
| **斑点环氧自流平地坪** (`MAT_FLOOR_EPOXY`) | 洁净室地面 (`VIS_room__floor`) | `Noise Texture(Scale=380, Detail=6)` 经 `ColorRamp` 映射 `(0.66, 0.68, 0.70)` 至 `(0.76, 0.78, 0.80)`，`Roughness=0.20–0.28` | 消除纯色平面的塑料感，呈现洁净室地坪特有的微颗粒漫反射 |

#### 2. 根治透明玻璃门“双像重影”的光学原理与节点代码
::: danger 核心踩坑：为什么有厚度的透明门会出现“重影（Double-Image Ghosting）”？
在第一版渲染中，工作站前门（`front_door_clear_-1/1`）和右侧护栏亚克力板同时设置了 `Alpha = 0.28`、`Transmission Weight = 0.96` 与 `IOR = 1.06`。在 Cycles 路径追踪器中，这意味着每根穿过玻璃门的光线被拆成两部分：
- **72% 的能量**走 `1 - Alpha` 的 `Transparent BSDF` 通道（等效 `IOR = 1.0`，**完全不发生折射偏折，沿直线穿透**）；
- **28% 的能量**走 `Alpha` 加权的 `Transmission` 通道（在进出有厚度的门板时按 `IOR = 1.06` 发生斯涅尔折射偏折，在 `0.3–0.6 m` 观察距离下**横向平移约 `1.5–2.5 cm`**）。

两束光线在相机传感器上叠加后，门后方的移液通道、孔板和铝型材立柱就会出现一个**横向错位 `~2 cm`、不透明度 `28%` 的双重曝光鬼影**！同时，`Principled BSDF` 的菲涅尔镜面反射还会把门外的白色 Panda 机械臂映在玻璃门中央。
:::

**标准解法（零折射薄壁建筑玻璃 `configure_thin_glass_material`）**：对场景中所有透明观察窗、聚碳酸酯防护门、亚克力挡板和试剂柜玻璃门，弃用厚介质折射，改用 **`Mix Shader(fac=0.03)` 混合 `97% Transparent BSDF`（零折射直线穿透）与 `3% Glossy BSDF (Roughness=0.03)`**，并检查将工作站侧透板（`left_clear_panel`、`rear_clear_panel`、`right_upper_clear_panel`）修正为同一材质，同时隐藏移液头 `v03_Z_joint` 上烘焙的静态吸头 `v03_tip_200ul`（避免与动态吸头 `VIS_tip_0..7` 重叠）：

```python
def configure_thin_glass_material(mat_name, tint=(0.96, 0.98, 1.00), reflection_weight=0.03, rough=0.03):
    """零折射薄壁建筑玻璃 Shader：97% 直线透明穿透 + 3% 锐利边缘高光，100% 根除厚板折射双影。"""
    m = bpy.data.materials.get(mat_name) or bpy.data.materials.new(mat_name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    mix = nt.nodes.new("ShaderNodeMixShader")
    transp = nt.nodes.new("ShaderNodeBsdfTransparent")
    glossy = nt.nodes.new("ShaderNodeBsdfGlossy")
    transp.inputs["Color"].default_value = (*tint, 1.0)
    glossy.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    glossy.inputs["Roughness"].default_value = rough
    mix.inputs["Fac"].default_value = reflection_weight
    nt.links.new(transp.outputs["BSDF"], mix.inputs[1])
    nt.links.new(glossy.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return m
```

### Step 4：连续三维悬链线走线与消除「断头电线」伪影

当把 AI 生成的墙面插座（`clean_wall_socket_clean.glb`）与程序化生成的三维电缆结合时，极易出现三种“电线看起来断掉了”的穿帮现象：
1. **插座下方出现“白色断口”**：单图 3D 生成的插座模型在底部 `4.8 cm`（`local z < 0.048`）处把参考图里的两截短电线与白墙背景一起烘焙成了凸出网格（前端面 `y = -1.420`），挡在了程序化黑色电缆（`y = -1.425`）正前方，从相机看过去就像插头和电线之间断开了一截白墙；
2. **设备后方露出“悬空断头”**：如果电缆终点只写到设备包围盒外侧几厘米（例如停在 `y = -0.94` 而离心机后壁在 `y = -0.85`），高位俯视镜头会清晰拍到电线停在半空；
3. **切墙镜头底边截断**：全景镜头（`01_overview`）隐藏南墙（`VIS_room__wall_south`）时，若南墙上的插座和跨墙电线未同步隐藏，电线就会向画面底边伸向虚空被相机裁剪面截断。

**四步根治方案**：
1. **用 `bmesh.ops.bisect_plane` 切除插座 GLB 底部烘焙残线**：导入 `clean_wall_socket_clean.glb` 后，沿局部高度 `z = 0.048 m` 水平切一刀并清除下半部分（`clear_inner=True`），只保留干净的白色双联面板；
2. **补齐 3D 模压黑插头护套与设备后壁防水接头**：在每个插孔正前方（`y = -1.416`）放置 3D 黑色插头体（`plug_head`）与应力释放护套（`plug_boot`），并在离心机、开盖器、观察站后壁安装黑色防水电缆接头（`rear_gland`）；
3. **4 阶 NURBS 悬链线两端深插**：曲线起点置于黑色插头护套中心（`y = -1.414, z = 1.078`），经过台面上方控制点自然垂落，终点穿过后壁防水接头**深入设备机壳内部 `5–8 cm`**（如离心机内部 `y = -0.76`）；
4. **随分期镜头联动显隐**：将南北墙上的线槽、插座、插头与电缆分别归入 `SOUTH_WALL_OBJS` 与 `NORTH_WALL_OBJS`，随相机朝向同步给 `hide_render` 打 `CONSTANT` 关键帧。

```python
# 切除 clean_wall_socket_clean.glb 底部 4.8 cm 烘焙的断头残线与白边遮挡
bm = bmesh.new()
bm.from_mesh(ws_obj.data)
bmesh.ops.bisect_plane(
    bm,
    geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
    plane_co=(0.0, 0.0, 0.048),
    plane_no=(0.0, 0.0, 1.0),
    clear_inner=True,
    clear_outer=False,
)
bm.to_mesh(ws_obj.data)
bm.free()
```

### Step 5：低调克制的工业品牌标识（`LUMEN TECH` & `LAB WORLD`）

真实工业设备上的品牌字样讲究克制、耐看，绝不用高饱和度大字。我们按基底材质分为两类工艺：
- **浅色烤漆面板丝印（`MAT_BRAND_SILKSCREEN`）**：用于工作站顶眉板右侧、下柜门、后龙门横梁、移液头前盖、Panda 导轨立柱及 4°C 冰箱门。采用哑光深石板灰（`Base Color = (0.20, 0.22, 0.25), Roughness = 0.48`），三维字体挤出厚度仅 `0.4–0.5 mm`，紧贴面板表面；
- **深灰理化板激光镭雕（`MAT_BRAND_LASER_ETCH`）**：用于工作站内部深灰台面左前角、离心机实验台后沿与观察站顶盖。采用半金属浅银灰（`Base Color = (0.56, 0.58, 0.61), Metallic = 0.65, Roughness = 0.32`），挤出 `0.3 mm`，在顶光下呈现细腻的激光蚀刻光泽；
- **运动与开盖部件避坑**：位于移动关节上的标识（如移液头 `v03_Z_joint`、导轨立柱 `ROOT_rail_carriage`）必须绑定为对应刚体的子对象并设 `matrix_parent_inverse = Matrix.Identity(4)`；而**在会大幅翻转开启的部件（如期 3 打开 $-100^\circ$ 的离心机顶盖）上严禁放置静态水平文字**，否则开盖时文字会悬空浮在转子腔上方。

### Step 6：箱内补光、AgX 色调映射与分期镜头联动

1. **解决“白墙过曝 vs 箱内欠曝”矛盾**：洁净室大面积白墙与白色机身在常规曝光下极易死白，而工作站内部的深灰理化板台面又容易偏暗。做法是：在工作站内部顶板下方增加一盏 `45 W` 矩形面光（`VIS_dress__ws_interior_led`，尺寸 `0.85 × 0.45 m`）专门照亮箱内台面与孔板，全局色彩管理采用 **`AgX` View Transform + `Exposure = -0.65`**，让高光柔和过渡、暗部层次分明。
2. **分期固定机位与墙面/线缆联动硬切**：全程 27,358 帧只装配一次，按 `camera_segments.json` 的四期边界设置固定镜头，并在切机位的同一帧同步切换南北墙及其附属插座线缆的 `hide_render` 状态（使用 Blender 5 分层动作 API 将相机与显隐曲线全部设为 `CONSTANT` 插值）：

| 分期镜头 | 起始帧 | 相机位置 `pos` | 目标点 `target` | 焦距 | 显隐联动状态 |
|---|---|---|---|---|---|
| **期 1 全景** | `0` | `[1.70, -1.42, 2.40]` | `[1.70, 0.25, 0.80]` | `13 mm` | 隐藏南墙及南墙线缆，显示北墙 |
| **期 2 工作站近景** | `3225` | `[1.30, 0.30, 1.45]` | `[1.45, 1.00, 0.93]` | `22 mm` | 隐藏南墙及南墙线缆，显示北墙 |
| **期 3 离心机/开盖器近景** | `6843` | `[0.70, 0.75, 2.35]` | `[0.70, -0.60, 0.80]` | `22 mm` | **显示南墙及南墙插座线缆**，隐藏北墙 |
| **期 4 全景** | `17853` | `[1.70, -1.42, 2.40]` | `[1.70, 0.25, 0.80]` | `13 mm` | 隐藏南墙及南墙线缆，显示北墙 |

---

## 三、 Look-Dev v2：Blender 侧真实感（对照参考图逐项校准）

六步做完后，画面仍然“一眼是 CG”：整体发白发灰、没有明暗层次、材质像塑料、背景是一堵白墙。问题不在模型，而在 Blender 侧的**反照率、灯光、表面微细节、相机**四件事。cell-passaging-lab 用一个脚本 `07-render/lookdev_v2/lookdev_realism.py` 在已绑定的 `render_scene.blend` 上统一升级（另存 `render_scene_lookdev.blend`），刚体位姿逐帧比对误差为 0。

<figure class="wb-figure"><img :src="$withBase('/img/lookdev-v2/compare.webp')" alt="旧渲染 / look-dev v2 / 参考目标图" /><figcaption>同一帧、同一机位：左 旧渲染，中 look-dev v2，右 参考目标图（风格锁定）。</figcaption></figure>

<div class="wb-grid2">
<figure class="wb-figure"><img :src="$withBase('/img/lookdev-v2/05_hero_robot.webp')" alt="机械臂伸进工作站" /><figcaption>帧 10200：机械臂伸进移液工作站（24 mm、f/2.8）。</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/lookdev-v2/06_hero_centrifuge.webp')" alt="离心机近景" /><figcaption>帧 11880：离心机开盖取管（30 mm、f/2.8）。</figcaption></figure>
</div>

### 1. 先量化，再调

用亮度统计对比参考图：均值、p5 / p50 / p95、削顶比例（>0.98）、饱和度（max−min）、冷暖偏移（B−R）。旧渲染 p50 0.82、饱和度 0.01（几乎纯灰）；参考图 p50 0.57、p95 0.83、饱和度 0.04 且偏冷。每轮改动都看这几个数，不靠肉眼猜曝光。

| 全景机位 | 均值 | p50 | p95 | 削顶 | 饱和度 |
|---|---|---|---|---|---|
| 旧渲染 | 0.765 | 0.824 | 0.910 | 0% | 0.010 |
| look-dev v2 | 0.537 | 0.585 | 0.830 | 0% | 0.037 |
| 参考目标图 | 0.548 | 0.573 | 0.835 | 0% | 0.040 |

### 2. 四类改动

| 类别 | 做法 | 为什么 |
|---|---|---|
| **反照率** | 白漆 0.86–1.0 → 0.70–0.78；白墙 0.9 → 0.60（偏冷）；地面灰底 ≈0.11；理化板 ≈0.035 | 全白场景里只要有纯白反照率，二次反弹就把整张图冲灰 |
| **灯光** | 删掉 6 盏 1 m 裸面光；加天花板 + 600×600 面板阵列（区域光 + 自发光漫射板），偏冷色温；世界光只留 0.03 | 没有天花板时光往上漏、墙靠世界光提亮，明暗是平的；灯盘出现在台面反射里是强真实感线索 |
| **表面微细节** | Bevel 着色器倒角高光（白漆 2.5 mm、铝 1.2 mm）；粗糙度噪声；白漆橘皮凹凸 + Coat；地面 Voronoi 颗粒 PVC；理化板细麻点（要细、要低对比，否则像花岗岩）；4040 型材换成 T 槽截面；机械臂外壳用缎面（粗糙度 0.38、不加清漆） | 6 面方盒的棱角接不到高光，纯色平面没有“材料感”；机械臂低粗糙度加清漆会像涂了一层油 |
| **相机与合成** | 按机位段打景深（f/8 / f/4 / f/5.6）和曝光关键帧；AgX + Medium High Contrast；合成加色散、弱 Bloom、暗角，静帧加胶片颗粒 | 真实照片有景深、镜头缺陷和颗粒 |

另外两项环境改动：东墙换成铝框玻璃隔断，后面程序化生成一间邻实验室（围栏工作站、岛台、高柜、风管）；南北墙加服务带、Unistrut 立槽、桥架、线管、压缩空气管；设备上贴程序生成的条码标签和黄色警示三角（运动件上的挂到对应 ROOT 下）。

::: danger 这一轮踩到的三个坑
- **Fresnel 玻璃变成黑镜子**：薄玻璃用 `Fresnel(1.5)` 混合 Transparent 和 Glossy 时，Fresnel 节点在背面按 1/IOR 计算，掠射角全内反射，整片玻璃发黑。改为 `Fresnel × (1 − Backfacing)`，只让入射面反射。
- **Bloom 阈值低于场景白**：阈值 1.2 时白墙本身就超过阈值，整张图蒙一层雾。阈值提到 4.0，只让灯盘反射和自发光起辉。
- **墙用 `hide_render` 隐藏会漏光**：墙一隐藏就既不挡光也不反射。改为把墙组的 hide_render 关键帧转成 `visible_camera` 关键帧；新加的墙面管线共用墙的 action，机位切换时一起对相机隐藏。
:::

::: warning 成片（16 spp）和静帧（512 spp）不一样：透明耗材的"碎冰"闪点
静帧没问题，换到成片 draft 档位，孔板、储液槽、吸头满是闪点，加到 128 spp 仍在。有两个原因：耗材还是折射透射；OptiX 降噪器压不住多层透明件的噪声。

处理分两步：
- 把薄壁塑料和薄液层也改成零折射薄层：Transparent 加按透射比例混入的 Diffuse，再按正面 Fresnel 混 Glossy。
- 成片降噪器改为 **OIDN**（GPU、精确预滤波）。16 spp 下闪点消失，每帧仍是约 2 s。

换外观重渲之前先清空 `frames/`：渲染脚本会跳过已存在的帧，旧帧不会被覆盖。
:::

::: tip Blender 5.4 合成器 API
没有 `scene.node_tree`，也没有 Composite 节点：新建 `CompositorNodeTree` 节点组，`interface.new_socket` 加一个 Image 输出，用 Group Output 收尾，再赋给 `scene.compositing_node_group`。合成树里混合用 `ShaderNodeMix`（RGBA），数学用 `ShaderNodeMath`；Glare、Lens Distortion 等节点的参数都变成了输入插座。颗粒用的是固定噪声图，逐帧不变，只用于静帧；放进成片会像镜头脏了。
:::

---

## 四、 多机位素材与剪辑

外观定下来之后，不再渲单机位的全长片。做法是先在 7 个固定机位上按录制倍速渲**原始素材**（无字幕），再用**剪辑表**剪出不同长度的视频：关键动作慢放，搬运和等待快放，换工位时切机位。机位怎么定、倍速怎么分、剪辑表怎么写、成本多少，见下一页 [07 续：录制与剪辑](./footage)。

<figure class="wb-figure"><img :src="$withBase('/img/footage/plan.webp')" alt="素材规划时间轴" /><figcaption>素材规划：每行一个机位，颜色越深录得越密；最下行是 1–2 min 剪辑版用到的源时段。</figcaption></figure>

---

## 五、 画质档位：默认 draft 审阅，按需高画质展示

渲染档位只改采样和分辨率，不动机位、灯光与材质。多机位素材用 `footage/render_footage.py` 的 `draft` / `final`；薄切片 01 用的是单机位的 `render_frames.py`，多一个 `eevee` 档：

| 档位 | 设置 | 实测吞吐 | 什么时候用 |
|---|---|---|---|
| `draft`（默认） | Cycles OptiX 720p、16 spp、自适应采样 + 降噪（look-dev 场景用 OIDN） | 白盒场景约 0.55–1.0 s / 帧；look-dev 场景 1.7–2.2 s / 帧 | 工程审阅与素材 |
| `final` | 1080p、128 spp | 白盒场景约 13.5 s / 帧 | 明确需要展示级单帧或宣传片段时 |
| `eevee` | 最快 | — | 透明门与箱内多层折射/透射表现差，本场景不用 |

<div class="wb-grid2">
<figure class="wb-figure"><img :src="$withBase('/img/slice/cmp_hq450.webp')" alt="final 档位局部" /><figcaption><b>final</b>，第 450 帧局部：玻璃门干净。</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/slice/cmp_draft450.webp')" alt="draft 档位局部" /><figcaption><b>draft</b>，同一帧同一位置：玻璃门上多一点颗粒，其他几乎一样。</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/slice/cmp_draft1080.webp')" alt="draft 全帧" /><figcaption><b>draft</b>，第 1080 帧：能看清箱内、机械臂和抽屉。</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/slice/cmp_eevee.webp')" alt="eevee 全帧" /><figcaption><b>eevee</b>，同一帧：玻璃门不透明，箱内的动作看不到了。</figcaption></figure>
</div>

::: warning 教训：先渲测试帧确认 Look-Dev 与机位，再开渲
薄切片 01 一开始用 1080p、128 spp，每帧 13–15 s，全片 1621 帧要约 6 h。改成 `draft` 后每帧约 0.55 s，快了约 25 倍。现在的规则：**开渲素材前，每个机位都在它的活动时段渲 1–2 张测试帧（`.webp`），检查遮挡、玻璃与透明件、贴花和曝光，再在后台开渲**。
:::

---

## 六、 收尾和验证门

逐帧写盘，已经存在的帧会跳过，中断后可以接着渲。渲完由 `render_full.sh finish` 收尾：按 `edits/*.json` 拼出各个剪辑版，然后跑验证门。

（薄切片 01 和全流程项目早期的单机位成片叠了 ASS 字幕：当前步骤、教学等待倒计时、计数结果标「模拟数据」。现在素材和剪辑版都不放字幕。）

```bash
uv run --extra sim wb gate <项目> render
```

| 编号 | 检查 |
|---|---|
| V1 | 场景中没有碰撞代理对象（`COL_` / `collision` 为 0） |
| V2 | 绑定帧数 = 仿真时长 × 30 |
| V3 | 抽检帧中各刚体的 Blender 世界位姿与仿真记录一致 |
| V4a | 多机位素材库完整：每个机位按录制倍速要录的帧都已渲出（有 `footage/footage_plan.json` 的项目） |
| V4b | 剪辑版能解码，帧数与剪辑表记录一致（缺 ffprobe 时判 BLOCKED） |
| V5 | 每次搬运，画面里两根手指到被夹物的距离在 ±1 mm 内（有素材规划的项目；`check_grasp.py` 在渲染用的场景上量） |
| V4 | 老项目（没有素材规划）：全长成片 `film.mp4` 能解码，时长与仿真一致 |

## 七、 常见踩坑速查

- **Windows 版 Blender 读不到 WSL 的 `/tmp` 且管道易挂起**：脚本和中间文件都放在 `/mnt/d` 下；WSL 调用 `blender.exe` 前先 `cd /mnt/d/...` 并附加 `< /dev/null`。
- **传给 Windows 版 Blender 的输出目录要用绝对路径**：`wslpath -w` 对相对路径原样返回，Blender 的工作目录是 `C:\`，帧会误写到 `C:\<目录名>`。
- **Blender 5 的分层动作没有 `action.fcurves`**：要经 `action.layers → strips → channelbags → fcurves` 取；用 `getattr(action, "fcurves", [])` 会静默拿到空列表，插值没改成 `CONSTANT`，导致相机分段在两个机位之间漂移渐变。
- **透明防护门出现双像重影**：`Principled BSDF` 同时开启 `Alpha < 1` 与 `Transmission (IOR > 1)` 会把直穿光线与折射偏移光线叠加成重影；一律改用 `97% Transparent BSDF + 3% Glossy BSDF` 薄壁玻璃节点。
- **AI 生成插座与手写电缆之间出现断口**：用 `bmesh.ops.bisect_plane` 切掉插座 GLB 底部烘焙的残线与白边，电缆两端分别深入 3D 黑插头护套与设备后壁机壳内部，并随分期镜头同步切换南北墙及附属线缆的 `hide_render`。
- **低采样下透明件“碎冰”闪点**：孔板、吸头、储液槽用折射透射时，16–128 spp 都有闪点；改零折射薄层，降噪用 OIDN。
- **换外观后旧帧没被重渲**：渲染脚本跳过已存在的帧；改了材质或贴花，先删旧素材。
- **停渲染只杀了 WSL 的 shell**：Windows 侧 `blender.exe` 还在跑；按命令行找 PID 再 `taskkill.exe /PID <pid> /F`。
- **收尾脚本死等**：用 `pgrep -f render_frames.py` 判断渲染是否结束会匹配到父 shell 自己的命令行；应按进程名 `blender.exe` 检查。

经验记录原文：`docs/lessons/07-pose-binding-render.md` 与 `docs/lessons/09-pixal3d-colab-scene-dressing.md`。
