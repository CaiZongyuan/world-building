> **先验经验（导入，未经本流程复核）**
> 来源：`modeliing1104/Assets_13_latest_candidates_and_increments.zip` → `03_project_modeling_lessons.zip` → `project_modeling_lessons_20261104/MODELING_LESSONS_zh.md`。文中证据路径指向原工作区，不在本仓库。
> 本流程的阶段经验记录会引用这里的条目，但不修改本文。

# 原创资产与场景建模：本次可复用经验

记录日期：2026-11-04。范围：当前可访问项目文件与已有独立QA的证据总结，不是新的物理仿真、法律审查或制造认证。所有相对证据路径以 `/workspace/scratch/a4c872a5ae85/` 为根；显式绝对路径除外。本记录独立保存，不更改旧资产、失败记录或任何skill，不上传Drive。

## 1. 先把概念、原创范围与许可拆开

- 概念图只冻结风格、构图、配色与产品意向；不能直接充当工程图。尺寸、密度、涂层、光学参数、紧固与密封分别记“标准锚点／设计假设／实测”。
- 新创Lumen几何不等于全部场景原创。保留第三方机器人来源、许可、不可变blob/SHA清单；不得给Panda改贴原创品牌。第三方软件许可、第三方网格许可与自建几何权利也分别列账。
- “可商用”应写清具体来源和许可证据，不扩大为商标清查、完整权利担保或OEM认证。Lumen是项目艺术身份；本次没有商标排查结论。
- 证据：`workstation_lumen_v02/SOURCE_NOTICE.md`；`lumen_style_studies/`概念图；`passaging_p3_visual_pipeline/assets/panda/PROVENANCE.md`及该目录许可文件。Panda来源记录覆盖49件视觉OBJ与Git blob校验，不能说整个场景是从零原创。

## 2. 支撑必须有真实载荷链，不只是看起来贴合

- 在建模前画出“载物→托盘→轴/滚轮→轨道→安装件→桌架→地面”的实体链；每个节点检查材料连续性、连接方式、真实孔/壁厚和装配顺序。软件同一刚体、焊接布尔融合或零穿插都不等于现实连接合格。
- R04轨道只沿边线相接，导出STL也非水密；R05补连续转角材料并逐件重载PLY验证。教训：必须验最终导出字节，不只验内存对象。
- 支座v02将原32.5µm穿插改为明确2µm间隙，但接触面积为0，机器人仍世界固定。必须标为“装配微间隙候选”，不能说承载通过；法兰投影覆盖不等于真实接触面积。
- 弯曲、剪切、承压、疲劳、预紧、制造公差不能互相替代。2mm滚轮轴仅算剪切会遗漏约316.65MPa的简化弯曲需求；3mm修订约93.82MPa仍未与材料许用及安全系数闭合。
- 证据：`workstation_layout_assessment_20261103/revision_05/REPORT_zh.md`、`load_screen.json`、`initial_disconnected_rail_and_2mm_axle_LIMIT.json`；`robot_pedestal_lumen_v02/README_zh.md`、`qa/interface_clearance.json`。

## 3. MuJoCo先验证自由体和碰撞“真的会失败”

- 编译后核查free joint、equality/mocap、碰撞角色/过滤、初始化后是否写载物qpos；不能用位置跟随、隐藏约束或关闭碰撞做“通过”。接触法向力应转换到共同世界系并核对作用方向。
- 正例必须配负例：去支撑应在松爪前停止；故意过插应产生可检测碰撞。`transfer_negative_audit_v10/full_workflow_report.json`实测支撑力0N，于86.781s触发`support_before_release_failed`，这是这个版本的负例，不能直接外推所有版本。
- 离心机独立审查保留适配器/试管过插负例与偏角失败，避免碰撞全关闭产生假阳性。逐步位置误差、穿透、接触力和强度是不同观测量。
- 有限离散姿态、局部直线路径和少数接触采样不能称连续扫掠、完整工作域或全程峰力。报告测试角度、步距、时间窗口、对象数及未采样范围。
- 证据：`p3_independent_full_run_review_zh.md`；`transfer_negative_audit_v10/full_workflow_report.json`；`/workspace/shared/centrifuge_v03_independent_qa/INDEPENDENT_REVIEW_zh.md`。

## 4. 源几何、碰撞代理与视觉资产保持可追溯对应

- 给每个部件显式标注visual/collision/physics-root；用映射表管理来源、坐标、单位、质量、材料、代理误差和允许差异。不要按名字、无材质或hide_render猜测导出角色。
- 16边碰撞代理和96边视觉曲面可以合理不同，但必须量化净空；字节不同也未必物理不同，需比较编译后的顶点/面/变换。反之，画面相似不证明碰撞形状等价。
- P1 GLB曾实际导入出62件无材质COL代理、744面。冻结原件不覆盖；新视觉导出在隔离副本中明确排除代理，重开核对象清单。不要把该数量套用其他格式/版本。
- 物理体世界变换驱动正式视觉几何；不以碰撞壳替代机器人外观。几何修改、碰撞修订、质量惯量和视觉重建必须写明联动或未联动。
- 证据：`passaging_exchange_known_limits_20261103.md`；上述离心机独立审查；`passaging_p3_verified_visual_v3/qa/reopened_timeline_audit.json`（当前COL_objects为空）。

## 5. 跨引擎与Blender画质分开验收

- 用分层状态：文件生成→解析/重开→目标引擎结构导入→关节/碰撞/材料读回→目标引擎动力学→打包运行。上一层不能替下一层。
- Newton/UE5目前NOT_RUN。脚手架、文档对照、GLB/USD读回、MuJoCo通过都不代表Newton或UE5通过；Sequencer播放也不是Chaos仿真。
- 目标引擎逐项对照单位/手性、wxyz/xyzw转换、刚体世界矩阵、关节轴和正方向、质量/COM/惯量、过滤、接触参数、执行器与自由体。源字段无法映射时明确记缺失，不能静默删掉再宣称等价。
- Blender保留原生节点材料不等于GLB/USD等价；透明、金属、文字、微纹理分别重导入并实际看像素。静帧、时间轴、连续视频和物理合格是不同验收。
- 新v3视觉绑定13,875真实/终态时点，315曲线；100Hz采样间30fps画面是NLERP等视觉插值，不是新增动力学。末帧静止补齐约7.733ms需披露。
- 三张验证帧不能代替整片遮挡/裁切审核。当前单线程CPU样帧89.66–192.33s/帧，整片粗估104–222小时；先做目标硬件短片吞吐测试，不能把线性估算当GPU承诺。
- 证据：`engine_import_audit/P3_ACCEPTANCE_zh.md`；`passaging_p3_verified_visual_v3/README_zh.md`、`qa/reopened_timeline_audit.json`、`qa/sample_render_manifest.json`。本记录未重新查询外部引擎API，执行时须按目标版本再核对。

## 6. 预注册验收、独立审查与失败保留

- 先冻结测量基线、时间窗口、终态条件和门限，再运行。runner停止界限与最终验收门限要分别命名；退出码0不能替代严格验收。
- 原P3 r2完成117.7256s，但最大被动平移0.225173668mm超过0.1mm严格限，仍为FAIL。不能事后改限或抹去失败。
- 新v3把21秒真实闭门预静置纳入完整流程，20–21s稳定窗口5001样本，通过后才启动动作时钟。原初态新运行、不重置自由体、不拼接试验末态；693628步/138.7256s，严格脚本17项通过，最大被动平移0.004089101mm。该通过只属于新合同/新分支。
- 最新结果文件可优先于旧准备说明，但应明确时间和阶段：v3内`metadata/REVIEW_NOTES.md`保留v2准备阶段内容，不能读到“未开始”就否定后来的实际终态，也不能用旧准备通过替代新运行证据。
- 证据：`p3_independent_full_run_review_zh.md`；`passaging_integration_p3_checkpoint_r2/qa/continuous_run/additional_acceptance_review.json`；`passaging_p3_presettle_fullflow_revision_v3/qa/RESUMED_FULLFLOW_RESULT_zh.md`、`qa/continuous_run/strict_acceptance_review.json`。本记录未独立重跑全流程，当前v3额外独立worker验收状态应由主任务另行更新。

## 7. 检查点既要恢复计算，也要恢复证据

- 保存原生MjData、版本、输入哈希、控制器门状态、累计统计和有效记录行数；latest原子替换、previous备份、恢复源按SHA不可变保留。日志退出与物理步数要对齐。
- 失败导出仅保存已测行，明确completed_steps与recorded_rows；后步失败少一行必须显式记缺失，不补零。预步失败没有新积分步，不可混为漏采样。
- 门控前后中断恢复要与连续分支比较原生状态、控制器和累计证据。局部窗口逐步一致，不证明任意崩溃点、整个长流程逐步等价或断电耐久性。
- 原r2滚动备份已替换78/77秒历史字节，只能审计现存检查点和恢复记录；新v3明确保留20.9秒、69秒恢复源。不可宣称拥有全部每秒不可变链。
- 证据：`p3_independent_full_run_review_zh.md`；`passaging_p3_presettle_fullflow_revision_v3/metadata/REVIEW_NOTES.md`、`qa/failure_and_backup_audit.json`、`qa/actual21s_gate_recovery_review.json`、`qa/environment_recovery_final_audit.json`。

## 下次开工的最小门单

1. 记录来源/许可、原创边界、参考图与尺寸假设，冻结输入SHA。
2. 先验真实实体载荷链、装配净空、自由度与拆装路径，再细化外观。
3. 分别冻结源几何、碰撞代理、视觉映射与质量假设。
4. 先跑碰撞/支撑负例和边界测试，再跑短流程和原生恢复测试。
5. 预注册完整门限，保存逐步证据、失败字节和恢复源。
6. 独立目录审查最终文件、重导入、实际像素，不污染候选。
7. 逐层声明支持范围；目标引擎没有运行就写NOT_RUN。

## 仍未闭合的问题

- 支座真实安装孔阵、锚固、螺栓预紧/承载；R05材料许用、焊缝、动态抽拉、卫生及真实退tip均未验证。
- v3仍是限定机械循环，无移液工作站、液体处理、旋盖或生物过程；不能称完整细胞传代。
- Newton/UE5实际导入与动力学、全片镜头质量/视频、可移机含许可与纹理的发布包尚未由本记录证明。
- 接触参数、材料密度、制造公差与真实硬件性能仍包含假设；仿真通过不自动升级为现实安全或制造合格。

维护方式：新结论追加“变更、证据、适用范围、未解决项”；失败不覆盖。引用文件快照SHA见同目录`evidence_snapshot.json`，用于识别本次阅读版本，而非资产完整冻结或原报告再认证。
