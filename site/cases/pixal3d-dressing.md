---
title: Colab 3D 生成与 Blender 修模
description: 用 Colab L4 批量运行 TencentARC/Pixal3D 生成实验室异形小件，经 Blender 5.4 自动修模后合入渲染场景的完整流程、代码与四维评测。
---

# Colab 3D 生成陈设与 Blender 自动修模

**一句话**：核心交互设备和大件规整柜体（冰箱、透明玻璃门试剂柜、实验台架）用 Blender 参数化建模；非接触异形小件（台下 UPS 电源盒、蓝色波纹集气罩、墙面双联插座、柜内 500 mL 试剂瓶、不锈钢废料桶）在远程 Colab L4 GPU 上按**五阶段零浪费 SOP** 批量运行 `TencentARC/Pixal3D` 单图转 3D，经本地 Blender 5.4 四步自动修模后作为 `VIS_pixal3d__*` 视觉对象无损合入场景。

<div class="wb-grid2">
<figure class="wb-figure"><img :src="$withBase('/img/pixal3d/overview_before.webp')" alt="合入前全景" /><figcaption><b>合入前（01_overview）</b>：左后方冰箱与试剂柜仅为白盒占位，墙面无插座与线槽，地面与台下缺乏真实机电细节。</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/pixal3d/overview_after.webp')" alt="合入后全景" /><figcaption><b>合入后（01_overview_pixal3d）</b>：采用「Blender 参数化透明玻璃门试剂柜 + 内部 16 个 Pixal3D 生成试剂瓶」混合装配，补充台下电源盒、集气罩、插座线槽与地面斑点环氧材质。</figcaption></figure>
</div>

<div class="wb-grid2">
<figure class="wb-figure"><img :src="$withBase('/img/pixal3d/centrifuge_before.webp')" alt="合入前离心机特写" /><figcaption><b>合入前（03_centrifuge）</b>：离心机与开盖器周边台下空旷，缺少排风集气罩、电源盒、废料桶与墙面供电插头。</figcaption></figure>
<figure class="wb-figure"><img :src="$withBase('/img/pixal3d/centrifuge_after.webp')" alt="合入后离心机特写" /><figcaption><b>合入后（03_centrifuge_pixal3d）</b>：合入 Pixal3D 生成并经 Blender 自动调平的波纹集气罩、230V 电源盒（带盘绕线）、双联插座插头与废料桶，V1/V3 验证门全部 PASS。</figcaption></figure>
</div>

---

## 一、 参数化建模与 AI 3D 生成的分工边界

单图 3D 生成模型并不是万能的。本次实验最核心的工程结论是**划清硬表面参数化建模与 AI 3D 生成的边界**：

| 对象类型 | 典型例子 | 推荐做法 | 为什么不能反过来 |
|---|---|---|---|
| **大型规整箱体与带透明门的柜体** | 立式冰箱、双门玻璃试剂柜、实验台铝型材框架、安全护栏 | **Blender 参数化硬表面建模**：<br/>① **外壳+内部组合法**：用 Blender 建笔直的柜体、隔板和真正的透射玻璃门（`Transmission=0.93`），里面的试剂瓶等小物件逐个用 3D 模型生成后摆进去；<br/>② **几何体+局部贴图法**：用 Blender 建规整冰箱几何体，外面贴正交面板贴图 | 单图 3D 扩散 + Dual Contouring 重拓扑在大面积平板与直棱角上边缘发“肉”、表面有波浪感，且烘焙进贴图的阴影与场景光照冲突；同时 `o_voxel` 强制导出 `OPAQUE` 材质，会把透明玻璃门和内部瓶子糊成高达 1,500 万面的实心白门 |
| **异形机电小件、软管线缆与散装容器** | 台下 230V UPS 电源盒（带盘绕电源线）、集气罩与蓝色波纹软管（带金属喉箍）、墙面双联插座（带弯头插头线）、500 mL 蓝盖培养基瓶、不锈钢内胆废料桶 | **Colab Pixal3D 批量单图转 3D + Blender 自动修模** | 这类小件包含螺旋波纹、盘绕电线、圆角倒角与复杂丝印，手工写参数化脚本极慢；3D 生成模型能一次还原褶皱几何与 2K PBR 材质（高光/粗糙度/金属度），放在台下、墙面或柜内隔板上效果极佳 |

<figure class="wb-figure"><img :src="$withBase('/img/pixal3d/grid_9models.webp')" alt="9 组 Pixal3D 模型修模后预览" /><figcaption>Colab L4 批量生成的 9 组 `.glb` 模型经 Blender 5.4 三维空间容差（2 mm）去碎块与最小包围盒体积（Min-Volume OBB）自动调平后的正交预览对比。</figcaption></figure>

---

## 二、 Colab 五阶段零浪费 SOP（耗时与算力削减 82%）

首次探索实验共消耗 **`3.37 CU`（约 104 分钟 L4 租期）**，但 9 个模型的纯批量推理仅占 **`16.6 min`（`0.54 CU`）**——高达 **82%** 的算力浪费在「开机后才准备参考图与脚本、串行单线程拉取 16.7 GB 权重（`182 s`）、排障重拉权重、以及本地跑 Blender 时未及时关停远端 GPU」。将全流程固化为以下 **五阶段 SOP** 后，9 模型总租期压缩至 **`~18.2 min`（`~0.59 CU`，折合单模型约 `¥0.05 RMB`）**：

| 阶段 | 执行位置与计费 | 核心动作 | 耗时（优化前 $\rightarrow$ 优化后） | 关键防呆与加速手段 |
|---|---|---|---|---|
| **Stage 0：开机前本地预检（Pre-Flight）** | 本地 WSL（**`0 CU`**） | ① 按分工筛除大柜体，只留异形小件；<br/>② 备齐全部 `.webp` 净图（浅灰底、无遮挡、3/4 视角、`FOV 20°–28°`）；<br/>③ 跑 `colab whoami` 与 `colab sessions` 确认凭证有效且无残留实例；<br/>④ 将 `inputs/*.webp`、补丁与批处理脚本打成**单包 `colab_payload.tar.gz`** | 混入租期 $\rightarrow$ **GPU 计费 `0 s`** | **严禁开机后再生成参考图或写脚本**；单包上传替代十余次零散 `colab upload` |
| **Stage 1：开机 + 双轨并行初始化** | Colab L4（**`1.94 CU/hr`**） | ① 本地先挂载 `trap 'colab stop -s pixal3d' EXIT INT TERM` 防异常泄漏；<br/>② `COLAB_CLI_RETRIES=1` 秒级申请 L4 并单次上传 `colab_payload.tar.gz`（`~12 s`）；<br/>③ 运行 `setup_and_prefetch.sh` **双轨并行**：<br/>• **轨道 A（CPU/磁盘，`~52 s`）**：`git clone` + `uv venv --python 3.10` + 预编译 `cp310` CUDA wheels + `patch_pixal3d.py` 自动打齐 3 处补丁；<br/>• **轨道 B（网络并发，`~55–65 s`）**：后台利用系统 Python 开启 `HF_HUB_ENABLE_HF_TRANSFER=1` + `snapshot_download(max_workers=8)` 并发预取 `Pixal3D`（15 GB）、`BiRefNet`（444 MB）、`MoGe-2`（1.3 GB）与 `NAF` | 串行 `234 s` $\rightarrow$ **双轨并行 `~65 s`**（热缓存加载仅 `~20 s`） | 利用 `uv` 装包期间的空闲网卡带宽并发拉满 1–2 Gbps 权重下载，消除首次推理 `182 s` 的串行 HTTP 阻塞 |
| **Stage 2：单进程四步批量生成** | Colab L4（**`1.94 CU/hr`**） | 单进程 `run_batch.py` 顺序执行：<br/>① **批量 `BiRefNet` 抠图**（首图含加载 `8.7 s`，后续 `0.8 s/张`）$\rightarrow$ **`del` 释放 `1.2 GB` 显存**；<br/>② **批量 `MoGe-2` 外参估计**（首图含加载 `9.5 s`，后续 `0.2 s/张`）$\rightarrow$ **`del` 释放 `1.5 GB` 显存**；<br/>③ **共享单份 `DINOv3+NAF`（省 `3.6 GB`）逐个跑 `1024_cascade` 扩散**（`55–140 s/个`，峰值显存稳定 `12.91 GB`），原始网格存 `/tmp/current_mesh.pt`；<br/>④ **子进程 `export_glb_worker.py` 隔离烘焙 GLB**（`20–38 s/个`），远端自动打包 `/content/outputs.tar.gz` | **`~129 s / 模型`**（9 模型共 `16.6 min`，`0.54 CU`） | 预处理模型用完即卸；C++/CUDA `CuMesh` 放入独立子进程并带 `remesh=False` 自动降级，主进程 15 GB 权重永不崩溃重拉 |
| **Stage 3：产物下载、Gate A 秒级校验与立即关机** | 远端 $\rightarrow$ 本地（**校验通过即刻停机**） | ① 单次 `colab download` 拉回 `outputs.tar.gz`（30 MB 约 `3–5 s`）；<br/>② 本地运行 `verify_glb_outputs.py`（**`< 0.1 s`**）做 **Gate A 完整性校验**：核对模型数量、glTF 2.0 魔数头（`0x46546C67`）、JSON 块可解析、`final_faces > 5000`；<br/>③ **Gate A 打印 `GATE_A_PASS` 后 1 秒内执行 `colab stop -s pixal3d`**，并用 `colab sessions` 确认输出 `No active sessions.` | **`~5 s`**（关机后 GPU 计费归零） | **验证拆为两级**：关机前只做 `< 1 s` 的二进制/面数完整性校验（Gate A），**绝不挂着 GPU 等待本地 Blender 渲染** |
| **Stage 4：本地 Blender 修模与场景验证（Gate B）** | 本地 WSL + Windows Blender 5.4（**`0 CU`**） | ① 运行 `render_glb_sheet.py` 做 `2 mm` 空间容差去碎块、最小包围盒体积调平与 `.webp` 预览渲染（`22 s`）；<br/>② 运行 `enrich_scene_pixal3d.py` 合入场景并渲染对比图（`58 s`），通过 `V1`（0 碰撞体泄漏）与 `V3`（动态位姿零改动）验证 | **`~80 s`**（纯本地，**`0 CU`**） | 本地修模与 Cycles 渲染完全不依赖 Colab，必须在确认 `colab stop` 之后执行 |

---

## 三、 详解一：如何在 Colab 上配置与批量运行 Pixal3D

### 1. 输入参考图四项硬指标与 Prompt 模板
`Pixal3D` 的前端由 `BiRefNet`（前景分割）+ `MoGe-2`（单目深度与相机内参/外参估计）组成，输入图必须满足：
1. **孤立单品、浅灰/纯白净底（RGB `225–240`）**：绝不用实景遮挡切图（实景切图如 `crop_fridge_overview` 会把相邻玻璃搁板误判为前景粘在模型侧面，遮挡处在体素扩散中坍缩成破洞）；
2. **标准 3/4 等轴微俯视角（俯角 `10°–20°`，水平偏角 `25°–35°`）**：必须同时露出物体的**正面、一侧侧面与顶面**；
3. **中长焦平缓透视（等效焦距 `50–85 mm`，对应 `MoGe-2` 估计 `fov_deg` 在 `20°–28°` 之间）**；
4. **分辨率与格式**：统一使用 `1024×1024` `.webp`。生成 Prompt 模板：
   ```text
   Single isolated [设备英文名, 如 laboratory under-bench UPS power supply box with coiled white power cord], 3/4 isometric product view, slight 15-degree top angle, neutral light-grey studio background, soft even studio lighting, no cast shadows on background, sharp industrial details, 50mm lens, photorealistic
   ```

### 2. 双轨并行初始化与 3 处必打源码补丁
Colab 默认环境为 Python 3.12（`cp312`），而 `Pixal3D` 依赖的 4 个核心 C++/CUDA 扩展（`o_voxel`、`cumesh`、`flex_gemm`、`nvdiffrast`）官方仅提供 **Python 3.10 (`cp310`) + PyTorch 2.6 (`cu124`)** 的预编译 wheel。开机后执行 `setup_and_prefetch.sh` 双轨并发初始化：

```bash
#!/usr/bin/env bash
set -euo pipefail

# 轨道 B (后台并发): 开启 Rust hf_transfer + 8 线程并发预取 16.7 GB 权重 (~55-65s)
(
  pip install -q hf_transfer huggingface_hub >/dev/null 2>&1 || true
  export HF_HUB_ENABLE_HF_TRANSFER=1
  python3 - <<'PY'
import concurrent.futures, torch
from huggingface_hub import snapshot_download

REPOS = [
    ("TencentARC/Pixal3D", ["ckpts/**", "*.json", "*.yaml", "*.pth", "*.safetensors"]),
    ("ZhengPeng7/BiRefNet", ["*.safetensors", "*.json", "*.py"]),
    ("Ruicheng/moge-2-vitl-normal", ["*.pt", "*.json"]),
]
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
    for fut in [pool.submit(lambda r: snapshot_download(r[0], allow_patterns=r[1], max_workers=8), item) for item in REPOS]:
        fut.result()
try:
    torch.hub.load("valeoai/NAF", "naf", pretrained=True, trust_repo=True)
except Exception:
    pass
PY
) &
PID_PREFETCH=$!

# 轨道 A (前台 ~52s): Python 3.10 虚拟环境 + 预编译 CUDA 12.4 wheels + 源码补丁
git clone --depth 1 https://github.com/TencentARC/Pixal3D.git /content/Pixal3D
uv venv /content/venv310 --python 3.10
grep -v -E "^MoGe" /content/Pixal3D/requirements-hfdemo.txt > /tmp/requirements_clean.txt
uv pip install -p /content/venv310/bin/python --index-strategy unsafe-best-match -r /tmp/requirements_clean.txt hf_transfer
uv pip install -p /content/venv310/bin/python --no-deps "MoGe @ git+https://github.com/EasternJournalist/MoGe.git@a8c37341bc0325ca99b9d57981cc3bb2bd3e255b"
/content/venv310/bin/python /content/payload/patch_pixal3d.py

wait "$PID_PREFETCH"
```

其中 `patch_pixal3d.py` 自动修复上游 3 处致命问题：
1. **抠图权重替换**：将 `BiRefNet.py` 中报 `401 Unauthorized` 的受门禁模型 `briaai/RMBG-2.0` 替换为同构公开权重 `ZhengPeng7/BiRefNet`；
2. **`valeoai/NAF` 邻域注意力 $256\times$ 显存优化（解决 L4 `sm_89` 算子报错与 24 GB OOM）**：利用 `nearest-exact` 放大 $16\times 16$ 与 `dilation=16` 的数学等价性，将高分 Query 按 $64\times 64$ 网格分组为 `[B, 64, 64, N, 256, D]` 直接与低分 $9\times 9$ 窗口做矩阵乘，**NAF 显存从 `~12 GB` 降至 `< 0.2 GB`，耗时从 `110 s` 降至 `18 ms`**；
3. **`o_voxel/postprocess.py` 补齐 `remesh=True` 非流形清理（根治 `CuMesh` CUDA 700 崩溃）**：在 `if remesh:` 分支的 `mesh.simplify(decimation_target)` 后补齐上游遗漏的 5 行清理代码：
   ```python
   mesh.remove_duplicate_faces()
   mesh.repair_non_manifold_edges()
   mesh.remove_small_connected_components(1e-5)
   mesh.fill_holes(max_hole_perimeter=3e-2)
   mesh.unify_face_orientations()
   ```

### 3. 单进程四步批量推理脚本与子进程隔离烘焙
```python
import subprocess, sys, torch
from PIL import Image
sys.path.insert(0, "/content/Pixal3D")
from pixal3d.pipelines import Pixal3DPipeline
from pixal3d.pipelines.rembg import BiRefNet
from moge.model.v2 import MoGeModel

# Step 1: 批量 BiRefNet 抠图 + 居中正方形裁剪，跑完即 del 释放 1.2 GB 显存
rembg_model = BiRefNet(model_name="ZhengPeng7/BiRefNet").cuda()
preproc_images = {t["id"]: rembg_model(Image.open(t["input_path"]).convert("RGB")) for t in TASKS}
del rembg_model
torch.cuda.empty_cache()

# Step 2: 批量 MoGe-2 估计相机视野角 (fov_deg) 与外参，跑完即 del 释放 1.5 GB 显存
moge = MoGeModel.from_pretrained("Ruicheng/moge-2-vitl-normal").cuda().eval()
cam_params = {tid: estimate_camera_with_moge(moge, img) for tid, img in preproc_images.items()}
del moge
torch.cuda.empty_cache()

# Step 3: 加载 Pixal3D 主干，并让 4 个特征提取器共享单份 DINOv3 + NAF 实例（立省 3.6 GB 显存）
pipe = Pixal3DPipeline.from_pretrained("TencentARC/Pixal3D")
shared_ext = pipe.models["image_cond_model_ss"]
for k in ("image_cond_model_shape_512", "image_cond_model_shape_1024", "image_cond_model_tex_1024"):
    if k in pipe.models:
        pipe.models[k].model = shared_ext.model
        pipe.models[k].naf_model = shared_ext.naf_model
pipe.cuda()

# Step 4: 逐任务跑 3D 稀疏体素扩散 + 子进程隔离导出 GLB
for t in TASKS:
    tid = t["id"]
    mesh = pipe.run(
        image=preproc_images[tid],
        seed=42,
        pipeline_type=t.get("pipeline_type", "1024_cascade"),  # 小件一律用 1024_cascade (12.9 GB VRAM)
        sparse_structure_sampler_params={"steps": 12, "cfg_strength": 7.5},
        shape_slat_sampler_params={"steps": 12, "cfg_strength": 7.5},
        tex_slat_sampler_params={"steps": 12, "cfg_strength": 3.0},
        camera_params=cam_params[tid],
    )[0]
    torch.save({
        "vertices": mesh.vertices.cpu(), "faces": mesh.faces.cpu(),
        "attr_volume": mesh.attrs.cpu(), "coords": mesh.coords.cpu(),
        "attr_layout": pipe.pbr_attr_layout, "grid_size": mesh.grid_size,
    }, "/tmp/current_mesh.pt")
    torch.cuda.empty_cache()

    # 子进程运行 o_voxel.postprocess.to_glb，保护主进程 15 GB 权重永不崩溃
    subprocess.run([
        "/content/venv310/bin/python", "/content/payload/export_glb_worker.py",
        "/tmp/current_mesh.pt", f"/content/outputs/{tid}.glb",
        str(t.get("decimation_target", 90000)), "2048", "1",
    ], check=True)
```

### 4. Gate A 秒级二进制完整性校验与立即关机
远端将 `/content/outputs` 打包为 `outputs.tar.gz` 并单次下载回本地后，**在关停 Colab 前只做耗时 `< 0.1 s` 的 Gate A 校验**（检查每个 `.glb` 的前 4 字节魔数 `0x46546C67 == b"glTF"`、版本号 `2`、文件大小一致、JSON chunk 包含网格与贴图、且 `final_faces > 5000`）。一旦打印 `GATE_A_PASS`，**1 秒内执行 `colab stop -s pixal3d` 并通过 `colab sessions` 确认输出 `No active sessions.`**，绝不挂着 GPU 等待本地 Blender 渲染。

---

## 四、 详解二：Blender 5.4 自动修模与场景合入四步法

### 1. 为什么原始生成的 `.glb` 不能直接摆进场景？
1. **UV 接缝切裂导致拓扑碎裂与外部悬空噪点并存**：`o_voxel` 的 `CuMesh.uv_unwrap()` 会沿所有 UV 接缝切开网格并复制顶点，导致单个物体在 `bmesh` 拓扑边上分裂成数千个 UV 块；同时 3D 扩散常在机身外残留几百到几千个顶点的真正悬空碎块（如 `clean_reagent_cabinet` 外围有 42 个悬空孤岛、2,320 个噪点顶点）。**若直接按 `bmesh` 拓扑边删小连通块，会把蓝色波纹管、门把手、贴纸全部误删！**
2. **单图相机俯仰/横滚倾角烘焙进顶点**：`MoGe-2` 从 3/4 视图估计的相机倾角（`11°–29.5°`）残留在导出网格中，直接放在水平桌面上会整体后仰或侧歪。
3. **尺度与原点随意**：导出顶点位于 `[-0.5, 0.5]^3` 归一化盒，原点在几何中心而非底面中心。

### 2. 第一步：三维空间容差（`2 mm`）网格哈希连通域过滤（跨 UV 接缝焊合）
将每个顶点的三维坐标量化到 `spatial_tol = 0.002`（`2 mm`）三维网格桶 `pos_buckets`；BFS 搜索连通分量时，同时沿拓扑边 `curr.link_edges` 和 27 邻域空间网格桶扩展，把被 UV 接缝切开的重合顶点在三维空间中逻辑焊合，从而 100% 保护主体表面分片，仅剔除顶点数不足主体 `2%` 的真正外部悬空碎块：

```python
from collections import defaultdict, deque
import bmesh

def remove_floating_islands_and_clean(obj, min_ratio=0.02, spatial_tol=0.002):
    """按 2mm 三维空间容差聚合连通分量（跨 UV 接缝焊合），仅剔除外部悬空碎块。"""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()

    loose_v = [v for v in bm.verts if not v.link_faces]
    if loose_v:
        bmesh.ops.delete(bm, geom=loose_v, context="VERTS")
        bm.verts.ensure_lookup_table()

    inv_tol = 1.0 / spatial_tol
    pos_buckets = defaultdict(list)
    for v in bm.verts:
        key = (int(round(v.co.x * inv_tol)), int(round(v.co.y * inv_tol)), int(round(v.co.z * inv_tol)))
        pos_buckets[key].append(v)

    visited = set()
    components = []
    for v in bm.verts:
        if v.index in visited:
            continue
        comp, q = [], deque([v])
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

### 3. 第二步：粗到细最小包围盒体积（Minimum-Volume OBB）自动调平
当正交工业小件因相机视角而倾斜 `11°–29°` 时，其世界轴对齐包围盒（AABB）体积 $\Delta X \cdot \Delta Y \cdot \Delta Z$ 会显著膨胀；当且仅当旋转矩阵 $R(r_x, r_y, r_z)$ 使物体的底面与侧壁严格对齐世界 $X/Y/Z$ 轴时，AABB 体积达到极小值。对 8,000 个采样顶点做两级粗到细网格搜索（单模型耗时 `< 80 ms`），即可自动扶正模型并将底面中心归零到 `(0, 0, 0)`：

```python
import math, numpy as np

def level_mesh_upright(obj, max_tilt_deg=28.0):
    """通过最小化三维 AABB 体积自动消除相机俯仰/横滚/偏航倾角，并将底面中心归零。"""
    verts_np = np.array([[v.co.x, v.co.y, v.co.z] for v in obj.data.vertices], dtype=np.float32)
    sample = verts_np[np.linspace(0, len(verts_np) - 1, 8000, dtype=int)] if len(verts_np) > 8000 else verts_np

    best_rx, best_ry, best_rz, best_vol = 0.0, 0.0, 0.0, float("inf")
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

### 4. 第三步与第四步：真实米制尺寸归一、混合装配与 `V1`/`V3` 门限验证
1. **米制尺寸归一化**：修模后的 `_clean.glb` 统一为 **`+Y` 正面、`X` 宽度、`+Z` 向上、原点在底面中心**。导入 `07-render/render_scene.blend` 时按 `dimensions.md` 的 `(width_x, depth_y, height_z)` 缩放顶点，直接放置到台面或地面高度 $z_{\text{target}}$，并命名为 `VIS_pixal3d__*` 挂入独立的 `pixal3d_dressing` Collection。
2. **透明柜壳 + 生成瓶混合装配**：双门玻璃试剂柜用 Blender 参数化建模笔直柜壳、三层隔板与 `Transmission=0.93` 透明玻璃门，内部将修模后的 `clean_reagent_bottle_clean.glb` 通过 `bottle_proto.copy()`（共享网格与 2K 贴图，零额外显存开销）实例化 16 瓶摆上隔板。
3. **验证门自检**：合入后检查场景中可渲染的 `COL_` / `collision` 对象数为 `0`（`V1` PASS），且全部 27,358 帧 MuJoCo 刚体动画曲线零改动（`V3` PASS）。

---

## 五、 9 组模型四维实测数据明细（NVIDIA L4 24 GB）

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

经验记录原文：`docs/lessons/09-pixal3d-colab-scene-dressing.md`。
