# 先跑 MuJoCo 物理，再把位姿绑定到 Blender 渲染；不手 K 帧

运动一律由 MuJoCo 仿真产生，记录的刚体位姿再绑定到 Blender 视觉模型，用 Cycles（OptiX）渲染。手 K 帧的传代动画已因穿模和夹爪错误被否决（`modeling/cell-passage-20261029/REJECTED_REVIEW.md`），所以“直接在 Blender 里做动画更快”这条路是被刻意放弃的。Blender 钉 5.4，Windows 侧 `blender.exe -b` 由 WSL 调用；Newton / Isaac 只作可选交叉验证。
