// The landing lab: the real layout of the 14-step cell-passaging project (preflight
// v3 boxes, movers and poses from layout.ts), drawn twice. The proxy tree is what
// the kinematic preflight sees; the model tree is what modelling produces. Which
// one shows, where the robot is and how far every door is open are pure functions
// of the story clock. Colors come from the --m-* tokens and follow the theme.

import * as THREE from 'three'
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js'
import { MOVERS, POSES, RAIL, STATIC, type PMover } from './layout'
import { clamp, lerp, ramp, smooth, window01 } from './story'

const V = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z)
/** MuJoCo (x, y, z-up) → three (x, y-up, z = −y). */
const M = (p: number[]) => V(p[0], p[2], -p[1])

function token(name: string) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
}
const col = (name: string, fallback = '#888888') => new THREE.Color(token(name) || fallback)
function num(name: string, fallback: number) {
  const v = parseFloat(token(name))
  return Number.isFinite(v) ? v : fallback
}
const std = (roughness = 0.7, metalness = 0, extra: THREE.MeshStandardMaterialParameters = {}) =>
  new THREE.MeshStandardMaterial({ roughness, metalness, ...extra })

type MatKey = 'body' | 'body2' | 'dark' | 'steel' | 'alu' | 'glass' | 'medium' | 'cap'

class Mats {
  floor = std(0.95)
  floorSide = std(0.95)
  body = std(0.5, 0.02)
  body2 = std(0.65)
  dark = std(0.5, 0.15)
  steel = std(0.3, 0.6)
  alu = std(0.4, 0.45)
  glass = std(0.06, 0, { transparent: true, opacity: 0.22, depthWrite: false })
  medium = std(0.35)
  cap = std(0.45)
  proxy = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.1, depthWrite: false })
  proxyBad = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.2, depthWrite: false })
  ghost = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.2, depthWrite: false })
  foot = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.08, depthWrite: false })
  wedge = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.12, depthWrite: false, side: THREE.DoubleSide })
  wedgeBad = new THREE.MeshBasicMaterial({ transparent: true, opacity: 0.25, depthWrite: false, side: THREE.DoubleSide })
  led = new THREE.MeshBasicMaterial()
  ok = new THREE.MeshBasicMaterial({ transparent: true })
  bad = new THREE.MeshBasicMaterial({ transparent: true })
  warn = new THREE.MeshBasicMaterial({ transparent: true })
  edge = new THREE.LineBasicMaterial({ transparent: true })
  edgeAccent = new THREE.LineBasicMaterial({ transparent: true })
  dash = new THREE.LineDashedMaterial({ transparent: true, dashSize: 0.06, gapSize: 0.04 })
  grid = new THREE.LineBasicMaterial({ transparent: true })
  ao: THREE.MeshBasicMaterial
  accent = new THREE.Color()
  dark01 = false
  edgeO = 0.3
  models: [THREE.MeshStandardMaterial, number][] = []

  constructor() {
    const c = document.createElement('canvas')
    c.width = c.height = 128
    const g = c.getContext('2d')!
    const grad = g.createRadialGradient(64, 64, 4, 64, 64, 64)
    grad.addColorStop(0, 'rgba(0,0,0,1)')
    grad.addColorStop(0.45, 'rgba(0,0,0,.55)')
    grad.addColorStop(1, 'rgba(0,0,0,0)')
    g.fillStyle = grad
    g.fillRect(0, 0, 128, 128)
    this.ao = new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false, polygonOffset: true, polygonOffsetFactor: -2 })
    this.models = [[this.body, 1], [this.body2, 1], [this.dark, 1], [this.steel, 1], [this.alu, 1], [this.glass, 0.22], [this.medium, 1], [this.cap, 1]]
  }

  apply() {
    this.dark01 = document.documentElement.classList.contains('dark')
    this.floor.color = col('--m-floor')
    this.floorSide.color = col('--m-floor-side')
    this.body.color = col('--m-body')
    this.body2.color = col('--m-body-2')
    this.dark.color = col('--m-dark')
    this.steel.color = col('--m-steel')
    this.alu.color = col('--m-alu')
    this.glass.color = col('--m-glass')
    this.medium.color = col('--m-medium')
    this.cap.color = col('--m-cap')
    this.accent = col('--accent')
    this.proxy.color = this.accent
    this.ghost.color = this.accent
    this.foot.color = this.accent
    this.wedge.color = this.accent
    this.proxyBad.color = col('--bad')
    this.wedgeBad.color = col('--bad')
    this.led.color = this.accent
    this.ok.color = col('--ok')
    this.bad.color = col('--bad')
    this.warn.color = col('--warn')
    this.edgeO = num('--m-edge-o', 0.3)
    this.edge.color = col('--m-edge')
    this.edgeAccent.color = this.accent
    this.dash.color = this.accent
    this.grid.color = col('--m-grid')
    this.ao.color = col('--m-shadow')
    for (const [m] of this.models) m.needsUpdate = true
  }

  /** Model tree fade: opaque materials go transparent only while fading. */
  fadeModels(o: number) {
    for (const [m, base] of this.models) {
      const transparent = m === this.glass || o < 0.999
      if (m.transparent !== transparent) { m.transparent = transparent; m.needsUpdate = true }
      m.opacity = base * o
      m.depthWrite = m !== this.glass && o > 0.5
    }
  }
}

// ---- Geometry helpers --------------------------------------------------------

function edgesOf(geo: THREE.BufferGeometry, mat: THREE.LineBasicMaterial, threshold = 30) {
  return new THREE.LineSegments(new THREE.EdgesGeometry(geo, threshold), mat)
}

/** Box centred at `c` (three frame) with full extents w × h × d. */
function boxAt(c: THREE.Vector3, w: number, h: number, d: number, mat: THREE.Material, edge: THREE.LineBasicMaterial | null, rounded: boolean) {
  const r = Math.min(0.012, w / 2.4, h / 2.4, d / 2.4)
  const geo = rounded && r > 0.002 ? new RoundedBoxGeometry(w, h, d, 2, r) : new THREE.BoxGeometry(w, h, d)
  const m = new THREE.Mesh(geo, mat)
  m.position.copy(c)
  m.castShadow = rounded
  m.receiveShadow = rounded
  if (edge) m.add(edgesOf(new THREE.BoxGeometry(w, h, d), edge))
  return m
}

function cylY(r: number, h: number, mat: THREE.Material, edge: THREE.LineBasicMaterial | null, seg = 28) {
  const geo = new THREE.CylinderGeometry(r, r, h, seg)
  geo.translate(0, h / 2, 0)
  const m = new THREE.Mesh(geo, mat)
  m.castShadow = true
  m.receiveShadow = true
  if (edge) m.add(edgesOf(geo, edge, 40))
  return m
}

function capsule(r: number, len: number, mat: THREE.Material) {
  const geo = new THREE.CapsuleGeometry(r, len, 6, 18)
  geo.translate(0, len / 2, 0)
  const m = new THREE.Mesh(geo, mat)
  m.castShadow = true
  return m
}

// ---- Robot arm (stylized Panda on a rail carriage) --------------------------------

const L1 = 0.47
const L2 = 0.45
const COLUMN = 0.26
const TOOL = 0.17

class ArmRig {
  root = new THREE.Group()
  yaw = new THREE.Group()
  shoulder = new THREE.Group()
  elbow = new THREE.Group()
  wrist = new THREE.Group()
  fingerL: THREE.Mesh
  fingerR: THREE.Mesh

  constructor(body: THREE.Material, dark: THREE.Material, edge: THREE.LineBasicMaterial | null) {
    this.root.add(cylY(0.09, 0.06, dark, edge))
    this.yaw.position.y = 0.06
    this.root.add(this.yaw)
    const column = capsule(0.06, COLUMN - 0.06 - 0.05, body)
    column.position.y = 0.02
    this.yaw.add(column)
    const joint = (r: number, w: number) => {
      const j = cylY(r, w, dark, edge, 24)
      j.rotation.x = Math.PI / 2
      j.position.z = w / 2
      return j
    }
    const sh = joint(0.07, 0.14)
    sh.position.y = COLUMN - 0.06
    this.yaw.add(sh)
    this.shoulder.position.y = COLUMN - 0.06
    this.yaw.add(this.shoulder)
    this.shoulder.add(capsule(0.052, L1, body))
    const el = joint(0.058, 0.12)
    el.position.y = L1
    this.shoulder.add(el)
    this.elbow.position.y = L1
    this.shoulder.add(this.elbow)
    this.elbow.add(capsule(0.045, L2, body))
    this.wrist.position.y = L2
    this.elbow.add(this.wrist)
    this.wrist.add(cylY(0.038, 0.06, dark, edge, 20))
    const palm = new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.03, 0.05), body)
    palm.position.y = 0.075
    palm.castShadow = true
    this.wrist.add(palm)
    const fg = new THREE.BoxGeometry(0.014, 0.075, 0.03)
    fg.translate(0, 0.0375, 0)
    this.fingerL = new THREE.Mesh(fg, dark)
    this.fingerR = new THREE.Mesh(fg, dark)
    this.fingerL.castShadow = this.fingerR.castShadow = true
    this.fingerL.position.y = this.fingerR.position.y = 0.09
    this.wrist.add(this.fingerL, this.fingerR)
    this.grip(1)
  }

  grip(open: number) {
    const x = 0.016 + 0.034 * clamp(open)
    this.fingerL.position.x = -x
    this.fingerR.position.x = x
  }

  /** Elbow-up IK with the tool pointing down; tcp in world (three) coordinates. */
  solve(tcp: THREE.Vector3) {
    const p = tcp.clone().sub(this.root.getWorldPosition(new THREE.Vector3()))
    const yaw = Math.atan2(-p.z, p.x)
    const r = Math.max(0.12, Math.hypot(p.x, p.z))
    let wx = r
    let wy = p.y - COLUMN + TOOL
    let d = Math.hypot(wx, wy)
    const dmax = L1 + L2 - 0.002
    if (d > dmax) { wx *= dmax / d; wy *= dmax / d; d = dmax }
    const alpha = Math.atan2(wx, wy)
    const beta = Math.acos(clamp((L1 * L1 + d * d - L2 * L2) / (2 * L1 * d), -1, 1))
    const gamma = Math.acos(clamp((L1 * L1 + L2 * L2 - d * d) / (2 * L1 * L2), -1, 1))
    const q2 = alpha - beta
    const q3 = Math.PI - gamma
    this.yaw.rotation.y = yaw
    this.shoulder.rotation.z = -q2
    this.elbow.rotation.z = -q3
    this.wrist.rotation.z = -(Math.PI - (q2 + q3))
  }

  tcpWorld() {
    const p = V(0, TOOL, 0)
    this.wrist.localToWorld(p)
    return p
  }
}

// ---- Layout grouping ---------------------------------------------------------------

type DevKey = 'incubator' | 'imager' | 'workstation' | 'centrifuge' | 'decapper' | 'sideRack' | 'waste' | 'rail'
const DEVICES: DevKey[] = ['incubator', 'imager', 'workstation', 'centrifuge', 'decapper', 'sideRack', 'waste', 'rail']

function devOf(name: string): DevKey {
  if (name.startsWith('incubator')) return 'incubator'
  if (name.startsWith('imager')) return 'imager'
  if (name.startsWith('workstation') || name.startsWith('ws_')) return 'workstation'
  if (name.startsWith('centrifuge')) return 'centrifuge'
  if (name.startsWith('decapper')) return 'decapper'
  if (name.startsWith('side_rack')) return 'sideRack'
  if (name.startsWith('waste')) return 'waste'
  return 'rail'
}

function matOf(name: string): MatKey {
  if (/panel|fascia/.test(name) || name === 'incubator_inner' || name.startsWith('ws_door')) return 'glass'
  if (/deck$|shelf|rotor/.test(name)) return 'steel'
  if (/bench|table|plinth/.test(name)) return 'body2'
  if (/gantry|waste_(w|tray)/.test(name)) return 'alu'
  if (/post|housing|deck_front|rail_beam|jaw/.test(name)) return 'dark'
  if (/tip_rack|reservoirs|waste_liquid|tube_holder/.test(name)) return 'medium'
  if (name === 'centrifuge_lid') return 'cap'
  return 'body'
}

interface Tree {
  root: THREE.Group
  dev: Record<DevKey, THREE.Group>
  movers: Record<string, THREE.Group>
}

/** Robot and plate keyframes in the simulation chapter (MuJoCo coordinates). */
interface Key { t: number; p: number[]; open: number; cx?: number }
const P = POSES
const up = (p: number[], dz: number) => [p[0], p[1], p[2] + dz]
const SIM: Key[] = [
  { t: 42.6, p: P.park, open: 1 },
  { t: 43.6, p: P.via_incubator, open: 1 },
  { t: 44.2, p: P.incubator_shelf3, open: 1 },
  { t: 44.5, p: P.incubator_shelf3, open: 0 },
  { t: 45.0, p: up(P.via_incubator, -0.02), open: 0 },
  { t: 45.9, p: P.via_imager, open: 0 },
  { t: 46.3, p: P.imager_drawer, open: 0 },
  { t: 46.6, p: P.imager_drawer, open: 1 },
  { t: 47.0, p: P.via_imager, open: 0.15 },
  { t: 47.2, p: P.via_side_rack, open: 0.15 },
  { t: 47.6, p: P.side_rack_tube, open: 0.15 },
  { t: 49.4, p: P.side_rack_tube, open: 0.15 },
  { t: 49.9, p: up(P.side_rack_tube, 0.08), open: 0.15 },
  { t: 50.6, p: P.side_rack_tube, open: 0.15 },
  { t: 50.9, p: P.side_rack_tube, open: 1 },
  { t: 51.4, p: P.via_side_rack, open: 1 },
  { t: 52.2, p: P.via_side_rack, open: 1 },
  { t: 54.4, p: P.via_side_rack, open: 1 },
  { t: 55.6, p: P.park, open: 1 },
]
/** IK preview during preflight: the ghost arm visits the key poses. */
const PREVIEW = ['park', 'incubator_shelf3', 'imager_drawer', 'centrifuge_pocket', 'side_rack_tube', 'ws_A_plate', 'ws_B_tube', 'decapper_tube', 'waste_drop', 'park']
/** Negative N4: ghost arm reaches into the workstation with the door shut. */
const NEG: Key[] = [
  { t: 52.4, p: P.via_ws_A, open: 1 },
  { t: 53.2, p: up(P.ws_A_plate, 0.04), open: 1 },
  { t: 54.6, p: up(P.ws_A_plate, 0.04), open: 1 },
]

function keyAt(keys: Key[], t: number) {
  if (t <= keys[0].t) return { p: M(keys[0].p), open: keys[0].open }
  for (let i = 1; i < keys.length; i++) {
    const b = keys[i]
    if (t <= b.t) {
      const a = keys[i - 1]
      const s = smooth((t - a.t) / (b.t - a.t))
      return { p: M(a.p).lerp(M(b.p), s), open: lerp(a.open, b.open, s) }
    }
  }
  const k = keys[keys.length - 1]
  return { p: M(k.p), open: k.open }
}

/** Carriage position along the rail for a TCP target, offset 0.25 m as in the project. */
const carriageFor = (tcp: THREE.Vector3) => clamp(tcp.x + (tcp.z > 0 ? 0.25 : -0.25), RAIL.range[0], RAIL.range[1])

// ---- Camera -------------------------------------------------------------------------

interface Cam { t: number; target: THREE.Vector3; span: number; el: number; az: number }
const C = V(1.55, 0.7, 0.0)
const FILM: Cam[] = [
  { t: 0, target: C, span: 10.5, el: 62, az: 24 },
  { t: 8.6, target: C, span: 9.6, el: 56, az: 28 },
  { t: 10.4, target: C, span: 8.8, el: 46, az: 32 },
  { t: 19.4, target: C, span: 8.6, el: 44, az: 38 },
  { t: 21.0, target: V(1.55, 0.8, 0), span: 8.4, el: 42, az: 30 },
  { t: 27.6, target: V(1.55, 0.8, 0), span: 8.2, el: 42, az: 26 },
  { t: 29.4, target: V(1.3, 0.85, 0.25), span: 6.6, el: 40, az: 22 },
  { t: 33.6, target: V(1.3, 0.85, 0.25), span: 6.5, el: 40, az: 26 },
  { t: 35.2, target: V(1.55, 1.55, 0), span: 10.6, el: 26, az: 34 },
  { t: 40.4, target: V(1.55, 1.45, 0), span: 10.2, el: 28, az: 30 },
  { t: 42.4, target: V(2.5, 0.9, 0.6), span: 5.4, el: 62, az: 166 },
  { t: 46.4, target: V(2.05, 0.9, 0.55), span: 5.6, el: 60, az: 176 },
  { t: 47.4, target: V(0.65, 0.85, 0.45), span: 5.4, el: 52, az: 184 },
  { t: 51.6, target: V(0.75, 0.85, 0.35), span: 5.6, el: 50, az: 190 },
  { t: 52.6, target: V(1.2, 0.95, -0.5), span: 5.3, el: 38, az: 16 },
  { t: 54.8, target: V(1.2, 0.95, -0.5), span: 5.3, el: 38, az: 18 },
  { t: 56.6, target: V(1.55, 0.55, 0.1), span: 7.4, el: 54, az: 2 },
  { t: 63.6, target: V(1.55, 0.55, 0.1), span: 7.2, el: 55, az: 0 },
  { t: 66.0, target: C, span: 10.0, el: 50, az: 34 },
  { t: 72.0, target: C, span: 11.0, el: 52, az: 52 },
]

function filmCam(t: number): Omit<Cam, 't'> {
  if (t <= FILM[0].t) return FILM[0]
  for (let i = 1; i < FILM.length; i++) {
    const b = FILM[i]
    if (t <= b.t) {
      const a = FILM[i - 1]
      const s = smooth((t - a.t) / (b.t - a.t))
      return {
        target: a.target.clone().lerp(b.target, s),
        span: Math.exp(lerp(Math.log(a.span), Math.log(b.span), s)),
        el: lerp(a.el, b.el, s),
        az: lerp(a.az, b.az, s),
      }
    }
  }
  return FILM[FILM.length - 1]
}

// ---- Stage --------------------------------------------------------------------------

export interface Projected { x: number; y: number; visible: boolean }

const BAD_V1 = new Set(['incubator_shelf3', 'via_incubator', 'ws_B_tube', 'decapper_tube'])
const BAD_V2 = new Set(['waste_drop', 'centrifuge_pocket'])
const LIFT = 1.15

export class LabStage {
  renderer: THREE.WebGLRenderer
  scene = new THREE.Scene()
  camera = new THREE.OrthographicCamera(-1, 1, 1, -1, -200, 400)
  mats = new Mats()
  hemi = new THREE.HemisphereLight()
  key = new THREE.DirectionalLight()
  proxy: Tree
  model: Tree
  feet: { dev: DevKey; mesh: THREE.Mesh; line: THREE.LineLoop; box: THREE.Box3 }[] = []
  wedges: { mover: string; mesh: THREE.Mesh }[] = []
  markers: { name: string; mesh: THREE.Mesh }[] = []
  arm: ArmRig
  ghost: ArmRig
  carriage: THREE.Group
  ghostCarriage: THREE.Group
  plate: THREE.Group
  tube: THREE.Group
  rings: Record<'bad' | 'ok' | 'warn', THREE.Mesh>
  anchors: Record<string, THREE.Vector3> = {}
  width = 1
  height = 1
  offsetX = 0
  offsetY = 0
  private baseHemi = 1.6
  private baseKey = 2.6
  private reduced: boolean

  constructor(canvas: HTMLCanvasElement, reduced = false) {
    this.reduced = reduced
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance', preserveDrawingBuffer: false })
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
    this.renderer.outputColorSpace = THREE.SRGBColorSpace
    this.renderer.toneMapping = THREE.NeutralToneMapping
    this.renderer.shadowMap.enabled = true
    this.renderer.shadowMap.type = THREE.PCFShadowMap
    this.renderer.setClearColor(0x000000, 0)

    this.scene.add(this.hemi, this.key, this.key.target)
    this.key.castShadow = true
    this.key.shadow.mapSize.set(2048, 2048)
    this.key.shadow.bias = -0.0004
    this.key.shadow.normalBias = 0.02
    const sc = this.key.shadow.camera
    sc.left = -3.5; sc.right = 3.5; sc.top = 3.5; sc.bottom = -3.5; sc.near = 0.5; sc.far = 30

    const m = this.mats
    this.buildRoom()
    this.proxy = this.buildTree(false)
    this.model = this.buildTree(true)
    this.scene.add(this.proxy.root, this.model.root)
    this.buildFootprints()
    this.buildWedges()
    this.buildMarkers()

    this.arm = new ArmRig(m.body, m.dark, m.edge)
    this.ghost = new ArmRig(m.ghost, m.ghost, null)
    this.ghost.root.traverse((o) => { o.castShadow = false })
    this.carriage = this.buildCarriage(m.body2, m.dark, m.edge)
    this.ghostCarriage = this.buildCarriage(m.ghost, m.ghost, null)
    this.carriage.add(this.arm.root)
    this.ghostCarriage.add(this.ghost.root)
    this.arm.root.position.y = this.ghost.root.position.y = RAIL.baseZ
    this.scene.add(this.carriage, this.ghostCarriage)

    this.plate = new THREE.Group()
    const plateBody = boxAt(V(0, 0, 0), 0.128, 0.016, 0.086, m.body, m.edge, true)
    const lid = boxAt(V(0, 0.011, 0), 0.128, 0.006, 0.086, m.cap, null, true)
    this.plate.add(plateBody, lid)
    this.tube = new THREE.Group()
    const tb = cylY(0.008, 0.11, m.glass, m.edge, 16)
    tb.position.y = -0.06
    const cap = cylY(0.0095, 0.018, m.cap, null, 16)
    cap.position.y = 0.05
    this.tube.add(tb, cap)
    this.scene.add(this.plate, this.tube)

    const ring = (mat: THREE.Material) => {
      const r = new THREE.Mesh(new THREE.RingGeometry(0.075, 0.095, 48), mat)
      r.rotation.x = -Math.PI / 2
      r.renderOrder = 3
      this.scene.add(r)
      return r
    }
    this.rings = { bad: ring(m.bad), ok: ring(m.ok), warn: ring(m.warn) }
    this.applyTheme()
  }

  private buildRoom() {
    const m = this.mats
    const room = new THREE.Group()
    const slab = new THREE.Mesh(new RoundedBoxGeometry(4.4, 0.08, 3.5, 2, 0.03), m.floor)
    slab.position.set(1.5, -0.04, 0.05)
    slab.receiveShadow = true
    room.add(slab)
    const side = new THREE.Mesh(new THREE.BoxGeometry(4.36, 0.16, 3.46), m.floorSide)
    side.position.set(1.5, -0.13, 0.05)
    room.add(side)
    const pts: number[] = []
    for (let x = -0.6; x <= 3.61; x += 0.25) pts.push(x, 0.001, -1.65, x, 0.001, 1.75)
    for (let z = -1.65; z <= 1.76; z += 0.25) pts.push(-0.6, 0.001, z, 3.6, 0.001, z)
    const gg = new THREE.BufferGeometry()
    gg.setAttribute('position', new THREE.Float32BufferAttribute(pts, 3))
    room.add(new THREE.LineSegments(gg, m.grid))
    this.scene.add(room)
  }

  private buildTree(model: boolean): Tree {
    const m = this.mats
    const root = new THREE.Group()
    const dev = {} as Record<DevKey, THREE.Group>
    for (const k of DEVICES) { dev[k] = new THREE.Group(); root.add(dev[k]) }
    const matFor = (name: string) => (model ? m[matOf(name)] : m.proxy)
    const edge = model ? m.edge : m.edgeAccent
    for (const b of STATIC) {
      const c = M(b.pos)
      dev[devOf(b.name)].add(boxAt(c, 2 * b.size[0], 2 * b.size[2], 2 * b.size[1], matFor(b.name), matOf(b.name) === 'glass' && model ? null : edge, model))
    }
    const movers: Record<string, THREE.Group> = {}
    for (const mv of MOVERS) {
      const pivot = new THREE.Group()
      pivot.position.copy(M(mv.anchor))
      for (const b of mv.boxes) {
        const c = M(b.pos)
        pivot.add(boxAt(c, 2 * b.size[0], 2 * b.size[2], 2 * b.size[1], matFor(mv.name), model && matOf(mv.name) === 'glass' ? null : edge, model))
      }
      pivot.userData.mover = mv
      movers[mv.name] = pivot
      dev[devOf(mv.name)].add(pivot)
    }
    if (model) {
      // A few parts the preflight never needed: carriage tray, handles, lamp strips.
      movers.incubator_outer.add(boxAt(M([-0.64, 0.05, 0.43]), 0.02, 0.32, 0.03, m.dark, null, true))
      for (const d of DEVICES) dev[d].traverse((o) => { if ((o as THREE.Mesh).isMesh) (o as THREE.Mesh).castShadow = true })
    }
    return { root, dev, movers }
  }

  private buildCarriage(body: THREE.Material, dark: THREE.Material, edge: THREE.LineBasicMaterial | null) {
    const g = new THREE.Group()
    g.add(boxAt(V(0, 0.13, 0), 0.32, 0.06, 0.3, body, edge, true))
    const col = cylY(0.07, RAIL.baseZ - 0.16, dark, edge)
    col.position.y = 0.16
    g.add(col)
    return g
  }

  private buildFootprints() {
    const m = this.mats
    for (const d of DEVICES) {
      if (d === 'rail') continue
      const box = new THREE.Box3()
      for (const b of STATIC) if (devOf(b.name) === d) {
        const c = M(b.pos)
        box.expandByPoint(V(c.x - b.size[0], 0, c.z - b.size[1]))
        box.expandByPoint(V(c.x + b.size[0], 0, c.z + b.size[1]))
      }
      const w = box.max.x - box.min.x
      const h = box.max.z - box.min.z
      const mesh = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m.foot)
      mesh.rotation.x = -Math.PI / 2
      mesh.position.set((box.min.x + box.max.x) / 2, 0.004, (box.min.z + box.max.z) / 2)
      const pts = [V(box.min.x, 0.006, box.min.z), V(box.max.x, 0.006, box.min.z), V(box.max.x, 0.006, box.max.z), V(box.min.x, 0.006, box.max.z)]
      const line = new THREE.LineLoop(new THREE.BufferGeometry().setFromPoints(pts), m.dash)
      line.computeLineDistances()
      this.scene.add(mesh, line)
      this.feet.push({ dev: d, mesh, line, box })
    }
  }

  private buildWedges() {
    const m = this.mats
    for (const mv of MOVERS) {
      if (mv.type !== 'hinge' || mv.name === 'centrifuge_lid' || mv.name === 'incubator_inner') continue
      const b = mv.boxes[0]
      const r = Math.hypot(b.pos[0], b.pos[1]) + b.size[0]
      const start = Math.atan2(b.pos[1], b.pos[0])
      const dir = mv.axis[2] < 0 ? -1 : 1
      const geo = new THREE.CircleGeometry(r, 40, 0, mv.range[1])
      const mesh = new THREE.Mesh(geo, m.wedge)
      // Circle lies in its XY plane; lay it on the floor and start at the closed door.
      mesh.rotation.x = -Math.PI / 2
      mesh.rotation.z = start + (dir < 0 ? -mv.range[1] : 0)
      mesh.position.set(0, 0.008, 0)
      const pivot = new THREE.Group()
      pivot.position.copy(M([mv.anchor[0], mv.anchor[1], 0]))
      pivot.add(mesh)
      this.scene.add(pivot)
      this.wedges.push({ mover: mv.name, mesh })
    }
  }

  private buildMarkers() {
    const geo = new THREE.SphereGeometry(0.026, 16, 12)
    for (const [name, p] of Object.entries(POSES)) {
      const mesh = new THREE.Mesh(geo, this.mats.ok)
      mesh.position.copy(M(p))
      mesh.renderOrder = 4
      this.scene.add(mesh)
      this.markers.push({ name, mesh })
    }
  }

  applyTheme() {
    this.mats.apply()
    this.hemi.color = col('--m-sky')
    this.hemi.groundColor = col('--m-gnd')
    this.key.color = col('--m-sun')
    this.baseHemi = num('--m-hemi', 0.8) * Math.PI * 0.82
    this.baseKey = num('--m-key', 0.9) * Math.PI * 1.08
  }

  resize(w: number, h: number) {
    this.width = Math.max(1, w)
    this.height = Math.max(1, h)
    this.renderer.setSize(this.width, this.height, false)
  }

  setOffset(x: number, y = 0) {
    this.offsetX = x
    this.offsetY = y
  }

  /** Joint value of a mover at time t (rad or m). */
  private moverQ(name: string, t: number): number {
    // Preflight sweeps every mover once to check it against the static scene.
    const sweep = (a: number, b: number, q: number) => q * Math.sin(Math.PI * clamp((t - a) / (b - a)))
    switch (name) {
      case 'incubator_outer':
        return t < 30 ? sweep(11.0, 12.8, 1.95) : 1.95 * Math.min(ramp(t, 42.6, 43.4), 1 - ramp(t, 45.0, 45.8))
      case 'incubator_inner':
        return t < 30 ? sweep(11.2, 12.8, 1.7) : 1.7 * Math.min(ramp(t, 42.7, 43.4), 1 - ramp(t, 45.0, 45.7))
      case 'ws_door_left':
      case 'ws_door_right':
        return t < 30 ? sweep(12.2, 13.8, 1.75) : 0
      case 'centrifuge_lid':
        return t < 30 ? sweep(12.8, 14.2, 1.6) : 0
      case 'imager_drawer':
        return t < 30 ? sweep(13.2, 14.4, 0.19) : 0.19 * Math.min(ramp(t, 45.0, 45.8), 1 - ramp(t, 47.0, 47.6))
    }
    return 0
  }

  update(t: number, now: number) {
    const m = this.mats
    const amb = this.reduced ? 0 : now

    // Camera.
    const cam = filmCam(t)
    const aspect = this.width / this.height
    const viewH = Math.max(cam.span / 1.78, (cam.span * 0.82) / aspect)
    const viewW = viewH * aspect
    const c = this.camera
    c.left = -viewW / 2 - this.offsetX * viewW
    c.right = viewW / 2 - this.offsetX * viewW
    c.top = viewH / 2 - this.offsetY * viewH
    c.bottom = -viewH / 2 - this.offsetY * viewH
    const az = THREE.MathUtils.degToRad(cam.az + 1.2 * Math.sin(amb * 0.11))
    const el = THREE.MathUtils.degToRad(cam.el)
    const dir = V(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el))
    c.position.copy(cam.target).addScaledVector(dir, 60)
    c.lookAt(cam.target)
    c.updateProjectionMatrix()
    this.hemi.intensity = this.baseHemi
    this.key.intensity = this.baseKey
    this.key.position.copy(cam.target).add(V(-2.6, 7, 4.2))
    this.key.target.position.copy(cam.target)

    // Footprints (scene list), then proxies rising out of them.
    DEVICES.forEach((d, i) => {
      const rise = ramp(t, 9.2 + i * 0.12, 10.1 + i * 0.12)
      const g = this.proxy.dev[d]
      g.scale.y = Math.max(0.001, rise)
      g.visible = rise > 0.005
    })
    this.feet.forEach((f, i) => {
      const o = window01(t, 5.7 + i * 0.3, 10.4, 0.35)
      ;(f.mesh.material as THREE.MeshBasicMaterial).opacity = 0.08
      f.mesh.visible = f.line.visible = o > 0.01
      f.mesh.scale.setScalar(lerp(0.85, 1, o))
    })
    m.dash.opacity = Math.max(...this.feet.map((_, i) => window01(t, 5.7 + i * 0.3, 10.4, 0.35))) * 0.9

    // Layout v1 → v3: the incubator starts nearer the rail, a plinth lower.
    const v1 = 1 - ramp(t, 13.8, 15.2)
    const plinth = 1 - ramp(t, 15.8, 16.4)
    for (const tree of [this.proxy, this.model]) tree.dev.incubator.position.set(-0.05 * v1, -0.12 * plinth, -0.32 * v1)

    // Proxy vs model.
    const modelO = ramp(t, 30.4, 35.0)
    const proxyO = t < 35 ? 1 : 1 - ramp(t, 39.6, 41.4)
    const lift = LIFT * window01(t, 35.4, 40.6, 1.0)
    this.proxy.root.position.y = lift
    this.proxy.root.visible = proxyO > 0.01
    m.proxy.opacity = 0.09 * proxyO * (t > 35 ? 1.6 : 1)
    m.edgeAccent.opacity = (t < 20 ? 0.6 : lerp(0.6, 0.35, ramp(t, 20, 22))) * proxyO
    m.edgeAccent.color.copy(m.accent)
    this.model.root.visible = modelO > 0.01
    m.fadeModels(modelO)
    m.edge.opacity = m.edgeO * modelO

    // Movers.
    for (const tree of [this.proxy, this.model]) {
      for (const [name, pivot] of Object.entries(tree.movers)) {
        const mv = pivot.userData.mover as PMover
        const q = this.moverQ(name, t)
        if (mv.type === 'slide') {
          pivot.position.copy(M(mv.anchor)).add(M([mv.axis[0] * q, mv.axis[1] * q, mv.axis[2] * q]))
        } else if (Math.abs(mv.axis[0]) > 0.5) {
          pivot.rotation.x = q * Math.sign(mv.axis[0])
        } else {
          pivot.rotation.y = q * Math.sign(mv.axis[2])
        }
      }
    }

    // Door sweep wedges and pose markers belong to the preflight chapter.
    const pf = window01(t, 10.4, 19.8, 0.5)
    for (const w of this.wedges) {
      const bad = w.mover === 'incubator_outer' && t < 14.6
      w.mesh.material = bad ? m.wedgeBad : m.wedge
      w.mesh.visible = pf > 0.01
      const mv = MOVERS.find((x) => x.name === w.mover)!
      w.mesh.parent!.position.set(mv.anchor[0], 0, -mv.anchor[1])
      if (w.mover.startsWith('incubator')) w.mesh.parent!.position.add(V(-0.05 * v1, 0, -0.32 * v1))
    }
    m.wedge.opacity = 0.13 * pf
    m.wedgeBad.opacity = 0.28 * pf
    const mk = window01(t, 10.8, 19.8, 0.4)
    for (const k of this.markers) {
      k.mesh.visible = mk > 0.01
      const bad = (t < 13.8 && BAD_V1.has(k.name)) || (t >= 13.8 && t < 16.2 && BAD_V2.has(k.name))
      k.mesh.material = bad ? m.bad : m.ok
      k.mesh.scale.setScalar(mk * (bad ? 1.25 + 0.2 * Math.sin(amb * 6) : 1))
      if (k.name.startsWith('incubator')) k.mesh.position.copy(M(POSES[k.name])).add(V(-0.05 * v1, -0.12 * plinth, -0.32 * v1))
    }
    m.ok.opacity = m.bad.opacity = m.warn.opacity = 1

    // Robot: ghost previews poses during preflight; the solid arm appears with the models.
    const ghostPreview = window01(t, 10.2, 17.2, 0.5)
    const neg = window01(t, 52.2, 55.0, 0.4)
    this.ghostCarriage.visible = ghostPreview > 0.01 || neg > 0.01
    m.ghost.opacity = 0.32 * Math.max(ghostPreview, neg)
    if (ghostPreview > 0.01) {
      const s = clamp((t - 10.6) / 6.2) * (PREVIEW.length - 1)
      const i = Math.min(PREVIEW.length - 2, Math.floor(s))
      const f = smooth(s - i)
      const tcp = M(POSES[PREVIEW[i]]).lerp(M(POSES[PREVIEW[i + 1]]), f)
      this.ghostCarriage.position.set(carriageFor(tcp), 0, 0)
      this.ghostCarriage.updateMatrixWorld(true)
      this.ghost.solve(tcp)
      this.ghost.grip(1)
    } else if (neg > 0.01) {
      const k = keyAt(NEG, t)
      this.ghostCarriage.position.set(carriageFor(k.p), 0, 0)
      this.ghostCarriage.updateMatrixWorld(true)
      this.ghost.solve(k.p)
      this.ghost.grip(k.open)
    }

    const armO = ramp(t, 32.0, 35.0)
    this.carriage.visible = armO > 0.01
    const k = t < 42.6 ? { p: M(POSES.park), open: 1 } : keyAt(SIM, t)
    const breathe = t < 42 || t > 55.6 ? V(0, 0.01 * Math.sin(amb * 0.8), 0.01 * Math.sin(amb * 0.6)) : V()
    const tcp = k.p.clone().add(breathe)
    this.carriage.position.set(carriageFor(tcp), 0, 0)
    this.carriage.updateMatrixWorld(true)
    this.arm.solve(tcp)
    this.arm.grip(k.open)
    this.carriage.updateMatrixWorld(true)
    const hand = this.arm.tcpWorld()

    // Plate: on shelf 3, in the hand, then on the drawer.
    this.plate.visible = modelO > 0.5
    const shelf = M([2.85, -0.82, 0.946])
    const drawerQ = this.moverQ('imager_drawer', t)
    if (t < 44.5) this.plate.position.copy(shelf).add(V(-0.05 * v1, -0.12 * plinth, -0.32 * v1))
    else if (t < 46.6) this.plate.position.copy(hand).add(V(0, -0.012, 0))
    else this.plate.position.copy(M([1.75, -0.535 - (0.19 - drawerQ), 0.916]))
    this.plate.rotation.y = 0

    // Balance tube: carried to the side rack, released after the fix.
    this.tube.visible = t > 46.8 && t < 64
    if (t < 50.9) this.tube.position.copy(hand).add(V(0, -0.02, 0))
    else this.tube.position.copy(M(up(P.side_rack_tube, -0.02)))

    // Verdict rings.
    const side = M([0.08, -0.56, 0.745])
    const pulse = 1 + 0.12 * Math.sin(amb * 7)
    const ringAt = (r: THREE.Mesh, p: THREE.Vector3, o: number, s = 1) => {
      r.visible = o > 0.01
      r.position.copy(p)
      r.scale.setScalar(s * lerp(0.6, 1, o))
      ;(r.material as THREE.MeshBasicMaterial).opacity = o
    }
    ringAt(this.rings.bad, side, window01(t, 47.6, 50.3, 0.25), pulse)
    ringAt(this.rings.ok, side, window01(t, 50.6, 52.2, 0.25))
    ringAt(this.rings.warn, M([1.3, 0.645, 0.92]), window01(t, 53.0, 55.0, 0.25), pulse * 1.4)

    // Anchors for HTML labels (three frame).
    const incOff = V(-0.05 * v1, -0.12 * plinth, -0.32 * v1)
    this.anchors = {
      incubator: M([2.85, -1.0, 1.36]).add(incOff),
      incDoor: M([2.75, -0.3, 0.6]).add(incOff),
      imager: M([1.75, -0.8, 1.14]),
      workstation: M([1.55, 1.02, 1.74]),
      wsDoor: M([1.0, 0.64, 1.32]),
      wsDeck: M([1.55, 1.095, 1.0]),
      wsTube: M([1.55, 0.84, 1.0]),
      centrifuge: M([0.55, -0.7, 1.02]),
      decapper: M([1.05, -0.67, 0.98]),
      rail: M([1.9, 0, 0.12]),
      sideRack: M([0.08, -0.56, 0.86]),
      visTag: M([0.98, 1.0, 1.72]),
      colTag: M([0.98, 1.0, 1.72]).add(V(0, lift, 0)),
      plateAt: this.plate.position.clone().add(V(0, 0.04, 0)),
    }
  }

  render() {
    this.renderer.render(this.scene, this.camera)
  }

  project(name: string): Projected {
    const a = this.anchors[name]
    if (!a) return { x: 0, y: 0, visible: false }
    const p = a.clone().project(this.camera)
    const x = (p.x * 0.5 + 0.5) * this.width
    const y = (-p.y * 0.5 + 0.5) * this.height
    return { x, y, visible: x > -40 && x < this.width + 40 && y > -20 && y < this.height + 20 }
  }

  dispose() {
    this.scene.traverse((o) => {
      const mesh = o as THREE.Mesh
      mesh.geometry?.dispose?.()
      const mat = mesh.material as THREE.Material | THREE.Material[] | undefined
      if (Array.isArray(mat)) mat.forEach((x) => x.dispose())
      else mat?.dispose?.()
    })
    this.renderer.dispose()
    this.renderer.forceContextLoss()
  }
}
