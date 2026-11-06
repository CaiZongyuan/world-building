# 09 Colab 部署 Pixal3D 批量生成 3D 陈设与 Blender 修模合入

## 这一步做什么

在核心交互设备（机器人、导轨、工作站、培养箱、离心机、开盖器）完成参数化建模与物理验证后，用远程 Colab GPU 批量运行单图转 3D 模型（`TencentARC/Pixal3D`）补充实验室里的**非接触环境陈设与异形机电小件**，经 Blender 5.4 自动化修模后作为纯视觉对象（`VIS_*`）合入渲染场景。

## 输入 / 产物 / 完成判据

- 输入：
  - 单品干净 3/4 视角参考图（浅灰底、无遮挡、无粘连，WebP 格式）
  - 已完成位姿绑定的主场景 `07-render/render_scene.blend`
- 产物：
  - Colab 批量生成的原始 `.glb` 与耗时报告 `benchmark_report.json`
  - Blender 修模后的 `_clean.glb`、预览图 `glb_previews/*.webp`
  - 合入陈设后的场景与对比图 `07-render/lookdev/*_pixal3d.webp`
- 完成判据：
  - 场景中无 `COL_` / `collision` 对象泄漏（`V1` PASS），既有 MuJoCo 刚体位姿零改动（`V3` PASS）；
  - 项目与仓库内所有图片统一为 `.webp`；
  - Colab 实例在下载完产物后立即关停（`colab status` 显示无活跃会话）。

## 工具与调用方式

- **Colab 远程推理**：使用全局 `colab-operator` skill（`colab exec -s <session>` / `colab upload` / `colab download` / `colab stop`），优先选 **NVIDIA L4 (24 GB)**（`1.94 CU/hr`）。
- **本地修模与合入**：从 `/mnt/d/...` 原生目录调用 Windows 版 Blender 5.4，并关闭 `stdin` 管道（`< /dev/null`）：
  ```bash
  cd /mnt/d/Projects/Robots/projects/<项目>
  /mnt/d/Environment/blender-5.4.0/blender.exe -b --factory-startup --python <脚本_win> -- <参数_win> < /dev/null
  ```

---

## 标准做法：参数化建模与 3D 生成的分工边界

### 1. 什么该用 Blender 参数化做，什么该用 3D 生成模型做

本次实验最重要的结论是**明确硬表面参数化建模与 AI 3D 生成的边界**：

| 对象类型 | 典型例子 | 推荐做法 | 为什么不能反过来 |
|---|---|---|---|
| **大型规整箱体与带透明门的柜体** | 立式冰箱、双门玻璃试剂柜、实验台铝型材框架、安全护栏 | **Blender 参数化硬表面建模**：<br/>① **外壳+内部组合法**：用 Blender 建笔直的柜体、隔板和真正的透明玻璃门（`Transmission=0.92`），里面的试剂瓶等小东西逐个用 3D 模型生成后摆进去；<br/>② **几何体+局部贴图法**：用 Blender 建规整冰箱几何体，外面贴正交面板贴图 | 单图 3D 扩散 + Dual Contouring 重拓扑在大面积平板与直棱角上边缘发“肉”、表面有波浪感，且烘焙进贴图的阴影与场景光照冲突，看起来怪异；同时 `o_voxel` 强制导出 `OPAQUE` 材质，会把透明玻璃门和内部数十个瓶子糊成高达 1,500 万面的实心白门 |
| **异形机电小件、软管线缆与散装容器** | 台下 230V UPS 电源盒（带盘绕电源线）、集气罩与蓝色波纹软管（带金属喉箍）、墙面双联插座（带弯头插头线）、500 mL 蓝盖培养基瓶、不锈钢内胆废料桶 | **Colab Pixal3D 批量单图转 3D + Blender 自动修模** | 这类小件包含螺旋波纹、盘绕电线、圆角倒角与复杂丝印，手工写参数化脚本极慢，而 3D 生成模型能一次还原褶皱几何与 2K PBR 材质（高光/粗糙度/金属度），放在台下、墙面或柜内隔板上效果极佳 |

### 2. 输入参考图准备：绝不用实景遮挡切图

- **反例（实景直接裁剪 `crop_fridge_overview`）**：从全局实景图直接裁出的局部图带有前景遮挡（离心机盖挡住左下角）和邻物粘连（右侧紧挨玻璃柜）。`BiRefNet` 会把隔壁玻璃搁板误判为前景粘在模型侧面，遮挡处在体素扩散中坍缩成黑洞，且广角透视（`FOV = 40.2°`）导致模型严重后仰变形。
- **正例（干净孤立 3/4 单品图）**：先生成或拍摄无遮挡、浅灰底、焦距平缓（`FOV ≈ 22°–27°`）的单物体 3/4 视图（保存为 `.webp`），再送入 Pixal3D，四面闭合完整率接近 100%。

### 3. Colab 零浪费五阶段全链路流程（从开机前预检到验证后秒级关停）

> **算力复盘**：首次实验共消耗 **`3.37 CU`（约 104 分钟 L4 租期）**，但 9 个模型的稳态推理仅占 **`19.7 min`（`0.64 CU`）**——高达 **81%（`2.73 CU`）** 的算力浪费在「开机后才生成/挑选参考图、多次零散上传、串行单线程拉取 16.7 GB 权重（`182 s`）、现场排障改代码、以及本地跑 Blender 时未及时关停远端 GPU」。将全流程固化为以下 **五阶段 SOP** 后，同等 9 模型批处理总租期可从 `104 min` 压缩至 **`~21.5 min`（`~0.70 CU`，节省 79% 算力）**：

| 阶段 | 执行位置与计费状态 | 核心动作 | 耗时（实测 / 优化后） | 关键防呆与加速手段 |
|---|---|---|---|---|
| **Stage 0：开机前本地预检（Pre-Flight）** | 本地 WSL（**`0 CU`**） | ① 按分工筛除大平板/透明门柜体，只留异形小件；<br/>② 准备好全部 `.webp` 净图（浅灰底、无遮挡、3/4 视角、`FOV 20°–28°`）；<br/>③ 跑 `colab whoami` 与 `colab sessions` 确认凭证有效且无残留实例；<br/>④ 将 `inputs/*.webp`、补丁与批处理脚本打成**单包 `colab_payload.tar.gz`** | 本地准备完成再开机（**GPU 计费 `0 s`**） | **严禁开机后再生成参考图或写脚本**；单包上传替代十余次零散 `colab upload` |
| **Stage 1：开机 + 环境与权重双轨并行初始化** | Colab L4（**`1.94 CU/hr`**） | ① 本地先挂载 `trap 'colab stop -s pixal3d' EXIT INT TERM` 防异常泄漏；<br/>② `COLAB_CLI_RETRIES=1` 秒级申请 L4 并单次上传 `colab_payload.tar.gz`（`~12 s`）；<br/>③ 运行 `setup_and_prefetch.sh` **双轨并行**：<br/>• **轨道 A（CPU/磁盘，`~52 s`）**：`git clone` + `uv venv --python 3.10` + 预编译 `cp310` CUDA wheels + `patch_pixal3d.py` 自动打齐 3 处补丁；<br/>• **轨道 B（网络并发，`~55–65 s`）**：后台利用系统 Python 开启 `HF_HUB_ENABLE_HF_TRANSFER=1` + `snapshot_download(max_workers=8)` 并发预取 `Pixal3D`（15 GB）、`BiRefNet`（444 MB）、`MoGe-2`（1.3 GB）与 `NAF` | 串行 `234 s` $\rightarrow$ **双轨并行 `~65 s`**（进入推理后热缓存加载仅 `~20 s`） | 利用 `uv` 装包期间的空闲网卡带宽并发拉满 1–2 Gbps 权重下载，消除首次推理 `182 s` 的串行 HTTP 阻塞 |
| **Stage 2：单进程四步批量生成** | Colab L4（**`1.94 CU/hr`**） | 单进程 `run_batch.py` 顺序执行：<br/>① **批量 `BiRefNet` 抠图**（首图含加载 `8.7 s`，后续 `0.8 s/张`）$\rightarrow$ **`del` 释放 `1.2 GB` 显存**；<br/>② **批量 `MoGe-2` 相机外参估计**（首图含加载 `9.5 s`，后续 `0.2 s/张`）$\rightarrow$ **`del` 释放 `1.5 GB` 显存**；<br/>③ **共享单份 `DINOv3+NAF`（省 `3.6 GB`）逐个跑 `1024_cascade` 扩散**（`55–140 s/个`，峰值显存稳定 `12.91 GB`），原始网格存 `/tmp/current_mesh.pt`；<br/>④ **子进程 `export_glb_worker.py` 隔离烘焙 GLB**（`20–38 s/个`），远端自动打包 `/content/outputs.tar.gz` | **`~129 s / 模型`**（9 模型约 `19.7 min`，耗 `0.64 CU`） | 预处理模型用完即卸；C++/CUDA `CuMesh` 放入独立子进程并带 `remesh=False` 自动降级，主进程 15 GB 权重永不崩溃重拉 |
| **Stage 3：产物下载、Gate A 秒级校验与立即关机** | 远端 $\rightarrow$ 本地（**校验通过即刻停机**） | ① 单次 `colab download` 拉回 `outputs.tar.gz`（30 MB 约 `3–5 s`）；<br/>② 本地运行 `verify_glb_outputs.py`（**`< 0.1 s`**）做 **Gate A 完整性校验**：核对模型数量、glTF 2.0 魔数头（`0x46546C67`）、JSON 块可解析、`final_faces > 5000`；<br/>③ **Gate A 打印 `GATE_A_PASS` 后 1 秒内执行 `colab stop -s pixal3d`**，并用 `colab sessions` 确认输出 `No active sessions.` | **`~5 s`**（关机后 GPU 计费归零） | **验证拆为两级**：关机前只做 `< 1 s` 的二进制/面数完整性校验（Gate A），**绝不挂着 GPU 等待本地 Blender 渲染** |
| **Stage 4：本地 Blender 修模与场景验证（Gate B）** | 本地 WSL + Windows Blender 5.4（**`0 CU`**） | ① 运行 `render_glb_sheet.py` 做 `2 mm` 空间容差去碎块、最小包围盒体积调平与 `.webp` 预览渲染（`22 s`）；<br/>② 运行 `enrich_scene_pixal3d.py` 合入场景并渲染对比图（`58 s`），通过 `V1`（0 碰撞体泄漏）与 `V3`（动态位姿零改动）验证 | **`~80 s`**（纯本地，**`0 CU`**） | 本地修模与 Cycles 渲染完全不依赖 Colab，必须在确认 `colab stop` 之后执行 |

### 4. 详解一：如何在 Colab 上配置与批量运行 Pixal3D 生成 3D 模型

#### 4.1 输入参考图规范与生成 Prompt 模板
`Pixal3D` 的前端由 `BiRefNet`（前景分割）+ `MoGe-2`（单目深度与相机内参/外参估计）组成，输入图片必须满足以下 4 条硬性要求：
1. **孤立单品、浅灰/纯白净底（RGB 约 `225–240`）**：避免纯黑或复杂实景背景，防止 `BiRefNet` 把背景阴影或邻近物体粘连进前景掩码；
2. **标准 3/4 等轴微俯视角（俯角 `10°–20°`，水平偏角 `25°–35°`）**：必须同时看到物体的**正面、一侧侧面与顶面**，给 3D 稀疏体素扩散提供完整的三轴深度约束；
3. **中长焦平缓透视（等效焦距 `50–85 mm`，对应 `MoGe-2` 估计 `fov_deg` 在 `20°–28°` 之间）**：严禁使用广角切图（`fov_deg > 38°` 会导致生成的 3D 网格出现梯形畸变与后仰）；
4. **分辨率与格式**：统一使用 `1024×1024`、无透明通道或白底 `.webp`。参考图生成 Prompt 模板：
   > `"Single isolated [设备英文名, 如 laboratory under-bench UPS power supply box with coiled white power cord], 3/4 isometric product view, slight 15-degree top angle, neutral light-grey studio background, soft even studio lighting, no cast shadows on background, sharp industrial details, 50mm lens, photorealistic"`

#### 4.2 双轨并行环境初始化与 3 处必打源码补丁
Colab 默认环境为 Python 3.12（`cp312`），而 `Pixal3D` 依赖的 4 个核心 C++/CUDA 扩展（`o_voxel`、`cumesh`、`flex_gemm`、`nvdiffrast`）官方仅提供 **Python 3.10 (`cp310`) + PyTorch 2.6 (`cu124`)** 的预编译 wheel。若在默认环境直接安装会触发长达 30 分钟的源码编译。

因此开机后通过 [setup_and_prefetch.sh](file:///mnt/d/Projects/Robots/projects/cell-passaging-lab/05-modelling/pixal3d_exp/colab_pipeline/setup_and_prefetch.sh) 同时启动两条轨道：
- **轨道 A（前台 `~52 s`）**：用 `uv venv /content/venv310 --python 3.10` 秒建 3.10 虚拟环境，剔除 `requirements-hfdemo.txt` 里锁死旧版 torch 的 `MoGe` 行后用 `uv pip install --index-strategy unsafe-best-match` 秒装预编译 wheel，再单独 `--no-deps` 装 `MoGe`；
- **轨道 B（后台 `~55–65 s`）**：同时用系统 Python 开启 `HF_HUB_ENABLE_HF_TRANSFER=1` 和 8 线程 `snapshot_download`，在装 pip 包期间并发预取 `TencentARC/Pixal3D`（15 GB）、`ZhengPeng7/BiRefNet`（444 MB）、`Ruicheng/moge-2-vitl-normal`（1.3 GB）与 `valeoai/NAF`。

紧接着运行 [patch_pixal3d.py](file:///mnt/d/Projects/Robots/projects/cell-passaging-lab/05-modelling/pixal3d_exp/colab_pipeline/patch_pixal3d.py) 自动修复上游 3 处致命问题：
1. **替换受门禁限制的抠图权重**：将 `pixal3d/pipelines/rembg/BiRefNet.py` 默认的 `briaai/RMBG-2.0`（在无 HF Token 时报 `401 Unauthorized`）替换为同构公开权重 `ZhengPeng7/BiRefNet`；
2. **重写 `valeoai/NAF` 邻域注意力（解决 L4 `sm_89` 算子报错与 24 GB OOM）**：
   - 上游 `valeoai/NAF` 先把 `[B, 1024, 64, 64]` 的低分特征用 `nearest-exact` 放大 $16\times 16=256$ 倍到 `1024×1024`（单张量 4 GB），再调 `natten` 算 `dilation=16` 的 $9\times 9$ 邻域注意力（预编译 `natten` 仅含 H100 `sm_90` 内核，在 L4 上直接报错，且显存飙至 22 GB）；
   - **数学等价改写**：因为 Key/Value 是 $16\times 16$ 最近邻复制且步长 `dilation=16` 恰好等于放大倍率，高分图上同一 $16\times 16$ 块内的 256 个 Query 访问的完全是低分图上同一个 $9\times 9$ 窗口。直接将 Query 重排为 `[B, 64, 64, N, 256, D]` 与低分 `k_win [B, 64, 64, N, D, 81]` 做分组矩阵乘，**零精度损失，显存降低 $256\times$（`< 0.2 GB`），单次耗时从 `110 s` 降至 `18 ms`**；
3. **补齐 `o_voxel/postprocess.py` 的 `remesh=True` 非流形清理（解决 `CuMesh` CUDA 700 崩溃）**：
   - 上游在 `if not remesh:` 分支做了完整的网格拓扑清理，但在 `if remesh:` 分支调完 `mesh.simplify(decimation_target)` 后漏写了清理代码，导致复杂网格简化后残留的非流形边在 `uv_unwrap()` 中触发 `CuMesh/src/atlas.cu:503` 非法内存访问。在 `mesh.simplify()` 后补齐以下 5 行即可根治：
   ```python
   mesh.remove_duplicate_faces()
   mesh.repair_non_manifold_edges()
   mesh.remove_small_connected_components(1e-5)
   mesh.fill_holes(max_hole_perimeter=3e-2)
   mesh.unify_face_orientations()
   ```

#### 4.3 单进程四步批量推理脚本与关键参数说明
在 Colab 上切勿对每张图单独跑一次 `python inference.py`（每次冷启动加载 15 GB safetensors 需 `~20–180 s`）。标准做法是用单进程批量脚本按以下四步流水线执行：

```python
import subprocess, sys, time, torch
from PIL import Image
sys.path.insert(0, "/content/Pixal3D")
from pixal3d.pipelines import Pixal3DPipeline
from pixal3d.pipelines.rembg import BiRefNet
from moge.model.v2 import MoGeModel

# Step 1: 批量 BiRefNet 抠图 + 居中裁剪填充，跑完即卸载释放 1.2 GB 显存
rembg_model = BiRefNet(model_name="ZhengPeng7/BiRefNet").cuda()
preproc_images = {}
for task in TASKS:
    raw_img = Image.open(task["input_path"]).convert("RGB")
    rgba = rembg_model(raw_img)  # 返回带 Alpha 通道的前景图与居中正方形裁剪
    preproc_images[task["id"]] = rgba
del rembg_model
torch.cuda.empty_cache()

# Step 2: 批量 MoGe-2 相机视野角 (FOV) 与外参估计，跑完即卸载释放 1.5 GB 显存
moge = MoGeModel.from_pretrained("Ruicheng/moge-2-vitl-normal").cuda().eval()
cam_params = {}
for task_id, rgba in preproc_images.items():
    cam_params[task_id] = estimate_camera_with_moge(moge, rgba)  # 输出 fov_deg, extrinsics
del moge
torch.cuda.empty_cache()

# Step 3: 加载 Pixal3D 主干，并让 4 个特征提取器共享同一份 DINOv3 + NAF 实例（立省 3.6 GB 显存）
pipe = Pixal3DPipeline.from_pretrained("TencentARC/Pixal3D")
shared_extractor = pipe.models["image_cond_model_ss"]
for key in ("image_cond_model_shape_512", "image_cond_model_shape_1024", "image_cond_model_tex_1024"):
    if key in pipe.models:
        pipe.models[key].model = shared_extractor.model
        pipe.models[key].naf_model = shared_extractor.naf_model
pipe.cuda()

# Step 4: 逐任务跑 3D 稀疏体素扩散 + 子进程隔离导出 GLB
for task in TASKS:
    tid = task["id"]
    outputs = pipe.run(
        image=preproc_images[tid],
        seed=42,
        pipeline_type=task.get("pipeline_type", "1024_cascade"),  # 小件用 1024_cascade，大件细节用 1536_cascade
        sparse_structure_sampler_params={"steps": 12, "cfg_strength": 7.5},
        shape_slat_sampler_params={"steps": 12, "cfg_strength": 7.5},
        tex_slat_sampler_params={"steps": 12, "cfg_strength": 3.0},
        camera_params=cam_params[tid],
    )
    mesh = outputs[0]
    # 先把原始体素与网格张量落盘到 /tmp/current_mesh.pt，再交由独立子进程跑 CuMesh 简化与 UV 烘焙
    torch.save({
        "vertices": mesh.vertices.cpu(),
        "faces": mesh.faces.cpu(),
        "attr_volume": mesh.attrs.cpu(),
        "coords": mesh.coords.cpu(),
        "attr_layout": pipe.pbr_attr_layout,
        "grid_size": mesh.grid_size,
    }, "/tmp/current_mesh.pt")
    torch.cuda.empty_cache()

    # 子进程调用 export_glb_worker.py（若 remesh=True 失败自动回退 remesh=False，绝不污染主进程）
    subprocess.run([
        "/content/venv310/bin/python", "/content/payload/export_glb_worker.py",
        "/tmp/current_mesh.pt", f"/content/outputs/{tid}.glb",
        str(task.get("decimation_target", 90000)),  # 目标面数：瓶子/插座 80k，电源盒/集气罩 100k
        "2048",                                     # PBR 贴图分辨率 2048x2048
        "1",                                        # remesh=1 (开启 Dual Contouring 重拓扑)
    ], check=True)
```

- **关键参数调优经验**：
  - `pipeline_type`：实验室小件（电源盒、集气罩、插座、试剂瓶、废料桶）一律选 **`"1024_cascade"`**（峰值显存稳定 `12.91 GB`，单模型 `75–176 s`）；仅当物体表面有极密集的百叶窗或细小凹槽时才选 `"1536_cascade"`（峰值显存 `18.71 GB`，耗时 `~208 s`）。
  - `decimation_target`：体素扩散直接提取的原始 Dual Contouring 网格高达 `370 万–1,506 万面`，不可直接进渲染器；设 `80,000–100,000` 面在保持圆角与波纹管褶皱不崩边的同时，将单个 `.glb` 体积控制在 **`3.1–4.4 MB`**。
  - `texture_size=2048`：烘焙 `BaseColor` + `MetallicRoughness` 两张 2K 贴图，丝印文字、警示黄标与不锈钢拉丝高光清晰度充足。

---

### 5. 详解二：Blender 5.4 自动化修模与场景合入四步法（含完整算法与代码）

从 Colab 下载并经 [verify_glb_outputs.py](file:///mnt/d/Projects/Robots/projects/cell-passaging-lab/05-modelling/pixal3d_exp/colab_pipeline/verify_glb_outputs.py) 校验通过、**立即执行 `colab stop` 关停远程机器后**，在本地调用 Windows 版 Blender 5.4（[render_glb_sheet.py](file:///mnt/d/Projects/Robots/projects/cell-passaging-lab/05-modelling/pixal3d_exp/render_glb_sheet.py) 与 [enrich_scene_pixal3d.py](file:///mnt/d/Projects/Robots/projects/cell-passaging-lab/05-modelling/pixal3d_exp/enrich_scene_pixal3d.py)）对原始 `.glb` 执行四步自动化修复。

#### 5.1 为什么原始生成的 `.glb` 绝不能直接摆进场景？
原始 `.glb` 存在四类共性缺陷：
1. **UV 接缝切裂与外部悬空噪点并存**：`o_voxel` 的 `CuMesh.uv_unwrap()` 为了展开 2K 贴图，会沿所有 UV 接缝切开网格并复制顶点，导致单个物体在 `bmesh` 拓扑边上碎裂成数千个独立 UV Chart；与此同时，3D 扩散常在机身外围残留几百到几千个顶点的真正悬空碎块（例如 `clean_reagent_cabinet` 外围有 42 个悬空孤岛、共 2,320 个噪点顶点）。**如果直接按常规 `bmesh` 拓扑边连通分量删小块，会把蓝色波纹管、门把手、前面板贴纸当成“小孤岛”全部误删！**
2. **单图视角倾角被烘焙进几何顶点**：`MoGe-2` 从 3/4 微俯视图估计出的相机俯仰角/横滚角/偏航角（实测高达 `11°–29.5°`）会残留在导出网格中，直接放到水平地面 $z=0$ 上时，设备会整体向后仰倒或向一侧歪斜。
3. **归一化盒子尺寸与中心原点**：导出顶点位于 `[-0.5, 0.5]^3` 归一化空间，原点在几何中心而非底面中心，且 glTF 默认为 `+Y` 向上，导入 Blender 后需先解除父子层级并应用变换（`transform_apply`）。
4. **材质强制 `OPAQUE`**：`o_voxel` 不支持透明通道，玻璃窗会被烘焙成死白或灰黑的不透明面。

#### 5.2 第一步：三维空间容差（`2 mm`）网格哈希连通域去碎块（焊合 UV 接缝）
为了既删掉真正的空间悬空噪点、又不误伤被 UV 接缝切开的表面分片，我们在 `remove_floating_islands_and_clean()` 中引入 **`spatial_tol = 0.002`（`2 mm`）三维空间哈希桶**：在 BFS 遍历时，除了沿拓扑边 `curr.link_edges` 扩展外，还将落在同一或相邻 `2 mm` 三维网格单元内的所有 UV 接缝重合顶点视为连通邻居（相当于在三维空间中把 UV 接缝逻辑焊合），最后只删除顶点数不足主连通分量 `2%` 的外部游离块：

```python
from collections import defaultdict, deque
import bmesh

def remove_floating_islands_and_clean(obj, min_ratio=0.02, spatial_tol=0.002):
    """按 2mm 三维空间容差聚合连通分量（跨 UV 接缝焊合），仅剔除外部悬空碎块。"""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()

    # 1. 先清理无面关联的孤立顶点
    loose_v = [v for v in bm.verts if not v.link_faces]
    if loose_v:
        bmesh.ops.delete(bm, geom=loose_v, context="VERTS")
        bm.verts.ensure_lookup_table()

    # 2. 将每个顶点的三维坐标量化到 2mm 网格桶，聚合被 UV 接缝切开的同位置顶点
    inv_tol = 1.0 / spatial_tol
    pos_buckets = defaultdict(list)
    for v in bm.verts:
        key = (int(round(v.co.x * inv_tol)), int(round(v.co.y * inv_tol)), int(round(v.co.z * inv_tol)))
        pos_buckets[key].append(v)

    # 3. 拓扑边 + 27 邻域空间桶双路 BFS 求三维空间连通分量
    visited = set()
    components = []
    for v in bm.verts:
        if v.index in visited:
            continue
        comp = []
        q = deque([v])
        visited.add(v.index)
        while q:
            curr = q.popleft()
            comp.append(curr)
            for e in curr.link_edges:
                nb = e.other_vert(curr)
                if nb.index not in visited:
                    visited.add(nb.index)
                    q.append(nb)
            ck = (int(round(curr.co.x * inv_tol)), int(round(curr.co.y * inv_tol)), int(round(curr.co.z * inv_tol)))
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for dz in (-1, 0, 1):
                        nk = (ck[0] + dx, ck[1] + dy, ck[2] + dz)
                        if nk in pos_buckets:
                            for sv in pos_buckets[nk]:
                                if sv.index not in visited:
                                    visited.add(sv.index)
                                    q.append(sv)
                            del pos_buckets[nk]
        components.append(comp)

    # 4. 剔除顶点数小于主体 2% 的悬空噪点块，并重算法线
    if len(components) > 1:
        max_len = max(len(c) for c in components)
        to_del = [v for c in components if len(c) < max_len * min_ratio for v in c]
        if to_del:
            bmesh.ops.delete(bm, geom=to_del, context="VERTS")

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
```

#### 5.3 第二步：粗到细最小包围盒体积（Minimum-Volume OBB）自动调平
实验室设备（电源盒、插座背板、废料桶底面、试剂瓶底、集气罩法兰）均具备明显的正交平面或水平底面。当物体因单图相机视角而倾斜 `11°–29°` 时，其世界轴对齐包围盒（AABB）体积 $\operatorname{Vol}(R) = (\max X - \min X)(\max Y - \min Y)(\max Z - \min Z)$ 会显著膨胀；**当且仅当旋转矩阵 $R(r_x, r_y, r_z)$ 使物体的主正交平面与世界 $X/Y/Z$ 轴严格对齐时，AABB 体积达到极小值**。

我们在 `level_mesh_upright()` 中对最多 `8,000` 个均匀采样顶点做两级粗到细搜索（俯仰/横滚先按 `3.0°` 搜 `±28°`、再按 `0.5°` 精搜 `±3.5°`；偏航角先按 `2.0°` 搜 `±22°`、再按 `0.4°` 精搜），单模型仅需 `~60 ms` 即可精准找回水平底面，并将底面中心移至原点 `(0, 0, 0)`：

```python
import math, numpy as np

def level_mesh_upright(obj, max_tilt_deg=28.0):
    """通过最小化三维轴对齐包围盒 (AABB) 体积自动消除相机俯仰/横滚/偏航倾角，并将底面中心归零。"""
    verts_np = np.array([[v.co.x, v.co.y, v.co.z] for v in obj.data.vertices], dtype=np.float32)
    sample = verts_np[np.linspace(0, len(verts_np) - 1, 8000, dtype=int)] if len(verts_np) > 8000 else verts_np

    best_rx, best_ry, best_rz, best_vol = 0.0, 0.0, 0.0, float("inf")

    # 1. 粗到细搜索俯仰角 (rx) 与横滚角 (ry)
    for step_deg, span_deg in ((3.0, max_tilt_deg), (0.5, 3.5)):
        rxs = np.radians(np.arange(math.degrees(best_rx) - span_deg, math.degrees(best_rx) + span_deg + 1e-4, step_deg))
        rys = np.radians(np.arange(math.degrees(best_ry) - span_deg, math.degrees(best_ry) + span_deg + 1e-4, step_deg))
        for rx in rxs:
            cx, sx = math.cos(rx), math.sin(rx)
            s_rx = sample @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float32).T
            for ry in rys:
                cy, sy = math.cos(ry), math.sin(ry)
                pts = s_rx @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float32).T
                ext = pts.max(axis=0) - pts.min(axis=0)
                vol = float(ext[0] * ext[1] * ext[2])
                if vol < best_vol:
                    best_vol, best_rx, best_ry = vol, float(rx), float(ry)

    # 2. 粗到细搜索偏航角 (rz)，使正面与 +Y 轴对齐
    cx, sx = math.cos(best_rx), math.sin(best_rx)
    cy, sy = math.cos(best_ry), math.sin(best_ry)
    Rxy = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]], dtype=np.float32) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]], dtype=np.float32)
    s_xy = sample @ Rxy.T
    for step_deg, span_deg in ((2.0, 22.0), (0.4, 2.5)):
        rzs = np.radians(np.arange(math.degrees(best_rz) - span_deg, math.degrees(best_rz) + span_deg + 1e-4, step_deg))
        for rz in rzs:
            cz, sz = math.cos(rz), math.sin(rz)
            pts = s_xy @ np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float32).T
            ext = pts.max(axis=0) - pts.min(axis=0)
            vol = float(ext[0] * ext[1] * ext[2])
            if vol < best_vol:
                best_vol, best_rz = vol, float(rz)

    # 3. 应用最优旋转矩阵，并将底面中心平移到世界原点 (0, 0, 0)
    cz, sz = math.cos(best_rz), math.sin(best_rz)
    R = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]], dtype=np.float32) @ Rxy
    new_verts = verts_np @ R.T
    min_pt, max_pt = new_verts.min(axis=0), new_verts.max(axis=0)
    new_verts[:, 0] -= (min_pt[0] + max_pt[0]) / 2.0
    new_verts[:, 1] -= (min_pt[1] + max_pt[1]) / 2.0
    new_verts[:, 2] -= min_pt[2]  # 底面严格贴合 z = 0

    for i, v in enumerate(obj.data.vertices):
        v.co.x, v.co.y, v.co.z = float(new_verts[i, 0]), float(new_verts[i, 1]), float(new_verts[i, 2])
    obj.data.update()
```

#### 5.4 第三步：真实米制尺寸归一与主场景无损摆放（`import_and_place_cleaned_glb`）
修模导出的 `<id>_clean.glb` 已经满足 **`+Y` 正面、`X` 宽度、`+Z` 向上、原点在底面中心**。合入主场景 `07-render/render_scene.blend` 时，通过 `import_and_place_cleaned_glb()` 直接按 `dimensions.md` 中的米制三轴尺寸 `local_dims_xyz = (width_x, depth_y, height_z)` 缩放顶点，并把对象放置到目标底面坐标 `target_pos_bottom_center`：

```python
def import_and_place_cleaned_glb(glb_name, target_name, local_dims_xyz, target_pos_bottom_center, yaw_rad=0.0):
    """导入修模后的 _clean.glb，按真实米制尺寸缩放，底面中心放置到 target_pos_bottom_center。"""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(CLEAN_GLB_DIR / f"{glb_name}_clean.glb"))
    imported = list(set(bpy.data.objects) - before)
    meshes = [o for o in imported if o.type == "MESH"]
    non_meshes = [o for o in imported if o.type != "MESH"]

    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = f"VIS_pixal3d__{target_name}"  # 严格遵守 VIS_ 前缀约定
    for o in non_meshes:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # 按米制尺寸 (width_x, depth_y, height_z) 归一化顶点并保持底面 z=0
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    zs = [v.co.z for v in obj.data.vertices]
    cx, cy, min_z = (min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0, min(zs)
    sx = local_dims_xyz[0] / max(max(xs) - min(xs), 1e-5)
    sy = local_dims_xyz[1] / max(max(ys) - min(ys), 1e-5)
    sz = local_dims_xyz[2] / max(max(zs) - min(zs), 1e-5)
    for v in obj.data.vertices:
        v.co.x = (v.co.x - cx) * sx
        v.co.y = (v.co.y - cy) * sy
        v.co.z = (v.co.z - min_z) * sz
    obj.data.update()

    obj.location = target_pos_bottom_center
    obj.rotation_euler = (0.0, 0.0, yaw_rad)
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    dress_coll.objects.link(obj)  # 放入独立 Collection，方便一键开关对比
    return obj
```

#### 5.5 第四步：混合装配范式（Blender 参数化透明柜壳 + Pixal3D 内部小件阵列）
针对双门玻璃试剂柜、带窗培养箱或立式冰箱，标准工程实践是**「参数化硬表面外壳 + 生成式内部陈设」混合装配**（见 [enrich_scene_pixal3d.py](file:///mnt/d/Projects/Robots/projects/cell-passaging-lab/05-modelling/pixal3d_exp/enrich_scene_pixal3d.py#L216-L270)）：
1. **外壳与透明门用 Blender 参数化构建**：用 `add_box` 建笔直的白色烤漆柜体、三层水平隔板（$z = 0.46, 0.90, 1.34\text{ m}$）、双扇门框以及真正的透射玻璃窗（`Transmission Weight = 0.93, IOR = 1.49, Roughness = 0.04`）；
2. **柜内陈设用 Pixal3D 生成并共享网格实例化**：先调用一次 `import_and_place_cleaned_glb("clean_reagent_bottle", ...)` 导入单个修模后的 500 mL 蓝盖试剂瓶（直径 `82 mm`、高 `175 mm`），再在三层隔板上通过 `b_obj = bottle_proto.copy()`（**共享同一份 `bottle_proto.data` 网格与 2K 贴图，零额外显存开销**）按不同偏航角摆放 16 瓶试剂。透过参数化玻璃门既能看到真实的玻璃折射高光，又能看到内部层次丰富的 3D 试剂瓶。
3. **合入后自检门限**：
   - **`V1`（零碰撞体泄漏）**：断言 `[o.name for o in bpy.data.objects if ("COL_" in o.name or "collision" in o.name.lower()) and not o.hide_render] == []`；
   - **`V3`（动态物理绑定零改动）**：只向独立的 `pixal3d_dressing` Collection 追加 `VIS_pixal3d__*` 与 `VIS_dress__*` 静态视觉对象，绝不修改任何 `ROOT_*` 对象的动画曲线（`action` / `fcurves`）。

---

## 四维实测数据（效果、效率、速度、成本）

### 1. 9 组模型全链路实测明细（NVIDIA L4 24 GB）

| 任务 ID | 级联模式 | 原始面数 $\rightarrow$ 最终面数 | 扩散耗时 | GLB 烘焙 | **单模型总耗时** | 峰值显存 | Blender 剔除外部孤岛 | 自动调平角度 `(rx, ry, rz)` | 适用性结论 |
|---|---|---|---|---|---|---|---|---|---|
| `clean_fridge_1024` | `1024` | `5.68M` $\rightarrow$ `115.4k` (`4.16 MB`) | `160.7 s`* | `20.7 s` | **`182.5 s`** | `20.79 GB`* | `2` 块 (`167` 顶点) | `[+2.0°, 0.0°, -20.9°]` | 大平面边缘偏肉，大冰箱宜改用 Blender 壳+贴图 |
| `clean_fridge_1536` | `1536` | `12.84M` $\rightarrow$ `142.1k` (`5.12 MB`) | `176.7 s` | `31.0 s` | **`208.8 s`** | `18.71 GB` | `0` 块 (`0` 顶点) | `[+2.0°, 0.0°, -20.9°]` | 百叶窗与把手比 1024 锐利，但大平板仍有烘焙脏迹 |
| `crop_fridge_overview_1024` | `1024` | `4.04M` $\rightarrow$ `119.5k` (`4.22 MB`) | `80.4 s` | `23.7 s` | **`104.9 s`** | `12.91 GB` | `8` 块 (`2,152` 顶点) | 对照组不调平 | **反例**：遮挡处坍缩破洞，侧面粘连邻柜残骸 |
| `clean_reagent_cabinet` | `1024` | `15.07M` $\rightarrow$ `74.7k` (`4.38 MB`) | `113.2 s` | `38.2 s` | **`152.5 s`** | `12.91 GB` | `42` 块 (`2,320` 顶点) | `[+0.5°, 0.0°, -18.0°]` | **反例**：玻璃门与内部瓶子糊成不透明白门；应改为 Blender 玻璃柜 + 内部摆生成瓶 |
| `clean_reagent_bottle` | `1024` | `3.71M` $\rightarrow$ `75.3k` (`3.12 MB`) | `55.3 s` | `19.5 s` | **`75.9 s`** | `12.91 GB` | `0` 块 (`0` 顶点) | `[+17.5°, 0.0°, -0.9°]` | **极佳**：75.9s 全场最快，适合批量摆进玻璃试剂柜和台面 |
| `clean_power_box` | `1024` | `7.33M` $\rightarrow$ `92.7k` (`4.16 MB`) | `84.3 s` | `26.9 s` | **`112.2 s`** | `12.91 GB` | `11` 块 (`140` 顶点) | `[+16.0°, +1.5°, +13.5°]` | **极佳**：散热孔、数显、开关与盘绕白线一次成型 |
| `clean_exhaust_hood` | `1024` | `7.93M` $\rightarrow$ `93.5k` (`3.97 MB`) | `95.6 s` | `24.6 s` | **`123.3 s`** | `12.91 GB` | `9` 块 (`301` 顶点) | `[+11.0°, 0.0°, +20.3°]` | **极佳**：波纹管褶皱、不锈钢喉箍与集气腔精度高 |
| `clean_wall_socket` | `1024` | `14.47M` $\rightarrow$ `76.2k` (`3.28 MB`) | `140.9 s` | `34.8 s` | **`176.6 s`** | `12.92 GB` | `13` 块 (`103` 顶点) | `[+16.0°, 0.0°, -22.5°]` | **极佳**：墙面双联插孔、安装挂耳与弯头插头立体感强 |
| `ref_waste_bin` | `1024` | `10.55M` $\rightarrow$ `87.6k` (`4.35 MB`) | `129.1 s` | `29.2 s` | **`159.2 s`** | `12.92 GB` | `11` 块 (`1,401` 顶点) | `[+29.5°, +1.0°, +19.9°]` | **极佳**：不锈钢内胆高光与黑边外桶质感好 |

> *注：任务 1 在优化 NAF `CrossAttention` 前运行；优化后（任务 3–9）`1024_cascade` 峰值显存从 `20.79 GB` 降至 **`12.91 GB`**，平均单模型总耗时 **`129.2 s`**。

### 2. 算力成本核算与优化前后对比

- **硬件与费率**：Colab **NVIDIA L4 (24 GB)**，单价 **`1.94 Compute Units / 小时`**（约 `$0.194 / hr`）。
- **探索期 vs 固化 SOP 算力对比（以 9 个 3D 模型批处理为例）**：

| 环节 | 探索期实测耗时 / 算力 | 优化后五阶段 SOP 耗时 / 算力 | 优化手段 |
|---|---|---|---|
| 开机前准备（筛图、生图、写脚本） | 边开 GPU 边准备（混入租期） | **`0 s` GPU 租期（`0 CU`）** | Stage 0 本地预检门 + 单包 `colab_payload.tar.gz` |
| 环境安装 + 16.7 GB 模型权重拉取 | `52 s` + `182 s` = **`234 s`（`0.13 CU`）** | **`~65 s` 双轨并行 + `~20 s` 热加载（`0.05 CU`）** | `setup_and_prefetch.sh`：`uv venv` 与 `HF_HUB_ENABLE_HF_TRANSFER=1` 8 线程并发预取重叠执行 |
| 9 模型单进程批量生成 + GLB 烘焙 | **`998 s`（`16.6 min`，`0.54 CU`）** | **`998 s`（`16.6 min`，`0.54 CU`）** | 批量 `BiRefNet`/`MoGe-2` 用完即卸 + 共享 `DINOv3+NAF` + 子进程 `export_glb_worker.py` |
| 产物下载 + Gate A 校验 + 关停实例 | 零散下载 + 本地跑完 Blender 才关机 | **`~5 s`（`< 0.01 CU`）** | 单包下载 `outputs.tar.gz` $\rightarrow$ `verify_glb_outputs.py`（`< 0.1 s` 校验 glTF 魔数与面数）$\rightarrow$ **立即 `colab stop` + `trap` 兜底** |
| 本地 Blender 修模 + 场景合入渲染 | 约 `80 s`（期间若未关机白烧 GPU） | **`~80 s`（已关机，`0 CU`）** | Gate B 完全在本地 `0 CU` 下执行 |
| **合计 GPU 计费时长 / 总成本** | **`~104 min` / `3.37 CU`（`¥2.45`）** | **`~18.2 min` / `~0.59 CU`（`¥0.43`，单模型 `~0.065 CU`）** | **消除了 82% 的非推理算力损耗** |

- **可复用流水线脚本清单**（位于项目 `05-modelling/pixal3d_exp/colab_pipeline/`）：
  - `colab_pixal3d_driver.sh`：本地一键主控脚本（含 Stage 0 预检、`trap 'colab stop ...' EXIT INT TERM`、上传、远端执行、下载、Gate A 校验、秒级停机、Gate B 本地 Blender 修模）；
  - `setup_and_prefetch.sh`：远端双轨并行脚本（前台 `uv venv /content/venv310 --python 3.10` 装预编译 CUDA wheels + 打补丁；后台 `HF_HUB_ENABLE_HF_TRANSFER=1` + `ThreadPoolExecutor` 并发拉齐 4 个仓库共 16.7 GB 权重）；
  - `patch_pixal3d.py`：幂等源码补丁（`BiRefNet` 公开权重、`NAF` $256\times$ 分组矩阵乘、`o_voxel` 5 行非流形清理）；
  - `export_glb_worker.py`：`CuMesh` 子进程隔离烘焙器（带 `remesh=False` 降级保护）；
  - `verify_glb_outputs.py`：本地 `< 0.1 s` 二进制 glTF 2.0 魔数头与面数校验器（Gate A 关机门限）。

---

## 踩过的坑（附证据与修复）

1. **`valeoai/NAF` 在 L4 (`sm_89`) 上报 `NATTEN failure: no kernel image is available` 且在 `1536_cascade` 下 24 GB OOM**：
   - 预编译 `natten` 仅含 Hopper (`sm_90`) 内核；且 `valeoai/NAF` 原实现先将 $64\times 64$ 的 1024 维特征 `nearest-exact` 放大 $256\times$ 到 $1024\times 1024$（单张量 4 GB）再做 `dilation=16` 邻域注意力。
   - **修复**：利用 `nearest-exact` 放大 $16\times 16$ 与 `dilation=16` 的数学等价性，把高分 Query 按 $64\times 64$ 低分网格分组为 `[B, 64, 64, N, 256, D]` 直接与低分 $9\times 9$ 窗口做矩阵乘，**NAF 显存降低 $256\times$（从 ~12 GB 降至 `< 0.2 GB`），耗时从 `~110 s` 降至 `18 ms`**。
2. **上游 `inference.py` 重复实例化 4 份 `DINOv3 + NAF` 浪费 `3.6 GB` 显存**：
   - `ss`、`shape_512`、`shape_1024`、`tex_1024` 四个特征提取器原本各自独立加载一份权重；改为共享同一个 `.model` 与 `.naf_model` 实例后，加载耗时仅 `1.65 s`，立省 `3.6 GB` 显存。
3. **上游 `o_voxel/postprocess.py` 在 `remesh=True` 分支漏写拓扑清理导致 `CuMesh` CUDA 700 崩溃**：
   - `o_voxel/postprocess.py` 第 85–88 行写了注释 `# Simplify and clean the remeshed result (similar logic to above)`，却只调用了 `mesh.simplify(decimation_target)`，漏掉了 `remove_duplicate_faces()`、`repair_non_manifold_edges()`、`remove_small_connected_components()` 等 5 行清理代码，导致 `clean_reagent_cabinet`（1,506 万面）简化后的非流形面触发 `CuMesh/src/atlas.cu:503` 非法内存访问。补齐 5 行清理并将 `to_glb` 放入独立子进程 `export_glb_worker.py` 后一次通过。
4. **`requirements-hfdemo.txt` 依赖冲突与 `briaai/RMBG-2.0` 401 门禁**：
   - 先剔除 `MoGe` 用 `uv pip install --index-strategy unsafe-best-match` 安装预编译 CUDA 12.4 wheels（`48 s` 装完），再用 `--no-deps` 装 `MoGe`；将 `BiRefNet.py` 中受门禁限制的 `briaai/RMBG-2.0` 指向公开同构权重 `ZhengPeng7/BiRefNet`。
5. **Blender 直接按 `bmesh` 拓扑边删孤岛会误删 UV Chart**：
   - `o_voxel` 的 `uv_unwrap()` 会沿 UV 接缝切开并复制顶点，导致单个模型在拓扑上分裂为数千个 UV 块（直接按拓扑边过滤会删掉集气罩的蓝色波纹管和冰箱门贴）。必须按 `2 mm` 三维空间网格聚合顶点后再过滤孤岛。
6. **WSL2 调用 Windows `blender.exe` 挂起**：
   - 从 Linux ext4 目录直接调 `blender.exe` 且未关闭 `stdin` 管道会在 WSL2 Interop 处阻塞；必须先 `cd /mnt/d/...` 并重定向 `< /dev/null`。

## 阶段日志摘要

Colab 环境安装约 48 s，9 个 3D 模型稳态批量推理共 19.7 min（耗费 0.64 CU），本地 Blender 5.4 自动修模与 9 张预览图渲染 22 s，主场景合入与双机位对比渲染 58 s。
