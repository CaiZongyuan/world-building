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

### 4. Blender 5.4 自动修模三步法

原始生成的 `.glb` 不能直接摆进场景，必须经过脚本自动执行三步修模：
1. **三维空间容差（`2 mm`）连通域去碎块**：将三维距离 $\le 2\text{ mm}$ 的顶点聚为同一空间连通分量（把被 `uv_unwrap` 切开的 UV 接缝重新焊合），再删除顶点数不足主体 2% 的外部悬空孤岛；
2. **最小包围盒体积（Minimum-Volume OBB）自动调平**：在俯仰/横滚/偏航角上做粗到细网格搜索使三维 AABB 体积最小，自动消除 `MoGe-2` 单图俯视带来的 `11°–29°` 倾角，让底面水平贴合 $z=0$；
3. **统一坐标系与无损合入**：修模后统一为 **`+Y` 正面、`X` 宽度、`+Z` 朝上、原点在底面中心**，按真实米制尺寸缩放，以 `VIS_pixal3d__*` 命名放入独立 Collection。

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
