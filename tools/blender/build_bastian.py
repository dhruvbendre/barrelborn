"""Build Bastian Gull (harbor shipwright NPC) procedurally: mesh + rig + idle/talk + GLB + previews.

Run (from anywhere):
  blender -b --factory-startup --python tools/blender/build_bastian.py [-- --no-render]
"""
import math
import os
import sys

import bpy  # noqa: F401  (run inside Blender)
from mathutils import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import humanoid as H  # noqa: E402
from humanoid import smoothstep as ss, lerp  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

PAL = H.Palette({
    "skin": "#c98a6a", "skin_dk": "#a86a4e", "nose": "#c76f5a", "blush": "#d47a68", "mouth": "#5a2420",
    "hair_w": "#f0efe8", "hair_g": "#cfcdc4", "eye_white": "#fbf7ee", "iris": "#5b8fc0", "iris_dk": "#2c4f78",
    "pupil": "#1a0f0a", "lash": "#3a2a22", "white": "#ffffff",
    "stripe": "#3c6fb0", "stripe_dk": "#2c5490", "shirt": "#f0f0ea", "shirt_dk": "#d6d6cc",
    "apron": "#7a4a2a", "apron_dk": "#58331c", "apron_lt": "#93603a", "strap": "#4a2a16",
    "trousers": "#4b4440", "trousers_dk": "#363130", "boot": "#3e2a1c", "boot_dk": "#2a1c12",
    "wood": "#a8784a", "wood_dk": "#7a5230", "wood_lt": "#c9995e", "wood_end": "#d8b27a",
    "iron": "#55575e", "iron_dk": "#3a3a42", "pencil": "#e2b23a", "graphite": "#2a2a2a",
})

# ----------------------------------------------------------------------------- layout
D_ARM = V((0.55, 0.0, -0.835)).normalized()          # left arm direction in the A-pose
J = dict(hips=(0, 0, 0.55), spine=(0, 0, 0.70), chest=(0, 0, 0.88), neck=(0, 0.01, 1.04),
         head=(0, 0.01, 1.09), head_top=(0, 0.01, 1.37), shoulder=(0.05, 0, 1.0),
         arm=(0.28, 0, 0.99), hip=(0.12, 0, 0.52), knee=(0.13, -0.01, 0.29),
         ankle=(0.13, 0.01, 0.075), toe=(0.14, -0.13, 0.02))
J["elbow"] = V(J["arm"]) + D_ARM * 0.21
J["wrist"] = J["elbow"] + D_ARM * 0.19
J["hand_end"] = J["wrist"] + D_ARM * 0.12
BONES = H.standard_skeleton(J)
FIST = 1.35

HC, HR = V((0, 0.0, 1.215)), (0.128, 0.13, 0.15)
head_pt = H.head_shape(HC, HR, jaw=0.2, jaw_front=0.05, jaw_z=0.9)


def side_fn(s, fn):
    return fn if s > 0 else (lambda v: fn(V((-v.x, v.y, v.z))))


def surf(bvh, x, z, off):
    """Point on the face surface seen from the front, lifted `off` toward the viewer."""
    hit, *_ = bvh.ray_cast(V((x, -0.6, z)), V((0, 1, 0)), 2.0)
    return (hit if hit else V((x, -0.1, z))) + V((0, -off, 0))


# ----------------------------------------------------------------------------- head & face
def build_head(parts):
    hp = H.Part(["head", ("neck", lambda v: ss(1.13, 1.08, v.z))])
    H.sphere(hp, head_pt, 24, 16, "skin")
    nf = len(hp.f)
    for s in (1, -1):  # ears
        H.ellipsoid(hp, (0.126 * s, 0.015, 1.205), (0.022, 0.032, 0.042), 8, 6, "skin")
    bvh = hp.bvh(0, nf)
    O, R, U = H.FACE
    for s in (1, -1):
        H.anime_eye(hp, bvh, 0.047, 1.226, s, k=0.78, iris="iris", iris_dk="iris_dk", brow_spec=None,
                    lid=0.32, lid_tilt=-0.25)
        H.decal(hp, bvh, O, R, U, H.ellipse_pts(0.078 * s, 1.18, 0.022, 0.013, 10), "blush", 0.0012)
        # crow's feet
        for dz in (-0.006, 0.006):
            H.decal_strip(hp, bvh, O, R, U, [(0.086 * s, 1.228 + dz), (0.104 * s, 1.226 + dz * 2)][::s],
                          [(0.086 * s, 1.2245 + dz), (0.104 * s, 1.2225 + dz * 2)][::s], "skin_dk", 0.0012)
    # forehead wrinkles
    for z in (1.298, 1.314):
        xs = [-0.05 + 0.1 * k / 6 for k in range(7)]
        H.decal_strip(hp, bvh, O, R, U, [(x, z + 0.004 * math.cos(x * 30)) for x in xs],
                      [(x, z - 0.0035 + 0.004 * math.cos(x * 30)) for x in xs], "skin_dk", 0.0012)
    # mouth peeking under the mustache
    H.decal(hp, bvh, O, R, U, H.ellipse_pts(0, 1.106, 0.02, 0.006, 10), "mouth", 0.0015)
    # bulbous nose
    H.ellipsoid(hp, surf(bvh, 0, 1.19, 0.012), (0.03, 0.028, 0.029), 10, 7, "nose")
    parts.append(hp)


def build_hair(parts):
    hp = H.Part(["head"])
    bvh = H.Part(["head"])
    H.sphere(bvh, head_pt, 24, 16, "skin")
    bvh = bvh.bvh()
    # bushy brows: one thick tapered tuft per side, drooping at the outer end, plus a stray hair flick
    for s in (1, -1):
        path = [(0.018, 1.258), (0.04, 1.266), (0.065, 1.266), (0.09, 1.254), (0.108, 1.234), (0.118, 1.215)]
        pts = [surf(bvh, x * s, z, 0.012) for x, z in path]
        pts[-1] += V((0.006 * s, -0.012, 0))
        rad = [(0.012, 0.014), (0.016, 0.02), (0.017, 0.022), (0.015, 0.019), (0.011, 0.013), (0.004, 0.004)]
        H.tube(hp, pts[:-1], rad[:-1], 8, lambda i, j: "hair_g" if j in (2, 5) else "hair_w",
               hint=V((0, -1, 0)), cap0="center", cap1=pts[-1])
        b = surf(bvh, 0.05 * s, 1.275, 0.012)
        H.tube(hp, [b, b + V((0.012 * s, -0.008, 0.012))], [(0.007, 0.009), (0.004, 0.005)], 6, "hair_w",
               hint=V((0, -1, 0)), cap1=b + V((0.02 * s, -0.012, 0.02)))
    # walrus mustache: central mass + two drooping lobes that hang past the jaw
    H.ellipsoid(hp, surf(bvh, 0, 1.152, 0.03), (0.062, 0.032, 0.034), 12, 7, "hair_w")
    for s in (1, -1):
        path = [(0.0, 1.162), (0.04, 1.158), (0.08, 1.138), (0.11, 1.105), (0.128, 1.065), (0.134, 1.035)]
        pts = [surf(bvh, x * s, z, 0.026 - 0.012 * k / 5) for k, (x, z) in enumerate(path)]
        pts[-1] += V((0.012 * s, -0.01, 0))
        pts[-2] += V((0.006 * s, -0.01, 0))
        rad = [(0.026, 0.04), (0.028, 0.045), (0.026, 0.042), (0.021, 0.034), (0.015, 0.024), (0.008, 0.012)]
        H.tube(hp, pts[:-1], rad[:-1], 10, lambda i, j: "hair_g" if j in (3, 7) else "hair_w",
               hint=V((0, -1, 0)), cap0="center", cap1=pts[-1])
    # white fringe from ear to ear around the back of the bald head
    ring = []
    for k in range(13):
        a = math.radians(-100 + 200 * k / 12)
        u = V((math.sin(a), math.cos(a), -0.05 + 0.12 * math.cos(a) ** 2)).normalized()
        ring.append(HC + (head_pt(u) - HC) * 1.02)
    rad = [(0.03, 0.018)] + [(0.042, 0.024)] * 11 + [(0.03, 0.018)]
    H.tube(hp, ring, rad, 8, lambda i, j: "hair_g" if j % 4 == 1 else "hair_w", hint=V((0, 0, 1)),
           cap0="center", cap1="center")
    parts.append(hp)


# ----------------------------------------------------------------------------- body
TORSO = [(0.42, 0.10, 0.08, 0.0), (0.45, 0.19, 0.15, 0.0), (0.50, 0.26, 0.20, -0.01), (0.58, 0.30, 0.235, -0.02),
         (0.68, 0.315, 0.25, -0.03), (0.78, 0.31, 0.24, -0.025), (0.88, 0.30, 0.22, -0.01), (0.95, 0.29, 0.195, 0.0),
         (1.00, 0.265, 0.165, 0.005), (1.04, 0.20, 0.13, 0.01), (1.07, 0.11, 0.09, 0.01)]


def torso_prof(z):
    z = min(max(z, TORSO[0][0]), TORSO[-1][0])
    for a, b in zip(TORSO, TORSO[1:]):
        if a[0] <= z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            return tuple(lerp(a[k], b[k], t) for k in (1, 2, 3))
    return TORSO[-1][1:]


def vring(z, rx, ry, yoff, n, cx=0.0):
    return H.ring((cx, yoff, z), (0, 0, 1), rx, ry, n, hint=V((1, 0, 0)))


def shirt_col(zm):
    if zm < 0.49:
        return "trousers"
    if zm < 0.515:
        return "strap"
    return "stripe" if int((zm - 0.515) / 0.05) % 2 == 0 else "shirt"


def build_body(parts):
    nk = H.Part(["chest", "neck", ("head", lambda v: ss(1.08, 1.12, v.z))])
    H.tube(nk, [(0, 0.01, 1.0), (0, 0.01, 1.06), (0, 0.01, 1.12)], [0.08, 0.077, 0.075], 12, "skin")
    parts.append(nk)
    sh = lambda s: (lambda v: ss(0.93, 0.99, v.z) * ss(0.05 * s, 0.16 * s, v.x))
    th = lambda s: (lambda v: ss(0.53, 0.44, v.z) * ss(0.0, 0.07 * s, v.x))
    tp = H.Part(["hips", "spine", "chest", ("neck", lambda v: ss(1.03, 1.07, v.z)),
                 ("shoulder.L", sh(1)), ("shoulder.R", sh(-1)), ("thigh.L", th(1)), ("thigh.R", th(-1))])
    zs = [0.42 + 0.025 * k for k in range(27)]
    rows = [vring(z, *torso_prof(z)[:2], torso_prof(z)[2], 18) for z in zs]
    H.loft(tp, rows, lambda i, j: shirt_col(zs[min(max(i, 0), len(zs) - 2)] + 0.0125), True,
           V((0, 0, 0.41)), V((0, 0.01, 1.085)))
    parts.append(tp)

    for s in (1, -1):
        S = "L" if s > 0 else "R"
        X = lambda p: V((p[0] * s, p[1], p[2]))
        # trouser thigh
        lp = H.Part(["hips", f"thigh.{S}", (f"shin.{S}", lambda v: 0.5 * ss(0.33, 0.27, v.z))])
        if s > 0:  # LEFT: rolled cuff above the peg
            pts = [(0.115, 0, 0.52), (0.12, -0.003, 0.42), (0.128, -0.008, 0.33), (0.13, -0.01, 0.30),
                   (0.13, -0.01, 0.285), (0.13, -0.01, 0.265), (0.13, -0.01, 0.264)]
            rs = [0.118, 0.11, 0.1, 0.098, 0.106, 0.104, 0.06]
            fc = lambda i, j: "trousers_dk" if i >= 3 else "trousers"
        else:  # RIGHT: tucked into the boot
            pts = [(0.115, 0, 0.52), (0.12, -0.003, 0.42), (0.128, -0.008, 0.33), (0.13, -0.005, 0.25),
                   (0.13, 0.0, 0.2)]
            rs = [0.118, 0.11, 0.1, 0.092, 0.085]
            fc = "trousers"
        H.tube(lp, [X(p) for p in pts], rs, 14, fc, hint=V((s, 0, 0)))
        parts.append(lp)
        if s > 0:
            # wooden peg leg: leather cup on the stump, turned shaft, iron band, tip
            pg = H.Part([f"shin.{S}", (f"thigh.{S}", lambda v: ss(0.24, 0.29, v.z))])
            H.tube(pg, [X(p) for p in ((0.13, -0.01, 0.275), (0.13, -0.008, 0.24), (0.13, -0.005, 0.205),
                                       (0.13, -0.004, 0.19))],
                   [0.088, 0.078, 0.06, 0.04], 12, lambda i, j: "strap" if i != 1 else "apron_dk",
                   hint=V((1, 0, 0)))
            prof = [(0.21, 0.04), (0.19, 0.05), (0.175, 0.054), (0.16, 0.047), (0.13, 0.041), (0.09, 0.036),
                    (0.085, 0.039), (0.065, 0.039), (0.06, 0.035), (0.03, 0.033), (0.006, 0.032)]
            cols = ["wood", "wood_lt", "wood", "wood", "wood", "iron", "iron", "iron", "wood_dk", "iron_dk"]
            H.tube(pg, [X((0.13, 0.0, z)) for z, _ in prof], [r for _, r in prof], 12,
                   lambda i, j: cols[min(max(i, 0), len(cols) - 1)], hint=V((1, 0, 0)),
                   cap1=X((0.13, 0.0, 0.0)))
            parts.append(pg)
        else:
            bt = H.Part([f"shin.{S}", (f"foot.{S}", lambda v: ss(0.13, 0.06, v.z))])
            rings = []
            for z, r in ((0.07, 0.072), (0.14, 0.074), (0.22, 0.08), (0.225, 0.09), (0.26, 0.094), (0.262, 0.07)):
                rings.append(vring(z, r, r * 0.95, 0.0, 14, -0.13))
            H.loft(bt, rings, lambda i, j: "boot_dk" if i >= 2 else "boot")
            f0, v0 = len(bt.f), len(bt.v)
            H.ellipsoid(bt, (-0.135, -0.04, 0.055), (0.078, 0.135, 0.066), 14, 10, "boot")
            for k in range(v0, len(bt.v)):
                p = bt.v[k]
                if p.y < -0.07:
                    p.z += 1.4 * (-0.07 - p.y) ** 2
                p.z = max(p.z, 0.0)
            bt.recolor(f0, lambda c, n: "boot_dk" if c.z < 0.016 else None)
            parts.append(bt)


# ----------------------------------------------------------------------------- apron
def apron_pt(z, phi, off=0.018):
    rx, ry, yo = torso_prof(max(z, 0.60))
    x, y = (rx + off) * math.sin(phi), yo - (ry + off) * math.cos(phi)
    if z < 0.60:  # below the belly the apron hangs, drifting slightly in
        t = 0.60 - z
        x *= 1 - 0.25 * t
        y += 0.12 * t
    return V((x, y, z))


def phimax(z):
    if z >= 0.93:
        return 0.42
    if z >= 0.76:
        return lerp(1.0, 0.42, (z - 0.76) / 0.17)
    return lerp(1.12, 1.0, (z - 0.30) / 0.46)


def build_apron(parts):
    thigh = lambda s: side_fn(s, lambda v: 0.7 * ss(0.5, 0.33, v.z) * ss(-0.03, 0.1, v.x))
    ap = H.Part(["hips", "spine", "chest", ("thigh.L", thigh(1)), ("thigh.R", thigh(-1))])
    zs = [1.00, 0.96, 0.92, 0.88, 0.84, 0.80, 0.76, 0.72, 0.68, 0.64, 0.60, 0.54, 0.48, 0.42, 0.36, 0.30]
    C = 13
    P = [[apron_pt(z, lerp(-phimax(z), phimax(z), c / (C - 1))) for c in range(C)] for z in zs]
    R = len(P)
    H.sheet(ap, P, 0.008, lambda r, c: "apron_dk" if (c in (0, C - 2) or r == R - 2) else "apron",
            "apron_dk", dict(top="apron_dk", bottom="apron_dk", left="apron_dk", right="apron_dk"))
    # pocket (on his right side) with a chisel and a pencil poking out
    pz = [0.60, 0.56, 0.52, 0.47]
    Pp = [[apron_pt(z, lerp(-0.62, 0.05, c / 5), 0.028) for c in range(6)] for z in pz]
    H.sheet(ap, Pp, 0.009, lambda r, c: "apron_dk" if r == 0 else "apron_lt", "apron_dk",
            dict(top="apron_dk", bottom="apron_dk", left="apron_dk", right="apron_dk"))
    base = apron_pt(0.57, -0.42, 0.04)
    top = base + V((-0.012, -0.012, 0.13))
    H.tube(ap, [base, lerp(base, top, 0.75), top], [0.017, 0.018, 0.015], 8,
           lambda i, j: "iron" if i == 1 else "wood_lt", hint=V((1, 0, 0)), cap1="center")
    base = apron_pt(0.57, -0.12, 0.04)
    top = base + V((0.02, -0.008, 0.10))
    H.tube(ap, [base, lerp(base, top, 0.85), top], [0.008, 0.008, 0.002], 6,
           lambda i, j: "graphite" if i >= 1 else "pencil", hint=V((1, 0, 0)))
    parts.append(ap)
    # neck strap + waist tie with a bow at the back
    st = H.Part(["chest", ("neck", lambda v: 0.5 * ss(1.05, 1.08, v.z))])
    a0 = apron_pt(1.0, -0.42, 0.014)
    a1 = apron_pt(1.0, 0.42, 0.014)
    path = [a1, V((0.118, -0.12, 1.05)), V((0.105, -0.04, 1.085)), V((0.08, 0.06, 1.085)), V((0, 0.1, 1.07)),
            V((-0.08, 0.06, 1.085)), V((-0.105, -0.04, 1.085)), V((-0.118, -0.12, 1.05)), a0]
    H.tube(st, path, [(0.006, 0.016)] * len(path), 6, "strap", hint=V((0, 0, 1)), cap0="center", cap1="center")
    parts.append(st)
    tie = H.Part(["hips", "spine"])
    z = 0.615
    rx, ry, yo = torso_prof(z)
    th = math.pi - phimax(z) + 0.12  # only around the back; the ends tuck under the apron edges
    arc = [lerp(-th, th, k / 18) for k in range(19)]
    arc = [V(((rx + 0.01) * math.sin(a), yo + (ry + 0.01) * math.cos(a), z)) for a in arc]
    H.tube(tie, arc, [(0.014, 0.004)] * len(arc), 6, "strap", hint=V((0, 0, 1)), cap0="center", cap1="center")
    bk = V((0, yo + ry + 0.03, z))
    for s in (1, -1):
        H.ellipsoid(tie, bk + V((0.03 * s, 0, 0.005)), (0.03, 0.01, 0.016), 8, 5, "strap")
        H.tube(tie, [bk + V((0.008 * s, 0.002, -0.01)), bk + V((0.03 * s, 0.006, -0.08)),
                     bk + V((0.035 * s, 0.004, -0.13))], [(0.004, 0.014)] * 3, 6, "strap",
               hint=V((0, 1, 0)), cap1="center")
    H.ellipsoid(tie, bk, (0.014, 0.012, 0.014), 6, 4, "apron_dk")
    parts.append(tie)


# ----------------------------------------------------------------------------- arms
def arm_frame(s):
    return V((D_ARM.x * s, 0, D_ARM.z)), V((J["arm"][0] * s, J["arm"][1], J["arm"][2]))


def hand_axes(s):
    d, sj = arm_frame(s)
    a, g = d, V((0, -1, 0))
    p = a.cross(g).normalized()
    if p.x * s > 0:
        p = -p
    return a, g, p, sj + d * 0.40


def build_arms(parts):
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        d, sj = arm_frame(s)
        at = lambda u: sj + d * u
        hint = V((0, -1, 0))
        sp = H.Part([f"shoulder.{S}", f"upper_arm.{S}", (f"forearm.{S}", lambda v: 0.4)])
        us = [-0.03, 0.0, 0.04, 0.08, 0.12, 0.155, 0.16, 0.172, 0.19, 0.205, 0.206]
        rs = [0.07, 0.09, 0.092, 0.088, 0.083, 0.08, 0.088, 0.094, 0.094, 0.088, 0.06]
        fc = lambda i, j: ("shirt" if i in (6, 7) else "stripe") if i >= 5 else ("stripe" if i % 2 else "shirt")
        H.tube(sp, [at(u) for u in us], rs, 14, fc, hint=hint)
        parts.append(sp)
        fp = H.Part([f"forearm.{S}", (f"hand.{S}", lambda v: 0.4), (f"upper_arm.{S}", lambda v: 0.4)])
        H.tube(fp, [at(u) for u in (0.18, 0.24, 0.3, 0.36, 0.41)], [0.066, 0.07, 0.062, 0.05, 0.046], 12,
               "skin", hint=hint)
        parts.append(fp)
        hp = H.Part([f"hand.{S}", (f"forearm.{S}", lambda v: 0.2)])
        a, g, p, w = hand_axes(s)
        H.fist(hp, w, a, g, p, "skin", size=FIST)
        parts.append(hp)


def build_mallet():
    a, g, p, w = hand_axes(-1)
    c = w + a * 0.044 * FIST
    mp = H.Part(["hand.R"])
    H.ellipsoid(mp, c - g * 0.1, (0.026, 0.026, 0.022), 8, 5, "wood_dk", H.axes(a, p, g))
    H.tube(mp, [c - g * 0.095, c - g * 0.06, c + g * 0.06, c + g * 0.1, c + g * 0.42],
           [0.021, 0.022, 0.022, 0.02, 0.019], 8,
           lambda i, j: "strap" if i == 1 else "wood_lt", hint=a)
    hc = c + g * 0.49
    zs = [-0.15, -0.148, -0.13, -0.115, -0.1, -0.05, 0.0, 0.05, 0.1, 0.115, 0.13, 0.148, 0.15]
    rs = [0.07, 0.077, 0.08, 0.084, 0.084, 0.089, 0.091, 0.089, 0.084, 0.084, 0.08, 0.077, 0.07]
    cols = ["wood_dk", "wood", "iron", "iron", "wood", "wood_dk", "wood", "wood", "iron", "iron", "wood", "wood_dk"]
    H.tube(mp, [hc + a * z for z in zs], rs, 12,
           lambda i, j: "wood_end" if i < 0 or i >= len(cols) else cols[i], hint=g,
           cap0="center", cap1="center")
    return mp


def build_parts():
    parts = []
    build_head(parts)
    build_hair(parts)
    build_body(parts)
    build_apron(parts)
    build_arms(parts)
    return parts


# ----------------------------------------------------------------------------- animation
P, OV, MX = H.pose, H.over, H.mix

BASE = P(hips_loc=(0, 0, -0.01), spine=(3, 0, 0), chest=(-6, 0, 0), neck=(2, 0, 0), head=(-4, 0, 0),
         thigh=(-4, -3, 0), shin=(6, 0, 0), foot=(-2, 3, 0),
         shoulder=((0, 0, 0), (0, -4, 0)),
         upper_arm=((18, -28, 0), (-35, 10, 0)), forearm=((0, 86, 0), (-135, 0, 0)),
         hand=((0, 0, 0), (-5, 0, 0)))


def build_actions(arm):
    acts = {}
    K = lambda name, keys, loop=False: acts.__setitem__(name, H.key_clip(arm, name, keys, loop))

    # idle 2.0 s: proud chest, mallet on shoulder, slow breath + weight rolls onto the good leg and back
    inhale = OV(BASE, hips_loc=(0, 0, -0.004), chest=(-9, 0, 0), head=(-6, 0, 0), shoulder=((0, -3, 0), (0, -7, 0)),
                upper_arm=((16, -30, 0), (-37, 9, 0)))
    shift = OV(BASE, hips_loc=(-0.018, 0, -0.012), hips=(0, -3, 0), spine=(3, 2, 0), chest=(-7, 2, 0), head=(-4, -2, 2),
               thigh=((-4, -5, 0), (-4, -1, 0)))
    K("idle", [(0, BASE), (20, inhale), (40, shift), (60, BASE)], True)

    # talk 2.4 s: mallet comes off the shoulder to point, taps the air, head nods, left hand opens
    point = OV(BASE, hips_loc=(0, 0, -0.014), spine=(6, 0, -4), chest=(-2, 0, -8), head=(8, 0, 6),
               upper_arm_R=(-72, -14, 0), forearm_R=(-62, 0, 0), hand_R=(-25, 0, 0))
    tap = OV(point, spine=(9, 0, -2), chest=(0, 0, -4), head=(-6, 0, 4),
             upper_arm_R=(-58, -16, 0), forearm_R=(-34, 0, 0), hand_R=(-5, 0, 0))
    open_l = OV(BASE, hips_loc=(0, 0, -0.012), spine=(4, 0, 4), chest=(-4, 0, 6), head=(10, 0, -4),
                upper_arm=((-42, -22, 0), (-50, 4, 0)), forearm=((-70, 20, 0), (-110, 0, 0)),
                hand=((0, 0, 0), (-15, 0, 0)))
    nod = OV(open_l, head=(-4, 0, -6), upper_arm_L=(-30, -26, 0), forearm_L=(-55, 30, 0))
    K("talk", [(0, BASE), (14, point), (24, tap), (32, MX(tap, point, 0.6)), (46, open_l), (58, nod), (72, BASE)],
      True)
    return acts


SHOTS = [("idle", 0), ("idle", 40), ("talk", 14), ("talk", 24), ("talk", 46), ("talk", 58)]

H.run_character("bastian", PAL, BONES, build_parts, build_actions, weapon=build_mallet, height=1.4,
                shots=SHOTS, poses_cols=3, args=ARGS)
