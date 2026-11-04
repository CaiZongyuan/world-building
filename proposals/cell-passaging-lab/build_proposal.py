"""生成方案预览 index.html：布局俯视图、位姿表直接取自 analysis/preflight.json 与预演报告，避免页面与预演不一致。"""
import html
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = json.loads((HERE / "analysis/preflight.json").read_text())
rep = json.loads((HERE / "analysis/preflight_report.json").read_text())
esc = html.escape

# ---------------------------------------------------------------- 结构化数据（验证门读取）
LIC_LUMEN = "Lumen 原创（本项目）"
devices = [
    dict(name="培养箱", source="复用", asset="薄切片 01", license=LIC_LUMEN, status="PASS", difficulty="L3", thumb="img/thumbs/slice01_incubator.webp",
         note="外门 + 内玻璃门（执行器），4 层隔板；新增 0.12 m 底座"),
    dict(name="观察站（兼计数）", source="复用", asset="plate_imager_p0", license=LIC_LUMEN, status="PASS", difficulty="L3", thumb="img/thumbs/slice01_film.webp",
         note="抽屉 0–190 mm；观察、计数结果只作标注"),
    dict(name="Panda + 偏置宽指", source="复用", asset="Menagerie 98a70c5 + 薄切片 01", license="Apache-2.0 + Lumen 原创", status="PASS", difficulty="L3",
         note="偏置指垫夹板（110–190 mm），原装指尖夹管（0–80 mm）"),
    dict(name="线性导轨 + 滑台立柱", source="新建", asset="—", license=LIC_LUMEN, status="NOT_RUN", difficulty="L2", note="行程 2.95 m，基座高 0.60 m，滑台执行器驱动"),
    dict(name="移液工作站 v03", source="修复后复用", asset="workstation_lumen_v02", license=LIC_LUMEN, status="NOT_RUN", difficulty="L3", thumb="img/thumbs/workstation.webp",
         note="补执行器、放开重力、Z 轴加长到 +0.16 m；兼当洁净操作区（D3）"),
    dict(name="吸头装卸", source="修复后复用", asset="workstation_lumen_v02（吸头、喷嘴来自 pipette v03）", license=LIC_LUMEN, status="IDEALIZED", difficulty="L4",
         thumb="img/thumbs/workstation_head.webp", note="源资产标 BLOCKED；对准后用约束挂上（理想化）"),
    dict(name="离心机 v04", source="修复后复用", asset="centrifuge_lumen_v03_engineering", license=LIC_LUMEN, status="NOT_RUN", difficulty="L4", thumb="img/thumbs/centrifuge_open.webp",
         note="盖、转子带执行器；转子分度；精简为 2 个装载孔"),
    dict(name="离心管、配平管", source="几何复用", asset="离心机 v03 原创 15 mL 级管", license=LIC_LUMEN, status="IDEALIZED", difficulty="L4", thumb="img/thumbs/centrifuge_rotor.webp",
         note="Ø22.2 × 122.8 mm；管盖独立刚体；小件夹持用约束（理想化）"),
    dict(name="开盖器", source="新建", asset="—", license=LIC_LUMEN, status="NOT_RUN", difficulty="L4", note="细柱管座 + 后方夹爪 + 旋盖头；管盖对准后用约束（理想化）"),
    dict(name="管座、配平管架", source="新建", asset="—", license=LIC_LUMEN, status="NOT_RUN", difficulty="L2", note="细柱，周围 ±70 mm 内没有宽于 ±50 mm 的结构"),
    dict(name="储液槽 ×3、废液槽", source="新建", asset="—", license=LIC_LUMEN, status="NOT_RUN", difficulty="L1", note="SBS 尺寸，放在工作站后排；只有静态液面"),
    dict(name="废吸头盒", source="复用", asset="waste_tip_station_lumen_v01", license=LIC_LUMEN, status="NOT_RUN", difficulty="L2", thumb="img/thumbs/tip_waste.webp",
         note="台面开孔下沉安装（1104 R05 方案）"),
    dict(name="固体废物箱", source="新建", asset="—", license=LIC_LUMEN, status="NOT_RUN", difficulty="L1", note="0.40 × 0.30 × 0.55 m，开口朝上"),
    dict(name="房间、陈设", source="新建", asset="—", license=LIC_LUMEN, status="NOT_RUN", difficulty="L1", note="冰箱、试剂柜只做视觉"),
]
steps = [
    (1, "培养箱开门，取出母板，关门", "培养箱执行器、导轨、Panda", "L3", "物理"),
    (2, "母板送观察站，观察（结果只作标注）", "Panda、观察站抽屉", "L3", "物理"),
    (3, "母板送进工作站 A 位；夹起板盖，丢进固体废物箱", "Panda、工作站门", "L3", "物理"),
    (4, "去旧液、PBS 清洗（取吸头 → 吸 → 排废液 → 弃吸头）", "龙门移液头", "L3", "理想化"),
    (5, "加解离液，教学等待", "龙门移液头", "L2", "符号化"),
    (6, "空离心管在开盖器开盖，送到工作站管座；加终止液，收集到管里", "开盖器、Panda、移液头", "L4", "理想化"),
    (7, "离心管送开盖器盖盖；转子分度，装入离心管和配平管", "Panda、开盖器、离心机", "L4", "理想化"),
    (8, "离心机关盖、低速转动（教学时长）、停稳、开盖", "离心机执行器", "L2", "物理"),
    (9, "取出两支管；离心管开盖后送回工作站管座", "Panda、开盖器", "L4", "理想化"),
    (10, "去上清，加培养基重悬、混匀", "龙门移液头", "L3", "理想化"),
    (11, "取样到计数板（C 位）；计数板送观察站计数；母板丢进固体废物箱", "移液头、Panda、观察站", "L3", "理想化"),
    (12, "子板从培养箱 4 层取出，送到 A 位；板盖放到 C 位；分液接种", "Panda、培养箱、移液头", "L3", "理想化"),
    (13, "子板盖盖，送回培养箱 3 层，关门", "Panda、培养箱执行器", "L3", "物理"),
    (14, "计数板丢进固体废物箱；Panda 回停靠位；设备复位", "Panda、各设备执行器", "L3", "物理"),
]
references = [
    dict(title="MuJoCo Menagerie: Franka Emika Panda", url="https://github.com/google-deepmind/mujoco_menagerie/tree/main/franka_emika_panda",
         license="Apache-2.0", usage="可作资产", note="机器人模型（commit 98a70c5），薄切片 01 已用"),
    dict(title="MuJoCo 文档：MjSpec 与模型编辑", url="https://mujoco.readthedocs.io/en/stable/programming/modeledit.html",
         license="Apache-2.0（文档）", usage="仅参考", note="场景装配方式"),
    dict(title="ANSI/SLAS 1-2004 微孔板外形尺寸", url="https://www.slas.org/education/ansi-slas-microplate-standards/",
         license="标准文本受版权保护，只引用尺寸", usage="仅参考", note="板外形 127.76 × 85.48 mm，决定夹板开口和板位"),
    dict(title="spatial-sync：LAB_CELL_PASSAGE_SPEC_V1（本地仓库）", url="https://github.com/CaiZongyuan/spatial-sync",
         license="用户自有仓库（私有）", usage="仅参考", note="工艺顺序、设备清单、导轨布局思路（决定 D2）"),
]
data = dict(devices=devices, steps=[dict(no=n, name=a, actor=b, difficulty=c, fidelity=d) for n, a, b, c, d in steps], references=references)

# ---------------------------------------------------------------- 布局俯视图（主题变量着色）
boxes = [(b["name"], b["pos"], b["size"], b.get("yaw", 0.0)) for b in spec["static"]]
lo = [-0.45, -1.5]; hi = [3.4, 1.65]
W = 960; sc = W / (hi[0] - lo[0]); H = int((hi[1] - lo[1]) * sc)
X = lambda x: (x - lo[0]) * sc  # noqa: E731
Y = lambda y: H - (y - lo[1]) * sc  # noqa: E731


def poly(c, s, yaw, cls):
    pts = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        vx, vy = sx * s[0], sy * s[1]
        pts.append(f"{X(c[0] + math.cos(yaw) * vx - math.sin(yaw) * vy):.1f},{Y(c[1] + math.sin(yaw) * vx + math.cos(yaw) * vy):.1f}")
    return f'<polygon class="{cls}" points="{" ".join(pts)}"/>'


svg = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="全实验室布局俯视图">',
       '<style>.st{fill:var(--surface-2);stroke:var(--line-2)}.dev{fill:var(--surface);stroke:var(--ink);stroke-width:1.2}'
       '.mv{fill:none;stroke:var(--accent);stroke-dasharray:4 3}.rail{fill:var(--ink)}.lb{fill:var(--ink);font:600 13px var(--font-ui)}'
       '.sm{fill:var(--muted);font:11.5px var(--font-ui)}.pk{fill:var(--c2)}.ok{fill:var(--ok)}.gr{stroke:var(--line);stroke-width:1}</style>']
for gx in range(0, 4):
    svg.append(f'<line class="gr" x1="{X(gx):.0f}" y1="0" x2="{X(gx):.0f}" y2="{H}"/><text class="sm" x="{X(gx) + 3:.0f}" y="{H - 4}">x={gx} m</text>')
groups = {}
for name, c, s, yaw in boxes:
    grp = name.split("_")[0]
    if name == "rail_beam":
        svg.append(poly(c, s, yaw, "rail")); continue
    if grp in ("workstation",) and not any(k in name for k in ("bench", "deck")):
        continue
    cls = "st" if any(k in name for k in ("bench", "table", "plinth", "deck")) else "dev"
    svg.append(poly(c, s, yaw, cls))
for mv in spec["movers"]:
    for b in mv["boxes"]:
        a = mv["joint"]["anchor"]
        svg.append(poly([a[0] + b["pos"][0], a[1] + b["pos"][1]], b["size"], b.get("yaw", 0.0), "mv"))
labels = [("培养箱", 2.85, -1.42), ("观察站", 1.75, -1.10), ("离心机", 0.55, -1.10), ("开盖器", 1.05, -1.10), ("配平管架", 0.08, -1.10),
          ("移液工作站（兼洁净区）", 1.55, 1.58), ("废物箱", 0.30, 1.10), ("导轨 2.95 m（Panda 在滑台立柱上）", 1.47, 0.20)]
for t, x, y in labels:
    svg.append(f'<text class="lb" x="{X(x):.1f}" y="{Y(y):.1f}" text-anchor="middle">{esc(t)}</text>')
okset = {r["id"][2:] for r in rep["poses"] if r["ok"]}
for p in spec["poses"]:
    if p["name"].startswith("via_") or p["name"] == "park":
        continue
    cls = "ok" if p["name"] in okset else "pk"
    svg.append(f'<circle class="{cls}" cx="{X(p["pos"][0]):.1f}" cy="{Y(p["pos"][1]):.1f}" r="5"/>')
svg.append("</svg>")
svg = "\n".join(svg)

pose_rows = "".join(
    f'<tr><td><code>{esc(r["id"][2:])}</code></td><td>{"PASS" if r["ok"] else "FAIL"}</td><td>{r.get("configurations", "—")}</td>'
    f'<td>{r["q"][0]:.2f}</td></tr>' for r in rep["poses"] if not r["id"].startswith("P:via_"))

dev_rows = "".join(
    f'<tr><td>{f"<img src=\"{d["thumb"]}\" alt=\"\">" if d.get("thumb") else ""}</td><td><b>{esc(d["name"])}</b><br><span class="small mute">{esc(d["asset"])}</span></td>'
    f'<td>{esc(d["source"])}</td><td><span class="tag {d["status"]}">{d["status"]}</span></td><td><span class="lv {d["difficulty"]}">{d["difficulty"]}</span></td>'
    f'<td class="small">{esc(d["note"])}<br><span class="mute">{esc(d["license"])}</span></td></tr>' for d in devices)
step_rows = "".join(f'<tr><td>{n}</td><td>{esc(a)}</td><td>{esc(b)}</td><td><span class="lv {c}">{c}</span></td><td>{d}</td></tr>' for n, a, b, c, d in steps)
ref_rows = "".join(f'<tr><td><a href="{r["url"]}" target="_blank" rel="noopener">{esc(r["title"])}</a></td><td>{esc(r["license"])}</td><td>{r["usage"]}</td><td>{esc(r["note"])}</td></tr>' for r in references)
pf = rep["summary"]

page = f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>全流程实验室方案预览</title>
<link rel="stylesheet" href="assets/theme.css">
<script>try{{const q=new URLSearchParams(location.search).get('theme');const t=q||localStorage.getItem('wb-theme');if(t)document.documentElement.dataset.theme=t}}catch(e){{}}</script>
<style>.svgcard svg{{display:block;width:100%;height:auto}} td img{{width:96px}}</style>
</head>
<body>
<button class="theme-btn" id="theme-btn" type="button">外观</button>
<main>
<header>
<div class="eyebrow">World Building · 方案预览 · cell-passaging-lab</div>
<h1>细胞传代黑灯实验室：全流程方案</h1>
<p class="lede">一台 Panda 沿 2.95 m 导轨，在 5 个区域之间完成一次贴壁细胞传代的全部机械动作。布局已经过运动学预演：{pf['total']} 项检查全部通过。</p>
<div class="meta"><span>2026-11-05</span><span>审批点①：自审（自主运行约定第 1 条）</span><span>最高难度 <span class="lv L4">L4</span></span><span>预演 {pf['total']} 项 PASS</span></div>
<nav class="toc"><a href="#goal"><span class="n">01</span>目标</a><a href="#renders"><span class="n">02</span>效果图</a><a href="#layout"><span class="n">03</span>布局</a><a href="#devices"><span class="n">04</span>设备</a><a href="#steps"><span class="n">05</span>工艺步骤</a><a href="#stages"><span class="n">06</span>分期</a><a href="#risks"><span class="n">07</span>风险与难度</a><a href="#references"><span class="n">08</span>外部参考</a></nav>
</header>

<section id="goal">
<h2><span class="n">01</span>目标与不做什么</h2>
<p class="sub">场景、流程、资产三张清单已在范围预览中确认（D1–D4）；这里给出可执行的方案。</p>
<div class="grid2">
<div class="card"><h3>目标</h3><p>用真实机械物理（MuJoCo）走通 14 步传代流程：母板出箱 → 观察 → 工作站内去旧液、清洗、解离、收集 → 开盖器 → 离心 → 重悬 → 计数 → 接种子板 → 子板回培养箱 → 废物收尾。按 4 期实现，每期一段成片，最后一段完整成片（draft 档位，不加速、不剪辑）。</p></div>
<div class="card"><h3>不做什么</h3><ul><li>液体与细胞状态模型（只记动作日志、画静态液面）</li><li>6 孔独立样本、Web 控制、Newton</li><li>机械臂旋盖、机械臂拿移液枪</li><li>强度、制造、真实硬件验证</li></ul></div>
</div>
<div class="callout"><b>工程决策</b><span class="mute small">（agent 依据预演和资产审查决定）</span><ol>
<li><b>布局：导轨沿 x 轴，南侧依次是离心台、观察站、培养箱，北侧是移液工作站和固体废物箱，各设备正面朝向导轨。</b>培养箱放在导轨末端，铰链朝外，外门往导轨外侧开；箱体垫高 0.12 m，让门下沿高过导轨梁。这一条解决了预演 v1 里外门扫过导轨的问题。</li>
<li><b>夹管不换指：</b>原装指尖夹管（0–80 mm），偏置指垫夹板（110–190 mm）。前提是夹管处周围 ±70 mm 内没有宽于 ±50 mm 的结构，所以开盖器、管座都做成细柱（预演 v1 → v2）。</li>
<li><b>离心机转子分度：</b>要装的孔先转到后方，管子沿 30° 孔轴从前上方插入。另外 6 个孔合并为静态几何，以减少碰撞体。</li>
<li><b>工作站 Z 轴加长到 +0.16 m（资产另存 v03）：</b>原行程只有 75 mm，吸头越不过 15 mL 管的管口，也伸不到管底。</li>
<li><b>板和盖的流转：</b>母板盖直接丢进废物箱；子板预先放在培养箱 4 层，接种时它的盖暂放在 C 位；计数板不带盖。这样前排 3 个板位就够用，后排留给吸头架、储液槽和废液槽。</li>
<li><b>机器人路线：</b>按工艺顺序走过 12 个取放位姿和 9 个门口过渡点，共 27 段过渡。这条路线也是仿真阶段的动作序列。</li>
</ol></div>
</section>

<section id="renders">
<h2><span class="n">02</span>效果图</h2>
<p class="sub">AI 概念图（gpt-image-2.5-flare），只用来对齐风格。和设计不一致的地方以第 03、04 节为准。</p>
<figure><img src="img/lab_wide.webp" alt="全景"><figcaption>全景：中间是导轨和滑台上的 Panda，一侧是离心台、观察站、培养箱，另一侧是移液工作站和废物箱。（概念图里的培养箱画成了高柜，布局也和第 03 节不完全一致。）</figcaption></figure>
<div class="grid2" style="margin-top:16px">
<figure><img src="img/ws_interior.webp" alt="工作站内部"><figcaption>工作站内部：门全开，Panda 从正面把板放到板位上；龙门移液头、吸头架、储液槽，前沿是一根细柱管座。（概念图里的手指不是偏置宽指。）</figcaption></figure>
<figure><img src="img/centrifuge_loading.webp" alt="离心机装管"><figcaption>离心机装管：盖开到约 100°，管子沿倾斜的孔轴插入；旁边是开盖器和配平管架。（概念图里的孔画成了竖直的，实际倾斜 30°。）</figcaption></figure>
</div>
</section>

<section id="layout">
<h2><span class="n">03</span>布局与运动学预演</h2>
<p class="sub">俯视图由 <code>analysis/layout.py</code> 生成，和预演输入是同一份数据。实线框是设备代理，虚线是门、抽屉、离心机盖的扫掠件，绿点是通过预演的取放位姿。</p>
<div class="card svgcard">{svg}</div>
<div class="grid2" style="margin-top:16px">
<div class="table-wrap"><table><tr><th>取放位姿</th><th>结果</th><th>无碰撞构型数</th><th>导轨位置 x (m)</th></tr>{pose_rows}</table></div>
<div class="card"><h3>预演迭代</h3><table><tr><th>版本</th><th>失败 / 总数</th><th>主要改动</th></tr>
<tr><td>v1</td><td>11 / 33</td><td>—</td></tr>
<tr><td>v2</td><td>10 / 33</td><td>培养箱挪到导轨末端；开盖器和管座改成细柱；水平侧夹管；停靠位挪到南侧</td></tr>
<tr><td>v3</td><td><b>0 / {pf['total']}</b></td><td>离心台挪近；培养箱垫高 0.12 m；加门口过渡点；按工艺顺序生成完整路线</td></tr></table>
<p class="small mute">预演只说明运动学可行：所有位姿可达、无碰撞，活动件扫掠不撞，过渡段能走通。搬运时盖不滑、接触穿透等问题由仿真阶段验证。完整记录见 <code>analysis/preflight_log.md</code>。</p></div>
</div>
</section>

<section id="devices">
<h2><span class="n">04</span>设备与资产</h2>
<p class="sub">资产审查见 <code>analysis/asset_audit.md</code>：缺失的网格按 SHA 从 1104 归档补齐（离心机 165 个、工作站 32 个），再用 MuJoCo 3.17 编译，读出关节和执行器。</p>
<div class="table-wrap"><table><tr><th></th><th>设备</th><th>来源</th><th>状态</th><th>难度</th><th>说明 / 许可</th></tr>{dev_rows}</table></div>
</section>

<section id="steps">
<h2><span class="n">05</span>工艺步骤</h2>
<p class="sub">合并样本：母板、子板、计数板各 1 块，离心管 1 支加配平管 1 支，离心 1 次。保真度：<b>物理</b>＝真实接触与支撑；<b>理想化</b>＝机械动作是物理的，但小件夹持用约束、液体只记日志；<b>符号化</b>＝只有等待和标注。</p>
<div class="table-wrap"><table><tr><th>#</th><th>工艺步骤</th><th>执行者</th><th>难度</th><th>保真度</th></tr>{step_rows}</table></div>
</section>

<section id="stages">
<h2><span class="n">06</span>分期与流程阶段</h2>
<p class="sub">每期都走完 建模 → 仿真 → 位姿绑定与渲染，并出一段成片；场景逐期累加，前一期的验证门和负例在后一期继续有效。</p>
<div class="flow"><div class="st done"><b>需求访谈</b><small>+ 范围预览</small></div><span class="arrow">→</span><div class="st now"><b>方案预览</b><small>本页</small></div><span class="ck">审批点①（自审）</span><span class="arrow">→</span><div class="st"><b>plan</b><small>冻结门限</small></div><span class="arrow">→</span><div class="st"><b>参考图</b><small>新建设备</small></div><span class="ck">审批点②（自审）</span><span class="arrow">→</span><div class="st"><b>期 1–4</b><small>建模 · 仿真 · 渲染</small></div><span class="arrow">→</span><div class="st"><b>期 5</b><small>完整运行</small></div></div>
<div class="table-wrap" style="margin-top:16px"><table><tr><th>期</th><th>工艺步骤</th><th>新加入的设备</th><th>成片</th></tr>
<tr><td>1 搬运与进工作站</td><td>1–3</td><td>导轨、工作站 v03（门执行器）、固体废物箱、房间</td><td>母板出箱 → 观察 → 进工作站，母板盖丢弃</td></tr>
<tr><td>2 工作站内移液</td><td>4–6（不含开盖器）</td><td>龙门执行器、吸头装卸约束、储液槽、废液槽、废吸头盒、管座</td><td>取吸头 → 吸 → 排 → 弃吸头；收集到管</td></tr>
<tr><td>3 开盖与离心</td><td>6–9</td><td>开盖器、离心机 v04、离心管与配平管、配平管架</td><td>开盖 → 装管 → 离心 → 卸管</td></tr>
<tr><td>4 计数、接种、回培养</td><td>10–14</td><td>计数板、子板</td><td>重悬 → 计数 → 接种 → 回培养箱 → 收尾</td></tr>
<tr><td>5 完整运行</td><td>1–14</td><td>—</td><td>一次连续运行，不剪辑</td></tr></table></div>
</section>

<section id="risks">
<h2><span class="n">07</span>风险与难度</h2>
<div class="table-wrap"><table><tr><th>#</th><th>风险</th><th>难度</th><th>对策</th></tr>
<tr><td>R1</td><td>小件夹持：管口只露出孔约 28 mm，靠原装指尖夹住</td><td><span class="lv L4">L4</span></td><td>先检查对准误差、接触和碰撞，通过后再用约束挂上（理想化，如实标注）；负例：对准偏差大时必须拒绝挂上</td></tr>
<tr><td>R2</td><td>偏置指垫比指尖再往下伸 70 mm，夹管时会擦到周围结构</td><td><span class="lv L3">L3</span></td><td>预演已经约束了开盖器、管座的形状；仿真阶段再做一遍运动学初筛</td></tr>
<tr><td>R3</td><td>工作站 Z 轴加长属于改资产，可能和龙门横梁干涉</td><td><span class="lv L3">L3</span></td><td>建模阶段做几何干涉核查；另存 v03，原资产不动</td></tr>
<tr><td>R4</td><td>离心机碰撞体多（1632 个），全场景仿真变慢</td><td><span class="lv L3">L3</span></td><td>只保留 2 个装载孔，其余合并为转子静态几何；每期测实际仿真吞吐</td></tr>
<tr><td>R5</td><td>远距离搬运时，带盖的板要保持水平</td><td><span class="lv L3">L3</span></td><td>沿用薄切片 01 的做法：绕底座竖轴圆弧加偏航插值，并加上导轨平移</td></tr>
<tr><td>R6</td><td>吸头装卸（源资产标 BLOCKED）</td><td><span class="lv L4">L4</span></td><td>理想化：喷嘴对准、插入到位后挂上；退吸头时解除，吸头靠重力落进废吸头盒</td></tr>
<tr><td>R7</td><td>全流程步骤多，仿真步数和渲染帧数都大</td><td><span class="lv L2">L2</span></td><td>按期推进；draft 档位渲染；不加速、不剪辑的约束不变</td></tr></table></div>
</section>

<section id="references">
<h2><span class="n">08</span>外部参考</h2>
<div class="table-wrap"><table><tr><th>参考</th><th>许可</th><th>用途</th><th>说明</th></tr>{ref_rows}</table></div>
</section>
<footer>数据：<code>analysis/preflight.json</code>、<code>analysis/preflight_report.json</code>、<code>analysis/asset_audit.md</code>；需求见 <code>01-requirements/requirements.md</code>。</footer>
<script type="application/json" id="proposal-data">{json.dumps(data, ensure_ascii=False)}</script>
<script>document.getElementById('theme-btn').onclick=()=>{{const r=document.documentElement,dark=r.dataset.theme?r.dataset.theme==='dark':matchMedia('(prefers-color-scheme: dark)').matches;r.dataset.theme=dark?'light':'dark';try{{localStorage.setItem('wb-theme',r.dataset.theme)}}catch(e){{}}}};</script>
</main>
</body>
</html>
"""
(HERE / "index.html").write_text(page, encoding="utf-8")
print("written", len(page))
