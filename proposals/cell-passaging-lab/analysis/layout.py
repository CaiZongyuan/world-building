"""全实验室布局 → 运动学预演输入（preflight.json）。

每个工位用"局部方盒代理 + 局部关键位姿"描述，尺寸取自真实资产（见 02-proposal/analysis/asset_dims.md）。
布局只由文件顶部的 LAYOUT 参数决定；改参数 → 重新生成 → `wb preflight` 检查。
世界坐标：Z 向上；导轨沿 +X，位于 y = 0；工位分列导轨两侧，正面朝向导轨。
"""
import json
import math
from pathlib import Path


HERE = Path(__file__).resolve().parent
S1 = Path("/mnt/d/Projects/Robots/projects/cell-passaging-slice-01")
FINGER = json.loads((S1 / "05-modelling/design.json").read_text())["offset_finger"]
D2R = math.radians

LAYOUT = dict(
    rail=dict(base=[0.0, 0.0, 0.85], range=[0.0, 2.95]),           # 仿真阶段修订 0.60 → 0.85：放板高度落在基座上方 0.05–0.15 的"低带"，肩高于工作站台面
    # 南侧（y < 0）：离心台（离心机、开盖器、配平管架）→ 观察站 → 培养箱（放在导轨末端，铰链在外侧，门往导轨外开）
    centrifuge=dict(pos=[0.55, -0.70, 0.70], yaw=math.pi),        # 正面朝 +Y（导轨）；台面高 0.72
    decapper=dict(pos=[1.05, -0.56, 0.70], yaw=math.pi),
    side_rack=dict(pos=[0.08, -0.56, 0.70], yaw=math.pi),          # 配平管架
    imager=dict(pos=[1.75, -0.78, 0.85], yaw=math.pi),            # 台面高 0.85（仿真阶段修订，原 0.60）：放板高度落在可达高度带 0.92–1.12
    incubator=dict(pos=[2.85, -1.00, 0.40], yaw=math.pi),         # 底座 0.40（仿真阶段修订，原 0.12）：第 3 层放板高度约 0.96；左铰链 → 世界 +X 侧
    # 北侧（y > 0）：移液工作站（前门朝导轨）、固体废物箱
    workstation=dict(pos=[1.55, 1.02, 0.0], yaw=0.0),             # 仿真阶段修订 1.12 → 1.02：手掌朝上时 0.94 m 高度最远约 0.95 m
    waste=dict(pos=[2.20, -0.70, 0.0], yaw=0.0),                 # 仿真阶段修订：挪到南侧观察站与培养箱之间，投放不用转身
)

PLATE_TCP_Z = 0.0085        # 指垫中心离板底（薄切片 01）
LID_TCP_Z = 0.019           # 夹盖：指垫落在盖裙高度（16.4–21.7 mm）
STOCK_TCP = [0.0, 0.0, 0.1034]   # 原装指尖中心（夹管用）
TUBE_R = 0.0111             # 离心管最大半径
TUBE_L = 0.1228


def tf(station, p):
    s = LAYOUT[station]; c, si = math.cos(s["yaw"]), math.sin(s["yaw"])
    return [s["pos"][0] + c * p[0] - si * p[1], s["pos"][1] + si * p[0] + c * p[1], s["pos"][2] + p[2]]


def rot(station, v):
    s = LAYOUT[station]; c, si = math.cos(s["yaw"]), math.sin(s["yaw"])
    return [c * v[0] - si * v[1], si * v[0] + c * v[1], v[2]]


def box(station, name, pos, size, yaw=0.0):
    return dict(name=f"{station}_{name}", pos=tf(station, pos), size=size, yaw=LAYOUT[station]["yaw"] + yaw)


static, movers, poses = [], [], []

# ---------------- 导轨与底座（新建）：导轨梁 + 滑台立柱（立柱随机器人移动，不放进静态代理）
r = LAYOUT["rail"]
L = r["range"][1] - r["range"][0]
static.append(dict(name="rail_beam", pos=[r["base"][0] + L / 2, 0.0, 0.05], size=[L / 2 + 0.15, 0.12, 0.05]))

# ---------------- 培养箱（薄切片 01，局部：原点在箱底中心，正面 -Y）
W = 0.015
for n, p, s in [("left", [-0.35 + W, 0, 0.475], [W, 0.35, 0.475]), ("right", [0.35 - W, 0, 0.475], [W, 0.35, 0.475]),
                ("back", [0, 0.35 - W, 0.475], [0.35, W, 0.475]), ("top", [0, 0, 0.95 - W], [0.35, 0.35, W]),
                ("floor", [0, 0, 0.04], [0.35, 0.35, 0.04])]:
    static.append(box("incubator", n, p, s))
for i, z in enumerate([0.315, 0.435, 0.555, 0.675], 1):
    static.append(box("incubator", f"shelf{i}", [0, 0.01, z - 0.003], [0.32, 0.31, 0.003]))
INC_OPEN = {"incubator_outer": D2R(115), "incubator_inner": D2R(105)}
movers += [
    dict(name="incubator_outer", joint=dict(type="hinge", anchor=tf("incubator", [-0.35, -0.3805, 0.08]), axis=[0, 0, -1], range=[0, D2R(115)]),
         boxes=[dict(pos=rot("incubator", [0.35, -0.02, 0.43]), size=[0.35, 0.02, 0.43], yaw=LAYOUT["incubator"]["yaw"])]),
    dict(name="incubator_inner", joint=dict(type="hinge", anchor=tf("incubator", [-0.262, -0.3245, 0.165]), axis=[0, 0, -1], range=[0, D2R(105)]),
         boxes=[dict(pos=rot("incubator", [0.262, -0.006, 0.37]), size=[0.262, 0.006, 0.37], yaw=LAYOUT["incubator"]["yaw"])],
         sweep_others={"incubator_outer": D2R(115)}),
]
for shelf, z in ((3, 0.555), (4, 0.675)):
    poses.append(dict(name=f"incubator_shelf{shelf}", pos=tf("incubator", [0, -0.18, z + PLATE_TCP_Z]),
                      approach=rot("incubator", [0, 1, 0]), opening_axis=rot("incubator", [1, 0, 0]),
                      standoff=0.25, movers=INC_OPEN, clearance=0.001, finger_q=0.1278 / 2 - FINGER["pad_y"]))

# ---------------- 观察站（plate_imager_p0，局部：原点在台面，抽屉沿 -Y 伸出 0.19）
static.append(dict(name="imager_table", pos=[LAYOUT["imager"]["pos"][0], LAYOUT["imager"]["pos"][1] - 0.02, LAYOUT["imager"]["pos"][2] / 2],
                   size=[0.22, 0.22, LAYOUT["imager"]["pos"][2] / 2]))
static += [box("imager", "housing", [0, 0.025, 0.145], [0.145, 0.165, 0.125])]
movers.append(dict(name="imager_drawer", attached_to=["imager_housing", "imager_table"], joint=dict(type="slide", anchor=tf("imager", [0, 0, 0]), axis=rot("imager", [0, -1, 0]), range=[0, 0.19]),
                   boxes=[dict(pos=rot("imager", [0, -0.145, 0.076]), size=[0.103, 0.005, 0.038], yaw=LAYOUT["imager"]["yaw"]),   # 抽屉面板
                          dict(pos=rot("imager", [0, -0.02, 0.058]), size=[0.10, 0.105, 0.006], yaw=LAYOUT["imager"]["yaw"])]))
poses.append(dict(name="imager_drawer", pos=tf("imager", [0, -0.245, 0.070 + PLATE_TCP_Z - 0.001]),
                  approach=rot("imager", [0, 1, 0]), opening_axis=rot("imager", [1, 0, 0]), standoff=0.12,
                  movers={"imager_drawer": 0.19}, clearance=0.001, finger_q=0.1278 / 2 - FINGER["pad_y"],
                  ignore=["imager_drawer"]))

# ---------------- 移液工作站（workstation_lumen_v02，局部：原点在地面中心，前门 y = -0.38）
ws = [("bench", [0, 0, 0.45], [0.566, 0.36, 0.45]), ("deck", [0, 0, 0.907], [0.56, 0.36, 0.007]),
      ("rear_gantry", [0, 0.30, 1.245], [0.54, 0.05, 0.345]), ("rear_panel", [0, 0.379, 1.285], [0.54, 0.003, 0.375]),
      ("left_panel", [-0.579, 0, 1.285], [0.003, 0.34, 0.375]), ("right_upper_panel", [0.579, 0, 1.579], [0.003, 0.34, 0.09]),
      ("top_fascia", [0.08, -0.379, 1.715], [0.66, 0.003, 0.053]), ("roof", [0, 0, 1.70], [0.58, 0.38, 0.03]),
      ("control_column", [0.67, -0.38, 1.294], [0.082, 0.04, 0.365]),
      ("post_fl", [-0.566, -0.366, 1.285], [0.01, 0.01, 0.385]), ("post_fr", [0.566, -0.366, 1.285], [0.01, 0.01, 0.385]),
      ("gantry_y_beam", [-0.30, -0.066, 1.348], [0.08, 0.284, 0.03]),      # X 轴停在 -0.30（左侧）
      ("gantry_head", [-0.30, 0.185, 1.11], [0.065, 0.06, 0.15]),          # Y 轴停在最后方
      ("tip_rack", [-0.25, 0.075, 0.95], [0.064, 0.043, 0.04]), ("reservoirs", [0.0, 0.075, 0.94], [0.064, 0.043, 0.026]),
      ("waste_liquid", [0.25, 0.075, 0.94], [0.064, 0.043, 0.026])]
static += [box("workstation", n, p, s) for n, p, s in ws]
WS_OPEN = {"ws_door_left": D2R(110), "ws_door_right": D2R(110)}
movers += [
    dict(name="ws_door_left", joint=dict(type="hinge", anchor=tf("workstation", [-0.554, -0.382, 0.914]), axis=[0, 0, -1], range=[0, D2R(110)]),
         boxes=[dict(pos=rot("workstation", [0.277, 0, 0.371]), size=[0.27, 0.006, 0.371], yaw=LAYOUT["workstation"]["yaw"])]),
    dict(name="ws_door_right", joint=dict(type="hinge", anchor=tf("workstation", [0.554, -0.382, 0.914]), axis=[0, 0, 1], range=[0, D2R(110)]),
         boxes=[dict(pos=rot("workstation", [-0.277, 0, 0.371]), size=[0.27, 0.006, 0.371], yaw=LAYOUT["workstation"]["yaw"])]),
]
DECK = 0.914
for nest, x in (("A", -0.25), ("C", 0.25)):
    poses.append(dict(name=f"ws_{nest}_plate", pos=tf("workstation", [x, -0.16, DECK + PLATE_TCP_Z]),
                      approach=rot("workstation", [0, 1, 0]), opening_axis=rot("workstation", [1, 0, 0]), standoff=0.30,
                      movers=WS_OPEN, clearance=0.001, finger_q=0.1278 / 2 - FINGER["pad_y"]))
poses.append(dict(name="ws_A_lid", pos=tf("workstation", [-0.25, -0.16, DECK + LID_TCP_Z]),
                  approach=rot("workstation", [0, 1, 0]), opening_axis=rot("workstation", [1, 0, 0]), standoff=0.30,
                  movers=WS_OPEN, clearance=0.001, finger_q=0.130 / 2 - FINGER["pad_y"]))
# 管架在 B 位（局部 x = 0），离心管竖直，原装指尖从上方夹管口下方 15 mm
TUBE_HOLDER_Y = -0.20
poses.append(dict(name="ws_B_tube", pos=tf("workstation", [0.0, TUBE_HOLDER_Y, DECK + 0.005 + 0.09]), tcp_in_hand=STOCK_TCP,
                  approach=rot("workstation", [0, 1, 0]), opening_axis=rot("workstation", [1, 0, 0]), standoff=0.25, movers=WS_OPEN,
                  clearance=0.002, finger_q=TUBE_R))
static.append(box("workstation", "tube_holder_B", [0.0, TUBE_HOLDER_Y + 0.02, DECK + 0.03], [0.012, 0.012, 0.03]))

# ---------------- 离心机（centrifuge_lumen_v03，局部：原点在地面中心，正面 -Y，盖铰链在后方）
cz = LAYOUT["centrifuge"]["pos"][2]
static.append(dict(name="centrifuge_bench", pos=[0.58, -0.72, cz / 2], size=[0.62, 0.27, cz / 2]))
static.append(dict(name="incubator_plinth", pos=[2.85, -1.0, LAYOUT["incubator"]["pos"][2] / 2], size=[0.36, 0.36, LAYOUT["incubator"]["pos"][2] / 2]))
static += [box("centrifuge", "front", [0, -0.246, 0.162], [0.23, 0.014, 0.112]), box("centrifuge", "rear", [0, 0.248, 0.162], [0.23, 0.012, 0.112]),
           box("centrifuge", "left", [-0.233, 0, 0.162], [0.003, 0.236, 0.112]), box("centrifuge", "right", [0.233, 0, 0.162], [0.003, 0.236, 0.112]),
           box("centrifuge", "base", [0, 0, 0.04], [0.23, 0.26, 0.04]), box("centrifuge", "rotor", [0, 0, 0.12], [0.10, 0.10, 0.04]),
           box("centrifuge", "deck_front", [0, -0.21, 0.279], [0.23, 0.05, 0.006])]
movers.append(dict(name="centrifuge_lid", attached_to=["centrifuge_"], joint=dict(type="hinge", anchor=tf("centrifuge", [0, 0.238, 0.296]), axis=rot("centrifuge", [-1, 0, 0]), range=[0, D2R(100)]),
                   rest=0.0, boxes=[dict(pos=rot("centrifuge", [0, -0.248, 0.0]), size=[0.229, 0.252, 0.02], yaw=LAYOUT["centrifuge"]["yaw"])]))
CF_OPEN = {"centrifuge_lid": D2R(100)}
# 后方孔位（局部 θ = 90°）：管轴朝上、朝前倾 30°；转子分度把要装的孔转到这里
axis_l = [0, -0.5, 0.866]
base_l = [0, 0.1357, 0.1502]
grip_l = [base_l[i] + axis_l[i] * (TUBE_L - 0.012) for i in range(3)]
poses.append(dict(name="centrifuge_pocket", pos=tf("centrifuge", grip_l), tcp_in_hand=STOCK_TCP,
                  approach=[-v for v in rot("centrifuge", axis_l)], opening_axis=rot("centrifuge", [1, 0, 0]),
                  standoff=0.10, movers=CF_OPEN, clearance=0.002, finger_q=TUBE_R))

# ---------------- 开盖器（新建）：夹住管身，管竖直，管口高 = 台面 + 0.20
static.append(box("decapper", "body", [0, 0.11, 0.13], [0.06, 0.05, 0.13]))          # 机身（含旋盖头，装卸时停在后上方）
static.append(box("decapper", "post", [0, 0, 0.04], [0.012, 0.012, 0.04]))           # 管底座柱
static.append(box("decapper", "jaw", [0, 0.035, 0.11], [0.018, 0.045, 0.02]))        # 夹管爪（从后方伸出）
poses.append(dict(name="decapper_tube", pos=tf("decapper", [0, 0, 0.08 + TUBE_L - 0.015]), tcp_in_hand=STOCK_TCP,
                  approach=[0, 0, -1], opening_axis=rot("decapper", [1, 0, 0]), standoff=0.10, clearance=0.002, finger_q=TUBE_R))

# ---------------- 配平管架
static.append(box("side_rack", "rack", [0, 0, 0.015], [0.06, 0.04, 0.015]))
poses.append(dict(name="side_rack_tube", pos=tf("side_rack", [0, 0, 0.03 + TUBE_L - 0.015]), tcp_in_hand=STOCK_TCP,
                  approach=[0, 0, -1], opening_axis=rot("side_rack", [1, 0, 0]), standoff=0.10, clearance=0.002, finger_q=TUBE_R))

# ---------------- 固体废物托盘（新建；仿真阶段修订：由 0.55 m 高的开口箱改为与放板高度同高的托盘，物品水平送入、贴底松手）
for n, p_, s in [("tray_floor", [0, 0, 0.885], [0.255, 0.16, 0.01]), ("w_back", [0, -0.155, 0.92], [0.255, 0.005, 0.025]),
                 ("w_w", [-0.25, 0, 0.92], [0.005, 0.16, 0.025]), ("w_e", [0.25, 0, 0.92], [0.005, 0.16, 0.025])]:
    static.append(box("waste", n, p_, s))
poses.append(dict(name="waste_drop", pos=tf("waste", [0, 0.0, 0.895 + 0.010 - 0.0021 + 0.0085]), approach=[0, -1, 0], opening_axis=[-1, 0, 0],
                  finger_q=0.1278 / 2 - FINGER["pad_y"], clearance=0.001))

# ---------------- 停靠位（导轨中段，手臂收拢）
poses.insert(0, dict(name="park", pos=[2.0, -0.30, 1.10], approach=[0, 0, -1], opening_axis=[1, 0, 0]))   # 避开工作站门的扫掠区

# ---------------- 门口过渡点（via）：真实规划先退到工位门口，再沿导轨移动
def via(name, x, side, approach, z=1.0, opening=(1, 0, 0), finger_q=0.04, tcp=None):
    d = dict(name=f"via_{name}", pos=[x, 0.30 * side, z], approach=list(approach), opening_axis=list(opening), finger_q=finger_q)
    if tcp:
        d["tcp_in_hand"] = tcp
    poses.append(d)

PLATE_Q = 0.1278 / 2 - FINGER["pad_y"]
via("incubator", LAYOUT["incubator"]["pos"][0], -1, [0, -1, 0], finger_q=PLATE_Q)
via("imager", LAYOUT["imager"]["pos"][0], -1, [0, -1, 0], finger_q=PLATE_Q)
via("ws_A", tf("workstation", [-0.25, 0, 0])[0], 1, [0, 1, 0], finger_q=PLATE_Q)
via("ws_C", tf("workstation", [0.25, 0, 0])[0], 1, [0, 1, 0], finger_q=PLATE_Q)
via("ws_B", tf("workstation", [0, 0, 0])[0], 1, [0, 1, 0], finger_q=TUBE_R, tcp=STOCK_TCP)
via("waste", LAYOUT["waste"]["pos"][0], -1, [0, -1, 0], finger_q=PLATE_Q)
via("decapper", LAYOUT["decapper"]["pos"][0], -1, [0, 0, -1], z=1.05, finger_q=TUBE_R, tcp=STOCK_TCP)
via("centrifuge", LAYOUT["centrifuge"]["pos"][0], -1, [0, -0.5, -0.866], z=1.10, finger_q=TUBE_R, tcp=STOCK_TCP)
via("side_rack", LAYOUT["side_rack"]["pos"][0] + 0.1, -1, [0, 0, -1], z=1.05, finger_q=TUBE_R, tcp=STOCK_TCP)

# 机器人按工艺顺序走过的位姿（同一路线也是仿真的动作序列）
ROUTE = [
    "park", "via_incubator", "incubator_shelf3", "via_incubator", "via_imager", "imager_drawer",          # 1–2 母板出箱、观察
    "via_imager", "via_ws_A", "ws_A_plate", "ws_A_lid", "via_ws_A", "via_waste", "waste_drop",           # 3 母板进工作站、母板盖弃置
    "via_waste", "via_decapper", "decapper_tube", "via_decapper", "via_ws_B", "ws_B_tube",               # 6 空管开盖后送管座
    "via_ws_B", "via_decapper", "decapper_tube", "via_decapper", "via_centrifuge", "centrifuge_pocket",   # 7 盖盖、装离心机
    "via_centrifuge", "via_side_rack", "side_rack_tube", "via_side_rack", "via_centrifuge", "centrifuge_pocket",  # 7 配平管
    "via_centrifuge", "via_side_rack", "side_rack_tube",                                                   # 9 卸配平管
    "via_side_rack", "via_centrifuge", "centrifuge_pocket", "via_centrifuge", "via_decapper", "decapper_tube",  # 9 卸离心管、开盖
    "via_decapper", "via_ws_B", "ws_B_tube", "via_ws_B",                                                   # 9 回管座
    "via_ws_C", "ws_C_plate", "via_ws_C", "via_imager", "imager_drawer", "via_imager",                     # 11 计数板送观察站
    "via_ws_A", "ws_A_plate", "via_ws_A", "via_waste", "waste_drop", "via_waste",                          # 母板弃置
    "via_incubator", "incubator_shelf4", "via_incubator", "via_ws_A", "ws_A_plate", "ws_A_lid", "via_ws_A",  # 12 子板进工作站、取盖
    "via_ws_C", "ws_C_plate", "via_ws_C", "via_ws_A", "ws_A_lid", "ws_A_plate", "via_ws_A",               # 13 盖回、子板出
    "via_incubator", "incubator_shelf3", "via_incubator", "via_imager", "imager_drawer", "via_imager",     # 13 回培养箱；14 计数板
    "via_waste", "waste_drop", "via_waste", "park"]
names = {p["name"] for p in poses}
assert all(n in names for n in ROUTE), [n for n in ROUTE if n not in names]
transitions = []
for a_, b_ in zip(ROUTE, ROUTE[1:]):
    if a_ != b_ and [a_, b_] not in transitions and [b_, a_] not in transitions:
        transitions.append([a_, b_])
first = {n: i for i, n in reversed(list(enumerate(ROUTE)))}
poses.sort(key=lambda p: first.get(p["name"], 999))

for p in poses:
    if "tcp_in_hand" not in p and "q" not in p:
        p["symmetric"] = False   # 偏置宽指：指垫在手掌下方 70 mm，绕进入方向转 180° 不是同一个抓取
spec = dict(
    clearance=0.005,
    robot=dict(mjcf="/mnt/d/Projects/Robots/assets/third_party/menagerie_franka_emika_panda/panda.xml",
               base=r["base"], yaw=0.0, rail=dict(axis=[1, 0, 0], range=r["range"]),
               tool=dict(tcp_in_hand=[FINGER["tcp_in_hand_x"], 0, FINGER["tcp_in_hand_z"]], opening_range=[0.0, FINGER["opening_range"][1]],
                         finger_boxes=[dict(name=p["name"], pos=p["pos"], size=p["size"]) for p in FINGER["parts"]])),
    static=static, movers=movers,
    workpieces=[dict(name="sixwell_plate_long", grip_width=0.1278), dict(name="lid_long", grip_width=0.130),
                dict(name="tube_15ml", grip_width=2 * TUBE_R)],
    poses=poses, park_pose="park", transitions=transitions)
(HERE / "preflight.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1))
print(f"{len(static)} 个静态代理，{len(movers)} 个活动件，{len(poses)} 个关键位姿，{len(transitions)} 段过渡")
