"""Build Captain Varga Chainhook (first boss): mesh + rig + 9 clips + GLB + previews.

Run (from anywhere):
  blender -b --factory-startup --python tools/blender/build_chainhook.py [-- --no-render]
"""
import math
import os
import sys

from mathutils import Vector as V

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import humanoid as H  # noqa: E402
from humanoid import smoothstep as ss, lerp, pose, over, mix  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
H.PAIRED.add("coat_tail")

PAL = H.Palette({
    "plum": "#5b2a6e", "plum_dk": "#3d1a4b", "plum_lt": "#7a3d8f", "gold": "#d9a531", "gold_dk": "#9c7018",
    "gold_lt": "#f4d36a", "iron": "#3a3a42", "iron_dk": "#24242a", "iron_lt": "#6a6a76", "bore": "#0c0c0f",
    "skin": "#d39a76", "skin_dk": "#a8714f", "hair": "#121016", "hat": "#1c1a22", "hat_dk": "#111015",
    "plume": "#f6f4ee", "plume_dk": "#d6d2c8", "shirt": "#f3efe4", "shirt_dk": "#d9d2c0", "pants": "#2c2a33",
    "boot": "#17151b", "boot_lt": "#2c2930", "glove": "#1a181e", "belt": "#1b1a20",
    "eye_white": "#fbf7ee", "iris": "#e0b52a", "iris_dk": "#6e4a12", "pupil": "#120a06", "lash": "#0e0a0c",
    "white": "#ffffff", "mouth": "#4a1418",
})

# ----------------------------------------------------------------------------- layout (2.6 m incl. hat)
D_ARM = V((0.30, 0.0, -0.954)).normalized()
J = dict(hips=(0, 0, 1.06), spine=(0, 0, 1.20), chest=(0, 0, 1.42), neck=(0, 0.01, 1.76),
         head=(0, 0.01, 1.87), head_top=(0, 0.01, 2.20), shoulder=(0.06, 0, 1.70),
         arm=(0.40, 0, 1.70), hip=(0.11, 0, 1.02), knee=(0.12, -0.01, 0.56),
         ankle=(0.125, 0.02, 0.11), toe=(0.13, -0.17, 0.03))
J["elbow"] = V(J["arm"]) + D_ARM * 0.40
J["wrist"] = J["elbow"] + D_ARM * 0.36
J["hand_end"] = J["wrist"] + D_ARM * 0.14
EXTRAS = [("hat", (0, 0.01, 2.13), (0, 0.01, 2.33), "head"),
          ("plume", (0.12, 0.03, 2.30), (0.02, 0.24, 2.56), "hat"),
          ("coat_tail.L", (0.12, 0.15, 1.14), (0.24, 0.27, 0.45), "hips"),
          ("coat_tail.R", (-0.12, 0.15, 1.14), (-0.24, 0.27, 0.45), "hips")]
BONES = H.standard_skeleton(J, EXTRAS)

HC, HR = V((0, 0.0, 2.03)), (0.13, 0.135, 0.17)
head_pt = H.head_shape(HC, HR, jaw=0.30, jaw_front=0.05, jaw_back=0.40, jaw_z=1.0)
FO, FR, FU = H.FACE


def side_fn(s, fn):
    return fn if s > 0 else (lambda v: fn(V((-v.x, v.y, v.z))))


def vring(z, rx, ry, yoff, n, cx=0.0):
    return H.ring((cx, yoff, z), (0, 0, 1), rx, ry, n, hint=V((1, 0, 0)))


def subdiv(poly, k):
    out = []
    for a, b in zip(poly, poly[1:] + poly[:1]):
        out += [(lerp(a[0], b[0], t / k), lerp(a[1], b[1], t / k)) for t in range(k)]
    return out


# ----------------------------------------------------------------------------- head & face
def build_head(parts):
    hp = H.Part(["head", ("neck", lambda v: 0.3 * ss(1.92, 1.86, v.z))])
    H.sphere(hp, head_pt, 24, 16, "skin")
    nf = len(hp.f)
    bvh = hp.bvh(0, nf)
    # hooked nose
    H.ellipsoid(hp, (0, -0.128, 2.0), (0.017, 0.022, 0.046), 8, 6, "skin",
                H.axes((1, 0, 0), (0, 0.89, 0.45), (0, -0.45, 0.89)))
    H.ellipsoid(hp, (0, -0.15, 1.968), (0.016, 0.015, 0.014), 8, 5, "skin")
    for s in (1, -1):
        H.ellipsoid(hp, (0.128 * s, 0.015, 2.02), (0.02, 0.032, 0.042), 8, 6, "skin")
        H.anime_eye(hp, bvh, 0.052, 2.045, s, k=1.0, iris="iris", iris_dk="iris_dk", brow="hair",
                    brow_spec=(0.036, 0.03, 0.024), lid=0.36, lid_tilt=0.8)
    # sneer: left corner (+X) hitched up, gold teeth showing
    n = 10
    bot = [(lerp(-0.05, 0.06, t / n), lerp(1.926, 1.946, t / n) - 0.026 * math.sin(math.pi * t / n) ** 0.7)
           for t in range(n + 1)]
    top = [(lerp(0.06, -0.05, t / n), lerp(1.946, 1.926, t / n) + 0.004 * math.sin(math.pi * t / n))
           for t in range(1, n)]
    H.decal(hp, bvh, FO, FR, FU, bot + top, "mouth", 0.0015)
    xs = [lerp(-0.036, 0.048, t / 8) for t in range(9)]
    lip = lambda x: lerp(1.926, 1.946, (x + 0.05) / 0.11) + 0.003
    H.decal_strip(hp, bvh, FO, FR, FU, [(x, lip(x) - 0.002) for x in xs], [(x, lip(x) - 0.014) for x in xs],
                  "gold_lt", 0.0025)
    for x in (-0.02, 0.006, 0.03):  # tooth gaps
        H.decal_strip(hp, bvh, FO, FR, FU, [(x - 0.0012, lip(x) - 0.0015), (x + 0.0012, lip(x) - 0.0015)],
                      [(x - 0.0012, lip(x) - 0.0145), (x + 0.0012, lip(x) - 0.0145)], "gold_dk", 0.0032)
    parts.append(hp)

    # curled black mustache + hooked goatee
    hr = H.Part(["head"])
    for s in (1, -1):
        pts = [(0.008, -0.146, 1.968), (0.04, -0.14, 1.958), (0.075, -0.126, 1.952), (0.11, -0.106, 1.958),
               (0.14, -0.09, 1.978), (0.152, -0.088, 2.0), (0.142, -0.092, 2.016), (0.126, -0.098, 2.012),
               (0.12, -0.1, 2.0)]
        rad = [0.012, 0.014, 0.013, 0.011, 0.009, 0.008, 0.007, 0.006, 0.004]
        H.tube(hr, [V((x * s, y, z)) for x, y, z in pts[:-1]], rad[:-1], 7, "hair",
               hint=V((0, -1, 0)), cap0="center", cap1=V((pts[-1][0] * s, pts[-1][1], pts[-1][2])))
    H.tube(hr, [(0, -0.07, 1.872), (0, -0.1, 1.83), (0, -0.13, 1.795), (0, -0.155, 1.785)],
           [(0.026, 0.018), (0.018, 0.014), (0.01, 0.009), (0.006, 0.005)], 8, "hair", hint=V((1, 0, 0)),
           cap0="center", cap1=V((0, -0.172, 1.792)))
    # slicked hair + sideburns under the hat
    nu = 24

    def tmax(psi):
        f = -math.sin(psi)  # 1 at the front, -1 at the back
        return math.radians(lerp(118, 62, (1 + f) / 2) + 34 * max(0.0, 1 - abs(f + 0.1) / 0.35))  # + sideburns

    def cap_pt(th, psi, sc):
        return HC + (head_pt(V((math.sin(th) * math.cos(psi), math.sin(th) * math.sin(psi), math.cos(th)))) - HC) * sc
    rows = []
    for s_, sc in [(1.0, 0.99), (1.0, 1.05), (0.75, 1.06), (0.5, 1.06), (0.25, 1.05)]:
        rows.append([cap_pt(s_ * tmax(2 * math.pi * j / nu), 2 * math.pi * j / nu, sc) for j in range(nu)])
    H.loft(hr, rows, "hair", True, None, HC + V((0, 0, HR[2] * 1.05)))
    # gold hoop earring (left)
    ring_pts = [V((0.142, 0.01, 1.958)) + V((0, math.cos(a) * 0.018, math.sin(a) * 0.018))
                for a in [2 * math.pi * k / 12 for k in range(12)]]
    H.tube(hr, ring_pts, [0.004] * 12, 5, "gold", hint=V((1, 0, 0)), closed_path=True)
    parts.append(hr)


def build_hat(parts):
    hp = H.Part(["hat"], smooth=True)
    cz, cy = 2.13, 0.01
    # crown
    crown = [(cz - 0.01, 0.152, 0.162), (cz + 0.08, 0.156, 0.165), (cz + 0.14, 0.14, 0.15),
             (cz + 0.175, 0.105, 0.112), (cz + 0.192, 0.055, 0.06)]
    H.loft(hp, [vring(z, rx, ry, cy, 24) for z, rx, ry in crown], lambda i, j: "hat_dk" if i == 0 else "hat",
           True, None, V((0, cy, cz + 0.198)))
    # tricorn brim: corners at front and back-sides, walls cocked up in between
    n = 48

    def bp(phi, t, dz=0.0):
        e = 60.0 - abs(((math.degrees(phi) + 60.0) % 120.0) - 60.0)  # 60 at corners, 0 at side centres
        R = 0.215 / max(math.cos(math.radians(e)), 0.2) ** 0.7
        h = 0.17 * (1 - e / 60.0) ** 1.1 + 0.01
        r0x, r0y = 0.155, 0.165
        dirv = V((math.sin(phi), -math.cos(phi), 0))
        r = lerp(1.0, R / 0.16, t)
        p = V((dirv.x * r0x * r, cy + dirv.y * r0y * r, cz + h * t ** 1.7 + dz))
        p -= dirv * (0.45 * h * t * t)
        return p
    ts = [0.0, 0.3, 0.6, 0.85, 1.0]
    top = [[bp(2 * math.pi * j / n, t) for j in range(n)] for t in ts]
    bottom = [[bp(2 * math.pi * j / n, t, -0.016) for j in range(n)] for t in ts[::-1]]
    nt = len(ts)
    H.loft(hp, top + bottom, lambda i, j: "gold" if nt - 3 <= i <= nt else ("hat" if i < nt else "hat_dk"))
    # gold rosette where the plume is pinned (left side)
    H.ellipsoid(hp, (0.155, 0.0, 2.22), (0.012, 0.034, 0.034), 10, 6, "gold", exp=0.8)
    H.ellipsoid(hp, (0.163, 0.0, 2.22), (0.008, 0.016, 0.016), 8, 4, "gold_lt")
    parts.append(hp)
    # plume: big flattened white feather arching up and back
    pl = H.Part(["plume", ("hat", lambda v: 2.0 * ss(2.36, 2.28, v.z))])
    pts = [V(p) for p in ((0.15, 0.0, 2.22), (0.17, 0.04, 2.38), (0.13, 0.13, 2.51), (0.05, 0.24, 2.57),
                          (-0.04, 0.33, 2.53), (-0.09, 0.39, 2.43))]
    rad = [(0.02, 0.03), (0.03, 0.065), (0.034, 0.08), (0.032, 0.08), (0.026, 0.062), (0.014, 0.035)]
    H.tube(pl, pts, rad, 10, lambda i, j: "plume_dk" if j in (0, 5) else "plume", hint=V((1, 0, 0.2)),
           cap0="center", cap1=V((-0.11, 0.4, 2.34)))
    parts.append(pl)


# ----------------------------------------------------------------------------- torso, coat, legs
TORSO = [(1.00, 0.06, 0.05, 0.0), (1.04, 0.16, 0.13, 0.0), (1.12, 0.148, 0.118, 0.0), (1.20, 0.158, 0.125, 0.0),
         (1.32, 0.24, 0.16, -0.005), (1.44, 0.32, 0.19, -0.012), (1.56, 0.37, 0.20, -0.012),
         (1.66, 0.40, 0.19, 0.0), (1.73, 0.38, 0.17, 0.01), (1.78, 0.28, 0.14, 0.01), (1.81, 0.12, 0.09, 0.01)]


def torso_prof(z):
    for a, b in zip(TORSO, TORSO[1:]):
        if a[0] <= z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            return tuple(lerp(a[k], b[k], t) for k in (1, 2, 3))
    return TORSO[-1][1:]


def front_pt(x, z, lift=0.0):
    rx, ry, yo = torso_prof(z)
    return V((x, yo - ry * math.sqrt(max(0.0, 1 - (x / rx) ** 2)) - lift, z))


def build_torso(parts):
    nk = H.Part(["chest", "neck", ("head", lambda v: ss(1.86, 1.92, v.z))])
    H.tube(nk, [(0, 0.015, 1.72), (0, 0.012, 1.84), (0, 0.01, 1.95)], [0.078, 0.072, 0.07], 12, "skin")
    parts.append(nk)
    sh = lambda s: side_fn(s, lambda v: ss(0.05, 0.22, v.x) * ss(1.48, 1.62, v.z))
    ua = lambda s: side_fn(s, lambda v: 0.6 * ss(0.32, 0.42, v.x) * ss(1.5, 1.62, v.z))
    tp = H.Part(["hips", "spine", "chest", ("neck", lambda v: ss(1.78, 1.82, v.z)),
                 ("shoulder.L", sh(1)), ("shoulder.R", sh(-1)), ("upper_arm.L", ua(1)), ("upper_arm.R", ua(-1))])
    H.loft(tp, [vring(z, rx, ry, yo, 28) for z, rx, ry, yo in TORSO], "plum", True,
           V((0, 0, 0.99)), V((0, 0.01, 1.815)))
    f0 = len(tp.f)
    bvh = tp.bvh(0, f0)
    # shirt V + gold lapel edges + double-breasted buttons
    V_ = [(0.0, 1.43), (0.15, 1.77), (-0.15, 1.77)]
    H.decal(tp, bvh, FO, FR, FU, subdiv(V_, 10), "shirt", 0.004, rings=9)
    for s in (1, -1):
        e0, e1 = (0.0, 1.43), (0.15 * s, 1.77)
        top = [(lerp(e0[0], e1[0], t / 8), lerp(e0[1], e1[1], t / 8)) for t in range(9)]
        bot = [(x + 0.03 * s, z) for x, z in top]
        if s < 0:
            top, bot = top[::-1], bot[::-1]
        H.decal_strip(tp, bvh, FO, FR, FU, top, bot, "gold", 0.005)
        for z in (1.22, 1.30, 1.38):
            H.ellipsoid(tp, front_pt(0.085 * s, z, 0.004), (0.016, 0.01, 0.016), 8, 5, "gold")
    # jabot ruffles
    for k, (z, r) in enumerate(((1.75, 0.05), (1.69, 0.046), (1.63, 0.04), (1.575, 0.032))):
        H.ellipsoid(tp, front_pt(0, z, 0.01), (r * 1.3, 0.02, 0.024), 12, 6, "shirt" if k % 2 == 0 else "shirt_dk", exp=0.7)
    parts.append(tp)

    # belt + buckle
    bp = H.Part(["hips", "spine"])
    rows = []
    for z, dr in ((1.10, 0.004), (1.105, 0.016), (1.175, 0.016), (1.18, 0.004)):
        rx, ry, yo = torso_prof(z)
        rows.append(vring(z, rx + dr, ry + dr, yo, 24))
    H.loft(bp, rows, "belt")
    p = front_pt(0, 1.14, 0.02)
    H.ellipsoid(bp, p, (0.05, 0.012, 0.04), 10, 6, "gold", exp=0.3)
    H.ellipsoid(bp, p - V((0, 0.008, 0)), (0.03, 0.006, 0.022), 8, 4, "belt", exp=0.3)
    parts.append(bp)

    # epaulettes: gold dome + downward-hooking spikes
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        ep = H.Part([f"shoulder.{S}", (f"upper_arm.{S}", lambda v: 0.35), ("chest", lambda v: 0.15)])
        c = V((0.38 * s, 0.0, 1.765))
        nrm = V((0.35 * s, 0, 1)).normalized()
        B = H.axes(V((1, 0, -0.35 * s)).normalized() * s, (0, 1, 0), nrm)
        H.ellipsoid(ep, c, (0.15, 0.14, 0.045), 14, 8, lambda i, j: "gold_dk" if i <= 1 else "gold", B)
        H.ellipsoid(ep, c + nrm * 0.035, (0.05, 0.05, 0.02), 10, 5, "gold_lt", B)
        for k in range(7):
            a = math.radians(-75 + 150 * k / 6)  # fan around the outer rim
            out = V((math.cos(a) * s, math.sin(a), 0))
            base = c + V((out.x * 0.125, out.y * 0.115, -0.01))
            tip_dir = (out * 1.0 + V((0, 0, 0.25))).normalized()
            L = 0.15 if k % 2 == 0 else 0.10
            pts = [base, base + tip_dir * L * 0.5]
            H.tube(ep, pts, [0.026, 0.017], 6, "gold", hint=V((0, 0, 1)), cap1=base + tip_dir * L + V((0, 0, -0.035)))
        parts.append(ep)

    # tall flared collar (open front)
    cl = H.Part(["chest", ("neck", lambda v: 0.7 * ss(1.8, 1.95, v.z))])
    P = []
    for z, rx, ry, yo, al in ((2.03, 0.215, 0.185, 0.06, 1.05), (1.95, 0.165, 0.145, 0.045, 0.95),
                              (1.87, 0.135, 0.12, 0.03, 0.85), (1.79, 0.15, 0.125, 0.02, 0.75)):
        P.append([V((rx * math.sin(ph), yo - ry * math.cos(ph), z)) for ph in
                  [lerp(al, 2 * math.pi - al, k / 19) for k in range(20)]])
    H.sheet(cl, P, 0.012, lambda r, c: "gold" if r == 0 else "plum", "plum_dk",
            dict(top="gold", bottom="plum_dk", left="gold", right="gold"))
    parts.append(cl)


COAT = [(1.17, 0.168, 0.138, 0.0, 0.22), (1.06, 0.195, 0.16, 0.01, 0.36), (0.95, 0.222, 0.182, 0.02, 0.48),
        (0.85, 0.245, 0.2, 0.03, 0.57), (0.76, 0.265, 0.215, 0.04, 0.64), (0.68, 0.28, 0.226, 0.048, 0.70),
        (0.62, 0.288, 0.232, 0.052, 0.73)]


def build_coat(parts):
    def thigh(s):
        return side_fn(s, lambda v: ss(1.10, 0.95, v.z) * ss(0.10, -0.08, v.y) * ss(-0.06, 0.06, v.x))

    def tail(s):
        return side_fn(s, lambda v: ss(1.12, 0.95, v.z) * ss(-0.08, 0.08, v.y) * ss(-0.1, 0.04, v.x))
    spec = ["hips", ("spine", lambda v: ss(1.1, 1.18, v.z))]
    for s, S in ((1, "L"), (-1, "R")):
        spec += [(f"thigh.{S}", thigh(s)), (f"coat_tail.{S}", tail(s))]
    cp = H.Part(spec)
    N = 24
    P = []
    for z, rx, ry, yo, al in COAT:
        dl = 0.016 / rx
        phis = [al, al + dl] + [lerp(al + dl, 2 * math.pi - al - dl, k / (N - 1)) for k in range(1, N - 1)] \
            + [2 * math.pi - al - dl, 2 * math.pi - al]
        P.append([V((rx * math.sin(p), yo - ry * math.cos(p), z)) for p in phis])
    R, C = len(P), len(P[0])
    H.sheet(cp, P, 0.014, lambda r, c: "gold" if (c in (0, C - 2) or r == R - 2) else "plum",
            "plum_dk", dict(top="plum_dk", bottom="gold", left="gold", right="gold"))
    parts.append(cp)


def build_legs(parts):
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        X = lambda p: V((p[0] * s, p[1], p[2]))
        lp = H.Part(["hips", f"thigh.{S}", (f"shin.{S}", lambda v: 0.5 * ss(0.66, 0.56, v.z))])
        H.tube(lp, [X(p) for p in ((0.105, 0, 1.08), (0.112, -0.004, 0.88), (0.118, -0.008, 0.70),
                                   (0.121, -0.01, 0.58))], [0.10, 0.088, 0.072, 0.066], 12, "pants", hint=V((s, 0, 0)))
        parts.append(lp)
        bt = H.Part([f"shin.{S}", (f"thigh.{S}", lambda v: ss(0.6, 0.68, v.z)), (f"foot.{S}", lambda v: ss(0.16, 0.08, v.z))])
        kn, an = V(J["knee"]), V(J["ankle"])
        rings = []
        for z, r in ((0.09, 0.074), (0.16, 0.072), (0.30, 0.08), (0.44, 0.084), (0.5, 0.088), (0.51, 0.112),
                     (0.58, 0.118), (0.6, 0.106), (0.602, 0.072)):
            c = lerp(an, kn, (z - an.z) / (kn.z - an.z))
            rings.append(vring(z, r, r * 0.95, c.y, 14, c.x * s))
        H.loft(bt, rings, lambda i, j: "gold" if i == 6 else ("boot_lt" if i >= 4 else "boot"))
        v0 = len(bt.v)
        f0 = len(bt.f)
        H.ellipsoid(bt, (0.128 * s, -0.05, 0.06), (0.072, 0.15, 0.062), 14, 10, "boot")
        for k in range(v0, len(bt.v)):
            p = bt.v[k]
            if p.y < -0.09:
                p.z += 2.2 * (-0.09 - p.y) ** 2
                p.x = lerp(p.x, 0.13 * s, ss(-0.1, -0.2, p.y) * 0.5)
            p.z = max(p.z, 0.0)
        bt.recolor(f0, lambda c, n: "boot_lt" if c.z < 0.014 else None)
        parts.append(bt)


# ----------------------------------------------------------------------------- arms
def arm_frame(s):
    d = V((D_ARM.x * s, 0, D_ARM.z))
    sj = V((J["arm"][0] * s, J["arm"][1], J["arm"][2]))
    o = V((-D_ARM.z * s, 0, D_ARM.x))  # outward, perpendicular to the arm
    return d, sj, o.normalized()


def build_arms(parts):
    for s in (1, -1):
        S = "L" if s > 0 else "R"
        d, sj, o = arm_frame(s)
        at = lambda u: sj + d * u
        u_of = lambda v: (v - sj).dot(d)
        hint = V((0, -1, 0))
        sh_w = (f"shoulder.{S}", lambda v, u_of=u_of: ss(0.12, -0.02, u_of(v)))
        if s > 0:  # plum sleeve, big turned-back cuff, black glove
            sp = H.Part([sh_w, f"upper_arm.{S}", f"forearm.{S}", (f"hand.{S}", lambda v: 0.12)])
            us = [-0.04, 0.03, 0.12, 0.25, 0.38, 0.50, 0.60, 0.62, 0.635, 0.66, 0.71, 0.74, 0.745]
            rs = [0.10, 0.118, 0.115, 0.106, 0.098, 0.094, 0.09, 0.09, 0.12, 0.13, 0.128, 0.12, 0.07]
            fc = ["plum"] * 7 + ["plum_dk", "gold", "plum_lt", "plum_lt", "gold"]
            H.tube(sp, [at(u) for u in us], rs, 14, lambda i, j: fc[min(max(i, 0), len(fc) - 1)], hint=hint)
            parts.append(sp)
            gp = H.Part([f"forearm.{S}", f"hand.{S}"])
            H.tube(gp, [at(u) for u in (0.70, 0.75, 0.78)], [0.07, 0.068, 0.062], 10, "glove", hint=hint)
            parts.append(gp)
            hp = H.Part([f"hand.{S}", (f"forearm.{S}", lambda v: 0.2)])
            g = V((0, -1, 0))
            p = d.cross(g).normalized()
            if p.x * s > 0:
                p = -p
            H.fist(hp, at(0.76), d, g, p, "glove", size=1.9)
            parts.append(hp)
        else:  # sleeve to the elbow, then the iron winch-gauntlet
            sp = H.Part([sh_w, f"upper_arm.{S}", (f"forearm.{S}", lambda v: 0.5)])
            us = [-0.04, 0.03, 0.12, 0.25, 0.34, 0.37, 0.40, 0.42]
            rs = [0.10, 0.118, 0.115, 0.108, 0.104, 0.122, 0.124, 0.10]
            H.tube(sp, [at(u) for u in us], rs, 14, lambda i, j: "gold" if i >= 5 else "plum", hint=hint)
            parts.append(sp)
            build_gauntlet(parts, d, sj, o, at, u_of)


def build_gauntlet(parts, d, sj, o, at, u_of):
    gp = H.Part(["forearm.R", ("hand.R", lambda v: 3.0 * ss(0.84, 0.92, u_of(v))),
                 ("upper_arm.R", lambda v: 0.6 * ss(0.44, 0.38, u_of(v)))], smooth=True)
    f = V((0, -1, 0))
    n = 16
    spec = [(0.38, 0.105, 0.105, "iron_dk"), (0.42, 0.12, 0.125, "iron"), (0.50, 0.135, 0.14, "iron"),
            (0.53, 0.14, 0.145, "iron_lt"), (0.56, 0.14, 0.145, "iron"), (0.70, 0.145, 0.15, "iron"),
            (0.78, 0.148, 0.152, "iron_lt"), (0.81, 0.148, 0.152, "iron"), (0.90, 0.15, 0.155, "iron"),
            (0.925, 0.168, 0.172, "gold"), (0.975, 0.168, 0.172, "gold"), (0.985, 0.15, 0.155, "iron_dk"),
            (0.99, 0.092, 0.092, "bore"), (0.94, 0.085, 0.085, "bore")]
    rings = [H.ring(at(u), d, rx, ry, n, hint=o) for u, rx, ry, _ in spec]
    H.loft(gp, rings, lambda i, j: spec[min(max(i, 0), len(spec) - 1)][3] if i < len(spec) - 1 else "bore",
           True, None, at(0.93))
    # rivets on the two light bands
    for u in (0.545, 0.795):
        for k in range(8):
            a = 2 * math.pi * k / 8 + 0.2
            r = o * math.cos(a) + f * math.sin(a)
            H.ellipsoid(gp, at(u) + r * 0.152, (0.012, 0.012, 0.012), 6, 4, "iron_lt")
    # winch drum on the outer side: gold-rimmed flanges, hub and crank
    c = at(0.62) + o * 0.155
    drum = [(-0.07, 0.05), (-0.065, 0.125), (-0.04, 0.125), (-0.036, 0.088), (0.036, 0.088),
            (0.04, 0.125), (0.065, 0.125), (0.07, 0.06)]
    dc = ["gold", "gold", "iron", "iron_dk", "iron", "gold", "gold"]
    H.loft(gp, [H.ring(c + o * w, o, r, r, 18, hint=d) for w, r in drum],
           lambda i, j: dc[min(max(i, 0), len(dc) - 1)], True, "center", "center")
    for k in range(10):  # gear teeth on the outer flange
        a = 2 * math.pi * k / 10
        r = d * math.cos(a) + f * math.sin(a)
        H.ellipsoid(gp, c + o * 0.052 + r * 0.13, (0.016, 0.016, 0.016), 6, 4, "gold_dk",
                    H.axes(r, r.cross(o), o), exp=0.5)
    hub = c + o * 0.08
    H.ellipsoid(gp, hub, (0.04, 0.04, 0.02), 10, 5, "gold_lt", H.axes(d, f, o))
    crank = [hub, hub + o * 0.03, hub + o * 0.04 - d * 0.07]
    H.tube(gp, crank, [0.012, 0.012, 0.012], 6, "iron_lt", hint=f, cap0="center", cap1="center")
    H.ellipsoid(gp, hub + o * 0.06 - d * 0.075, (0.018, 0.018, 0.026), 8, 5, "gold", H.axes(d, f, o))
    # heavy top plate along the forearm (front side) for a chunkier read
    for u in (0.47, 0.66):
        H.ellipsoid(gp, at(u) - o * 0.02 + f * 0.13, (0.07, 0.03, 0.06), 10, 6, "iron", H.axes(o, f, d), exp=0.5)
    parts.append(gp)


# ----------------------------------------------------------------------------- animation
def mir(p):
    """Swap L/R and negate lean/turn of centre bones (anatomical values stay valid)."""
    out = {}
    for k, v in p.items():
        if k == "hips_loc":
            out[k] = (-v[0], v[1], v[2])
        elif k.endswith((".L", ".R")):
            out[k[:-1] + ("R" if k[-1] == "L" else "L")] = v
        else:
            out[k] = (v[0], -v[1], -v[2])
    return out


BASE = pose(hips_loc=(0, 0, -0.02), spine=(-3, 0, 0), chest=(-7, 0, 0), neck=(2, 0, 0), head=(-6, 0, 0),
            thigh=(-3, -7, 0), shin=(6, 0, 0), foot=(-3, 7, 0),
            upper_arm=((4, -12, 0), (-10, -10, 0)), forearm=((-25, 0, 0), (-18, 0, 0)), coat_tail=(4, 0, 0))
WIDE = dict(hips_loc=(0, 0, -0.11), thigh=(-22, -18, 0), shin=(40, 0, 0), foot=(-18, 18, 0))


def build_actions(arm):
    acts = {}
    K = lambda name, keys, loop=False: acts.__setitem__(name, H.key_clip(arm, name, keys, loop))

    # idle 2.0 s: chest-out swagger, weight rocks side to side, plume bobs
    a = over(BASE, hips_loc=(0.025, 0, -0.025), hips=(0, 4, 0), spine=(-3, -3, 4), chest=(-9, -2, 6),
             head=(-9, 4, -6), plume=(-6, 0, 0))
    b = over(BASE, hips_loc=(-0.025, 0, -0.025), hips=(0, -4, 0), spine=(-3, 3, -4), chest=(-6, 2, -6),
             head=(-4, -3, 6), plume=(6, 0, 0), upper_arm=((4, -12, 0), (-16, -10, 0)))
    K("idle", [(0, BASE), (15, a), (30, BASE), (45, b), (60, BASE)], True)

    # walk 32 f: heavy strut, shoulders roll against the hips
    cL = pose(hips_loc=(0, 0, -0.045), hips=(0, 0, -8), spine=(-2, 0, 4), chest=(-8, 0, 12), head=(-6, 0, -8),
              thigh=((-28, -4, 0), (20, -4, 0)), shin=((8, 0, 0), (30, 0, 0)), foot=((-6, 4, 0), (12, 4, 0)),
              upper_arm=((22, -14, 0), (-26, -12, 0)), forearm=((-20, 0, 0), (-28, 0, 0)),
              coat_tail=((4, 0, 0), (18, 0, 0)), plume=(6, 0, 0))
    pL = pose(hips_loc=(0, 0, 0.0), spine=(-4, 0, 0), chest=(-9, 0, 0), head=(-6, 0, 0),
              thigh=((-4, -4, 0), (-28, -4, 0)), shin=((6, 0, 0), (75, 0, 0)), foot=((-4, 4, 0), (12, 4, 0)),
              upper_arm=((2, -14, 0), (-8, -12, 0)), forearm=((-24, 0, 0), (-20, 0, 0)),
              coat_tail=(14, 0, 0), plume=(-6, 0, 0))
    K("walk", [(0, cL), (8, pL), (16, mir(cL)), (24, mir(pL)), (32, cL)], True)

    # sweep_tell 0.8 s: plant wide, gauntlet raised and circling overhead
    tell = over(BASE, spine=(4, 0, -6), chest=(-6, 0, -12), head=(-10, 0, 10), upper_arm_L=(-40, -55, -10),
                forearm_L=(-30, 0, 0), forearm_R=(-55, 0, 0), coat_tail=(-6, 0, 0), **WIDE)
    circ = [over(tell, upper_arm_R=(-162, -18, -90 * k), shoulder_R=(0, -12, 0), plume=(8 * math.cos(k * 1.57), 0, 0))
            for k in range(5)]
    K("sweep_tell", [(0, BASE), (4, circ[0]), (9, circ[1]), (14, circ[2]), (19, circ[3]), (24, circ[4])])

    # sweep 0.45 s: wind back -> fast horizontal arc across the front -> follow-through
    sw0 = over(tell, hips=(0, 0, -10), spine=(4, 0, -15), chest=(-4, 0, -35), head=(-8, 0, 25),
               upper_arm_R=(0, -78, 45), forearm_R=(-8, 0, 0), upper_arm_L=(-30, -60, -30), coat_tail=(0, 0, 0))
    sw1 = over(sw0, hips=(0, 0, 0), spine=(6, 0, 0), chest=(0, 0, 0), head=(-8, 0, 5), upper_arm_R=(0, -82, 0))
    sw2 = over(sw0, hips=(0, 0, 12), spine=(8, 0, 15), chest=(2, 0, 35), head=(-8, 0, -20),
               upper_arm_R=(0, -80, -80), upper_arm_L=(10, -50, 20), coat_tail=((25, 0, 0), (5, 0, 0)))
    sw3 = over(sw2, chest=(4, 0, 48), spine=(10, 0, 18), upper_arm_R=(5, -70, -115), forearm_R=(-20, 0, 0),
               coat_tail=((35, 0, 0), (0, 0, 0)), plume=(-12, 0, 0))
    K("sweep", [(0, sw0), (3, sw1), (6, sw2), (9.5, sw3), (13.5, mix(sw3, tell, 0.25))])

    # stuck (loop): leaning back, both hands hauling on the chain in front
    st0 = pose(hips_loc=(0, 0.06, -0.14), hips=(-10, 0, 0), spine=(-12, 0, 0), chest=(-6, 0, 0), head=(14, 0, 0),
               thigh=((-38, -8, 0), (22, -8, 0)), shin=((40, 0, 0), (32, 0, 0)), foot=((8, 8, 0), (-30, 8, 0)),
               upper_arm=((-34, 14, -18), (-30, 8, -10)), forearm=((-38, 0, 0), (-22, 0, 0)),
               coat_tail=(-4, 0, 0), plume=(10, 0, 0))
    st1 = over(st0, hips_loc=(0, 0.12, -0.17), hips=(-16, 0, 0), spine=(-18, 0, 0), chest=(-8, 0, 3), head=(18, 0, -4),
               upper_arm=((-14, 16, -18), (-10, 8, -8)), forearm=((-70, 0, 0), (-55, 0, 0)), plume=(-8, 0, 0))
    st2 = over(st1, chest=(-6, 0, -4), head=(16, 0, 5), hips_loc=(0, 0.115, -0.168))
    K("stuck", [(0, st0), (12, st1), (20, st2), (28, mix(st1, st0, 0.6)), (40, st0)], True)

    # shot_tell 0.6 s: square up, gauntlet aimed straight ahead (-Y)
    aim = over(BASE, hips_loc=(0, 0, -0.06), hips=(0, 0, 6), spine=(2, 0, 4), chest=(-2, 0, 6), head=(-4, 0, -8),
               thigh=((10, -8, 0), (-22, -6, 0)), shin=((18, 0, 0), (22, 0, 0)), foot=((-22, 8, 0), (0, 6, 0)),
               upper_arm_R=(-88, 0, -30), forearm_R=(0, 0, 0), upper_arm_L=(12, -38, 0), forearm_L=(-45, 0, 0),
               shoulder_R=(0, 0, -8))
    aim2 = over(aim, upper_arm_R=(-89, 0, -31), chest=(-3, 0, 7))
    K("shot_tell", [(0, BASE), (6, aim), (12, aim2), (18, aim)])

    # shot 0.2 s: muzzle kicks up, body rocks back
    kick = over(aim, upper_arm_R=(-120, 0, -30), forearm_R=(-14, 0, 0), spine=(-6, 0, 2), chest=(-12, 0, 4),
                head=(-14, 0, -8), hips_loc=(0, 0.04, -0.05), plume=(-14, 0, 0), coat_tail=(-10, 0, 0))
    K("shot", [(0, aim), (2, kick), (6, mix(kick, aim, 0.6))])

    # stunned (loop): dizzy circling head, sagging knees, hat knocked askew
    def dz(k):
        a = k * math.pi / 2
        return pose(hips_loc=(0.03 * math.sin(a), 0, -0.07), hips=(0, 4 * math.sin(a), 0),
                    spine=(6 + 4 * math.cos(a), 6 * math.sin(a), 0), chest=(8, 5 * math.sin(a + 1), 0),
                    neck=(6, 0, 0), head=(12 + 10 * math.cos(a), 14 * math.sin(a), 8 * math.sin(a)),
                    thigh=(-14, -6, 0), shin=(28, 0, 0), foot=(-14, 6, 0),
                    upper_arm=((-4 + 6 * math.sin(a), -16, 0), (-6, -12, 0)), forearm=((-8, 0, 0), (-6, 0, 0)),
                    hat=(-10, 30, 14), plume=(28 + 8 * math.cos(a), 0, 0), coat_tail=(4, 0, 0))
    K("stunned", [(k * 10, dz(k)) for k in range(5)], True)

    # death: recoil, stagger, topple backward, bounce, hold
    rec = over(BASE, spine=(-14, 0, 6), chest=(-16, 0, 4), head=(-24, 0, 8), upper_arm=((-20, -60, 0), (-30, -55, 0)),
               forearm=(-30, 0, 0), hat=(-15, 0, 0))
    stag = pose(hips_loc=(0, 0.14, -0.06), hips=(-14, 0, 4), spine=(-12, 0, 6), chest=(-10, 0, 0), head=(-20, 0, 10),
                thigh=((-34, -6, 0), (10, -8, 0)), shin=((30, 0, 0), (10, 0, 0)), foot=((10, 6, 0), (-10, 6, 0)),
                upper_arm=((-50, -70, 0), (-60, -60, 0)), forearm=(-30, 0, 0), hat=(-30, 10, 0), coat_tail=(-10, 0, 0))
    fall = pose(hips_loc=(0, 0.32, -0.42), hips=(-50, 0, 6), spine=(-8, 0, 0), head=(-10, 0, 10),
                thigh=((28, -8, 0), (40, -8, 0)), shin=((20, 0, 0), (35, 0, 0)), foot=(10, 0, 0),
                upper_arm=((-80, -80, 0), (-90, -75, 0)), forearm=(-20, 0, 0), hat=(-60, 15, 0),
                coat_tail=(-25, 0, 0), plume=(20, 0, 0))
    flat = pose(hips_loc=(0, 0.42, -0.9), hips=(-88, 0, 4), spine=(-2, 0, 0), head=(4, 0, 55),
                thigh=((6, -10, 0), (2, -6, 0)), shin=((8, 0, 0), (14, 0, 0)), foot=(35, 0, 0),
                upper_arm=((-8, -80, 0), (-12, -62, 0)), forearm=((0, 30, 0), (-5, 0, 0)),
                hat=(-100, 0, 0), coat_tail=(-35, 0, 0), plume=(30, 0, 0))
    bounce = over(flat, hips_loc=(0, 0.42, -0.86), hips=(-84, 0, 4), thigh=((-6, -10, 0), (-10, -6, 0)),
                  head=(-2, 0, 50))
    K("death", [(0, BASE), (4, rec), (11, stag), (19, fall), (25, flat), (29, bounce), (36, flat)])
    return acts


def build_parts():
    parts = []
    build_head(parts)
    build_hat(parts)
    build_torso(parts)
    build_coat(parts)
    build_legs(parts)
    build_arms(parts)
    return parts


SHOTS = [("idle", 15), ("walk", 0), ("sweep_tell", 9), ("sweep", 6), ("stuck", 12), ("shot_tell", 18),
         ("shot", 2), ("stunned", 10), ("death", 36)]
H.run_character("chainhook", PAL, BONES, build_parts, build_actions, height=2.6, shots=SHOTS, args=ARGS)
