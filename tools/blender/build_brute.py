"""Build the Bilge Brute (melee deckhand enemy): mesh + rig + 7 clips + GLB + previews.

Run (from anywhere):
  blender -b --factory-startup --python tools/blender/build_brute.py [-- --no-render]
"""
import math
import os
import sys

from mathutils import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import humanoid as H  # noqa: E402
from humanoid import smoothstep as ss  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

PAL = H.Palette({
    "red": "#b83a2e", "red_dk": "#8a2a22", "offwhite": "#efe6d2", "offwhite_dk": "#cfc4ac",
    "olive": "#6f7a3a", "olive_dk": "#4f5828", "skin": "#c98a62", "skin_dk": "#a56a48",
    "stubble": "#9a7058", "nose": "#cf7c60", "pants": "#4a3d33", "pants_dk": "#33291f", "patch": "#7d6c48",
    "boot": "#3b2a20", "boot_dk": "#24180f", "boot_lt": "#55402f", "rope": "#b89a64", "rope_dk": "#8a7044",
    "leather": "#5a3520", "eye_white": "#f4ecd8", "iris": "#d8b030", "iris_dk": "#7a5a10",
    "pupil": "#1a0f0a", "lash": "#1a1210", "brow": "#2a1a12", "white": "#ffffff",
    "mouth": "#4a1714", "teeth": "#f2e8c8", "gold": "#e0a82e", "scar": "#e8a890",
    "wood": "#8a5a36", "wood_dk": "#5e3c22", "wood_lt": "#a87448", "iron": "#4a4a52", "iron_lt": "#7a7a86",
})

# ----------------------------------------------------------------------------- layout (hunch is built in)
D_ARM = V((0.26, -0.08, -0.96)).normalized()          # left arm hangs long and wide
J = dict(hips=(0, 0, 0.48), spine=(0, 0, 0.62), chest=(0, -0.01, 0.80), neck=(0, -0.05, 0.99),
         head=(0, -0.10, 1.08), head_top=(0, -0.12, 1.33), shoulder=(0.07, -0.02, 0.97), arm=(0.29, -0.02, 0.99),
         hip=(0.12, 0, 0.47), knee=(0.14, -0.015, 0.27), ankle=(0.15, 0.01, 0.085), toe=(0.155, -0.15, 0.025))
J["elbow"] = V(J["arm"]) + D_ARM * 0.24
J["wrist"] = J["elbow"] + D_ARM * 0.25
J["hand_end"] = J["wrist"] + D_ARM * 0.14
BONES = H.standard_skeleton(J)
FIST = 1.7

HC, HR = V((0, -0.12, 1.17)), (0.125, 0.12, 0.155)
HEAD = H.head_shape(HC, HR, jaw=-0.14, jaw_front=0.04, jaw_back=0.3, jaw_z=0.9)


def side_fn(s, fn):
    return fn if s > 0 else (lambda v: fn(V((-v.x, v.y, v.z))))


# ----------------------------------------------------------------------------- head
def build_head(parts):
    hp = H.Part(["head"])
    H.sphere(hp, HEAD, 20, 12, "skin")
    nf = len(hp.f)
    bvh = hp.bvh(0, nf)
    O, R, U = H.FACE

    def surf(x, z):
        hit = bvh.ray_cast(V((x, -0.8, z)), V((0, 1, 0)), 2.0)[0]
        return hit if hit is not None else V((x, HC.y - HR[1], z))

    # stubble muzzle under everything else on the face
    H.decal(hp, bvh, O, R, U, H.ellipse_pts(0, 1.088, 0.098, 0.045, 16), "stubble", 0.0008)
    for s in (1, -1):
        H.anime_eye(hp, bvh, 0.043, 1.178, s, k=0.78, iris="iris", iris_dk="iris_dk", lash="lash", brow="brow",
                    lid=0.42, lid_tilt=0.75, brow_spec=(0.022, 0.03, 0.03))
    # clenched grimace: corners pulled down, teeth showing
    xs = [-0.044 + 0.088 * k / 10 for k in range(11)]
    top = [(x, 1.093 + 0.01 * (1 - (x / 0.044) ** 2)) for x in xs]
    bot = [(x, 1.081 + 0.004 * (1 - (x / 0.044) ** 2)) for x in xs]
    H.decal(hp, bvh, O, R, U, top[::-1] + bot[1:-1], "mouth", 0.0016)
    H.decal_strip(hp, bvh, O, R, U, [(x, z - 0.0025) for x, z in top[2:-2]], [(x, z + 0.0025) for x, z in bot[2:-2]],
                  "teeth", 0.0024)
    # scar across the right brow / eye
    a, b = V((-0.078, 1.225)), V((-0.026, 1.142))
    n = V((-(b - a).y, (b - a).x)).normalized() * 0.0035
    pts = [a + (b - a) * (k / 6) for k in range(7)]
    H.decal_strip(hp, bvh, O, R, U, [tuple(p + n) for p in pts], [tuple(p - n) for p in pts], "scar", 0.0062)
    # bulbous nose, ears, gold hoop, lower tusk
    H.ellipsoid(hp, surf(0, 1.135) + V((0, -0.012, 0)), (0.03, 0.027, 0.026), 10, 7, "nose")
    for s in (1, -1):
        H.ellipsoid(hp, (HR[0] * 0.98 * s, HC.y + 0.01, HC.z - 0.005), (0.016, 0.026, 0.034), 8, 6, "skin")
    ring = [V((HR[0] * 1.02 + 0.012 * math.cos(2 * math.pi * k / 12) * 0.25, HC.y + 0.006 + 0.016 * math.cos(2 * math.pi * k / 12),
               HC.z - 0.05 + 0.016 * math.sin(2 * math.pi * k / 12))) for k in range(12)]
    H.tube(hp, ring, [0.0042] * 12, 5, "gold", hint=V((1, 0, 0)), closed_path=True)
    t0 = surf(0.024, 1.082) + V((0, -0.006, 0))
    H.tube(hp, [t0, t0 + V((0, -0.004, 0.012))], [0.0065, 0.004], 6, "teeth", hint=V((1, 0, 0)),
           cap0="center", cap1=t0 + V((0, -0.005, 0.02)))
    parts.append(hp)


def build_bandana(parts):
    bp = H.Part(["head"])
    nu = 20

    def tmax(psi):
        f = -math.sin(psi)  # 1 at the front
        return math.radians(104 - (104 - 60) * (1 + f) / 2)

    def cap_pt(th, psi, sc):
        u = V((math.sin(th) * math.cos(psi), math.sin(th) * math.sin(psi), math.cos(th)))
        return HC + (HEAD(u) - HC) * sc
    rows = []
    for fr, sc in ((1.0, 0.99), (1.0, 1.05), (0.82, 1.065), (0.62, 1.07), (0.42, 1.07), (0.22, 1.065)):
        rows.append([cap_pt(fr * tmax(2 * math.pi * j / nu), 2 * math.pi * j / nu, sc) for j in range(nu)])
    H.loft(bp, rows, lambda i, j: "olive_dk" if i <= 0 else "olive", True, None, HC + V((0, 0, HR[2] * 1.065)))
    # knot at the back + two tails
    kd = V((0.25, 1.0, 0.05)).normalized()
    kc = HC + (HEAD(kd) - HC) * 1.1
    H.ellipsoid(bp, kc, (0.03, 0.022, 0.026), 8, 6, "olive_dk")
    for dx, L in ((0.05, 0.13), (-0.02, 0.1)):
        pts = [kc + V((dx * t, 0.03 * t + 0.03 * t * t, -L * t)) for t in (0.0, 0.35, 0.7, 1.0)]
        H.tube(bp, pts[:-1], [(0.022, 0.006), (0.024, 0.006), (0.02, 0.005)], 6, "olive",
               hint=V((0, 1, 0)), cap0="center", cap1=pts[-1])
    parts.append(bp)


# ----------------------------------------------------------------------------- torso
# (z, rx, ry_front, ry_back): pot belly in front, hump on the back
TORSO = [(0.42, 0.17, 0.14, 0.13), (0.47, 0.215, 0.17, 0.16), (0.54, 0.235, 0.20, 0.17), (0.62, 0.245, 0.215, 0.17),
         (0.70, 0.255, 0.21, 0.175), (0.78, 0.275, 0.195, 0.19), (0.86, 0.30, 0.18, 0.21), (0.93, 0.31, 0.17, 0.225),
         (0.98, 0.29, 0.15, 0.22), (1.02, 0.22, 0.13, 0.18), (1.05, 0.12, 0.10, 0.11)]


def prof(z):
    for a, b in zip(TORSO, TORSO[1:]):
        if a[0] <= z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            return tuple(H.lerp(a[k], b[k], t) for k in (1, 2, 3))
    return TORSO[-1][1:]


def tring(z, d=0.0, n=20):
    rx, rf, rb = prof(z)
    out = []
    for j in range(n):
        a = 2 * math.pi * j / n
        ry = rb if math.sin(a) > 0 else rf
        out.append(V(((rx + d) * math.cos(a), (ry + d) * math.sin(a), z)))
    return out


def stripe(c, n):
    if c.z < 0.505:
        return "pants"
    if c.z > 1.005 or (abs(c.x) > 0.19 and c.z > 0.9 and c.y > -0.12):
        return "skin"  # neckline + sleeveless armholes
    return "red" if int((c.z - 0.505) / 0.055) % 2 == 0 else "offwhite"


def build_torso(parts):
    nk = H.Part(["chest", "neck", ("head", lambda v: ss(1.06, 1.11, v.z))])
    H.tube(nk, [(0, -0.03, 0.95), (0, -0.09, 1.07), (0, -0.11, 1.12)], [0.085, 0.08, 0.07], 10, "skin")
    parts.append(nk)

    def sh(s):
        return side_fn(s, lambda v: ss(0.12, 0.26, v.x) * ss(0.84, 0.95, v.z))

    def th(s):
        return side_fn(s, lambda v: ss(0.56, 0.46, v.z) * ss(0.0, 0.08, v.x))
    tp = H.Part(["hips", "spine", "chest", ("neck", lambda v: ss(1.01, 1.05, v.z)),
                 ("shoulder.L", sh(1)), ("shoulder.R", sh(-1)), ("thigh.L", th(1)), ("thigh.R", th(-1))])
    zs = [0.42 + (1.05 - 0.42) * k / 20 for k in range(21)]
    H.loft(tp, [tring(z) for z in zs], "red", True, V((0, 0, 0.40)), V((0, -0.02, 1.062)))
    tp.recolor(0, stripe)
    parts.append(tp)

    # rope belt with a knot and hanging ends
    rp = H.Part(["hips", "spine"])
    H.tube(rp, tring(0.508, 0.012, 24), [0.015] * 24, 6, lambda i, j: "rope_dk" if i % 2 else "rope",
           hint=V((0, 0, 1)), closed_path=True)
    kc = V((0.13, -0.205, 0.505))
    H.ellipsoid(rp, kc, (0.026, 0.02, 0.022), 8, 5, "rope")
    for dx in (0.0, 0.03):
        pts = [kc + V((dx * t, -0.012 * t, -0.11 * t)) for t in (0.0, 0.5, 1.0)]
        H.tube(rp, pts[:-1], [0.011, 0.01], 5, "rope", hint=V((1, 0, 0)), cap1=pts[-1])
    parts.append(rp)


# ----------------------------------------------------------------------------- legs
def build_legs(parts):
    O, R, U = H.FACE
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        X = lambda p: V((p[0] * s, p[1], p[2]))
        lp = H.Part(["hips", f"thigh.{S}", (f"shin.{S}", lambda v: 0.6 * ss(0.32, 0.25, v.z))])
        f0 = len(lp.f)
        H.tube(lp, [X(p) for p in ((0.12, 0, 0.52), (0.135, -0.005, 0.38), (0.143, -0.012, 0.27), (0.146, -0.01, 0.215),
                                   (0.146, -0.01, 0.205), (0.146, -0.01, 0.204))],
               [0.118, 0.108, 0.094, 0.096, 0.096, 0.06], 12, lambda i, j: "pants_dk" if i >= 2 else "pants",
               hint=V((s, 0, 0)))
        if s > 0:  # square patch on the left thigh
            H.decal(lp, lp.bvh(f0), O, R, U, [(0.135 + 0.032 * math.copysign(abs(math.cos(a)) ** 0.4, math.cos(a)), 0.37 + 0.034 * math.copysign(abs(math.sin(a)) ** 0.4, math.sin(a))) for a in (2 * math.pi * k / 12 + 0.1 for k in range(12))], "patch", 0.003)
        parts.append(lp)
        cp = H.Part([(f"thigh.{S}", lambda v: ss(0.24, 0.3, v.z)), f"shin.{S}"])
        H.tube(cp, [X(p) for p in ((0.146, -0.008, 0.24), (0.148, 0.0, 0.18), (0.15, 0.005, 0.13))],
               [0.07, 0.068, 0.06], 10, "skin", hint=V((s, 0, 0)))
        parts.append(cp)
        bt = H.Part([f"shin.{S}", (f"foot.{S}", lambda v: ss(0.12, 0.06, v.z))])
        rings = [H.ring(X((0.15, 0.008, z)), (0, 0, 1), r, r * 0.95, 12, hint=V((1, 0, 0)))
                 for z, r in ((0.06, 0.07), (0.12, 0.072), (0.15, 0.08), (0.17, 0.08), (0.171, 0.05))]
        H.loft(bt, rings, lambda i, j: "boot_lt" if i >= 2 else "boot")
        f0, v0 = len(bt.f), len(bt.v)
        H.ellipsoid(bt, X((0.153, -0.04, 0.05)), (0.078, 0.13, 0.058), 12, 8, "boot")
        for k in range(v0, len(bt.v)):
            p = bt.v[k]
            if p.y < -0.07:
                p.z += 1.4 * (-0.07 - p.y) ** 2
            p.z = max(p.z, 0.0)
        bt.recolor(f0, lambda c, n: "boot_dk" if c.z < 0.016 else None)
        parts.append(bt)


# ----------------------------------------------------------------------------- arms
def arm_frame(s):
    return V((D_ARM.x * s, D_ARM.y, D_ARM.z)), V((J["arm"][0] * s, J["arm"][1], J["arm"][2]))


def fist_frame(s):
    d, sj = arm_frame(s)
    g = V((0, -1, 0))
    p = d.cross(g).normalized()
    if p.x * s > 0:
        p = -p
    return d, g, p, sj + d * 0.49


def build_arms(parts):
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        d, sj = arm_frame(s)
        at = lambda u: sj + d * u
        hint = V((0, -1, 0))
        up = H.Part([(f"shoulder.{S}", lambda v: 0.5), f"upper_arm.{S}", (f"forearm.{S}", lambda v: 0.5)])
        H.ellipsoid(up, sj + d * 0.025 + V((0.008 * s, 0, 0.0)), (0.104, 0.1, 0.098), 12, 8, "skin")
        H.tube(up, [at(u) for u in (0.0, 0.08, 0.16, 0.25)], [0.094, 0.088, 0.076, 0.072], 10, "skin", hint=hint)
        parts.append(up)
        fp = H.Part([f"forearm.{S}", (f"upper_arm.{S}", lambda v: 0.5), (f"hand.{S}", lambda v: 0.3)])
        H.tube(fp, [at(u) for u in (0.23, 0.28, 0.34, 0.40, 0.45, 0.48)], [0.074, 0.095, 0.106, 0.1, 0.082, 0.07], 12,
               "skin", hint=hint, cap1="center")
        H.tube(fp, [at(u) for u in (0.435, 0.45, 0.49, 0.505)], [0.08, 0.084, 0.078, 0.07], 12,
               lambda i, j: "leather" if i == 1 else "rope_dk" if i == 0 else "leather", hint=hint)
        parts.append(fp)
        hp = H.Part([f"hand.{S}", (f"forearm.{S}", lambda v: 0.2)])
        a, g, p, w = fist_frame(s)
        H.fist(hp, w, a, g, p, "skin", size=FIST)
        parts.append(hp)


def build_parts():
    parts = []
    build_head(parts)
    build_bandana(parts)
    build_torso(parts)
    build_legs(parts)
    build_arms(parts)
    return parts


# ----------------------------------------------------------------------------- belaying-pin club
def build_club():
    a, g, p, w = fist_frame(-1)
    c = w + a * 0.044 * FIST
    cp = H.Part(["hand.R"])
    # (offset along grip axis, radius, color): knob, handle, collar, fat tapered body, iron bands, domed end
    prof_ = [(-0.115, 0.0, "wood_dk"), (-0.11, 0.024, "wood_dk"), (-0.09, 0.034, "wood_dk"), (-0.075, 0.026, "wood"),
             (0.09, 0.026, "wood"), (0.105, 0.04, "wood_dk"), (0.125, 0.042, "wood_dk"), (0.14, 0.036, "wood"),
             (0.30, 0.05, "wood"), (0.34, 0.054, "iron"), (0.37, 0.054, "wood_lt"), (0.50, 0.06, "wood"),
             (0.53, 0.064, "iron"), (0.56, 0.064, "wood_lt"), (0.62, 0.058, "wood"), (0.655, 0.04, "wood_dk"),
             (0.67, 0.0, "wood_dk")]
    rings = [H.ring(c + g * t, g, max(r, 0.002), max(r, 0.002), 8, hint=a) for t, r, _ in prof_]
    H.loft(cp, rings, lambda i, j: prof_[min(max(i, 0), len(prof_) - 1)][2], True)
    return cp


# ----------------------------------------------------------------------------- animation
CENTER = ("hips", "spine", "chest", "neck", "head", "root")


def mirror_pose(p):
    out = {}
    for k, v in p.items():
        if k == "hips_loc":
            out[k] = (-v[0], v[1], v[2])
        elif k.endswith(".L"):
            out[k[:-2] + ".R"] = v
        elif k.endswith(".R"):
            out[k[:-2] + ".L"] = v
        else:
            out[k] = (v[0], -v[1], -v[2])
    return out


BASE = H.pose(hips_loc=(0, 0, -0.02), spine=(10, 0, 0), chest=(4, 0, 0), neck=(-6, 0, 0), head=(-12, 0, 0),
              thigh=(-14, -6, 0), shin=(26, 0, 0), foot=(-12, 6, 0),
              upper_arm=((-10, -4, 0), (-16, -4, 0)), forearm=((-20, 0, 0), (-26, 0, 0)), hand=((0, 0, 0), (62, 0, 0)))


def build_actions(arm):
    acts = {}
    K = lambda name, keys, loop=False: acts.__setitem__(name, H.key_clip(arm, name, keys, loop))

    # idle 1.6 s: heavy breathing, shoulders heave, club dangles
    inhale = H.over(BASE, hips_loc=(0, 0, -0.012), spine=(3, 0, 0), chest=(0, 0, 0), head=(-12, 0, 0),
                    shoulder=(0, -4, 0), upper_arm=((-12, -7, 0), (-18, -7, 0)), hand=((0, 0, 0), (58, 0, 0)))
    K("idle", [(0, BASE), (24, inhale), (48, BASE)], True)

    # walk 0.8 s waddle: big side-to-side roll over the planted leg, short stomping steps
    cL = H.over(BASE, hips_loc=(0, 0, -0.04), hips=(0, -4, -8), spine=(8, 8, 6), chest=(6, 4, 6), head=(-10, -10, -4),
                thigh=((-30, -8, 0), (14, -8, 0)), shin=((22, 0, 0), (30, 0, 0)), foot=((8, 8, 0), (-22, 8, 0)),
                upper_arm=((12, -8, 0), (-30, -6, 0)), forearm=((-20, 0, 0), (-34, 0, 0)))
    pL = H.over(BASE, hips_loc=(0, 0, -0.005), hips=(0, 8, 0), spine=(8, 10, 0), chest=(6, 4, 0), head=(-10, -12, 0),
                thigh=((-10, -8, 0), (-34, -12, 0)), shin=((14, 0, 0), (62, 0, 0)), foot=((-4, 8, 0), (-8, 8, 0)),
                upper_arm=((0, -10, 0), (-18, -10, 0)))
    cR, pR = mirror_pose(cL), mirror_pose(pL)
    for p in (cR, pR):  # the club arm stays the club arm
        p["hand.R"], p["hand.L"] = (62, 0, 0), (0, 0, 0)
    K("walk", [(0, cL), (6, pL), (12, cR), (18, pR), (24, cL)], True)

    # windup 0.5 s: dip, then heave the club high overhead, leaning way back (the "flash" pose)
    dip = H.over(BASE, hips_loc=(0, 0, -0.06), spine=(16, 0, 0), chest=(8, 0, 0), head=(-18, 0, 0),
                 thigh=((-26, -8, 0), (-6, -8, 0)), shin=((44, 0, 0), (36, 0, 0)), foot=((-18, 8, 0), (-30, 8, 0)),
                 upper_arm=((-20, -10, 0), (20, -8, 0)), forearm=((-30, 0, 0), (-50, 0, 0)), hand=((0, 0, 0), (40, 0, 0)))
    high = H.pose(hips_loc=(0, 0.01, -0.03), hips=(-4, 0, 0), spine=(-10, 0, -6), chest=(-10, 0, -8), neck=(4, 0, 0),
                  head=(-6, 0, 6), thigh=((-24, -10, 0), (8, -10, 0)), shin=((26, 0, 0), (22, 0, 0)),
                  foot=((0, 10, 0), (-28, 10, 0)), upper_arm=((-70, -30, 0), (-172, -14, 0)),
                  forearm=((-40, 0, 0), (-20, 0, 0)), hand=((0, 0, 0), (85, 0, 0)))
    peak = H.over(high, spine=(-13, 0, -6), chest=(-12, 0, -9), upper_arm_R=(-176, -14, 0), hand_R=(95, 0, 0))
    K("windup", [(0, BASE), (5, dip), (11, high), (15, peak)])

    # strike 0.15 s: slam down in front, body folds over
    mid = H.pose(hips_loc=(0, 0, -0.05), hips=(4, 0, 0), spine=(8, 0, 0), chest=(4, 0, 0), head=(-12, 0, 0),
                 thigh=((-32, -10, 0), (10, -10, 0)), shin=((36, 0, 0), (28, 0, 0)), foot=((-4, 10, 0), (-34, 10, 0)),
                 upper_arm=((-40, -30, 0), (-120, -8, 0)), forearm=((-20, 0, 0), (-10, 0, 0)), hand=((0, 0, 0), (30, 0, 0)))
    slam = H.pose(hips_loc=(0, 0, -0.08), hips=(14, 0, 0), spine=(22, 0, 4), chest=(12, 0, 4), head=(-26, 0, 0),
                  thigh=((-44, -10, 0), (12, -10, 0)), shin=((58, 0, 0), (40, 0, 0)), foot=((-14, 10, 0), (-40, 10, 0)),
                  upper_arm=((-20, -30, 0), (-74, -6, 0)), forearm=((-20, 0, 0), (-8, 0, 0)), hand=((0, 0, 0), (68, 0, 0)))
    # 0.15 s = 4.5 f, but the glTF exporter samples whole frames (4.5 -> 4, ending short of contact), so the
    # slam lands on f4: 0.133 s in the GLB with the full contact pose.
    K("strike", [(0, peak), (2, mid), (4, slam)])

    # recover 0.7 s: club bitten into the deck, both hands tug, finally wrench it free
    # body leans back by b degrees -> club arm swings forward by b so the club stays planted
    tug = H.over(slam, hips_loc=(0, 0.02, -0.09), hips=(12, 0, 0), spine=(20, 0, 2), chest=(10, 0, 2), head=(-34, 0, 0),
                 upper_arm=((-70, 12, -24), (-68, -6, 0)), forearm=((-20, 0, 0), (-8, 0, 0)), hand=((0, 0, 0), (68, 0, 0)))
    heave = H.over(tug, hips_loc=(0, 0.04, -0.10), hips=(8, 0, 0), spine=(14, 0, -3), chest=(6, 0, -3), head=(-38, 0, 4),
                   upper_arm=((-60, 12, -24), (-54, -6, 0)), shoulder=(0, 6, 0))
    free = H.over(BASE, hips_loc=(0, 0, -0.05), spine=(4, 0, 0), head=(-14, 0, 0),
                  upper_arm=((-20, -6, 0), (-40, -6, 0)), forearm=((-30, 0, 0), (-40, 0, 0)), hand=((0, 0, 0), (35, 0, 0)))
    K("recover", [(0, slam), (4, tug), (8, heave), (11, tug), (15, heave), (18, free), (21, BASE)])

    # hurt 0.3 s: snap back
    rec = H.pose(hips_loc=(0, 0.03, -0.03), spine=(-14, 0, 6), chest=(-12, 0, 6), head=(-22, 0, 10),
                 thigh=((-6, -8, 0), (-20, -8, 0)), shin=((20, 0, 0), (34, 0, 0)), foot=((-10, 8, 0), (-10, 8, 0)),
                 upper_arm=((16, -30, 0), (12, -26, 0)), forearm=((-30, 0, 0), (-40, 0, 0)), hand=((0, 0, 0), (40, 0, 0)))
    K("hurt", [(0, BASE), (2, rec), (5, H.mix(rec, BASE, 0.5)), (9, BASE)])

    # death 1.0 s: stagger back, knees give, flop onto the back, club arm flops out (held)
    st = H.over(rec, spine=(-20, 0, 8), head=(-30, 0, 10), thigh=((-30, -8, 0), (-10, -8, 0)), shin=((40, 0, 0), (20, 0, 0)))
    sit = H.pose(hips_loc=(0, 0.1, -0.26), hips=(-30, 0, 0), spine=(-6, 0, 0), chest=(4, 0, 0), head=(10, 0, 0),
                 thigh=(-70, -14, 0), shin=(80, 0, 0), foot=(-10, 10, 0),
                 upper_arm=((-10, -40, 0), (-10, -40, 0)), forearm=(-30, 0, 0), hand=((0, 0, 0), (40, 0, 0)))
    flat = H.pose(hips_loc=(0, 0.2, -0.245), hips=(-82, 0, 0), spine=(-4, 0, 0), chest=(-4, 0, 0), head=(4, 0, 30),
                  thigh=((8, -14, 0), (-4, -16, 0)), shin=((14, 0, 0), (30, 0, 0)), foot=(-10, 10, 0),
                  upper_arm=((5, -80, 0), (10, -84, 0)), forearm=((-10, 0, 0), (0, 0, 0)), hand=((0, 0, 0), (0, 0, 90)))
    settle = H.over(flat, hips_loc=(0, 0.2, -0.25), thigh=((10, -14, 0), (-2, -16, 0)), head=(2, 0, 34))
    K("death", [(0, BASE), (4, rec), (9, st), (16, sit), (23, flat), (26, H.mix(flat, settle, 1.4)), (30, settle)])
    return acts


SHOTS = [("idle", 0), ("walk", 0), ("walk", 6), ("windup", 15), ("strike", 2), ("strike", 4),
         ("recover", 8), ("hurt", 2), ("death", 30)]

H.run_character("brute", PAL, BONES, build_parts, build_actions, weapon=build_club, height=1.35, shots=SHOTS,
                args=ARGS)
