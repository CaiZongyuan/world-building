# 经验记录

流程每个阶段一份，阶段复盘后更新。由这里提炼出的 skill：`.agents/skills/lab-scene-pipeline`（见 `docs/adr/0001`）。

**入门先读教程站点**：https://caizongyuan.github.io/world-building/（源码 `site/`）。七个阶段怎么接力、物理建模与物理测试、怎么用 skill，附 7 个可在浏览器里运行 MuJoCo 的实验台。
- 实验台定义 `site/labs/labs.json` 由网页、`runner.py`（生成预计算回放 `site/labs/fallback/`）、`play.py`（在本机 MuJoCo 窗口里播放）共用；改了定义要重跑 `runner.py`。
- 项目的案例页与专项评测已发布到教程站点：[薄切片 01](https://caizongyuan.github.io/world-building/cases/slice-01)、[全流程实验室](https://caizongyuan.github.io/world-building/cases/full-lab)、[Colab 3D 生成与 Blender 修模](https://caizongyuan.github.io/world-building/cases/pixal3d-dressing)。

每份阶段记录的固定结构：这一步做什么 → 输入 / 产物 / 完成判据 → 工具与调用方式 → 标准做法 → 踩过的坑（附证据）→ 阶段日志摘要。

| 文件 | 阶段 | 状态 |
|---|---|---|
| `00-prior-lumen-1104.md` | 先验（1104 项目经验，导入） | 只读 |
| `01-requirements-grilling.md` | 需求访谈 | 初稿（薄切片 01） |
| `02-proposal-preview.md` | 方案预览 | 初稿（薄切片 01） |
| `03-plan.md` | plan | 初稿（薄切片 01） |
| `04-reference-images.md` | 参考图 | 初稿（薄切片 01） |
| `05-modelling.md` | 建模 | 初稿（薄切片 01） |
| `06-simulation.md` | 仿真 | 初稿（薄切片 01）· 问题最大的阶段 |
| `07-pose-binding-render.md` | 位姿绑定与渲染 | 完成（薄切片 01 + 全流程实验室） |
| `08-retro-slice01.md` | 汇总复盘（薄切片 01） | 完成 |
| `09-pixal3d-colab-scene-dressing.md` | Colab 3D 生成陈设与 Blender 修模合入 | 完成（全流程实验室） |
