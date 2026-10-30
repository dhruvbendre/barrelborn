"""Build the Powder Gull (ranged gunner enemy): mesh + rig + 7 clips + GLB + previews.

Run (from anywhere):
  blender -b --factory-startup --python tools/blender/build_gunner.py [-- --no-render]
"""
import math
import os
import sys

import bpy  # noqa: F401
from mathutils import Vector as V, Matrix

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import humanoid as H  # noqa: E402
from humanoid import smoothstep as ss  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
H.PAIRED.add("coat_tail")

PAL = H.Palette({
    "navy": "#2a3350", "navy_dk": "#1a2036", "navy_lt": "#3d4a74", "trim": "#b8913f",
    "brass": "#c9a23f", "brass_dk": "#86681f", "hat": "#b48a5a", "hat_dk": "#8a6538", "hat_band": "#4a3324",
    "feather": "#f2f0ea", "feather_dk": "#a7b0ba", "feather_tip": "#2b2e33",
    "skin": "#d9b48f", "skin_dk": "#b08462", "nose": "#d6957a", "hair": "#3b3631", "hair_dk": "#25211e",
    "eye_white": "#f4efdc", "iris": "#e3bd2f", "iris_dk": "#9a7414", "pupil": "#14100c", "lash": "#120d0b",
    "white": "#ffffff", "mouth": "#4a1d1a", "shirt": "#e2d8bf", "shirt_dk": "#bfb396",
    "trousers": "#4a4c57", "boot": "#2f2622", "boot_dk": "#1c1614", "boot_lt": "#4a3a31",
    "leather": "#6a4329", "leather_dk": "#4a2e1c", "horn": "#e6d6b0", "horn_dk": "#b59f72",
    "wood": "#6b4126", "wood_dk": "#4a2c19", "wood_lt": "#8a5a36",
    "iron": "#4a4d55", "iron_dk": "#1e2024", "iron_lt": "#8e939c",
})

# ----------------------------------------------------------------------------- layout (2.0 m incl. hat)
D_ARM = V((0.40, 0.0, -0.916)).normalized()
J = dict(hips=(0, 0, 0.97), spine=(0, 0, 1.10), chest=(0, 0, 1.24), neck=(0, 0.01, 1.42),
         head=(0, 0.01, 1.50), head_top=(0, 0.01, 1.78), shoulder=(0.03, 0, 1.38), arm=(0.16, 0, 1.37),
         hip=(0.075, 0, 0.95), knee=(0.08, -0.005, 0.50), ankle=(0.085, 0.01, 0.08), toe=(0.09, -0.15, 0.02))
J["elbow"] = V(J["arm"]) + D_ARM * 0.31
J["wrist"] = J["elbow"] + D_ARM * 0.29
J["hand_end"] = J["wrist"] + D_ARM * 0.09
EXTRAS = [("coat_tail.L", (0.07, 0.10, 1.0), (0.13, 0.17, 0.45), "hips"),
          ("coat_tail.R", (-0.07, 0.10, 1.0), (-0.13, 0.17, 0.45), "hips")]
BONES = H.standard_skeleton(J, EXTRAS)
SZ = 0.9  # fist size

HC, HR = V((0, 0.005, 1.625)), (0.094, 0.10, 0.13)
HEAD = H.head_shape(HC, HR, jaw=0.5, jaw_front=0.02, jaw_back=0.45, jaw_z=0.98)
lerp = H.lerp


def side_fn(s, fn):
    return fn if s > 0 else (lambda v: fn(V((-v.x, v.y, v.z))))


def hand_rest(S):
    """Rest frame of a fist: a along the hand bone, g grip axis (forward), p palm normal, wrist position."""
    s = 1 if S == "L" else -1
    a = V((D_ARM.x * s, 0, D_ARM.z))
    g = V((0, -1, 0))
    p = a.cross(g) if S == "L" else g.cross(a)
    w = V(J["wrist"])
    return a, g, p, V((w.x * s, w.y, w.z))


# ----------------------------------------------------------------------------- head
def build_head(parts):
    hp = H.Part(["head"])
    H.sphere(hp, HEAD, 18, 12, "skin")
    nf = len(hp.f)
    # lank hair at the back/sides below the hat line
    hp.recolor(0, lambda c, n: "hair" if (c.z > 1.585 and c.y > 0.005) or (c.z > 1.665 and abs(c.x) > 0.055) else None)
    bvh = hp.bvh(0, nf)
    O, R, U = H.FACE
    for s in (1, -1):
        H.anime_eye(hp, bvh, 0.037, 1.634, s, k=0.72, iris="iris", iris_dk="iris_dk", brow="hair_dk",
                    brow_spec=(0.046, 0.028, 0.02), lid=0.4, lid_tilt=0.75)
        # thin drooping mustache
        top = [(0.004 * s, 1.561), (0.018 * s, 1.559), (0.031 * s, 1.551), (0.041 * s, 1.535)]
        bot = [(0.004 * s, 1.554), (0.018 * s, 1.552), (0.029 * s, 1.546), (0.039 * s, 1.535)]
        if s < 0:
            top, bot = top[::-1], bot[::-1]
        H.decal_strip(hp, bvh, O, R, U, top, bot, "hair_dk", 0.003)
    # sly lopsided smirk (his left corner hooks up)
    xs = [-0.022 + 0.048 * k / 8 for k in range(9)]
    zc = lambda x: 1.532 + 0.011 * max(0.0, x / 0.026) ** 2 - 0.002 * max(0.0, -x / 0.022)
    H.decal_strip(hp, bvh, O, R, U, [(x, zc(x) + 0.0025) for x in xs], [(x, zc(x) - 0.0022) for x in xs], "mouth", 0.002)
    # long hooked gull-beak nose
    pts = [(0, -0.078, 1.648), (0, -0.106, 1.618), (0, -0.13, 1.592), (0, -0.141, 1.574), (0, -0.135, 1.561)]
    H.tube(hp, pts, [(0.009, 0.010), (0.011, 0.012), (0.011, 0.011), (0.008, 0.008), (0.005, 0.005)], 8,
           lambda i, j: "nose" if i >= 2 else "skin", hint=V((1, 0, 0)), cap1=V((0, -0.125, 1.555)))
    # pointed goatee: a downward wedge
    H.tube(hp, [(0, -0.048, 1.515), (0, -0.064, 1.48), (0, -0.07, 1.452)], [(0.017, 0.012), (0.011, 0.008), (0.005, 0.004)],
           6, "hair_dk", hint=V((1, 0, 0)), cap0="center", cap1=V((0, -0.068, 1.425)))
    for s in (1, -1):
        H.ellipsoid(hp, (0.093 * s, 0.012, 1.622), (0.011, 0.02, 0.03), 6, 4, "skin")
    # stringy locks hanging under the hat
    for k, deg in enumerate((75, 105, 140, 180, 220, 255, 285)):
        ph = math.radians(deg)
        o = V((math.sin(ph), -math.cos(ph), 0))
        path = [HC + V((o.x * r, o.y * r + 0.005, z - HC.z)) for r, z in
                ((0.078, 1.70), (0.098, 1.62), (0.108, 1.545), (0.112 + 0.01 * (k % 2), 1.49 - 0.02 * (k % 3)))]
        H.tube(hp, path, [(0.009, 0.026), (0.009, 0.026), (0.008, 0.022), (0.006, 0.014)], 4,
               "hair_dk" if k % 2 else "hair", hint=o, cap1="center")
    parts.append(hp)


def build_hat(parts):
    hp = H.Part(["head"])
    z0 = 1.70
    ctr = V((0, 0.012, z0))
    nu = 20

    def brim_pt(r, ph, dz=0.0):
        t = (r - 0.09) / 0.16
        droop = (0.07 - 0.035 * math.cos(2 * ph) + 0.012 * math.sin(5 * ph + 0.5)) * t * t
        return ctr + V((r * math.sin(ph), -r * 1.04 * math.cos(ph), -droop + dz))
    phs = [2 * math.pi * j / nu for j in range(nu)]
    radii = [0.09, 0.16, 0.25]
    rings = [[brim_pt(r, p) for p in phs] for r in radii]
    rings += [[brim_pt(r, p, -0.012) for p in phs] for r in radii[::-1]]
    H.loft(hp, rings, lambda i, j: "hat" if i < 2 else ("hat_dk" if i > 2 else "hat_band"), wrap_path=True)
    # slumped crown with a front-to-back crease, tip flopping back-left
    crown = []
    for k, (h, rx, ry) in enumerate(((0.0, 0.108, 0.118), (0.025, 0.106, 0.116), (0.06, 0.098, 0.108),
                                     (0.095, 0.082, 0.092), (0.13, 0.04, 0.055))):
        t = h / 0.13
        c = ctr + V((0.012 * t * t, 0.02 * t * t, h))
        rr = []
        for p in phs:
            x, y = math.sin(p), -math.cos(p)
            dent = 0.03 * t * t * math.exp(-(x / 0.35) ** 2)
            rr.append(c + V((rx * x, ry * y, -dent)))
        crown.append(rr)
    H.loft(hp, crown, lambda i, j: "hat_band" if i == 0 else "hat", cap1=ctr + V((0.012, 0.02, 0.105)))
    # band bump + gull feather tucked on his left, sweeping up and back
    H.tube(hp, [ctr + V((0.104, 0.0, 0.012)), ctr + V((0.11, 0.02, 0.016))], [0.016, 0.014], 6, "brass",
           hint=V((0, 0, 1)), cap0="center", cap1="center")
    fp = [ctr + V(p) for p in ((0.105, 0.02, 0.02), (0.13, 0.07, 0.11), (0.13, 0.13, 0.21), (0.11, 0.18, 0.28),
                               (0.09, 0.205, 0.31))]
    H.tube(hp, fp[:-1], [(0.004, 0.012), (0.005, 0.028), (0.005, 0.032), (0.004, 0.02)], 6,
           lambda i, j: "feather_tip" if i >= 2 else ("feather_dk" if j in (0, 3) else "feather"),
           hint=V((1, 0, 0)), cap1=fp[-1])
    # rakish tilt toward his left, slightly back
    M = Matrix.Translation(ctr) @ Matrix.Rotation(math.radians(7), 4, "Y") @ \
        Matrix.Rotation(math.radians(-3), 4, "X") @ Matrix.Translation(-ctr)
    hp.v = [M @ v for v in hp.v]
    parts.append(hp)


# ----------------------------------------------------------------------------- body
TORSO = [(0.90, 0.05, 0.05, 0.0), (0.93, 0.10, 0.074, 0.004), (0.98, 0.11, 0.078, 0.004), (1.05, 0.104, 0.074, 0.0),
         (1.12, 0.10, 0.072, 0.0), (1.22, 0.114, 0.078, 0.0), (1.30, 0.124, 0.08, 0.0), (1.36, 0.124, 0.078, 0.004),
         (1.40, 0.10, 0.064, 0.008), (1.43, 0.05, 0.045, 0.008)]


def prof(table, z):
    for a, b in zip(table, table[1:]):
        lo, hi = sorted((a[0], b[0]))
        if lo <= z <= hi:
            t = (z - a[0]) / (b[0] - a[0])
            return tuple(lerp(a[k], b[k], t) for k in range(1, len(a)))
    return table[-1][1:]


def vring(z, rx, ry, yoff, n, cx=0.0):
    return H.ring((cx, yoff, z), (0, 0, 1), rx, ry, n, hint=V((1, 0, 0)))


def build_body(parts):
    nk = H.Part(["chest", "neck", ("head", lambda v: ss(1.48, 1.52, v.z))])
    H.tube(nk, [(0, 0.012, 1.40), (0, 0.01, 1.47), (0, 0.008, 1.545)], [0.034, 0.031, 0.034], 10, "skin")
    parts.append(nk)
    sh = lambda s: (lambda v: ss(1.32, 1.38, v.z) * ss(0.02 * s, 0.08 * s, v.x))
    th = lambda s: (lambda v: ss(1.0, 0.92, v.z) * ss(0.0, 0.05 * s, v.x))
    tp = H.Part(["hips", "spine", "chest", ("neck", lambda v: ss(1.40, 1.43, v.z)),
                 ("shoulder.L", sh(1)), ("shoulder.R", sh(-1)), ("thigh.L", th(1)), ("thigh.R", th(-1))])
    rows = [vring(z, rx, ry, yo, 12) for z, rx, ry, yo in TORSO]
    H.loft(tp, rows, lambda i, j: "trousers" if 0 <= i < len(rows) - 1 and TORSO[i][0] < 1.04 else "shirt",
           True, V((0, 0, 0.89)), V((0, 0.008, 1.435)))
    parts.append(tp)
    # cravat ruffle
    cv = H.Part(["chest", ("neck", lambda v: 0.5)])
    H.ellipsoid(cv, (0, -0.05, 1.415), (0.03, 0.02, 0.022), 6, 4, "shirt")
    H.ellipsoid(cv, (0, -0.066, 1.38), (0.024, 0.016, 0.032), 6, 4, "shirt_dk")
    H.ellipsoid(cv, (0, -0.074, 1.345), (0.018, 0.012, 0.024), 6, 4, "shirt")
    parts.append(cv)
    # belt + buckle (shows in the coat opening)
    bp = H.Part(["hips", "spine"])
    brows = []
    for z, dr in ((1.04, 0.003), (1.046, 0.009), (1.084, 0.009), (1.09, 0.003)):
        rx, ry, yo = prof(TORSO, z)
        brows.append(vring(z, rx + dr, ry + dr, yo, 12))
    H.loft(bp, brows, "leather_dk")
    rx, ry, yo = prof(TORSO, 1.065)
    H.ellipsoid(bp, (0, yo - ry - 0.012, 1.065), (0.022, 0.006, 0.019), 8, 5, "brass", exp=0.35)
    H.ellipsoid(bp, (0, yo - ry - 0.016, 1.065), (0.012, 0.004, 0.009), 6, 4, "leather_dk", exp=0.35)
    parts.append(bp)

    for s in (1, -1):
        S = "L" if s > 0 else "R"
        X = lambda p: V((p[0] * s, p[1], p[2]))
        lp = H.Part(["hips", f"thigh.{S}", (f"shin.{S}", lambda v: 0.5 * ss(0.56, 0.48, v.z))])
        H.tube(lp, [X(p) for p in ((0.072, 0, 1.0), (0.077, -0.002, 0.85), (0.079, -0.004, 0.68),
                                   (0.08, -0.005, 0.52), (0.081, -0.005, 0.46))],
               [0.068, 0.06, 0.052, 0.047, 0.045], 10, "trousers", hint=V((s, 0, 0)))
        parts.append(lp)
        # tall boots with a folded cuff over the knee
        bt = H.Part([f"shin.{S}", (f"thigh.{S}", lambda v: ss(0.49, 0.53, v.z)), (f"foot.{S}", lambda v: ss(0.13, 0.06, v.z))])
        kn, an = V(J["knee"]), V(J["ankle"])
        rings = []
        for z, r in ((0.07, 0.048), (0.15, 0.047), (0.28, 0.05), (0.40, 0.052), (0.46, 0.054), (0.465, 0.064),
                     (0.50, 0.067), (0.522, 0.062), (0.523, 0.042)):
            c = kn.lerp(an, (kn.z - z) / (kn.z - an.z))
            rings.append(vring(z, r, r * 0.95, c.y, 10, c.x * s))
        H.loft(bt, rings, lambda i, j: "boot_lt" if i >= 4 else "boot")
        f0, v0 = len(bt.f), len(bt.v)
        H.ellipsoid(bt, (0.087 * s, -0.05, 0.045), (0.05, 0.125, 0.047), 10, 6, "boot")
        for k in range(v0, len(bt.v)):
            p = bt.v[k]
            if p.y < -0.08:  # pointed, slightly upturned toe
                t = (-0.08 - p.y) / 0.095
                p.x = 0.087 * s + (p.x - 0.087 * s) * (1 - 0.45 * t)
                p.z += 0.25 * (-0.08 - p.y) ** 1.5
            p.z = max(p.z, 0.0)
        bt.recolor(f0, lambda c, n: "boot_dk" if c.z < 0.012 else None)
        parts.append(bt)


# ----------------------------------------------------------------------------- coat
COAT = [(1.445, 0.072, 0.066, 0.008, 0.62), (1.425, 0.105, 0.08, 0.008, 0.55), (1.395, 0.165, 0.098, 0.008, 0.46),
        (1.355, 0.182, 0.104, 0.008, 0.40), (1.30, 0.165, 0.10, 0.01, 0.32), (1.23, 0.142, 0.094, 0.01, 0.28),
        (1.16, 0.127, 0.089, 0.012, 0.32), (1.10, 0.125, 0.089, 0.014, 0.38), (1.02, 0.14, 0.10, 0.016, 0.44),
        (0.92, 0.157, 0.116, 0.02, 0.50), (0.80, 0.172, 0.13, 0.024, 0.57), (0.62, 0.189, 0.145, 0.029, 0.63),
        (0.42, 0.202, 0.158, 0.035, 0.68), (0.41, 0.203, 0.159, 0.035, 0.68)]


def coat_pt(z, rx, ry, yo, phi):
    return V((rx * math.sin(phi), yo - ry * math.cos(phi), z))


def coat_spec():
    def thigh(s):
        return side_fn(s, lambda v: ss(0.95, 0.75, v.z) * ss(0.08, -0.06, v.y) * ss(-0.05, 0.05, v.x))

    def tail(s):
        return side_fn(s, lambda v: ss(1.0, 0.82, v.z) * ss(-0.06, 0.06, v.y) * ss(-0.06, 0.04, v.x))

    def shoulder(s):
        return side_fn(s, lambda v: ss(0.03, 0.12, v.x) * ss(1.30, 1.37, v.z))

    def uarm(s):
        return side_fn(s, lambda v: 0.6 * ss(0.13, 0.18, v.x) * ss(1.28, 1.34, v.z))
    spec = ["hips", "spine", "chest", ("neck", lambda v: ss(1.42, 1.45, v.z))]
    for s, S in ((1, "L"), (-1, "R")):
        spec += [(f"shoulder.{S}", shoulder(s)), (f"upper_arm.{S}", uarm(s)),
                 (f"thigh.{S}", thigh(s)), (f"coat_tail.{S}", tail(s))]
    return spec


def build_coat(parts):
    cp = H.Part(coat_spec())
    N = 14
    P = []
    for z, rx, ry, yo, al in COAT:
        dl = 0.014 / rx
        phis = [al, al + dl] + [lerp(al + dl, 2 * math.pi - al - dl, k / (N - 1)) for k in range(1, N - 1)] \
            + [2 * math.pi - al - dl, 2 * math.pi - al]
        P.append([coat_pt(z, rx, ry, yo, p) for p in phis])
    R, C = len(P), len(P[0])
    H.sheet(cp, P, 0.01, lambda r, c: "trim" if (c in (0, C - 2) or r == R - 2) else "navy",
            "navy_dk", dict(top="navy_dk", bottom="trim", left="trim", right="trim"))
    # brass buttons down both front edges
    for z in (1.31, 1.23, 1.15):
        rx, ry, yo, al = prof(COAT, z)
        for phi in (al + 0.2, 2 * math.pi - al - 0.2):
            p = coat_pt(z, rx, ry, yo, phi)
            nrm = V((math.sin(phi) / rx, -math.cos(phi) / ry, 0)).normalized()
            H.ellipsoid(cp, p + nrm * 0.006, (0.009, 0.009, 0.009), 6, 3, "brass")
    parts.append(cp)
    # tall popped collar, open at the front
    cl = H.Part(["chest", ("neck", lambda v: 0.6)])
    Pc = []
    for z, rx, ry, yo, al in ((1.535, 0.098, 0.094, 0.016, 0.95), (1.505, 0.088, 0.084, 0.013, 0.85),
                              (1.47, 0.077, 0.072, 0.01, 0.75), (1.44, 0.072, 0.066, 0.008, 0.66)):
        Pc.append([coat_pt(z, rx, ry, yo, lerp(al, 2 * math.pi - al, k / 11)) for k in range(12)])
    H.sheet(cl, Pc, 0.009, lambda r, c: "trim" if r == 0 else "navy", "navy_dk",
            dict(top="trim", bottom="navy_dk", left="trim", right="trim"))
    parts.append(cl)
    # bandolier over the coat (left shoulder -> right hip) + powder horn on the right hip
    st = H.Part(["hips", "spine", "chest", ("shoulder.L", lambda v: ss(1.3, 1.4, v.z) * ss(0.05, 0.12, v.x))])
    rings = []
    for k in range(16):
        th = 2 * math.pi * k / 16
        z = 1.22
        for _ in range(3):
            rx, ry, yo, _al = prof(COAT, z)
            z = 1.22 + 1.05 * rx * math.sin(th)
        rx, ry, yo, _al = prof(COAT, z)
        c = coat_pt(z, rx + 0.012, ry + 0.012, yo, th)
        out = V((math.sin(th), -math.cos(th), 0))
        t = V((math.cos(th) * rx, math.sin(th) * ry, 1.05 * rx * math.cos(th))).normalized()
        rings.append(H.ring(c, t, 0.004, 0.022, 4, hint=out))
    H.loft(st, rings, "leather", wrap_path=True)
    parts.append(st)
    hn = H.Part(["hips", ("spine", lambda v: 0.4)])
    hpth = [V(p) for p in ((-0.176, -0.03, 1.03), (-0.19, -0.075, 0.99), (-0.185, -0.11, 0.94), (-0.165, -0.125, 0.905))]
    H.tube(hn, hpth[:-1], [0.03, 0.022, 0.012], 6, lambda i, j: "horn_dk" if i == 0 else "horn",
           hint=V((1, 0, 0)), cap1=hpth[-1])
    H.tube(hn, [hpth[0] + V((0, 0.012, 0.012)), hpth[0] + V((0.0, 0.03, 0.03))], [0.032, 0.026], 6, "brass",
           hint=V((1, 0, 0)), cap0="center", cap1="center")
    parts.append(hn)


# ----------------------------------------------------------------------------- arms
def fist(part, wrist, a, g, p, color, size=1.0):
    """Low-poly H.fist (enemy budget): palm block + knuckle ridge + thumb."""
    a, g, p = V(a).normalized(), V(g).normalized(), V(p).normalized()
    B = H.axes(g, p, a)
    c = V(wrist) + a * 0.044 * size
    H.ellipsoid(part, c, (0.045 * size, 0.037 * size, 0.047 * size), 8, 6, color, B, exp=0.8)
    H.ellipsoid(part, c + a * (0.03 * size) - p * (0.02 * size), (0.047 * size, 0.016 * size, 0.017 * size), 8, 4, color, B)
    H.ellipsoid(part, c + p * (0.026 * size) + g * (0.03 * size) - a * (0.004 * size),
                (0.026 * size, 0.014 * size, 0.016 * size), 6, 4, color, B)


def build_arms(parts):
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        d = V((D_ARM.x * s, 0, D_ARM.z))
        sj = V((J["arm"][0] * s, J["arm"][1], J["arm"][2]))
        at = lambda u: sj + d * u
        sp = H.Part([f"shoulder.{S}", f"upper_arm.{S}", f"forearm.{S}", (f"hand.{S}", lambda v: 0.15)])
        us = [-0.01, 0.03, 0.10, 0.20, 0.31, 0.42, 0.49, 0.50, 0.53, 0.565, 0.575, 0.58]
        rs = [0.042, 0.05, 0.047, 0.043, 0.041, 0.039, 0.037, 0.05, 0.055, 0.054, 0.05, 0.034]
        fc = ["navy"] * 6 + ["navy_dk", "trim", "navy_lt", "navy_lt", "trim"]
        H.tube(sp, [at(u) for u in us], rs, 10, lambda i, j: fc[min(max(i, 0), len(fc) - 1)], hint=V((0, -1, 0)))
        parts.append(sp)
        wp = H.Part([f"forearm.{S}", f"hand.{S}"])
        H.tube(wp, [at(u) for u in (0.54, 0.585, 0.62)], [0.026, 0.024, 0.023], 8, "skin", hint=V((0, -1, 0)))
        parts.append(wp)
        a, g, p, w = hand_rest(S)
        hp = H.Part([f"hand.{S}", (f"forearm.{S}", lambda v: 0.2)])
        fist(hp, w, a, g, p, "skin", size=SZ)
        parts.append(hp)


def build_parts():
    parts = []
    build_head(parts)
    build_hat(parts)
    build_body(parts)
    build_coat(parts)
    build_arms(parts)
    return parts


# ----------------------------------------------------------------------------- musket (Weapon on hand.R)
def musket():
    a, g, p, w = hand_rest("R")
    c0 = w + a * 0.044 * SZ
    f, U = g, p           # barrel axis = grip axis, gun top = palm side
    S = f.cross(U)        # gun's right side (lock side)
    m = H.Part(["hand.R"], smooth=True)
    P = lambda t, u=0.0, s=0.0: c0 + f * t + U * u + S * s
    # stock: butt plate -> wrist (through the fist) -> lock -> fore-stock
    st = [(-0.36, -0.045, 0.062, 0.022), (-0.335, -0.043, 0.064, 0.023), (-0.22, -0.03, 0.052, 0.021),
          (-0.12, -0.012, 0.03, 0.019), (-0.06, -0.004, 0.02, 0.017), (0.0, 0.0, 0.019, 0.016),
          (0.06, 0.008, 0.028, 0.018), (0.15, 0.008, 0.024, 0.017), (0.32, 0.01, 0.02, 0.016),
          (0.80, 0.012, 0.016, 0.014), (0.84, 0.014, 0.011, 0.011)]
    rings = [H.ring(P(t, u), f, h, wd, 6, hint=U) for t, u, h, wd in st]
    H.loft(m, rings, lambda i, j: "brass" if i <= 0 else ("wood_dk" if j in (2, 3, 4) and i < 4 else "wood"),
           True, "center", "center")
    # barrel with a dark bore, bands, front sight
    H.tube(m, [P(t, 0.028) for t in (0.02, 0.5, 1.10, 1.115, 1.15)], [0.012, 0.011, 0.0105, 0.0135, 0.0135], 6,
           lambda i, j: "iron_dk" if i >= 5 else ("iron_lt" if j == 1 else "iron"), hint=U, cap0="center",
           cap1=P(1.13, 0.028))
    for t in (0.46, 0.78):
        H.tube(m, [P(t - 0.012, 0.016), P(t + 0.012, 0.016)], [(0.03, 0.019)] * 2, 6, "brass", hint=U,
               cap0="center", cap1="center")
    H.ellipsoid(m, P(1.10, 0.042), (0.004, 0.004, 0.005), 6, 4, "brass")
    H.tube(m, [P(0.78, -0.002), P(1.09, 0.008)], [0.0045, 0.0045], 6, "wood_lt", hint=U, cap0="center",
           cap1="center")
    # flintlock: plate, cock (hammer) with flint, frizzen
    B = H.axes(f, U, S)
    H.ellipsoid(m, P(0.085, 0.01, 0.018), (0.05, 0.015, 0.004), 8, 4, "iron_lt", B, exp=0.4)
    cock = [P(0.05, 0.012, 0.02), P(0.035, 0.04, 0.021), P(0.045, 0.06, 0.021), P(0.07, 0.066, 0.021)]
    H.tube(m, cock, [0.0065, 0.006, 0.0055, 0.005], 6, "iron", hint=S, cap0="center", cap1="center")
    H.ellipsoid(m, P(0.078, 0.062, 0.021), (0.008, 0.006, 0.005), 6, 4, "iron_dk", B)
    H.ellipsoid(m, P(0.115, 0.042, 0.019), (0.005, 0.02, 0.006), 6, 4, "iron", B, exp=0.5)
    # trigger guard + trigger
    H.tube(m, [P(-0.045, -0.018), P(-0.02, -0.042), P(0.03, -0.046), P(0.07, -0.02)], [0.004] * 4, 5, "brass",
           hint=S, cap0="center", cap1="center")
    H.tube(m, [P(0.02, -0.012), P(0.012, -0.034)], [0.003, 0.003], 4, "iron", hint=f, cap0="center", cap1="center")
    return m


# ----------------------------------------------------------------------------- IK (two-hand musket holds)
def ordered_bones(arm):
    out = []

    def rec(b):
        out.append(b)
        for c in b.children:
            rec(c)
    for b in arm.data.bones:
        if b.parent is None:
            rec(b)
    return out


def fk(arm, pz):
    """Pose matrices (armature space) for a key_clip-style pose dict, without touching the scene."""
    P = {}
    for b in ordered_bones(arm):
        L = H.local_quat(arm, b.name, pz.get(b.name, (0, 0, 0))).to_matrix().to_4x4()
        if b.name == "hips":
            L = Matrix.Translation(H.local_loc(arm, "hips", pz.get("hips_loc", (0, 0, 0)))) @ L
        base = P[b.parent.name] @ b.parent.matrix_local.inverted() if b.parent else Matrix()
        P[b.name] = base @ b.matrix_local @ L
    return P


def euler_of(q, bone):
    x, y, z = (math.degrees(e) for e in q.to_euler("XYZ"))
    return (x, -y, -z) if bone.endswith(".R") else (x, y, z)


def solve_arm(arm, pz, S, grip, g_t, p_t, pole):
    """Two-bone IK: fist centre to `grip`, grip axis g_t, palm normal p_t; elbow toward `pole`."""
    g_t = V(g_t).normalized()
    p_t = V(p_t) - g_t * V(p_t).dot(g_t)
    p_t.normalize()
    a_t = p_t.cross(g_t) if S == "R" else g_t.cross(p_t)
    wrist = V(grip) - a_t * 0.044 * SZ
    P = fk(arm, pz)
    bones = arm.data.bones
    ua, fa, hd = f"upper_arm.{S}", f"forearm.{S}", f"hand.{S}"
    L1, L2 = bones[ua].length, bones[fa].length
    A = P[ua].translation.copy()
    d = wrist - A
    dist = max(min(d.length, (L1 + L2) * 0.999), abs(L1 - L2) + 1e-3)
    dn = d.normalized()
    ca = (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist)
    sa = math.sqrt(max(0.0, 1 - ca * ca))
    pp = V(pole) - dn * V(pole).dot(dn)
    pp.normalize()
    E = A + dn * (L1 * ca) + pp * (L1 * sa)
    W = A + dn * dist
    rdir = lambda n: (bones[n].matrix_local.to_3x3() @ V((0, 1, 0))).normalized()
    par = bones[ua].parent
    Dp = (P[par.name] @ par.matrix_local.inverted()).to_quaternion()
    Du = (Dp @ rdir(ua)).rotation_difference((E - A).normalized()) @ Dp
    Df = (Du @ rdir(fa)).rotation_difference((W - E).normalized()) @ Du
    ar, gr, pr, _ = hand_rest(S)
    Dh = (Matrix((a_t, g_t, p_t)).transposed() @ Matrix((ar, gr, pr)).transposed().inverted()).to_quaternion()
    out = dict(pz)
    out[ua] = euler_of(Dp.inverted() @ Du, ua)
    out[fa] = euler_of(Du.inverted() @ Df, fa)
    out[hd] = euler_of(Df.inverted() @ Dh, hd)
    return out


def hold(arm, pz, c, f, up, left=0.42, frame=None, poleR=(-1, 0.3, -0.5), poleL=(0.6, -0.2, -1),
         lgrip=None, lg=None, lp=None):
    """Right fist grips the musket wrist at c, barrel along f, gun top toward `up`; left fist on the fore-stock
    (c + f*left) palm-up, or at an explicit lgrip/lg/lp. frame='chest' makes c/f/up chest-relative."""
    c, f, up = V(c), V(f).normalized(), V(up)
    if frame:
        T = fk(arm, pz)[frame] @ arm.data.bones[frame].matrix_local.inverted()
        R3 = T.to_3x3()
        c, f, up = T @ c, R3 @ f, R3 @ up
        poleR, poleL = R3 @ V(poleR), R3 @ V(poleL)
        lgrip = T @ V(lgrip) if lgrip is not None else None
        lg = R3 @ V(lg) if lg is not None else None
        lp = R3 @ V(lp) if lp is not None else None
    up = (up - f * up.dot(f)).normalized()
    out = solve_arm(arm, pz, "R", c, f, up, poleR)
    if left is not None or lgrip is not None:
        gl = lgrip if lgrip is not None else c + f * left
        out = solve_arm(arm, out, "L", gl, lg if lg is not None else f, lp if lp is not None else up, poleL)
    return out


# ----------------------------------------------------------------------------- animation
P, over, mix = H.pose, H.over, H.mix
TORSO_IDLE = P(hips_loc=(0, 0, -0.012), hips=(0, 3, 0), spine=(6, 0, 0), chest=(5, 0, 4), neck=(-2, 0, 0),
               head=(-6, -6, 8), thigh=((-3, -4, 0), (2, -3, 0)), shin=((6, 0, 0), (4, 0, 0)), foot=((-3, 0, 0), (-6, 0, 0)),
               shoulder=(0, 2, 0), coat_tail=(4, 0, 0))
PORT = dict(c=(-0.14, -0.17, 1.02), f=(0.42, -0.22, 0.88), up=(0.1, -1, 0.2), frame="chest",
            poleR=(-1, 0.5, -0.4), poleL=(1, 0.3, -0.6))
TORSO_AIM = P(hips_loc=(0, 0, -0.035), hips=(0, 0, -14), spine=(5, 0, -8), chest=(2, -3, -12), neck=(4, 0, 12),
              head=(12, -12, 18), thigh=((-16, -6, 0), (12, -6, 0)), shin=((14, 0, 0), (10, 0, 0)),
              foot=((2, 0, 0), (-20, 0, 0)), shoulder_R=(0, -6, 0), coat_tail=(6, 0, 0))
AIM = dict(c=(-0.13, -0.33, 1.42), f=(0, -1, 0), up=(0, 0, 1), poleR=(-1, 0.5, -0.5), poleL=(0.4, -0.2, -1))


def tilt(f, deg):
    """Pitch a forward-ish direction up by deg."""
    f = V(f).normalized()
    side = f.cross(V((0, 0, 1))).normalized()
    return Matrix.Rotation(math.radians(deg), 3, side) @ f


def build_actions(arm):
    acts = {}
    K = lambda name, keys, loop=False: acts.__setitem__(name, H.key_clip(arm, name, keys, loop))
    hp = lambda base, **kw: hold(arm, base, **{**PORT, **kw})
    ha = lambda base, **kw: hold(arm, base, **{**AIM, **kw})

    # idle 1.6 s: slouched, musket at port-arms, sly sway
    idle0 = hp(TORSO_IDLE)
    idle1 = hp(over(TORSO_IDLE, hips_loc=(0, 0, -0.02), chest=(3, 0, 6), head=(-4, -9, 12), hips=(0, 5, 0)))
    K("idle", [(0, idle0), (24, idle1), (48, idle0)], True)

    # aim 0.7 s: swing the musket up to the shoulder, settle level, hold
    aim = ha(TORSO_AIM)
    mid_t = mix(TORSO_IDLE, TORSO_AIM, 0.55)
    raise_ = hold(arm, mid_t, c=(-0.15, -0.28, 1.25), f=tilt((0, -1, 0), 40), up=(0, 0.6, 1),
                  poleR=(-1, 0.4, -0.5), poleL=(0.6, -0.2, -1))
    over_ = ha(over(TORSO_AIM, chest=(0, -3, -13)), c=(-0.13, -0.33, 1.44), f=tilt((0, -1, 0), 4))
    K("aim", [(0, idle0), (7, raise_), (13, over_), (16, aim), (21, aim)])

    # fire 0.2 s: kick back + muzzle climb, settle toward aim
    kick_t = over(TORSO_AIM, hips_loc=(0, 0.012, -0.035), spine=(-4, 0, -8), chest=(-8, -3, -14), head=(4, -12, 20))
    kick = ha(kick_t, c=(-0.13, -0.27, 1.46), f=tilt((0, -1, 0), 16))
    half = ha(mix(kick_t, TORSO_AIM, 0.6), c=(-0.13, -0.31, 1.435), f=tilt((0, -1, 0), 6))
    K("fire", [(0, aim), (1, kick), (3, half), (6, aim)])

    # reload 1.4 s: musket grounded upright, powder from the horn, two ram strokes, back to port-arms
    rt = over(TORSO_IDLE, spine=(12, 0, 0), chest=(6, 0, -4), head=(14, -4, 6), neck=(4, 0, 0))
    RL = dict(c=(-0.15, -0.21, 0.86), f=(0.12, -0.32, 0.94), up=(0, -1, -0.3), frame=None,
              poleR=(-1, 0.4, -0.4), poleL=(1, 0.1, -0.5))
    rf = V(RL["f"]).normalized()
    rl = lambda base, **kw: hold(arm, base, **{**RL, **kw})
    low = rl(rt)
    horn = rl(over(rt, chest=(6, 0, -12), head=(18, -2, -10)), lgrip=(-0.13, -0.15, 1.0), lg=(0, 0, -1),
              lp=(-1, 0, 0))
    ram = lambda t, z=0.0: rl(over(rt, head=(4, -4, 6), spine=(8, 0, 0)), lgrip=V(RL["c"]) + rf * t + V((0.035, 0, z)),
                              lg=rf, lp=(-1, 0, 0), poleL=(1, 0.2, -0.3))
    K("reload", [(0, aim), (6, low), (11, horn), (15, horn), (19, ram(0.82)), (23, ram(0.52)), (27, ram(0.80)),
                 (31, ram(0.52)), (36, mix(low, idle0, 0.5)), (42, idle0)])

    # hop 0.5 s: crouch, spring back (feet trail behind), land, recover - in place
    crouch_t = over(TORSO_IDLE, hips_loc=(0, 0, -0.1), spine=(14, 0, 0), chest=(6, 0, 4), head=(-14, -6, 8),
                    thigh=(-30, -4, 0), shin=(58, 0, 0), foot=(-28, 0, 0), coat_tail=(10, 0, 0))
    air_t = over(TORSO_IDLE, hips_loc=(0, 0, 0.13), hips=(8, 0, 0), spine=(14, 0, 0), chest=(8, 0, 4),
                 head=(-18, -6, 8), thigh=((14, -5, 0), (24, -5, 0)), shin=((40, 0, 0), (55, 0, 0)),
                 foot=((30, 0, 0), (35, 0, 0)), coat_tail=(-25, 0, 0))
    land_t = over(TORSO_IDLE, hips_loc=(0, 0, -0.07), spine=(12, 0, 0), chest=(6, 0, 4), head=(-10, -6, 8),
                  thigh=(-22, -4, 0), shin=(44, 0, 0), foot=(-22, 0, 0), coat_tail=(30, 0, 0))
    K("hop", [(0, idle0), (3, hp(crouch_t)), (7, hp(air_t)), (11, hp(land_t)), (15, idle0)])

    # hurt 0.3 s: snap back, left hand flies off the stock
    hurt_t = over(TORSO_IDLE, hips_loc=(0, 0.02, -0.01), spine=(-14, 0, 6), chest=(-10, 0, 6), head=(-24, 8, 12),
                  upper_arm_L=(10, -55, 0), forearm_L=(-35, 0, 0), hand_L=(0, 0, 20), coat_tail=(-14, 0, 0))
    hurt = hp(hurt_t, left=None, c=(-0.17, -0.10, 1.05))
    K("hurt", [(0, idle0), (2, hurt), (5, mix(hurt, idle0, 0.45)), (9, idle0)])

    # death 1.2 s: shot recoil -> stagger -> topples onto his back, holds
    d1_t = over(hurt_t, spine=(-20, 0, 10), chest=(-14, 0, 8), head=(-30, 10, 14), upper_arm_L=(20, -80, 0))
    d1 = hp(d1_t, left=None, c=(-0.2, -0.05, 1.1))
    sag = P(hips_loc=(0, 0.06, -0.24), hips=(-18, 0, 6), spine=(-6, 0, 6), chest=(-6, 0, 4), head=(-20, 8, 18),
            thigh=((-40, -6, 0), (-20, -8, 0)), shin=((70, 0, 0), (55, 0, 0)), foot=((-20, 0, 0), (-25, 0, 0)),
            upper_arm=((25, -60, 0), (10, -55, 0)), forearm=((-30, 0, 0), (-25, 0, 0)), hand=((0, 0, 0), (0, 0, 0)),
            coat_tail=(-10, 0, 0))
    fall = P(hips_loc=(0, 0.32, -0.62), hips=(-62, 0, 8), spine=(-6, 0, 0), head=(-12, 10, 16),
             thigh=((-36, -8, 0), (-18, -10, 0)), shin=((40, 0, 0), (30, 0, 0)), foot=(10, 0, 0),
             upper_arm=((-10, -85, 0), (-20, -80, 0)), forearm=((-20, 0, 0), (-15, 0, 0)), coat_tail=(-30, 0, 0))
    flat = P(hips_loc=(0, 0.45, -0.855), hips=(-87, 0, 10), spine=(-3, 0, 0), chest=(-2, 0, 0), head=(4, 14, 40),
             thigh=((-8, -10, 0), (-4, -12, 0)), shin=((14, 0, 0), (6, 0, 0)), foot=((40, 0, 0), (55, 0, 0)),
             upper_arm=((-30, -95, 0), (-20, -85, 0)), forearm=((-30, 0, 0), (-10, 0, 0)), hand=((0, 0, 0), (10, 0, 0)),
             coat_tail=(-40, 0, 0))
    # musket tips over and ends lying flat beside him (right hand still on the wrist)
    fall = hold(arm, fall, c=(-0.42, 0.22, 0.42), f=(0.15, -0.8, -0.45), up=(-0.3, 0, 1), left=None,
                poleR=(-1, 0.3, 0.2))
    flat = hold(arm, flat, c=(-0.46, 0.30, 0.06), f=(0.12, -1, -0.02), up=(-0.3, 0, 1), left=None,
                poleR=(-1, 0, 0.6))
    bounce = over(flat, hips_loc=(0, 0.45, -0.835), head=(-2, 14, 36), thigh=((-14, -10, 0), (-8, -12, 0)))
    K("death", [(0, idle0), (4, d1), (12, hp(sag, left=None, c=(-0.22, -0.02, 1.0))), (21, fall), (26, flat),
                (30, bounce), (34, flat), (36, flat)])
    return acts


SHOTS = [("idle", 0), ("aim", 21), ("fire", 1), ("reload", 11), ("reload", 23), ("hop", 7), ("hurt", 2),
         ("death", 12), ("death", 36)]

if __name__ == "__main__":
    H.run_character("gunner", PAL, BONES, build_parts, build_actions, weapon=musket, height=2.0, shots=SHOTS,
                    args=ARGS)
