"""Build Kito Brineheart (hero) procedurally: mesh + rig + 12 clips + GLB + previews.

Run (from anywhere):
  blender -b --factory-startup --python tools/blender/build_kito.py [-- --no-render]
"""
import math
import os
import sys

import bpy
from mathutils import Vector as V, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import humanoid as H  # noqa: E402
from humanoid import smoothstep as ss  # noqa: E402

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
BLEND = os.path.join(ROOT, "art_source", "blender", "kito.blend")
PREV = os.path.join(ROOT, "art_source", "blender", "previews")
OUT = os.path.join(ROOT, "assets", "characters", "kito")
GLB = os.path.join(OUT, "kito.glb")
PAL_PNG = os.path.join(OUT, "kito_palette.png")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

PAL = H.Palette({
    "coral": "#e2483d", "coral_dk": "#a9302a", "gold": "#f2b630", "gold_dk": "#c98a1e",
    "cream": "#f3e7c9", "navy": "#26365e", "navy_dk": "#1a2645", "boot": "#6b4126",
    "boot_dk": "#432716", "boot_lt": "#8a5a36", "skin": "#b9794f", "skin_dk": "#94593a",
    "hair": "#15202a", "hair_teal": "#1f4b55", "eye_white": "#fbf7ee", "amber": "#f3a72c",
    "amber_dk": "#a5561a", "pupil": "#1a0f0a", "lash": "#120c0a", "mouth": "#5a1f1c",
    "teeth": "#fffaf0", "tongue": "#d0605a", "bandage": "#f4f1ea", "bandage_dk": "#d4cdbd",
    "bandaid": "#e8c08e", "bandaid_pad": "#f6dfba", "belt": "#5a3520", "brass": "#d4a03a",
    "brass_dk": "#8f6618", "cord_red": "#c4282a", "steel": "#c3ccd5", "steel_dk": "#7f8b98",
    "steel_lt": "#eef3f7", "rope": "#b89a64", "rope_dk": "#8a7044", "seaglass": "#5fd0a8",
    "white": "#ffffff",
})

# ----------------------------------------------------------------------------- layout
D_ARM = V((0.52, 0.0, -0.854)).normalized()          # left arm direction in the A-pose
J = dict(hips=(0, 0, 0.72), spine=(0, 0, 0.82), chest=(0, 0, 0.92), neck=(0, 0.005, 1.03),
         head=(0, 0.005, 1.11), head_top=(0, 0.005, 1.40), shoulder=(0.035, 0, 1.0),
         arm=(0.165, 0, 0.985), hip=(0.075, 0, 0.70), knee=(0.08, -0.005, 0.40),
         ankle=(0.085, 0.01, 0.085), toe=(0.09, -0.125, 0.025))
J["elbow"] = V(J["arm"]) + D_ARM * 0.22
J["wrist"] = J["elbow"] + D_ARM * 0.20
J["hand_end"] = J["wrist"] + D_ARM * 0.10
EXTRAS = [("topknot", (0, 0.04, 1.44), (0, 0.05, 1.55), "head"),
          ("coat_tail.L", (0.085, 0.10, 0.76), (0.15, 0.20, 0.32), "hips"),
          ("coat_tail.R", (-0.085, 0.10, 0.76), (-0.15, 0.20, 0.32), "hips")]
BONES = H.standard_skeleton(J, EXTRAS)

HC, HR = V((0, 0.0, 1.245)), (0.132, 0.128, 0.152)


def head_pt(u, scale=1.0):
    x, y, z = u.x * HR[0], u.y * HR[1], u.z * HR[2]
    if u.z < 0:
        t = (-u.z) ** 1.6
        x *= 1 - 0.42 * t
        y *= 1 - (0.12 if u.y < 0 else 0.35) * t
        z *= 0.88  # shorter jaw
    y *= 0.94 if u.y < 0 else 1.05
    return HC + V((x, y, z)) * scale


def lerp(a, b, t):
    return a + (b - a) * t


def side_fn(s, fn):
    """Mirror a weight multiplier for the .R side."""
    return fn if s > 0 else (lambda v: fn(V((-v.x, v.y, v.z))))


# ----------------------------------------------------------------------------- head & face
def build_head(parts):
    hp = H.Part(["head"])
    H.sphere(hp, head_pt, 24, 16, "skin")
    H.ellipsoid(hp, (0, -0.119, 1.221), (0.011, 0.013, 0.017), 8, 6, "skin",
                H.axes((1, 0, 0), (0, 0.94, 0.34), (0, -0.34, 0.94)))
    nf = len(hp.f)
    for s in (1, -1):
        H.ellipsoid(hp, (0.127 * s, 0.012, 1.232), (0.02, 0.03, 0.036), 8, 6, "skin")
    bvh = hp.bvh(0, nf)
    O, R, U = V((0, -0.3, 0)), V((1, 0, 0)), V((0, 0, 1))

    for s in (1, -1):
        ex, ez = 0.05 * s, 1.252

        def E(cx, cy, rx, ry, n=16, flat=1.0):
            pts = []
            for j in range(n):
                a = 2 * math.pi * j / n
                yy = ry * math.sin(a) * (flat if math.sin(a) < 0 else 1.0)
                pts.append((ex + s * (cx + rx * math.cos(a)), ez + cy + yy))
            return pts if s > 0 else pts[::-1]
        H.decal(hp, bvh, O, R, U, E(0, 0, 0.025, 0.031, 18, 0.88), "eye_white", 0.0015)
        H.decal(hp, bvh, O, R, U, E(-0.002, -0.002, 0.0175, 0.025), "amber_dk", 0.0026)
        H.decal(hp, bvh, O, R, U, E(-0.002, -0.009, 0.015, 0.015), "amber", 0.0034)
        H.decal(hp, bvh, O, R, U, E(-0.002, -0.002, 0.0072, 0.011, 12), "pupil", 0.0042)
        H.decal(hp, bvh, O, R, U, E(0.006, 0.01, 0.0055, 0.0055, 8), "white", 0.005, 1)
        H.decal(hp, bvh, O, R, U, E(-0.008, -0.013, 0.003, 0.003, 6), "white", 0.005, 1)
        # upper lash line: thick dark arc with an outer flick
        ths = [math.radians(a) for a in range(185, -20, -15)]
        if s < 0:
            ths = ths[::-1]
        top, bot = [], []
        for a in ths:
            flick = 0.004 if math.cos(a) > 0.8 else 0.0
            top.append((ex + s * ((0.025 + 0.006 + flick) * math.cos(a)), ez + (0.031 + 0.007) * math.sin(a) + flick))
            bot.append((ex + s * (0.024 * math.cos(a)), ez + 0.029 * math.sin(a)))
        H.decal_strip(hp, bvh, O, R, U, top, bot, "lash", 0.0032)
        # thick brows, rising outward
        xs = [0.018 + 0.07 * k / 6 for k in range(7)]
        if s < 0:
            xs = xs[::-1]
        top, bot = [], []
        for x in xs:
            t = (x - 0.018) / 0.07
            zc = 1.294 + 0.013 * t + 0.005 * math.sin(math.pi * t)
            th = 0.016 * (1 - t) + 0.008 * t
            top.append((s * x, zc + th / 2))
            bot.append((s * x, zc - th / 2))
        H.decal_strip(hp, bvh, O, R, U, top, bot, "hair", 0.004)

    # grin: D-shaped open mouth with teeth and tongue
    mouth = [(0.027, 1.175), (0.013, 1.171), (0.0, 1.170), (-0.013, 1.171), (-0.027, 1.175)]
    for a in range(200, 345, 20):
        r = math.radians(a)
        mouth.append((0.026 * math.cos(r), 1.169 + 0.02 * math.sin(r)))
    H.decal(hp, bvh, O, R, U, mouth, "mouth", 0.0015)
    H.decal_strip(hp, bvh, O, R, U, [(-0.02, 1.1712), (0, 1.1702), (0.02, 1.1712)],
                  [(-0.019, 1.1655), (0, 1.1645), (0.019, 1.1655)], "teeth", 0.0025)
    H.decal(hp, bvh, O, R, U, H.ellipse_pts(0.003, 1.1555, 0.011, 0.0045, 10), "tongue", 0.0025, 1)
    # band-aid on the nose bridge
    ba = [(0.021 * math.copysign(abs(math.cos(a)) ** 0.5, math.cos(a)),
           0.0068 * math.copysign(abs(math.sin(a)) ** 0.5, math.sin(a))) for a in
          [2 * math.pi * j / 14 for j in range(14)]]
    rot = -0.18
    ba = [(x * math.cos(rot) - y * math.sin(rot), 1.232 + x * math.sin(rot) + y * math.cos(rot)) for x, y in ba]
    H.decal(hp, bvh, O, R, U, ba, "bandaid", 0.0035)
    H.decal(hp, bvh, O, R, U, H.ellipse_pts(0, 1.232, 0.0065, 0.0045, 8, rot), "bandaid_pad", 0.0045, 1)
    parts.append(hp)


def build_hair(parts):
    hp = H.Part(["head"])
    nu = 24

    def tmax(psi, j):
        f = -math.sin(psi)  # 1 at the front
        t = 125 - (125 - 58) * (1 + f) / 2
        if f < 0.2:
            t += 7 * (j % 2)  # jagged nape/side hairline
        return math.radians(t)

    def cap_pt(th, psi, sc):
        return HC + (head_pt(V((math.sin(th) * math.cos(psi), math.sin(th) * math.sin(psi), math.cos(th)))) - HC) * sc
    rows = []
    for k, (s, sc) in enumerate([(1.0, 0.99), (1.0, 1.075), (0.86, 1.08), (0.7, 1.085), (0.54, 1.085),
                                 (0.38, 1.08), (0.22, 1.075), (0.1, 1.07)]):
        rows.append([cap_pt(s * tmax(2 * math.pi * j / nu, j), 2 * math.pi * j / nu, sc) for j in range(nu)])
    H.loft(hp, rows, "hair", True, None, HC + V((0, 0, HR[2] * 1.07)))

    def spike(anchor, d, L, r0, flat=0.55, bend=(0, 0.25, 0.1), n=6, part=hp):
        u = V(anchor).normalized()
        base = HC + (head_pt(u) - HC) * 0.97
        d, b = V(d).normalized(), V(bend)
        pts, rad = [], []
        for k in range(5):
            t = k / 4.0
            pts.append(base + d * (L * t) + b * (L * t * t))
            r = r0 * (1 - t) ** 0.85 + 0.002
            rad.append((r * flat, r))
        H.tube(part, pts[:-1], rad[:-1], n, "hair", hint=u, cap1=pts[-1])
    # (anchor dir on skull, growth dir, length, base radius); mirrored pairs listed once with x>0
    crown = [((0.0, -0.3, 0.95), (0, -0.3, 1), 0.085, 0.045, False),
             ((0.4, -0.08, 0.9), (0.7, 0.0, 0.8), 0.10, 0.046, True),
             ((0.22, 0.25, 0.95), (0.3, 0.45, 1), 0.11, 0.048, True),
             ((0.3, 0.7, 0.6), (0.5, 0.6, 0.5), 0.12, 0.05, True),
             ((0, 0.85, 0.45), (0, 0.75, 0.6), 0.12, 0.055, False),
             ((0.6, 0.7, 0.1), (0.75, 0.45, -0.45), 0.11, 0.05, True),
             ((0.35, 0.85, -0.25), (0.45, 0.45, -0.8), 0.10, 0.05, True),
             ((0, 0.9, -0.3), (0, 0.5, -0.9), 0.10, 0.05, False),
             ((0.85, 0.15, 0.45), (1, 0.25, 0.4), 0.10, 0.042, True),
             ((0.8, 0.4, 0.05), (0.8, 0.5, -0.4), 0.08, 0.042, True)]
    bangs = [((0.05, -0.72, 0.7), (0.08, -0.6, -0.8), 0.06, 0.036, False),
             ((0.38, -0.62, 0.68), (0.35, -0.5, -0.8), 0.055, 0.034, False),
             ((-0.33, -0.64, 0.68), (-0.3, -0.55, -0.8), 0.06, 0.036, False),
             ((0.72, -0.45, 0.45), (0.5, -0.3, -0.85), 0.08, 0.034, True)]
    for lst, kw in ((crown, {}), (bangs, dict(flat=0.45, bend=(0, -0.15, 0.0)))):
        for a, d, L, r, mir in lst:
            spike(a, d, L, r, **kw)
            if mir:
                spike((-a[0], a[1], a[2]), (-d[0], d[1], d[2]), L, r, **kw)
    sheen = V((0, -0.3, 0.95)).normalized()
    hp.recolor(0, lambda c, n: "hair_teal" if 0.5 < n.dot(sheen) < 0.8 and c.z > 1.3 else "hair")
    parts.append(hp)

    # topknot: bound bundle + red cord + splayed tuft (own bone for follow-through)
    tk = H.Part(["topknot", ("head", lambda v: 3.0 * ss(1.46, 1.41, v.z))])
    H.tube(tk, [(0, 0.03, 1.385), (0, 0.04, 1.44), (0, 0.047, 1.485)], [0.034, 0.028, 0.026], 10, "hair",
           hint=V((1, 0, 0)), cap1="center")
    for zc, rc in ((1.462, 0.03), (1.476, 0.029)):
        cord = [V((0, 0.045, zc)) + V((math.cos(a) * rc, math.sin(a) * rc, 0))
                for a in [2 * math.pi * k / 14 for k in range(14)]]
        H.tube(tk, cord, [0.0072] * 14, 6, "cord_red", hint=V((0, 0, 1)), closed_path=True)
    for d, L in (((0.55, 0.15, 1), 0.06), ((-0.55, 0.25, 1), 0.055), ((0.05, -0.45, 1), 0.05),
                 ((0, 0.6, 0.8), 0.055), ((0.05, 0.05, 1), 0.07)):
        base, d = V((0, 0.047, 1.478)), V(d).normalized()
        pts = [base + d * (L * t) + V((0, 0.2, 0)) * (L * t * t) for t in (0, 0.33, 0.66, 1.0)]
        H.tube(tk, pts[:-1], [(0.014, 0.02), (0.011, 0.015), (0.006, 0.008)], 6, "hair", hint=d.cross(V((0, 0, 1))) + V((0.001, 0, 0)),
               cap1=pts[-1])
    parts.append(tk)


# ----------------------------------------------------------------------------- body
TORSO = [(0.64, 0.05, 0.05, 0.0), (0.67, 0.112, 0.084, 0.005), (0.71, 0.126, 0.09, 0.005),
         (0.76, 0.12, 0.086, 0.0), (0.80, 0.114, 0.082, 0.0), (0.86, 0.12, 0.085, 0.0),
         (0.92, 0.13, 0.088, 0.0), (0.97, 0.13, 0.083, 0.004), (1.0, 0.11, 0.07, 0.008),
         (1.03, 0.06, 0.055, 0.008)]


def torso_prof(z):
    for a, b in zip(TORSO, TORSO[1:]):
        if a[0] <= z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            return tuple(lerp(a[k], b[k], t) for k in (1, 2, 3))
    return TORSO[-1][1:]


def vring(z, rx, ry, yoff, n, cx=0.0):
    return H.ring((cx, yoff, z), (0, 0, 1), rx, ry, n, hint=V((1, 0, 0)))


def build_body(parts):
    # neck
    nk = H.Part(["chest", "neck", ("head", lambda v: ss(1.09, 1.12, v.z))])
    H.tube(nk, [(0, 0.01, 0.99), (0, 0.008, 1.06), (0, 0.006, 1.13)], [0.05, 0.046, 0.048], 12, "skin")
    parts.append(nk)
    # shirt torso + shorts seat
    sh = lambda s: (lambda v: ss(0.94, 0.99, v.z) * ss(0.02 * s, 0.08 * s, v.x))
    th = lambda s: (lambda v: ss(0.73, 0.66, v.z) * ss(0.0, 0.05 * s, v.x))
    tp = H.Part(["hips", "spine", "chest", ("neck", lambda v: ss(1.0, 1.03, v.z)),
                 ("shoulder.L", sh(1)), ("shoulder.R", sh(-1)), ("thigh.L", th(1)), ("thigh.R", th(-1))])
    rows = [vring(z, rx, ry, yo, 20) for z, rx, ry, yo in TORSO]
    H.loft(tp, rows, lambda i, j: "navy" if 0 <= i < len(rows) - 1 and TORSO[i][0] < 0.755 else "cream",
           True, V((0, 0.0, 0.63)), V((0, 0.008, 1.04)))
    parts.append(tp)
    # belt + buckle
    bp = H.Part(["hips", "spine"])
    brows = []
    for z, dr in ((0.752, 0.003), (0.758, 0.011), (0.806, 0.011), (0.812, 0.003)):
        rx, ry, yo = torso_prof(z)
        brows.append(vring(z, rx + dr, ry + dr, yo, 24))
    H.loft(bp, brows, "belt")
    rx, ry, yo = torso_prof(0.782)
    yf = yo - ry - 0.011
    H.ellipsoid(bp, (0, yf - 0.004, 0.782), (0.029, 0.008, 0.023), 10, 6, "brass", exp=0.35)
    H.ellipsoid(bp, (0, yf - 0.009, 0.782), (0.016, 0.005, 0.012), 8, 4, "belt", exp=0.35)
    H.ellipsoid(bp, (0.004, yf - 0.013, 0.782), (0.011, 0.003, 0.0025), 6, 4, "brass_dk")
    parts.append(bp)
    # pendant: cord loop + brass barrel plug with cross slot
    pp = H.Part(["chest", ("neck", lambda v: ss(1.0, 1.04, v.z))])
    cord = []
    for k in range(22):
        a = 2 * math.pi * k / 22
        f = max(0.0, math.cos(a))
        cord.append(V((0.06 * math.sin(a) * (1 - 0.6 * f ** 4), 0.008 - math.cos(a) * 0.053 - 0.05 * f ** 3,
                       1.035 - 0.093 * f ** 3)))
    H.tube(pp, cord, [0.0035] * 22, 5, "rope_dk", hint=V((0, 0, 1)), closed_path=True)
    f0 = len(pp.f)
    H.tube(pp, [(0, -0.091, 0.928), (0, -0.101, 0.928), (0, -0.104, 0.928)], [0.022, 0.022, 0.018], 16, "brass",
           hint=V((1, 0, 0)), cap0="center", cap1="center")
    L, w = 0.013, 0.0024
    plus = [(w, -w), (L, -w), (L, w), (w, w), (w, L), (-w, L), (-w, w), (-L, w), (-L, -w), (-w, -w), (-w, -L), (w, -L)]
    H.decal(pp, pp.bvh(f0), V((0, -0.3, 0)), V((1, 0, 0)), V((0, 0, 1)), [(x, 0.928 + y) for x, y in plus],
            "brass_dk", 0.0008)
    parts.append(pp)

    for s in (1, -1):
        S = "L" if s > 0 else "R"
        X = lambda p: V((p[0] * s, p[1], p[2]))
        # navy knee shorts
        lp = H.Part(["hips", f"thigh.{S}", (f"shin.{S}", lambda v: 0.5 * ss(0.45, 0.38, v.z))])
        pts = [X(p) for p in ((0.07, 0, 0.75), (0.075, -0.002, 0.62), (0.079, -0.004, 0.50),
                              (0.082, -0.006, 0.40), (0.082, -0.006, 0.385), (0.082, -0.006, 0.384))]
        H.tube(lp, pts, [0.082, 0.077, 0.072, 0.074, 0.074, 0.05], 14,
               lambda i, j: "navy_dk" if i >= 3 else "navy", hint=V((s, 0, 0)))
        parts.append(lp)
        # calf
        cp = H.Part([(f"thigh.{S}", lambda v: ss(0.36, 0.42, v.z)), f"shin.{S}"])
        H.tube(cp, [X(p) for p in ((0.081, -0.005, 0.43), (0.082, 0.0, 0.33), (0.084, 0.004, 0.22))],
               [0.046, 0.049, 0.043], 12, "skin", hint=V((s, 0, 0)))
        parts.append(cp)
        # boot shaft with rolled cuff
        bt = H.Part([f"shin.{S}", (f"foot.{S}", lambda v: ss(0.13, 0.06, v.z))])
        kn, an = V(J["knee"]), V(J["ankle"])
        rings, cols = [], []
        for z, r in ((0.07, 0.058), (0.13, 0.059), (0.2, 0.061), (0.245, 0.063), (0.25, 0.073),
                     (0.285, 0.078), (0.303, 0.072), (0.304, 0.05)):
            c = lerp(an, kn, (z - an.z) / (kn.z - an.z))
            rings.append(vring(z, r, r * 0.95, c.y, 14, c.x * s))
        H.loft(bt, rings, lambda i, j: "boot_lt" if i >= 3 else "boot")
        # boot foot: big rounded toe, flat sole
        f0 = len(bt.f)
        v0 = len(bt.v)
        H.ellipsoid(bt, (0.087 * s, -0.035, 0.05), (0.062, 0.118, 0.058), 14, 10, "boot")
        for k in range(v0, len(bt.v)):
            p = bt.v[k]
            if p.y < -0.06:
                p.z += 1.6 * (-0.06 - p.y) ** 2
            p.z = max(p.z, 0.0)
        bt.recolor(f0, lambda c, n: "boot_dk" if c.z < 0.016 else None)
        parts.append(bt)


# ----------------------------------------------------------------------------- coat
COAT = [(1.045, 0.082, 0.072, 0.006, 0.62), (1.025, 0.125, 0.092, 0.006, 0.55), (0.995, 0.19, 0.118, 0.006, 0.46),
        (0.955, 0.196, 0.124, 0.006, 0.42), (0.90, 0.18, 0.122, 0.008, 0.40), (0.85, 0.166, 0.115, 0.01, 0.42),
        (0.80, 0.16, 0.112, 0.012, 0.47), (0.74, 0.172, 0.124, 0.015, 0.56), (0.66, 0.192, 0.142, 0.02, 0.66),
        (0.56, 0.212, 0.162, 0.025, 0.76), (0.46, 0.23, 0.18, 0.03, 0.84), (0.37, 0.245, 0.194, 0.035, 0.9),
        (0.30, 0.255, 0.203, 0.04, 0.95), (0.284, 0.258, 0.206, 0.041, 0.96)]


def coat_rows():
    rows = []
    for a, b in zip(COAT, COAT[1:]):
        rows.append(a)
        if a[0] >= 0.80:
            rows.append(tuple(lerp(a[k], b[k], 0.5) for k in range(5)))
    rows.append(COAT[-1])
    return rows


def coat_prof(z):
    for a, b in zip(COAT, COAT[1:]):
        if b[0] <= z <= a[0]:
            t = (z - a[0]) / (b[0] - a[0])
            return tuple(lerp(a[k], b[k], t) for k in (1, 2, 3, 4))
    return COAT[-1][1:]


def coat_pt(z, rx, ry, yo, phi):
    return V((rx * math.sin(phi), yo - ry * math.cos(phi), z))


def coat_spec():
    def thigh(s):
        return side_fn(s, lambda v: ss(0.72, 0.55, v.z) * ss(0.08, -0.06, v.y) * ss(-0.05, 0.05, v.x))

    def tail(s):
        return side_fn(s, lambda v: ss(0.76, 0.6, v.z) * ss(-0.06, 0.06, v.y) * ss(-0.06, 0.04, v.x))

    def shoulder(s):
        return side_fn(s, lambda v: ss(0.03, 0.12, v.x) * ss(0.9, 0.98, v.z))

    def uarm(s):
        return side_fn(s, lambda v: 0.6 * ss(0.14, 0.2, v.x) * ss(0.88, 0.95, v.z))
    spec = ["hips", "spine", "chest", ("neck", lambda v: ss(1.0, 1.04, v.z))]
    for s, S in ((1, "L"), (-1, "R")):
        spec += [(f"shoulder.{S}", shoulder(s)), (f"upper_arm.{S}", uarm(s)),
                 (f"thigh.{S}", thigh(s)), (f"coat_tail.{S}", tail(s))]
    return spec


def build_coat(parts):
    cp = H.Part(coat_spec())
    rows = coat_rows()
    N = 20
    P = []
    for z, rx, ry, yo, al in rows:
        dl = 0.014 / rx
        phis = [al, al + dl] + [lerp(al + dl, 2 * math.pi - al - dl, k / (N - 1)) for k in range(1, N - 1)] \
            + [2 * math.pi - al - dl, 2 * math.pi - al]
        P.append([coat_pt(z, rx, ry, yo, p) for p in phis])
    R, C = len(P), len(P[0])
    H.sheet(cp, P, 0.012,
            lambda r, c: "gold" if (c in (0, C - 2) or r == R - 2) else "coral",
            "coral_dk", dict(top="coral_dk", bottom="gold", left="gold", right="gold"))
    bvh = cp.bvh()
    # sun-compass emblem on the back: ring + 8-ray sun, projected onto the coat
    O, Rv, Uv = V((0, 0.3, 0)), V((-1, 0, 0)), V((0, 0, 1))
    cz = 0.875
    circ = lambda r, n: [(r * math.cos(-2 * math.pi * k / n), cz + r * math.sin(-2 * math.pi * k / n)) for k in range(n + 1)]
    H.decal_strip(cp, bvh, O, Rv, Uv, circ(0.074, 32), circ(0.064, 32), "gold", 0.004)
    H.decal(cp, bvh, O, Rv, Uv, H.ellipse_pts(0, cz, 0.021, 0.021, 14), "gold", 0.004)
    for k in range(8):
        a = math.pi / 2 + k * math.pi / 4
        r1 = 0.058 if k % 2 == 0 else 0.046
        w, n = (math.cos(a), math.sin(a)), (-math.sin(a), math.cos(a))
        b = (0.019 * w[0], cz + 0.019 * w[1])
        hw = 0.0085
        tri = [(b[0] - n[0] * hw, b[1] - n[1] * hw), (r1 * w[0], cz + r1 * w[1]), (b[0] + n[0] * hw, b[1] + n[1] * hw)]
        H.decal(cp, bvh, O, Rv, Uv, tri, "gold", 0.0045, 1)
    # gold buttons near both front edges
    for z in (0.93, 0.865):
        rx, ry, yo, al = coat_prof(z)
        for phi in (al + 0.16, 2 * math.pi - al - 0.16):
            p = coat_pt(z, rx, ry, yo, phi)
            nrm = V((math.sin(phi) / rx, -math.cos(phi) / ry, 0)).normalized()
            H.ellipsoid(cp, p + nrm * 0.005, (0.011, 0.011, 0.011), 6, 4, "gold")
    parts.append(cp)
    # tall captain's collar, open at the front
    cl = H.Part(["chest", ("neck", lambda v: 0.6)])
    Pc = []
    for z, rx, ry, yo, al in ((1.118, 0.12, 0.11, 0.014, 0.85), (1.09, 0.106, 0.096, 0.012, 0.78),
                              (1.06, 0.093, 0.083, 0.009, 0.72), (1.03, 0.085, 0.075, 0.006, 0.66)):
        Pc.append([coat_pt(z, rx, ry, yo, lerp(al, 2 * math.pi - al, k / 17)) for k in range(18)])
    H.sheet(cl, Pc, 0.01, lambda r, c: "gold" if r == 0 else "coral", "coral_dk",
            dict(top="gold", bottom="coral_dk", left="gold", right="gold"))
    parts.append(cl)


# ----------------------------------------------------------------------------- arms
def arm_frame(s):
    d = V((D_ARM.x * s, 0, D_ARM.z))
    sj = V((J["arm"][0] * s, J["arm"][1], J["arm"][2]))
    return d, sj


def build_arms(parts):
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        d, sj = arm_frame(s)
        at = lambda u: sj + d * u
        hint = V((0, -1, 0))
        if s > 0:  # full sleeve, rolled cuff
            sp = H.Part([f"shoulder.{S}", f"upper_arm.{S}", f"forearm.{S}", (f"hand.{S}", lambda v: 0.15)])
            us = [-0.01, 0.03, 0.08, 0.15, 0.22, 0.29, 0.345, 0.352, 0.37, 0.392, 0.402, 0.406, 0.407]
            rs = [0.05, 0.066, 0.066, 0.061, 0.058, 0.056, 0.057, 0.066, 0.07, 0.07, 0.066, 0.062, 0.046]
            fc = ["coral"] * 6 + ["coral_dk"] * 3 + ["gold", "gold", "coral_dk"]
            H.tube(sp, [at(u) for u in us], rs, 14, lambda i, j: fc[min(max(i, 0), len(fc) - 1)], hint=hint)
            parts.append(sp)
            wp = H.Part([f"forearm.{S}", f"hand.{S}"])
            H.tube(wp, [at(u) for u in (0.33, 0.39, 0.445)], [0.032, 0.03, 0.028], 10, "skin", hint=hint)
            parts.append(wp)
        else:  # torn-off sleeve at the elbow + bandaged forearm
            sp = H.Part([f"shoulder.{S}", f"upper_arm.{S}", (f"forearm.{S}", lambda v: 0.6)])
            us = [-0.01, 0.03, 0.08, 0.15, 0.205, 0.235, 0.236]
            rs = [0.05, 0.066, 0.066, 0.062, 0.06, 0.061, 0.048]
            grid = H.tube(sp, [at(u) for u in us], rs, 14, lambda i, j: "coral_dk" if i >= 5 else "coral", hint=hint)
            jag = [0, -0.018, 0.006, -0.026, -0.004, 0.01, -0.02, -0.008, 0.012, -0.03, -0.01, 0.004, -0.015, 0.008]
            for rr in grid[-2:]:
                for j, vi in enumerate(rr):
                    sp.v[vi] += d * (jag[j] + 0.012)
            parts.append(sp)
            fp = H.Part([f"forearm.{S}", (f"hand.{S}", lambda v: 0.5), (f"upper_arm.{S}", lambda v: 0.5)])
            H.tube(fp, [at(u) for u in (0.18, 0.25, 0.33, 0.40, 0.445)], [0.04, 0.036, 0.033, 0.03, 0.028], 12,
                   "skin", hint=hint)
            us = [0.215 + 0.18 * k / 10 for k in range(11)]
            rs = [lerp(0.041, 0.034, k / 10) for k in range(11)]
            rs[0], rs[-1] = 0.038, 0.031
            H.tube(fp, [at(u) for u in us], rs, 12,
                   lambda i, j: "bandage_dk" if (j + i) % 4 == 0 else "bandage", hint=hint)
            parts.append(fp)
        # oversized fist
        hp = H.Part([f"hand.{S}", (f"forearm.{S}", lambda v: 0.2)])
        a = d
        g = V((0, -1, 0))
        p = a.cross(g).normalized()
        if p.x * s > 0:
            p = -p
        H.fist(hp, at(0.42), a, g, p, "skin", size=1.0)
        parts.append(hp)


def hand_frame_R():
    d, sj = arm_frame(-1)
    a = d
    g = V((0, -1, 0))
    p = a.cross(g).normalized()
    if p.x < 0:
        p = -p
    c = sj + d * 0.42 + a * 0.044
    return a, g, p, c


def build_cutlass():
    a, g, p, c = hand_frame_R()
    cp = H.Part(["hand.R"], smooth=False)
    # rope grip with wrap bands
    gp = [c + g * t for t in [-0.058 + 0.11 * k / 8 for k in range(9)]]
    H.tube(cp, gp, [0.0145 + 0.0015 * (k % 2) for k in range(9)], 8,
           lambda i, j: "rope_dk" if i % 2 else "rope", hint=a, cap0="center", cap1="center")
    # pommel: sea-glass ball on a brass collar
    H.tube(cp, [c - g * 0.058, c - g * 0.064], [0.016, 0.016], 8, "brass", hint=a, cap0="center", cap1="center")
    H.ellipsoid(cp, c - g * 0.078, (0.019, 0.019, 0.019), 10, 7, "seaglass", H.axes(a, p, -g))
    # brass shell guard + knuckle bow
    H.ellipsoid(cp, c + g * 0.062 + a * 0.01, (0.036, 0.027, 0.006), 12, 6, "brass", H.axes(a, p, g))
    bow = [c + g * 0.06 + a * 0.042, c + g * 0.035 + a * 0.066, c + a * 0.074, c - g * 0.035 + a * 0.066,
           c - g * 0.06 + a * 0.035, c - g * 0.064 + a * 0.012]
    H.tube(cp, bow, [0.0055] * 6, 6, "brass", hint=p, cap0="center", cap1="center")
    # curved blade (edge toward +a, curving back toward the spine)
    L, n = 0.55, 12
    rings = []
    for k in range(n):
        s = k / (n - 1) * 0.97
        ctr = c + g * (0.066 + s * L) - a * (0.07 * s * s)
        T = (g * L - a * (0.14 * s)).normalized()
        u = (a - T * a.dot(T)).normalized()
        v = T.cross(u)
        w = (0.032 + 0.012 * math.sin(min(s / 0.8, 1) * math.pi / 2)) * (1.0 if s < 0.85 else 1 - (s - 0.85) / 0.25)
        t = 0.0065 * (1 - 0.5 * s)
        ctr = ctr - u * (0.004 if s < 0.85 else (s - 0.85) * 0.1)
        rings.append([ctr + u * (w / 2), ctr + u * (w * 0.2) + v * (t * 0.35), ctr - u * (w / 2) + v * (t / 2),
                      ctr - u * (w / 2) - v * (t / 2), ctr + u * (w * 0.2) - v * (t * 0.35)])
    tip = c + g * (0.066 + L) - a * (0.07 + 0.01)
    fcol = ["steel_lt", "steel", "steel_dk", "steel", "steel_lt"]
    H.loft(cp, rings, lambda i, j: fcol[j] if 0 <= i < n else "steel", True, "center", tip)
    return cp


# ----------------------------------------------------------------------------- animation
def pose(**kw):
    """Shorthand: pose(spine=(..), arm=(L, R)) where paired names take an (L, R) tuple or one value."""
    out = {}
    for k, v in kw.items():
        if k == "hips_loc":
            out[k] = v
        elif k in ("upper_arm", "forearm", "hand", "thigh", "shin", "foot", "shoulder", "coat_tail"):
            l, r = (v if isinstance(v[0], (tuple, list)) else (v, v))
            out[f"{k}.L"], out[f"{k}.R"] = l, r
        elif k.endswith(("_L", "_R")):
            out[k[:-2] + "." + k[-1]] = v
        else:
            out[k] = v
    return out


def mix(a, b, t):
    keys = set(a) | set(b)
    return {k: tuple(lerp(x, y, t) for x, y in zip(a.get(k, (0, 0, 0)), b.get(k, (0, 0, 0)))) for k in keys}


def over(base, **kw):
    d = dict(base)
    d.update(pose(**kw))
    return d


BASE = pose(hips_loc=(0, 0, -0.024), spine=(8, 0, 0), chest=(6, 0, 0), neck=(-4, 0, 0), head=(-8, 0, 0),
            thigh=(-16, -3, 0), shin=(32, 0, 0), foot=(-16, 3, 0),
            upper_arm=((-8, 12, 0), (-25, 8, 0)), forearm=((-35, 0, 0), (-45, 0, 0)), hand=((0, 0, 0), (30, 0, 0)),
            coat_tail=(8, 0, 0))


def build_actions(arm):
    acts = {}
    K = lambda name, keys, loop=False: acts.__setitem__(name, H.key_clip(arm, name, keys, loop))

    # idle 1.6 s: eager forward lean + breathing
    inhale = over(BASE, hips_loc=(0, 0, -0.018), chest=(3, 0, 0), head=(-6, 0, 0), shoulder=(0, -3, 0),
                  upper_arm=((-11, 10, 0), (-27, 6, 0)), topknot=(-4, 0, 0), coat_tail=(5, 0, 0))
    K("idle", [(0, BASE), (24, inhale), (48, BASE)], True)

    # run 16 frames: contact / passing, strong arm swing, coat flare
    cL = pose(hips_loc=(0, 0, -0.03), hips=(0, 0, -8), spine=(14, 0, 0), chest=(6, 0, 10), head=(-14, 0, -2),
              thigh=((-42, 0, 0), (30, 0, 0)), shin=((18, 0, 0), (55, 0, 0)), foot=((-10, 0, 0), (25, 0, 0)),
              upper_arm=((45, 10, 0), (-55, 8, 0)), forearm=((-60, 0, 0), (-50, 0, 0)), hand=((0, 0, 0), (45, 0, 0)),
              coat_tail=((25, 0, 0), (35, 0, 0)), topknot=(-10, 0, 0))
    pL = pose(hips_loc=(0, 0, 0.025), spine=(14, 0, 0), chest=(6, 0, 0), head=(-14, 0, 0),
              thigh=((-5, 0, 0), (-30, 0, 0)), shin=((15, 0, 0), (95, 0, 0)), foot=((-8, 0, 0), (20, 0, 0)),
              upper_arm=((5, 10, 0), (-20, 8, 0)), forearm=((-70, 0, 0), (-60, 0, 0)), hand=((0, 0, 0), (45, 0, 0)),
              coat_tail=(45, 0, 0), topknot=(-16, 0, 0))
    cR = pose(hips_loc=(0, 0, -0.03), hips=(0, 0, 8), spine=(14, 0, 0), chest=(6, 0, -10), head=(-14, 0, 2),
              thigh=((30, 0, 0), (-42, 0, 0)), shin=((55, 0, 0), (18, 0, 0)), foot=((25, 0, 0), (-10, 0, 0)),
              upper_arm=((-55, 10, 0), (40, 8, 0)), forearm=((-50, 0, 0), (-60, 0, 0)), hand=((0, 0, 0), (45, 0, 0)),
              coat_tail=((35, 0, 0), (25, 0, 0)), topknot=(-10, 0, 0))
    pR = pose(hips_loc=(0, 0, 0.025), spine=(14, 0, 0), chest=(6, 0, 0), head=(-14, 0, 0),
              thigh=((-30, 0, 0), (-5, 0, 0)), shin=((95, 0, 0), (15, 0, 0)), foot=((20, 0, 0), (-8, 0, 0)),
              upper_arm=((-20, 10, 0), (5, 8, 0)), forearm=((-60, 0, 0), (-70, 0, 0)), hand=((0, 0, 0), (45, 0, 0)),
              coat_tail=(45, 0, 0), topknot=(-16, 0, 0))
    K("run", [(0, cL), (4, pL), (8, cR), (12, pR), (16, cL)], True)

    # jump: anticipation crouch -> launch -> rising tuck
    crouch = pose(hips_loc=(0, 0, -0.12), spine=(25, 0, 0), chest=(10, 0, 0), head=(-20, 0, 0),
                  thigh=(-38, 0, 0), shin=(76, 0, 0), foot=(-38, 0, 0),
                  upper_arm=((45, 5, 0), (45, 5, 0)), forearm=((-20, 0, 0), (-30, 0, 0)), hand=((0, 0, 0), (30, 0, 0)))
    launch = pose(hips_loc=(0, 0, 0.04), spine=(-5, 0, 0), chest=(-5, 0, 0), head=(-10, 0, 0),
                  thigh=(5, 0, 0), shin=(5, 0, 0), foot=(40, 0, 0),
                  upper_arm=((-140, 0, 0), (-120, 0, 0)), forearm=(-20, 0, 0), hand=((0, 0, 0), (50, 0, 0)),
                  coat_tail=(15, 0, 0), topknot=(10, 0, 0))
    tuck = pose(hips_loc=(0, 0, 0.04), spine=(4, 0, 0), head=(-6, 0, 0),
                thigh=((-55, 0, 0), (-20, 0, 0)), shin=((85, 0, 0), (60, 0, 0)), foot=((10, 0, 0), (20, 0, 0)),
                upper_arm=((-110, -20, 0), (-90, 8, 0)), forearm=((-30, 0, 0), (-60, 0, 0)), hand=((0, 0, 0), (40, 0, 0)),
                coat_tail=(30, 0, 0), topknot=(-6, 0, 0))
    K("jump", [(0, BASE), (3, crouch), (6, launch), (9, tuck), (12, mix(tuck, launch, 0.15))])

    # fall loop: arms up, slight flail, coat lifted
    f0 = pose(hips_loc=(0, 0, 0.02), spine=(-4, 0, 0), head=(10, 0, 0),
              upper_arm=((-30, -95, 0), (-40, -85, 0)), forearm=((-25, 0, 0), (-30, 0, 0)), hand=((0, 0, 0), (30, 0, 0)),
              thigh=((-35, 0, 0), (-10, 0, 0)), shin=((60, 0, 0), (35, 0, 0)), foot=(15, 0, 0),
              coat_tail=(60, 0, 0), topknot=(-8, 0, 0))
    f1 = over(f0, upper_arm=((-40, -108, 0), (-30, -74, 0)), forearm=((-40, 0, 0), (-18, 0, 0)),
              thigh=((-24, 0, 0), (-22, 0, 0)), shin=((45, 0, 0), (52, 0, 0)), coat_tail=(70, 0, 0), topknot=(-14, 0, 0))
    K("fall", [(0, f0), (8, f1), (16, f0)], True)

    # land 0.2 s: impact squash, overshoot, settle into the idle stance
    imp = pose(hips_loc=(0, 0, -0.082), spine=(22, 0, 0), chest=(10, 0, 0), head=(-15, 0, 0),
               thigh=(-30, 0, 0), shin=(60, 0, 0), foot=(-30, 0, 0),
               upper_arm=((-35, -30, 0), (-35, -30, 0)), forearm=(-30, 0, 0), hand=((0, 0, 0), (30, 0, 0)),
               coat_tail=(40, 0, 0), topknot=(12, 0, 0))
    deep = over(imp, hips_loc=(0, 0, -0.117), spine=(28, 0, 0), thigh=(-36, 0, 0), shin=(72, 0, 0), foot=(-36, 0, 0),
                upper_arm=((-20, -40, 0), (-20, -40, 0)), coat_tail=(-10, 0, 0), topknot=(18, 0, 0))
    K("land", [(0, imp), (2, deep), (6, BASE)])

    # slash 0.33 s: 2f wind-up, fast wide horizontal arc, 5f follow-through
    legs = dict(thigh=((-25, -4, 0), (6, -6, 0)), shin=((40, 0, 0), (30, 0, 0)), foot=((-15, 0, 0), (-28, 0, 0)))
    wind = pose(hips_loc=(0, 0, -0.035), hips=(0, 0, -8), spine=(10, 0, -12), chest=(5, 0, -30), head=(-8, 0, 30),
                upper_arm=((-50, -20, -20), (0, -62, 50)), forearm=((-30, 0, 0), (-40, 0, 0)), hand=((0, 0, 0), (0, 0, 0)),
                coat_tail=((10, 0, 0), (20, 0, 0)), **legs)
    mid = over(wind, hips=(0, 0, 4), spine=(10, 0, 2), chest=(5, 0, 12), head=(-8, 0, -6),
               upper_arm=((-20, -25, 10), (-10, -78, -30)), forearm=((-30, 0, 0), (-12, 0, 0)), hand=((0, 0, 0), (50, 0, 0)))
    hit = over(mid, hips=(0, 0, 10), spine=(12, 0, 12), chest=(5, 0, 38), head=(-8, 0, -28),
               upper_arm=((10, -20, 20), (-15, -62, -85)), forearm=((-30, 0, 0), (-18, 0, 0)), hand=((0, 0, 0), (65, 0, 0)),
               coat_tail=((35, 0, 0), (15, 0, 0)))
    thru = over(hit, hips=(0, 0, 12), spine=(14, 0, 16), chest=(8, 0, 46), head=(-8, 0, -32),
                upper_arm=((30, -12, 20), (-5, -45, -102)), forearm=((-35, 0, 0), (-35, 0, 0)), hand=((0, 0, 0), (55, 0, 0)),
                coat_tail=((40, 0, 0), (10, 0, 0)), topknot=(0, 0, -15))
    K("slash", [(0, BASE), (2, wind), (4, mid), (5, hit), (7, thru), (10, mix(thru, BASE, 0.45))])

    # air_slash 0.33 s: overhead -> downward arc while airborne
    air = pose(hips_loc=(0, 0, 0.02), thigh=((-50, 0, 0), (-25, 0, 0)), shin=((80, 0, 0), (70, 0, 0)),
               foot=(10, 0, 0), coat_tail=(40, 0, 0), upper_arm=((-40, -40, 0), (-60, 5, 0)),
               forearm=((-30, 0, 0), (-40, 0, 0)), hand=((0, 0, 0), (30, 0, 0)))
    up = over(air, spine=(-12, 0, 0), chest=(-8, 0, -10), head=(-10, 0, 0), upper_arm=((-40, -55, 0), (-172, -10, 0)),
              forearm=((-20, 0, 0), (-55, 0, 0)), hand=((0, 0, 0), (10, 0, 0)), coat_tail=(55, 0, 0), topknot=(-12, 0, 0))
    down = over(air, spine=(26, 0, 0), chest=(14, 0, 6), head=(4, 0, 0), upper_arm=((20, -45, 0), (-58, -5, 0)),
                forearm=((-30, 0, 0), (-5, 0, 0)), hand=((0, 0, 0), (45, 0, 0)), coat_tail=(20, 0, 0), topknot=(14, 0, 0))
    deeper = over(down, spine=(32, 0, 0), upper_arm=((25, -45, 0), (-22, -5, 0)), forearm=((-30, 0, 0), (-12, 0, 0)),
                  hand=((0, 0, 0), (55, 0, 0)))
    K("air_slash", [(0, air), (2, up), (5, down), (7, deeper), (10, mix(deeper, air, 0.4))])

    # cast 0.4 s: chamber, then thrust the cutlass forward (wind crescent release)
    cham = pose(hips_loc=(0, 0, -0.04), spine=(10, 0, -10), chest=(5, 0, -30), head=(-8, 0, 28),
                thigh=((-30, 0, 0), (15, 0, 0)), shin=((40, 0, 0), (25, 0, 0)), foot=((-10, 0, 0), (-30, 0, 0)),
                upper_arm=((-55, -25, 0), (25, -10, 25)), forearm=((-20, 0, 0), (-100, 0, 0)), hand=((0, 0, 0), (40, 0, 0)),
                coat_tail=(12, 0, 0))
    thrust = pose(hips_loc=(0, 0, -0.06), spine=(15, 0, 10), chest=(8, 0, 25), head=(-12, 0, -22),
                  thigh=((-50, 0, 0), (25, 0, 0)), shin=((55, 0, 0), (15, 0, 0)), foot=((-5, 0, 0), (-25, 0, 0)),
                  upper_arm=((35, -20, 10), (-88, 5, -15)), forearm=((-30, 0, 0), (-5, 0, 0)), hand=((0, 0, 0), (55, 0, 0)),
                  coat_tail=((35, 0, 0), (45, 0, 0)), topknot=(-14, 0, 0))
    hold = over(thrust, upper_arm=((38, -20, 10), (-92, 5, -18)), chest=(8, 0, 28))
    K("cast", [(0, BASE), (3, cham), (6, thrust), (8, hold), (12, mix(hold, BASE, 0.6))])

    # hurt 0.25 s: snap back recoil
    rec = pose(hips_loc=(0, 0.02, -0.01), spine=(-18, 0, 8), chest=(-12, 0, 6), head=(-25, 0, 10),
               upper_arm=((15, -45, 0), (10, -40, 0)), forearm=((-20, 0, 0), (-30, 0, 0)), hand=((0, 0, 0), (30, 0, 0)),
               thigh=(-5, 0, 0), shin=(15, 0, 0), foot=(-10, 0, 0), coat_tail=(-15, 0, 0), topknot=(15, 0, 0))
    K("hurt", [(0, BASE), (2, rec), (5, mix(rec, BASE, 0.5)), (8, BASE)])

    # death 0.9 s: recoil -> knees buckle -> topple forward -> hold
    rec2 = over(rec, spine=(-25, 0, 10), chest=(-15, 0, 8), head=(-30, 0, 12))
    kneel = pose(hips_loc=(0, 0, -0.33), hips=(10, 0, 0), spine=(15, 0, 0), chest=(10, 0, 0), head=(25, 0, 0),
                 thigh=(-10, -4, 0), shin=(95, 0, 0), foot=(20, 0, 0),
                 upper_arm=((5, 10, 0), (5, 10, 0)), forearm=(-10, 0, 0), hand=((0, 0, 0), (10, 0, 0)), coat_tail=(-5, 0, 0))
    topple = pose(hips_loc=(0, -0.12, -0.45), hips=(55, 0, 0), spine=(8, 0, 0), head=(5, 0, 20),
                  thigh=(-30, -4, 0), shin=(70, 0, 0), foot=(30, 0, 0),
                  upper_arm=((-60, -20, 0), (-60, -20, 0)), forearm=(-20, 0, 0), hand=((0, 0, 0), (10, 0, 0)),
                  coat_tail=(-20, 0, 0), topknot=(20, 0, 0))
    flat = pose(hips_loc=(0, -0.15, -0.585), hips=(86, 0, 0), head=(-25, 0, 70),
                thigh=(-2, -6, 0), shin=(12, 0, 0), foot=(50, 0, 0),
                upper_arm=((-110, -40, 0), (-100, -45, 0)), forearm=(-20, 0, 0), hand=((0, 0, 0), (10, 0, 0)),
                coat_tail=(-10, 0, 0), topknot=(25, 0, 0))
    settle = over(flat, hips_loc=(0, -0.15, -0.58), head=(-22, 0, 72), topknot=(18, 0, 0))
    K("death", [(0, BASE), (5, rec2), (12, kneel), (20, topple), (24, flat), (27, settle)])

    # interact 0.4 s: reach forward with the free (left) hand
    reach = over(BASE, spine=(22, 0, -4), chest=(8, 0, -6), head=(-15, 0, 0), upper_arm_L=(-80, 5, -10),
                 forearm_L=(-10, 0, 0), upper_arm_R=(-10, 12, 0), forearm_R=(-30, 0, 0),
                 thigh=((-25, -3, 0), (-12, -3, 0)), shin=((32, 0, 0), (34, 0, 0)), coat_tail=(14, 0, 0))
    K("interact", [(0, BASE), (4, reach), (8, over(reach, upper_arm_L=(-86, 5, -10))), (12, BASE)])

    # victory 1.2 s: crouch, spring up with the cutlass raised, left fist pumps twice
    ant = pose(hips_loc=(0, 0, -0.08), spine=(20, 0, 0), chest=(6, 0, 0), head=(-10, 0, 0),
               thigh=(-28, 0, 0), shin=(56, 0, 0), foot=(-28, 0, 0),
               upper_arm=((30, 5, 0), (30, 5, 0)), forearm=((-40, 0, 0), (-40, 0, 0)), hand=((0, 0, 0), (30, 0, 0)))
    upv = pose(hips_loc=(0, 0, 0.03), spine=(-12, 0, 0), chest=(-8, 0, 0), head=(-20, 0, 0),
               thigh=(0, -3, 0), shin=(0, 0, 0), foot=(25, 0, 0),
               upper_arm=((-50, -35, 0), (-170, -15, 0)), forearm=((-120, 0, 0), (-10, 0, 0)), hand=((0, 0, 0), (55, 0, 0)),
               coat_tail=(-10, 0, 0), topknot=(10, 0, 0))
    pump_dn = over(upv, hips_loc=(0, 0, -0.02), thigh=(-12, -3, 0), shin=(24, 0, 0), foot=(-12, 0, 0), spine=(-4, 0, 0),
                   upper_arm_L=(-28, -30, 0), forearm_L=(-135, 0, 0), coat_tail=(15, 0, 0), topknot=(-10, 0, 0))
    pump_up = over(upv, upper_arm_L=(-62, -35, 0), forearm_L=(-110, 0, 0), head=(-25, 0, 0), hips_loc=(0, 0, 0.01))
    K("victory", [(0, BASE), (6, ant), (11, upv), (16, pump_dn), (21, pump_up), (28, pump_up),
                  (36, over(pump_up, hips_loc=(0, 0, 0.0), chest=(-6, 0, 0)))])
    return acts


# ----------------------------------------------------------------------------- main
def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = H.FPS
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PREV, exist_ok=True)

    img = PAL.image("kito_palette", PAL_PNG)
    mat = PAL.material("kito_mat", img)
    arm = H.build_armature(BONES)

    parts = []
    build_head(parts)
    build_hair(parts)
    build_body(parts)
    build_coat(parts)
    build_arms(parts)
    body = H.build_body("Kito", parts, PAL, mat, arm, BONES)
    sword = H.bone_attached_mesh("Cutlass", build_cutlass(), PAL, mat, arm, "hand.R")

    acts = build_actions(arm)
    H.reset_pose(arm)
    arm.animation_data.action = acts["idle"]
    sc.frame_start, sc.frame_end, sc.frame_current = 0, 48, 0

    bt, st = H.tri_count(body), H.tri_count(sword)
    zs = [v.co.z for v in body.data.vertices]
    print(f"[kito] body tris={bt} cutlass tris={st} total={bt + st} materials={len(bpy.data.materials)} "
          f"height={max(zs) - min(zs):.3f}")
    for n, a in acts.items():
        print(f"[kito] action {n}: frames {a.frame_range[0]:.0f}-{a.frame_range[1]:.0f} "
              f"({(a.frame_range[1] - a.frame_range[0]) / H.FPS:.2f}s)")

    H.export_glb(GLB, [arm, body, sword])
    print("[kito] exported", GLB)

    if "--no-render" not in ARGS:
        render_previews(arm, acts)
    H.reset_pose(arm)
    arm.animation_data.action = acts["idle"]
    bpy.context.preferences.filepaths.save_version = 0  # no kito.blend1 backups
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("[kito] saved", BLEND)


def render_previews(arm, acts):
    sc = bpy.context.scene
    cam = H.setup_render((720, 960))
    H.reset_pose(arm)
    for name, yaw in (("front", 0), ("side", 90), ("back", 180), ("3q", 40)):
        H.render_view(os.path.join(PREV, f"kito_{name}.png"), cam, yaw)
    H.render_view(os.path.join(PREV, "kito_face.png"), cam, 20, target=(0, 0, 1.27), scale=0.42)
    shots = [("idle", 0), ("run", 0), ("run", 4), ("jump", 3), ("jump", 9), ("fall", 0), ("land", 2),
             ("slash", 2), ("slash", 5), ("slash", 7), ("air_slash", 2), ("air_slash", 5), ("cast", 6),
             ("hurt", 2), ("death", 27), ("interact", 6), ("victory", 11), ("victory", 21)]
    sc.render.resolution_x, sc.render.resolution_y = 360, 480
    paths = []
    for name, f in shots:
        arm.animation_data.action = acts[name]
        sc.frame_set(f)
        p = os.path.join(PREV, "_tmp", f"{name}_{f:02d}.png")
        H.render_view(p, cam, 35, target=(0, 0, 0.74), scale=2.25, pitch_deg=84)
        paths.append(p)
    H.contact_sheet(paths, os.path.join(PREV, "kito_poses.png"), 6)
    sc.render.resolution_x, sc.render.resolution_y = 720, 960
    for name, f, fn in (("slash", 5, "kito_pose_slash.png"), ("run", 0, "kito_pose_run.png"),
                        ("victory", 21, "kito_pose_victory.png")):
        arm.animation_data.action = acts[name]
        sc.frame_set(f)
        H.render_view(os.path.join(PREV, fn), cam, 35, target=(0, 0, 0.78), scale=1.85, pitch_deg=82)
    import shutil
    shutil.rmtree(os.path.join(PREV, "_tmp"), ignore_errors=True)


main()
