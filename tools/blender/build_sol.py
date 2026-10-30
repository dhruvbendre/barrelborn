"""Build Marisol "Sol" Quill (navigator NPC): mesh + rig + idle/talk/point + GLB + previews.

Run (from anywhere):
  blender -b --factory-startup --python tools/blender/build_sol.py [-- --no-render]
"""
import math
import os
import sys

import bpy  # noqa: F401
from mathutils import Vector as V, Quaternion, Euler

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import humanoid as H  # noqa: E402
from humanoid import smoothstep as ss  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

PAL = H.Palette({
    "teal": "#2f8f8a", "teal_dk": "#1f625e", "brass": "#c79a3b", "brass_dk": "#8a6520",
    "white": "#f5f2ea", "white_dk": "#d6d0c2", "auburn": "#9a3f22", "auburn_dk": "#6e2a16",
    "auburn_lt": "#b8552e", "charcoal": "#3a3d44", "charcoal_dk": "#26282d", "skin": "#f1d3bd",
    "skin_dk": "#d9ab8f", "freckle": "#c27a55", "boot": "#4e3426", "boot_dk": "#33211a",
    "boot_lt": "#6b4a36", "leather": "#7a4f2e", "leather_dk": "#553419", "tube": "#c2a074",
    "tube_dk": "#9c7c52", "glass": "#9fd8d0", "glass_dk": "#5fa8a0", "eye_white": "#fbf7ee",
    "iris": "#4f9a7e", "iris_dk": "#2c5a4b", "pupil": "#1a0f0a", "lash": "#2a120c", "hi": "#ffffff",
    "mouth": "#9c4a42", "pencil": "#e8b83a", "wood": "#e8c9a0", "graphite": "#333333",
    "eraser": "#d98a8a", "face": "#f3ead2", "needle": "#c4282a", "steel": "#7f8b98",
})

# ----------------------------------------------------------------------------- layout (1.7 m)
D_ARM = V((0.30, 0.0, -0.954)).normalized()
J = dict(hips=(0, 0, 0.90), spine=(0, 0, 1.00), chest=(0, 0, 1.12), neck=(0, 0.005, 1.31),
         head=(0, 0.005, 1.39), head_top=(0, 0.005, 1.66), shoulder=(0.03, 0, 1.27),
         arm=(0.15, 0, 1.255), hip=(0.075, 0, 0.88), knee=(0.08, -0.005, 0.49),
         ankle=(0.085, 0.012, 0.09), toe=(0.09, -0.13, 0.025))
J["elbow"] = V(J["arm"]) + D_ARM * 0.27
J["wrist"] = J["elbow"] + D_ARM * 0.24
J["hand_end"] = J["wrist"] + D_ARM * 0.09
U_WRIST = 0.51  # wrist distance from the shoulder joint along the arm

HC, HR = V((0, 0.005, 1.505)), (0.112, 0.116, 0.138)
head_pt = H.head_shape(HC, HR, jaw=0.45, jaw_front=0.15)
HAND = 0.88
HEAD_DZ = -0.02


def hand_axes(s):
    a = V((D_ARM.x * s, 0, D_ARM.z))
    g = V((0, -1, 0))
    p = a.cross(g).normalized()
    if p.x * s > 0:
        p = -p
    return a, g, p


def index_root():
    a, g, p = hand_axes(1)
    c = V(J["wrist"]) + a * 0.044 * HAND
    return c + g * (1.5 * 0.022 * HAND) - p * (0.02 * HAND) + a * (0.01 * HAND)


K3 = index_root()
EXTRAS = [("braid.1", (0, 0.11, 1.42), (0, 0.125, 1.20), "head"),
          ("braid.2", (0, 0.125, 1.20), (0, 0.125, 0.96), "braid.1"),
          ("index.L", K3, K3 + D_ARM * 0.055, "hand.L")]
BONES = H.standard_skeleton(J, EXTRAS)


def ccw(pts):
    a = sum(x0 * y1 - x1 * y0 for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]))
    return pts if a > 0 else pts[::-1]


# ----------------------------------------------------------------------------- head & face
def build_head(parts):
    hp = H.Part(["head"])
    H.sphere(hp, head_pt, 24, 16, "skin")
    H.ellipsoid(hp, (0, -0.106, 1.474), (0.010, 0.012, 0.016), 8, 6, "skin",
                H.axes((1, 0, 0), (0, 0.94, 0.34), (0, -0.34, 0.94)))
    bvh = hp.bvh()
    O, R, U = H.FACE
    for s in (1, -1):
        # dry, observant: half-lidded; her LEFT brow cocked up in permanent skepticism
        brow = (0.052, 0.012, 0.012) if s > 0 else (0.040, -0.004, 0.012)
        H.anime_eye(hp, bvh, 0.044, 1.503, s, k=0.88, iris="iris", iris_dk="iris_dk", hi="hi",
                    brow="auburn_dk", lid=0.3 if s < 0 else 0.22, brow_spec=brow)
        H.ellipsoid(hp, (0.109 * s, 0.012, 1.49), (0.016, 0.023, 0.031), 8, 6, "skin")
        for fx, fz in ((0.034, 1.466), (0.05, 1.472), (0.066, 1.463), (0.044, 1.455), (0.06, 1.452), (0.017, 1.482)):
            H.decal(hp, bvh, O, R, U, ccw(H.ellipse_pts(fx * s, fz, 0.0034, 0.0030, 6)), "freckle", 0.0018, 1)
    # flat, slightly lopsided mouth (left corner up): unimpressed
    top = [(-0.017, 1.4335), (-0.008, 1.4325), (0.0, 1.4325), (0.009, 1.4335), (0.019, 1.437)]
    bot = [(-0.016, 1.4295), (-0.008, 1.4285), (0.0, 1.4285), (0.009, 1.4295), (0.018, 1.4335)]
    H.decal_strip(hp, bvh, O, R, U, top, bot, "mouth", 0.002)
    parts.append(hp)


def build_hair(parts):
    hp = H.Part(["head"])
    nu = 24

    def tmax(psi, j):
        f = -math.sin(psi)  # 1 at the front
        t = 52 + 78 * ((1 - f) / 2) ** 0.55
        if f > 0.97:
            t -= 9  # centre-part notch
        elif f < 0.3:
            t += 4 * (j % 2)
        return math.radians(t)

    def cap_pt(th, psi, sc):
        return head_pt(V((math.sin(th) * math.cos(psi), math.sin(th) * math.sin(psi), math.cos(th))), sc)
    rows = []
    for s, sc in [(1.0, 0.99), (1.0, 1.07), (0.85, 1.075), (0.68, 1.08), (0.5, 1.08), (0.32, 1.075), (0.16, 1.07)]:
        rows.append([cap_pt(s * tmax(2 * math.pi * j / nu, j), 2 * math.pi * j / nu, sc) for j in range(nu)])
    H.loft(hp, rows, "auburn", True, None, HC + V((0, 0, HR[2] * 1.07)))
    sheen = V((0, -0.3, 0.95)).normalized()
    hp.recolor(0, lambda c, n: "auburn_lt" if 0.55 < n.dot(sheen) < 0.8 and c.z > HC.z + 0.06 else None)
    # straight side locks framing the face (vertical lines)
    for s in (1, -1):
        pts = [V((0.078 * s, -0.084, 1.60)), V((0.102 * s, -0.075, 1.53)), V((0.107 * s, -0.066, 1.46))]
        H.tube(hp, pts, [(0.011, 0.024), (0.011, 0.022), (0.009, 0.018)], 6, "auburn", hint=V((s, 0, 0)),
               cap0="center", cap1=V((0.106 * s, -0.062, 1.425)))
    # nape gather
    H.ellipsoid(hp, (0, 0.1, 1.44), (0.047, 0.036, 0.042), 8, 5, "auburn")
    parts.append(hp)

    # single long braid: alternating chevron lobes, own 2-bone chain
    bp = H.Part([("head", lambda v: 2.0 * ss(1.39, 1.44, v.z)), "braid.1", "braid.2"])
    n = 10
    for k in range(n):
        t = k / (n - 1)
        z = H.lerp(1.425, 1.03, t)
        y = 0.114 + 0.014 * ss(1.43, 1.30, z) - 0.004 * t
        tap = 1.0 - 0.28 * t
        sg = 1 if k % 2 == 0 else -1
        ang = math.radians(28) * sg
        B = H.axes((math.cos(ang), 0, math.sin(ang)), (0, 1, 0), (-math.sin(ang), 0, math.cos(ang)))
        H.ellipsoid(bp, (0.008 * sg * tap, y, z), (0.024 * tap, 0.02 * tap, 0.034 * tap), 7, 4,
                    "auburn_dk" if k % 2 else "auburn", B)
    tie = [V((0, 0.103, 1.005)) + V((math.cos(a) * 0.016, math.sin(a) * 0.014, 0))
           for a in [2 * math.pi * j / 10 for j in range(10)]]
    H.tube(bp, tie, [0.006] * 10, 5, "teal", hint=V((0, 0, 1)), closed_path=True)
    H.tube(bp, [(0, 0.103, 1.0), (0, 0.104, 0.975), (0, 0.106, 0.95)], [0.013, 0.02, 0.016], 8, "auburn",
           hint=V((1, 0, 0)), cap0="center", cap1=V((0, 0.107, 0.935)))
    parts.append(bp)


def build_goggles(parts):
    gp = H.Part(["head"])
    # leather strap: ring tilted back (forehead -> below the crown at the back)
    beta, th0 = math.radians(25), math.radians(55)
    n_ax = V((0, math.sin(beta), math.cos(beta)))
    e1 = V((1, 0, 0))
    e2 = n_ax.cross(e1)
    ring = []
    for j in range(28):
        ph = 2 * math.pi * j / 28
        d = (n_ax * math.cos(th0) + (e1 * math.cos(ph) + e2 * math.sin(ph)) * math.sin(th0)).normalized()
        ring.append(head_pt(d, 1.085))
    H.tube(gp, ring, [(0.012, 0.0045)] * 28, 6, "leather_dk", hint=n_ax, closed_path=True)
    inner = []
    for s in (1, -1):
        u = V((0.40 * s, -0.62, 0.68)).normalized()
        base = head_pt(u, 1.085)
        ax = ((base - HC).normalized() + V((0, -0.35, 0.1))).normalized()
        out = base + ax * 0.026
        H.tube(gp, [base - ax * 0.004, base + ax * 0.012, out], [0.026, 0.028, 0.027], 12,
               lambda i, j: "glass" if i >= 3 else ("brass_dk" if i == 0 else "brass"), hint=V((1, 0, 0)),
               cap0="center", cap1=out - ax * 0.004)
        bz = [out + v for v in H.ring(V(), ax, 0.028, 0.028, 12, hint=V((1, 0, 0)))]
        H.tube(gp, bz, [0.0055] * 12, 5, "brass", hint=ax, closed_path=True)
        # lens glint
        side = ax.cross(V((0, 0, 1))).normalized()
        H.ellipsoid(gp, out - ax * 0.002 + side * 0.009 * s + V((0, 0, 0.01)), (0.006, 0.006, 0.0015), 6, 4,
                    "hi", H.axes(side, ax.cross(side), ax))
        inner.append(base + ax * 0.012 - V((0.024 * s, 0, 0)))
    H.tube(gp, [inner[0], (inner[0] + inner[1]) / 2 + V((0, -0.006, 0.006)), inner[1]], [0.006] * 3, 6, "brass",
           hint=V((0, 0, 1)), cap0="center", cap1="center")
    parts.append(gp)


def build_pencil(parts):
    pp = H.Part(["head"], smooth=False)
    a, b = V((-0.13, -0.035, 1.526)), V((-0.131, 0.07, 1.54))
    d = (b - a).normalized()
    H.tube(pp, [a, b], [0.0058, 0.0058], 6, "pencil", hint=V((0, 0, 1)))
    H.tube(pp, [b, b + d * 0.008], [0.006, 0.006], 6, "brass", hint=V((0, 0, 1)))
    H.tube(pp, [b + d * 0.008, b + d * 0.016], [0.0056, 0.0056], 6, "eraser", hint=V((0, 0, 1)), cap1="center")
    H.tube(pp, [a, a - d * 0.014], [0.0058, 0.0022], 6, "wood", hint=V((0, 0, 1)), cap1=a - d * 0.021)
    parts.append(pp)


# ----------------------------------------------------------------------------- body
TORSO = [(0.82, 0.05, 0.04, 0.0), (0.845, 0.10, 0.068, 0.005), (0.88, 0.126, 0.078, 0.006),  # seat sits inside the trouser tubes
         (0.94, 0.132, 0.083, 0.006), (1.00, 0.122, 0.078, 0.004), (1.07, 0.126, 0.082, 0.0),
         (1.14, 0.136, 0.088, -0.004), (1.21, 0.142, 0.085, 0.0), (1.255, 0.13, 0.072, 0.004),
         (1.285, 0.09, 0.058, 0.006), (1.31, 0.045, 0.04, 0.008)]


def torso_prof(z):
    for a, b in zip(TORSO, TORSO[1:]):
        if a[0] <= z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            return tuple(H.lerp(a[k], b[k], t) for k in (1, 2, 3))
    return TORSO[-1][1:]


def sring(z, rx, ry, yo, n=20, e=0.75):
    """Boxy (superellipse) horizontal ring: straight-sided, 'vertical rectangle' torso."""
    out = []
    for j in range(n):
        a = 2 * math.pi * j / n
        c, s = math.cos(a), math.sin(a)
        out.append(V((rx * math.copysign(abs(c) ** e, c), yo + ry * math.copysign(abs(s) ** e, s), z)))
    return out


def vw(z):
    return max(0.0, (z - 1.10) / 0.17) * 0.066


def torso_col(c, n):
    if c.z < 0.93:
        return "charcoal"
    return "teal" if c.y < 0.02 else "teal_dk"


def build_body(parts):
    nk = H.Part(["chest", "neck", ("head", lambda v: ss(1.38, 1.41, v.z))])
    H.tube(nk, [(0, 0.01, 1.26), (0, 0.008, 1.34), (0, 0.006, 1.42)], [0.04, 0.037, 0.04], 12, "skin")
    parts.append(nk)
    # stand-up blouse collar (closed thick ring)
    cl = H.Part(["chest", ("neck", lambda v: 0.7)])
    rr = [H.ring((0, 0.008, z), (0, 0, 1), r, r * 0.95, 12, hint=V((1, 0, 0))) for z, r in
          ((1.285, 0.054), (1.35, 0.05), (1.35, 0.044), (1.29, 0.046))]
    H.loft(cl, rr, lambda i, j: "white_dk" if i == 1 else "white", True, wrap_path=True)
    parts.append(cl)

    sh = lambda s: (lambda v: ss(1.2, 1.26, v.z) * ss(0.03 * s, 0.1 * s, v.x))
    th = lambda s: (lambda v: ss(0.9, 0.82, v.z) * ss(0.0, 0.05 * s, v.x))
    tp = H.Part(["hips", "spine", "chest", ("neck", lambda v: ss(1.27, 1.31, v.z)),
                 ("shoulder.L", sh(1)), ("shoulder.R", sh(-1)), ("thigh.L", th(1)), ("thigh.R", th(-1))])
    rows = [sring(z, rx, ry, yo) for z, rx, ry, yo in TORSO]
    H.loft(tp, rows, "teal", True, V((0, 0.0, 0.79)), V((0, 0.008, 1.315)))
    tp.recolor(0, torso_col)
    parts.append(tp)
    bvh = tp.bvh()
    O, R, U = H.FACE
    det = H.Part(["hips", "spine", "chest"])
    # waistcoat lapel edges + centre seam, pointed hem tabs, brass buttons
    vpoly = [(0, 1.10), (0.066, 1.27), (0.05, 1.284), (-0.05, 1.284), (-0.066, 1.27)]
    dense = [(H.lerp(a[0], b[0], t / 6), H.lerp(a[1], b[1], t / 6))  # dense outline so it hugs the curved chest
             for a, b in zip(vpoly, vpoly[1:] + vpoly[:1]) for t in range(6)]
    H.decal(det, bvh, O, R, U, ccw(dense), "white", 0.004, rings=3)
    for s in (1, -1):
        zs = [1.10 + 0.17 * k / 6 for k in range(7)]
        top = [(s * vw(z) + 0.004 * s, z) for z in zs]
        bot = [(s * vw(z) - 0.004 * s, z) for z in zs]
        H.decal_strip(det, bvh, O, R, U, top if s > 0 else bot, bot if s > 0 else top, "teal_dk", 0.006)
        H.decal(det, bvh, O, R, U, ccw([(0.004 * s, 0.97), (0.11 * s, 0.97), (0.035 * s, 0.9)]), "teal", 0.022)
    H.decal_strip(det, bvh, O, R, U, [(-0.003, 1.1), (-0.003, 0.97)], [(0.003, 1.1), (0.003, 0.97)], "teal_dk", 0.005)
    for z in (1.08, 1.035, 0.99):
        rx, ry, yo = torso_prof(z)
        H.ellipsoid(det, (0.012, yo - ry * 0.98 - 0.006, z), (0.0085, 0.006, 0.0085), 6, 4, "brass")
    # belt
    brows = []
    for z, dr in ((0.925, 0.003), (0.93, 0.009), (0.962, 0.009), (0.967, 0.003)):
        rx, ry, yo = torso_prof(z)
        brows.append(sring(z, rx + dr, ry + dr, yo, 20))
    H.loft(det, brows, "leather")
    rx, ry, yo = torso_prof(0.946)
    H.ellipsoid(det, (-0.045, yo - ry - 0.014, 0.946), (0.016, 0.006, 0.015), 8, 4, "brass", exp=0.35)
    parts.append(det)
    build_strap(parts, bvh)

    for s in (1, -1):
        S = "L" if s > 0 else "R"
        X = lambda p: V((p[0] * s, p[1], p[2]))
        lp = H.Part(["hips", f"thigh.{S}", (f"shin.{S}", lambda v: 0.6 * ss(0.56, 0.48, v.z))])
        pts = [X(p) for p in ((0.068, 0.004, 0.935), (0.072, 0.002, 0.86), (0.076, -0.002, 0.72), (0.079, -0.004, 0.60),
                              (0.081, -0.005, 0.56), (0.082, -0.005, 0.53), (0.082, -0.005, 0.52))]
        H.tube(lp, pts, [(0.07, 0.08), (0.079, 0.088), 0.066, 0.062, 0.064, 0.058, 0.04], 12,
               lambda i, j: "charcoal_dk" if i >= 4 else "charcoal", hint=V((s, 0, 0)))
        parts.append(lp)
        bt = H.Part([(f"thigh.{S}", lambda v: ss(0.5, 0.56, v.z)), f"shin.{S}",
                     (f"foot.{S}", lambda v: ss(0.13, 0.06, v.z))])
        kn, an = V(J["knee"]), V(J["ankle"])
        rings = []
        for z, r in ((0.07, 0.052), (0.14, 0.051), (0.25, 0.056), (0.36, 0.059), (0.46, 0.06), (0.50, 0.061),
                     (0.505, 0.068), (0.545, 0.07), (0.55, 0.05)):
            c = H.lerp(an, kn, (z - an.z) / (kn.z - an.z))
            rings.append(H.ring((c.x * s, c.y, z), (0, 0, 1), r, r * 0.95, 12, hint=V((1, 0, 0))))
        H.loft(bt, rings, lambda i, j: "boot_lt" if i >= 5 else "boot")
        f0, v0 = len(bt.f), len(bt.v)
        H.ellipsoid(bt, (0.088 * s, -0.04, 0.047), (0.056, 0.115, 0.05), 12, 8, "boot")
        for k in range(v0, len(bt.v)):
            p = bt.v[k]
            if p.y < -0.07:
                p.z += 1.2 * (-0.07 - p.y) ** 2
            p.z = max(p.z, 0.0)
        bt.recolor(f0, lambda c, n: "boot_dk" if c.z < 0.014 else None)
        H.ellipsoid(bt, (0.088 * s, 0.03, 0.024), (0.044, 0.042, 0.025), 8, 5, "boot_dk", exp=0.5)
        parts.append(bt)


TUBE_A, TUBE_B = V((0.085, 0.138, 0.98)), V((0.16, 0.138, 1.47))


def build_strap(parts, bvh):
    def surf(x, z, back=False, off=0.007):
        d = V((0, -1, 0)) if back else V((0, 1, 0))
        hit, nrm, _, _ = bvh.ray_cast(V((x, 0, z)) - d * 0.6, d, 2.0)
        if nrm.dot(d) > 0:
            nrm = -nrm
        return hit + nrm * off
    sp = H.Part(["chest", "spine", ("hips", lambda v: ss(1.0, 0.94, v.z))])
    front = [surf(x, z) for x, z in ((0.09, 1.25), (0.06, 1.19), (0.0, 1.10), (-0.06, 1.02), (-0.112, 0.955))]
    H.tube(sp, front, [(0.0035, 0.013)] * 5, 6, "leather_dk", hint=V((0, -1, 0)), cap0="center", cap1="center")
    top = [front[0], V((0.093, -0.025, 1.293)), V((0.096, 0.03, 1.292)), surf(0.11, 1.24, True)]
    H.tube(sp, top, [(0.013, 0.0035)] * 4, 6, "leather_dk", hint=V((1, 0, 0)), cap0="center", cap1="center")
    H.ellipsoid(sp, front[1] + V((0, -0.006, 0)), (0.014, 0.004, 0.012), 6, 4, "brass", exp=0.4)
    back = [surf(0.1, 1.06, True), surf(0.0, 1.0, True), surf(-0.1, 0.96, True), surf(-0.128, 0.95, True)]
    H.tube(sp, back, [(0.0035, 0.012)] * 4, 6, "leather_dk", hint=V((0, 1, 0)), cap0="center", cap1="center")
    parts.append(sp)
    # map tube (rigid on the chest), brass-capped, with a lid knob and strap loops
    tp = H.Part(["chest"])
    a, b = TUBE_A, TUBE_B
    ax = (b - a).normalized()
    L = (b - a).length
    us = [0.0, 0.02, 0.045, 0.06, 0.2, 0.22, 0.24, 0.62, 0.64, 0.66, 0.9, 0.915, 0.95, 0.97, 1.0]
    rs = [0.034, 0.042, 0.042, 0.038, 0.038, 0.042, 0.038, 0.038, 0.042, 0.038, 0.038, 0.043, 0.043, 0.041, 0.034]
    cols = ["brass_dk", "brass", "brass", "tube", "leather", "leather", "tube", "tube_dk", "leather", "leather",
            "tube", "brass", "brass", "brass", "brass"]
    H.tube(tp, [a + ax * (L * u) for u in us], rs, 10, lambda i, j: cols[min(max(i, 0), len(cols) - 1)],
           hint=V((0, -1, 0)), cap0="center", cap1="center")
    H.ellipsoid(tp, b + ax * 0.012, (0.012, 0.012, 0.012), 8, 5, "brass")
    parts.append(tp)


# ----------------------------------------------------------------------------- arms & hands
def build_arms(parts):
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        d = V((D_ARM.x * s, 0, D_ARM.z))
        sj = V((J["arm"][0] * s, J["arm"][1], J["arm"][2]))
        at = lambda u: sj + d * u
        hint = V((0, -1, 0))
        sp = H.Part([f"shoulder.{S}", f"upper_arm.{S}", f"forearm.{S}", (f"hand.{S}", lambda v: 0.15)])
        us = [-0.01, 0.03, 0.09, 0.17, 0.25, 0.30, 0.38, 0.44, 0.46, 0.48, 0.49]
        rs = [0.045, 0.052, 0.05, 0.045, 0.042, 0.043, 0.045, 0.044, 0.036, 0.035, 0.026]
        H.tube(sp, [at(u) for u in us], rs, 12, lambda i, j: "white_dk" if i >= 7 else "white", hint=hint)
        parts.append(sp)
        wp = H.Part([f"forearm.{S}", f"hand.{S}"])
        H.tube(wp, [at(u) for u in (0.45, 0.49, 0.53)], [0.026, 0.025, 0.024], 10, "skin", hint=hint)
        parts.append(wp)
        a, g, p = hand_axes(s)
        if s < 0:
            hp = H.Part([f"hand.{S}", (f"forearm.{S}", lambda v: 0.2)])
            H.fist(hp, at(U_WRIST), a, g, p, "skin", size=HAND)
            parts.append(hp)
        else:
            build_left_hand(parts, at(U_WRIST), a, g, p)
            build_gauntlet(parts, at, d, -p)


def build_left_hand(parts, wrist, a, g, p):
    """Fist with a separate index finger on its own bone (curled in idle/talk, extended to point)."""
    hp = H.Part(["hand.L", ("forearm.L", lambda v: 0.2)])
    sz = HAND
    B = H.axes(g, p, a)
    c = wrist + a * 0.044 * sz
    H.ellipsoid(hp, c, (0.045 * sz, 0.037 * sz, 0.047 * sz), 12, 8, "skin", B, exp=0.8)
    for k in range(3):
        kc = c + g * ((k - 1.5) * 0.022 * sz) + a * (0.03 * sz) - p * (0.02 * sz)
        H.ellipsoid(hp, kc, (0.012 * sz, 0.014 * sz, 0.016 * sz), 6, 4, "skin", B)
    tc = c + p * (0.026 * sz) + g * (0.03 * sz) - a * (0.004 * sz)
    H.ellipsoid(hp, tc, (0.026 * sz, 0.014 * sz, 0.016 * sz), 8, 5, "skin", B)
    parts.append(hp)
    ip = H.Part(["index.L", ("hand.L", lambda v: 0.25)])
    tip = K3 + a * 0.072 * sz
    H.tube(ip, [K3, K3 + a * 0.03 * sz, tip], [0.0115, 0.011, 0.0095], 6, "skin", hint=p,
           cap0="center", cap1=tip + a * 0.007)
    parts.append(ip)


def build_gauntlet(parts, at, d, out):
    gp = H.Part(["forearm.L", ("hand.L", lambda v: 0.25)])
    us = [0.33, 0.335, 0.35, 0.47, 0.485, 0.49]
    rs = [0.044, 0.05, 0.049, 0.046, 0.047, 0.038]
    H.tube(gp, [at(u) for u in us], rs, 14, lambda i, j: "leather_dk" if i in (0, 4) else "leather",
           hint=V((0, -1, 0)))
    for u in (0.37, 0.455):  # buckle straps
        H.tube(gp, [at(u - 0.006), at(u + 0.006)], [0.0515, 0.0515], 14, "leather_dk", hint=V((0, -1, 0)))
    parts.append(gp)
    # brass compass on the outside of the LEFT wrist
    cp = H.Part(["forearm.L"])
    c0 = at(0.415) + out * 0.044
    r = V((0, -1, 0))
    up = out.cross(r)
    H.tube(cp, [c0, c0 + out * 0.012, c0 + out * 0.016], [0.033, 0.033, 0.028], 12,
           lambda i, j: "face" if i >= 2 else "brass", hint=r, cap0="center", cap1="center")
    bz = [c0 + out * 0.016 + v for v in H.ring(V(), out, 0.031, 0.031, 12, hint=r)]
    H.tube(cp, bz, [0.0045] * 12, 5, "brass", hint=out, closed_path=True)
    H.ellipsoid(cp, c0 + out * 0.004 + up * 0.037, (0.008, 0.008, 0.008), 6, 4, "brass")  # crown/hinge
    bvh = cp.bvh()
    face_o = c0 + out * 0.3
    H.decal(cp, bvh, face_o, r, up, [(0.0035, 0.0), (0.0, 0.022), (-0.0035, 0.0)], "needle", 0.0015, 1)
    H.decal(cp, bvh, face_o, r, up, [(-0.0035, 0.0), (0.0, -0.02), (0.0035, 0.0)], "steel", 0.0015, 1)
    H.decal(cp, bvh, face_o, r, up, ccw(H.ellipse_pts(0, 0, 0.004, 0.004, 6)), "brass_dk", 0.002, 1)
    parts.append(cp)


def build_parts():
    parts = []
    build_head(parts)
    build_hair(parts)
    build_goggles(parts)
    build_pencil(parts)
    for p in parts:  # sit the whole head 2 cm lower (shorter neck) without re-deriving every face coordinate
        for v in p.v:
            v.z += HEAD_DZ
    build_body(parts)
    build_arms(parts)
    return parts


# ----------------------------------------------------------------------------- animation
REST_ARM = [V(J["elbow"]) - V(J["arm"]), V(J["wrist"]) - V(J["elbow"]), V(J["hand_end"]) - V(J["wrist"])]


def eul(q):
    return tuple(math.degrees(x) for x in q.to_euler("XYZ"))


def q_of(e):
    return Euler([math.radians(x) for x in e], "XYZ").to_quaternion()


def chest_q(p, mirror=False):
    q = q_of(p.get("hips", (0, 0, 0))) @ q_of(p.get("spine", (0, 0, 0))) @ q_of(p.get("chest", (0, 0, 0)))
    return Quaternion((q.w, q.x, -q.y, -q.z)) if mirror else q


def arm(p, side, dirs, twist=(0, 0, 0), world=False):
    """FK from target directions (left-side space; the .R arm is mirrored by key_clip).
    world=False: dirs are in the chest's rest frame (arm moves with the torso); True: true world dirs."""
    Q = chest_q(p, side == "R") if world else Quaternion()
    for bone, rest, want, tw in zip(("upper_arm", "forearm", "hand"), REST_ARM, dirs, twist):
        w = Q.inverted() @ V(want).normalized()
        q = rest.normalized().rotation_difference(w)
        if tw:
            q = Quaternion(w, math.radians(tw)) @ q
        Q = Q @ q
        p[f"{bone}.{side}"] = eul(q)
    return p


def chain(pts):
    return [V(b) - V(a) for a, b in zip(pts, pts[1:])]


A0 = V(J["arm"])
CROSS_L = chain([A0, (0.165, -0.10, 1.01), (-0.03, -0.19, 1.095), (-0.11, -0.15, 1.10)])
CROSS_R = chain([A0, (0.16, -0.085, 0.995), (-0.035, -0.155, 0.98), (-0.12, -0.12, 0.995)])
HIP_HAND = chain([A0, (0.29, 0.03, 1.07), (0.19, -0.01, 0.975), (0.165, 0.03, 0.915)])
a_, g_, p_ = hand_axes(1)
CURL = eul(Quaternion(a_.cross(p_), math.radians(110)))


def braid(p, b1, b2):
    p["braid.1"], p["braid.2"] = b1, b2
    return p


def stance(**kw):
    """Weight on the right leg: left hip dropped, left knee relaxed forward."""
    base = dict(hips_loc=(-0.018, 0, -0.008), hips=(0, 5, 0), spine=(0, -4, 0), chest=(-3, -3, 0),
                neck=(0, 0, 0), head=(-4, 3, 6), thigh=((-10, 3, -6), (0, -5, 0)), shin=((18, 0, 0), (0, 0, 0)),
                foot=((-8, -2, 0), (0, 5, 0)), index_L=CURL)
    base.update(kw)
    p = H.pose(**{k: v for k, v in base.items() if k != "index_L"})
    p["index.L"] = base["index_L"]
    return p


def build_actions(armo):
    acts = {}
    K = lambda name, keys, loop=False: acts.__setitem__(name, H.key_clip(armo, name, keys, loop))

    # idle 2.4 s: arms crossed, weight on the right leg, slow breath, braid settles
    def idle_pose(breath):
        p = stance(chest=(-3 - 2 * breath, -3, 0), head=(-4 + 1.5 * breath, 3, 6 - 2 * breath),
                   hips_loc=(-0.018, 0, -0.008 + 0.004 * breath), shoulder=(0, -2 * breath, 0))
        arm(p, "L", CROSS_L)
        arm(p, "R", CROSS_R)
        return braid(p, (3 + 2 * breath, 0, 0), (2 - 2 * breath, 0, 0))
    i0, i1 = idle_pose(0), idle_pose(1)
    K("idle", [(0, i0), (36, i1), (72, i0)], True)

    # talk 2.0 s: left fist on hip (compass out), right hand making two points, head nods
    def talk_pose(dirs, head, chest, b):
        p = stance(head=head, chest=chest, hips=(0, 4, 0))
        arm(p, "L", HIP_HAND, twist=(0, 0, 0))
        arm(p, "R", dirs)
        return braid(p, b, (b[0] * 0.6, 0, 0))
    g1 = chain([A0, (0.2, -0.07, 1.03), (0.17, -0.29, 1.08), (0.15, -0.37, 1.11)])
    g2 = chain([A0, (0.22, -0.08, 1.06), (0.21, -0.27, 1.20), (0.20, -0.33, 1.26)])
    g3 = chain([A0, (0.25, -0.03, 1.04), (0.36, -0.2, 1.10), (0.42, -0.26, 1.12)])
    t0 = talk_pose(g1, (-2, 2, 4), (-3, -3, 0), (3, 0, 0))
    t1 = talk_pose(g2, (-8, 0, 8), (-5, -2, -4), (8, 0, 0))
    t2 = talk_pose(g1, (2, 3, 2), (-2, -3, 2), (0, 0, 0))
    t3 = talk_pose(g3, (-5, -2, -6), (-4, -4, 6), (6, 0, 0))
    K("talk", [(0, t0), (10, t1), (22, t2), (36, t3), (60, t0)], True)

    # point 0.67 s: uncross, left compass arm snaps out to the horizon (-Y), hold
    def point_pose(lift, chest_z, b, curl):
        p = stance(hips_loc=(-0.01, -0.012, -0.005), hips=(0, 3, -4), spine=(2, -2, -4), chest=(-4, -2, chest_z),
                   head=(-7, 1, 10), thigh=((-16, 2, -4), (2, -4, 0)), shin=((14, 0, 0), (2, 0, 0)),
                   foot=((2, -2, 0), (-4, 4, 0)), index_L=curl)
        d = V((0.06, -1.0, lift))
        arm(p, "L", [d, d, d], twist=(0, 0, 0), world=True)
        arm(p, "R", HIP_HAND)
        return braid(p, b, (b[0] * 0.8, 0, 0))
    pt_hit = point_pose(0.24, -12, (14, 0, 0), (0, 0, 0))
    pt_hold = point_pose(0.17, -10, (5, 0, 0), (0, 0, 0))
    wind = stance(chest=(-2, -3, 6), head=(-4, 2, 2))
    arm(wind, "L", chain([A0, (0.2, -0.05, 1.02), (0.22, -0.2, 1.15), (0.22, -0.26, 1.2)]))
    arm(wind, "R", chain([A0, (0.22, 0.0, 1.03), (0.2, -0.04, 0.95), (0.18, 0.0, 0.89)]))
    braid(wind, (2, 0, 0), (4, 0, 0))
    K("point", [(0, i0), (6, wind), (12, pt_hit), (20, pt_hold)])
    return acts


def main():
    H.run_character("sol", PAL, BONES, build_parts, build_actions, height=1.7, args=ARGS, poses_cols=3,
                    shots=[("idle", 0), ("idle", 36), ("talk", 10), ("talk", 36), ("point", 6), ("point", 20)])


if __name__ == "__main__":
    main()
