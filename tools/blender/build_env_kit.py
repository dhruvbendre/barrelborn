"""Gullhaven modular environment kit (Blender 4.5, headless-safe, deterministic: no RNG, no operators on geometry).

From the project root (PowerShell):
    & "C:\\Program Files\\Blender Foundation\\Blender 4.5\\blender.exe" -b --factory-startup --python tools/blender/build_env_kit.py
    ... -- --no-render      skip contact sheet + harbor mock
    ... -- --verify         fresh-import every GLB and print tris / bbox / material count
    ... -- --qa <dir>       also write one 480 px render per module into <dir> (review only)

Every module is ONE mesh, ONE shared material (`env_palette`: a flat-swatch atlas, `assets/environment/env_palette.png`),
built in place at its contract origin with identity transforms. Contract + dimensions: tools/blender/ENV_KIT.md.
Axes while building: Blender X = gameplay lane, -Y = toward the camera, Z = up (exported as glTF/Godot +Y up, -Y -> +Z).
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import humanoid as H  # read-only reuse: Palette atlas, Part, tube/ellipsoid, palette UVs, render + contact sheet

ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "assets", "environment")
BLEND = os.path.join(ROOT, "art_source", "blender", "env_kit.blend")
PREV = os.path.join(ROOT, "art_source", "blender", "previews")
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

# Walkable tops are the lightest/warmest swatches; backgrounds (walls, rock faces, hull) sit darker or cooler.
PAL = H.Palette({
    "deck": "#ebb676", "deck_b": "#dea769", "deck_worn": "#b47c49", "pave": "#f6e0b0", "pave_b": "#ecd29e",
    "rock_top": "#97b8a8", "moss_top": "#8ab362", "seam": "#4e321d",
    "timber": "#8a5a36", "timber_dk": "#5e3a22", "timber_lt": "#a8744a", "crate": "#d3a165", "crate_b": "#c18f56",
    "crate_dk": "#93603a", "oak": "#a86f3f", "oak_b": "#94603a", "brand": "#3e2414",
    "stone": "#d8a268", "stone_b": "#c9915a", "stone_c": "#e2b67f", "stone_wet": "#a87b4e", "mortar": "#7e5a3b",
    "algae": "#4f6e45", "rock": "#5f8486", "rock_b": "#527579", "rock_dk": "#3c5c62", "moss": "#5e8a48",
    "wall": "#e8dbc0", "wall_sh": "#d4c4a6", "plinth": "#c9a274", "roof": "#c8573a", "roof_lt": "#d96d4a",
    "roof_dk": "#8f3a25", "shutter": "#2f8f8a", "shutter_dk": "#1f6662", "glass": "#2a3e52", "door": "#7a4a2a",
    "door_b": "#6a3f23", "leaf": "#5d8f45",
    "coral": "#e2483d", "gold": "#f2b630", "cream": "#f3e7c9", "teal": "#2fa6a0", "navy": "#26365e",
    "iron": "#3a3a42", "brass": "#c79a3b", "lamp": "#ffd98a", "rope": "#d2ac6e", "rope_dk": "#a5804b",
    "sail_sh": "#ddcfab", "antifoul": "#a8362f",
    "sea": "#2fb3b8",  # mock water plane only
}, cols=8, cell=16)


# ============================================================================= geometry primitives
def P():
    return H.Part([], smooth=False)


def poly(p, pts, col, away=None):
    """One flat face; with `away` the normal is flipped to point away from that point. Zero-area faces are dropped."""
    q = []
    for v in pts:
        v = Vector(v)
        if not q or (v - q[-1]).length > 1e-7:
            q.append(v)
    if len(q) > 1 and (q[0] - q[-1]).length < 1e-7:
        q.pop()
    if len(q) < 3:
        return
    n = Vector()
    for a, b in zip(q, q[1:] + q[:1]):
        n += a.cross(b)
    if n.length < 1e-8:
        return
    if away is not None and n.dot(sum(q, Vector()) / len(q) - Vector(away)) < 0:
        q.reverse()
    p.face([p.vert(v) for v in q], col)


def seg(cols):
    """tube()/loft() colour fn: per ring-segment colour list (caps clamp to the ends)."""
    return lambda i, j: cols[min(max(i, 0), len(cols) - 1)]


def basis(o, x, y, z):
    return Matrix(((x[0], y[0], z[0], o[0]), (x[1], y[1], z[1], o[1]), (x[2], y[2], z[2], o[2]), (0, 0, 0, 1)))


def xform(p, v0, M):
    for k in range(v0, len(p.v)):
        p.v[k] = M @ p.v[k]


SIDE = lambda ax, s: ("-" if s < 0 else "+") + "xyz"[ax]


def bbox(p, lo, hi, col, b=0.0, cut=(), M=None):
    """Box with chamfered edges (width b). col: name or {side: name, '*': default} (sides '-x'..'+z').
    `cut` sides get no chamfer on their edges, so a block split by a tile boundary rejoins seamlessly."""
    lo, hi = Vector(lo), Vector(hi)
    c, h = (lo + hi) / 2, (hi - lo) / 2
    M = M or Matrix.Identity(4)
    cols = col if isinstance(col, dict) else {"*": col}
    cut = set(cut)

    def colr(*sides):
        if "+z" in sides and "+z" in cols:  # chamfers take the top colour: walkable edges read light
            return cols["+z"]
        return cols.get(sides[0], cols["*"])

    def fv(ax, sg):
        q = Vector()
        for k in range(3):
            ins = 0.0 if k == ax or SIDE(ax, sg[ax]) in cut or SIDE(k, sg[k]) in cut else b
            q[k] = sg[k] * (h[k] - ins)
        return M @ (c + q)

    ctr = M @ c
    for ax in range(3):
        a1, a2 = [k for k in range(3) if k != ax]
        for s in (-1, 1):
            pts = []
            for u, v in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                sg = [0, 0, 0]
                sg[ax], sg[a1], sg[a2] = s, u, v
                pts.append(fv(ax, sg))
            poly(p, pts, colr(SIDE(ax, s)), ctr)
    if b <= 0:
        return
    for a1 in range(3):
        for a2 in range(a1 + 1, 3):
            a3 = 3 - a1 - a2
            for s1 in (-1, 1):
                for s2 in (-1, 1):
                    if SIDE(a1, s1) in cut or SIDE(a2, s2) in cut:
                        continue
                    pts = []
                    for t, ax in ((-1, a1), (1, a1), (1, a2), (-1, a2)):
                        sg = [0, 0, 0]
                        sg[a1], sg[a2], sg[a3] = s1, s2, t
                        pts.append(fv(ax, sg))
                    poly(p, pts, colr(SIDE(a1, s1), SIDE(a2, s2)), ctr)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                sg = [sx, sy, sz]
                if any(SIDE(k, sg[k]) in cut for k in range(3)):
                    continue
                poly(p, [fv(k, sg) for k in range(3)], colr(SIDE(2, sz), SIDE(0, sx)), ctr)


def prism(p, o, U, V, pts2, t, col):
    """Extrude a convex 2D outline (coords along U, V from o) by t along U x V."""
    o, U, V = Vector(o), Vector(U), Vector(V)
    N = U.cross(V).normalized()
    f = [o + U * a + V * b for a, b in pts2]
    k = [v + N * t for v in f]
    ctr = sum(f, Vector()) / len(f) + N * t / 2
    poly(p, f, col, ctr)
    poly(p, k, col, ctr)
    for i in range(len(f)):
        j = (i + 1) % len(f)
        poly(p, (f[i], f[j], k[j], k[i]), col, ctr)


def cyl(p, a, b, r, n, col, r1=None, phase=None):
    phase = math.pi / n if phase is None else phase
    H.tube(p, [a, b], [r, r if r1 is None else r1], n, col, cap0="center", cap1="center", phase=phase)


def lathe(p, x, y, prof, n, cols, phase=None):
    """Vertical turned shape. prof: [(z, r)], cols: per-segment colour list."""
    H.tube(p, [(x, y, z) for z, _ in prof], [r for _, r in prof], n, seg(cols), cap0="center", cap1="center",
           phase=math.pi / n if phase is None else phase)


def cup(p, c, r_out, r_in, z0, z1, n, col, rim):
    """Open-top round tub (crow's nest): outer + inner wall, rim, floor."""
    c = Vector(c)
    ang = [2 * math.pi * k / n for k in range(n + 1)]
    P2 = lambda r, a, z: c + Vector((r * math.cos(a), r * math.sin(a), z))
    for a, b in zip(ang, ang[1:]):
        poly(p, (P2(r_out, a, z0), P2(r_out, b, z0), P2(r_out, b, z1), P2(r_out, a, z1)), col, c + Vector((0, 0, (z0 + z1) / 2)))
        mid = (a + b) / 2
        poly(p, (P2(r_in, a, z0 + 0.06), P2(r_in, b, z0 + 0.06), P2(r_in, b, z1), P2(r_in, a, z1)), col,
             P2(r_out * 3, mid, (z0 + z1) / 2))
        poly(p, (P2(r_in, a, z1), P2(r_in, b, z1), P2(r_out, b, z1), P2(r_out, a, z1)), rim, c + Vector((0, 0, z0)))
    poly(p, [P2(r_in, a, z0 + 0.06) for a in ang[:-1]], "timber_lt", c + Vector((0, 0, z0 - 1)))
    poly(p, [P2(r_out, a, z0) for a in ang[:-1]], col, c + Vector((0, 0, z1 + 1)))


# ============================================================================= tiles
def dock_2m():
    p = P()
    bbox(p, (-1, -1.9, -0.32), (1, 2, -0.03), "seam")          # shadow bed: shows through the plank seams
    bbox(p, (-1, -1.66, -1.2), (1, -1.56, -0.3), "seam")       # dark under-deck backing behind the bracing
    tones = ["deck", "deck_b", "deck_worn", "deck", "deck_b", "deck", "deck_worn", "deck_b"]
    splits = {1: -0.55, 4: 0.8}                                # butt joints, staggered
    for i, tone in enumerate(tones):  # planks 0.25 m wide run across the lane; seams split evenly at tile edges
        x0 = -1 + 0.25 * i
        ys = [-2.0, splits[i], 2.0] if i in splits else [-2.0, 2.0]
        for y0, y1 in zip(ys, ys[1:]):
            bbox(p, (x0 + 0.012, y0 + (0.01 if y0 > -2 else 0), -0.1), (x0 + 0.238, y1 - (0.01 if y1 < 2 else 0), 0),
                 tone, b=0.022)
    bbox(p, (-1, -1.97, -0.42), (1, -1.78, -0.1), {"*": "timber", "+z": "timber_lt"}, b=0.03, cut=("-x", "+x"))
    bbox(p, (-1, -1.95, -1.2), (1, -1.78, -0.95), "timber_dk", b=0.03, cut=("-x", "+x"))
    for (xa, za, xb, zb), y in (((-0.45, -0.45, 0.45, -0.95), -1.86), ((-0.45, -0.95, 0.45, -0.45), -1.8)):
        L, th = math.hypot(xb - xa, zb - za), math.atan2(-(zb - za), xb - xa)
        M = Matrix.Translation(((xa + xb) / 2, y, (za + zb) / 2)) @ Matrix.Rotation(th, 4, "Y")
        bbox(p, (-L / 2, -0.035, -0.06), (L / 2, 0.035, 0.06), "timber", b=0.015, M=M)
    for x in (-0.5, 0.5):  # piles: algae foot, wet band, rope lashing
        prof = [(-2.6, 0.16), (-1.75, 0.16), (-1.6, 0.16), (-0.72, 0.16), (-0.7, 0.18), (-0.56, 0.18), (-0.54, 0.16),
                (-0.1, 0.15)]
        lathe(p, x, -1.83, prof, 8, ["algae", "timber_dk", "timber", "rope_dk", "rope", "rope_dk", "timber"])
    return p


def seawall_2m():
    p = P()
    bbox(p, (-1, -1.9, -1.4), (1, 2, -0.15), "mortar")
    for x0, x1 in ((-1, 0), (0, 1)):  # coping: overhangs the face, walkable top is the lightest stone
        bbox(p, (x0, -2.0, -0.32), (x1, -1.3, 0), {"*": "stone_c", "+z": "pave"}, b=0.06)
    rows = (((-1.3, 0.35), [(-1, -0.5, ("-x",)), (-0.5, 0.5, ()), (0.5, 1, ("+x",))], ["pave_b", "pave", "pave_b"]),
            ((0.35, 2.0), [(-1, 0, ()), (0, 1, ())], ["pave", "pave_b"]))
    for (y0, y1), blocks, tops in rows:
        for (x0, x1, cut), top in zip(blocks, tops):
            bbox(p, (x0, y0, -0.2), (x1, y1, 0), {"*": "stone", "+z": top}, b=0.04, cut=cut)
    courses = (  # (top z, bottom z, blocks (x0, x1, cut sides, colour)) - joints staggered, seamless across tiles
        (-0.32, -0.68, [(-1, -0.45, ("-x",), "stone"), (-0.45, 0.5, (), "stone_c"), (0.5, 1, ("+x",), "stone")]),
        (-0.68, -1.04, [(-1, -0.05, (), "stone_b"), (-0.05, 1, (), "stone")]),
        (-1.04, -1.4, [(-1, -0.6, ("-x",), "stone_wet"), (-0.6, 0.3, (), "stone_b"), (0.3, 1, ("+x",), "stone_wet")]),
    )
    for zt, zb, blocks in courses:
        for x0, x1, cut, col in blocks:
            bbox(p, (x0, -1.96, zb), (x1, -1.78, zt), col, b=0.05, cut=cut)
    return p


def stone_block_1m():
    p = P()
    bbox(p, (-0.5, -1.5, -1), (0.5, 1.5, 0), {"*": "stone", "+z": "pave", "-y": "stone_c"}, b=0.07)
    return p


def cave_rock_2m():
    p = P()
    NX = 16
    xs = [-1 + 2 * i / NX for i in range(NX + 1)]
    S = lambda x, a, k, ph: a * math.sin(k * math.pi * x + ph)  # integer k -> period divides 2 m: tiles along X
    zb = lambda x: -1.2 + 0.06 * (1 - math.cos(2 * math.pi * x)) + 0.05 * (1 - math.cos(6 * math.pi * x))
    rowdef = [  # (z(x), recess-from-front d(x)) top -> bottom
        (lambda x: 0.0, lambda x: 0.10 + S(x, 0.03, 2, 0.4)),
        (lambda x: -0.17 + S(x, 0.06, 3, 2.0), lambda x: 0.02 + S(x, 0.025, 3, 1.1)),      # mossy overhang lip
        (lambda x: -0.42 + S(x, 0.06, 2, 0.9), lambda x: 0.24 + S(x, 0.09, 2, 2.3) + S(x, 0.05, 5, 0)),
        (lambda x: -0.68 + S(x, 0.05, 3, 0.2), lambda x: 0.12 + S(x, 0.11, 1, 0.7) + S(x, 0.05, 4, 1.0)),
        (lambda x: -0.95 + S(x, 0.05, 2, 1.7), lambda x: 0.2 + S(x, 0.08, 3, 2.6)),
        (zb, lambda x: 0.32 + S(x, 0.08, 2, 1.9)),
    ]
    dmin = min(fd(x) for _, fd in rowdef for x in xs)
    rows = [[Vector((x, -2 + fd(x) - dmin, fz(x))) for x in xs] for fz, fd in rowdef]
    for r in range(len(rows) - 1):
        for i in range(NX):
            a, b, c, d = rows[r][i], rows[r][i + 1], rows[r + 1][i + 1], rows[r + 1][i]
            tris = ((a, b, c), (a, c, d)) if (i + r) % 2 else ((a, b, d), (b, c, d))
            for k, t in enumerate(tris):
                hsh = (i * 7 + r * 13 + k * 5) % 11
                if r == 0 or (r == 1 and hsh in (1, 4, 8) and k == 0):
                    col = "moss"                                       # moss lip + a few drips
                elif r >= 4:
                    col = "rock_dk" if hsh % 3 else "rock_b"
                else:
                    col = ("rock", "rock_b", "rock", "rock_dk")[hsh % 4]
                cen = sum(t, Vector()) / 3
                poly(p, t, col, cen + Vector((0, 1, 0)))
    ym = lambda x: -1.62 + S(x, 0.07, 3, 0.5)
    for i in range(NX):
        x0, x1 = xs[i], xs[i + 1]
        e0, e1 = rows[0][i], rows[0][i + 1]
        m0, m1 = Vector((x0, ym(x0), 0)), Vector((x1, ym(x1), 0))
        poly(p, (e0, e1, m1, m0), "moss_top", (0, 0, -1))
        poly(p, (m0, m1, (x1, 2, 0), (x0, 2, 0)), "rock_top", (0, 0, -1))
    for side, idx in ((-1, 0), (1, NX)):  # end caps share the same profile (periodic) -> seamless
        prof = [rows[r][idx] for r in range(len(rows))]
        poly(p, prof + [Vector((side, 2, zb(side))), Vector((side, 2, 0))], "rock_dk", (0, 0, -0.6))
    return p


# ============================================================================= houses
def roof(p, along, across, Hh, pitch, over, side_over, K=5):
    """Ridge along local X. Tiled courses = bevelled slabs with dark gaps, alternating tone; gable ends whitewash."""
    a = math.radians(pitch)
    half = across / 2
    rz = Hh + half * math.tan(a)
    slope = (half + over) / math.cos(a)
    xa = along / 2 + side_over
    for s in (-1, 1):
        poly(p, [(s * along / 2, -half, Hh), (s * along / 2, half, Hh), (s * along / 2, 0, rz)], "wall", (0, 0, Hh))
    for sy in (-1, 1):
        u = Vector((0, sy * math.cos(a), -math.sin(a)))
        n = Vector((0, sy * math.sin(a), math.cos(a)))
        M = basis((0, 0, rz), (1, 0, 0), u, n)
        bbox(p, (-xa, -0.02, -0.12), (xa, slope, 0.0), "roof_dk", M=M)
        step = slope / K
        for k in range(K):
            bbox(p, (-xa, k * step + 0.02, -0.01), (xa, (k + 1) * step - 0.02, 0.085),
                 "roof" if (K - k) % 2 else "roof_lt", b=0.035, M=M)
    cyl(p, (-xa - 0.04, 0, rz + 0.05), (xa + 0.04, 0, rz + 0.05), 0.12, 6, "roof_dk")
    return rz


def house(W, Hh, pitch, gable_front, feats, D=3.0, over=0.35, side_over=0.3):
    p = P()
    F = -D / 2
    bbox(p, (-W / 2 - 0.06, F - 0.06, 0), (W / 2 + 0.06, D / 2 + 0.06, 0.3), "plinth", b=0.03)
    bbox(p, (-W / 2, F, 0.25), (W / 2, D / 2, Hh), "wall", b=0.04)
    bbox(p, (-W / 2 - 0.05, F - 0.05, Hh - 0.16), (W / 2 + 0.05, D / 2 + 0.05, Hh), "wall_sh", b=0.02)
    v0 = len(p.v)
    if gable_front:
        roof(p, D, W, Hh, pitch, over, side_over)
        xform(p, v0, Matrix.Rotation(math.pi / 2, 4, "Z"))
    else:
        roof(p, W, D, Hh, pitch, over, side_over)
    feats(p, F)
    return p


def door(p, F, x, w=1.0, h=2.1, z0=0.3, col=("door", "door_b"), step=True):
    bbox(p, (x - w / 2 - 0.14, F - 0.08, z0), (x - w / 2, F + 0.02, z0 + h), "plinth", b=0.02)
    bbox(p, (x + w / 2, F - 0.08, z0), (x + w / 2 + 0.14, F + 0.02, z0 + h), "plinth", b=0.02)
    bbox(p, (x - w / 2 - 0.2, F - 0.1, z0 + h), (x + w / 2 + 0.2, F + 0.02, z0 + h + 0.16), "plinth", b=0.03)
    for k in range(3):
        a = x - w / 2 + k * w / 3
        bbox(p, (a + 0.008, F - 0.03, z0), (a + w / 3 - 0.008, F + 0.02, z0 + h), col[k % 2])
    bbox(p, (x + w / 2 - 0.2, F - 0.07, z0 + h * 0.47), (x + w / 2 - 0.11, F - 0.03, z0 + h * 0.53), "brass")
    if step:
        bbox(p, (x - w / 2 - 0.22, F - 0.45, 0), (x + w / 2 + 0.22, F - 0.04, z0), {"*": "plinth", "+z": "pave"}, b=0.03)


def window(p, F, x, z, w=0.8, h=1.0, shutters=True, flowers=False):
    bbox(p, (x - w / 2, F - 0.02, z), (x + w / 2, F + 0.05, z + h), "glass")
    bbox(p, (x - 0.03, F - 0.05, z), (x + 0.03, F, z + h), "wall_sh")
    bbox(p, (x - w / 2, F - 0.05, z + h * 0.55 - 0.03), (x + w / 2, F, z + h * 0.55 + 0.03), "wall_sh")
    bbox(p, (x - w / 2 - 0.1, F - 0.16, z - 0.1), (x + w / 2 + 0.1, F + 0.02, z), "plinth", b=0.025)
    bbox(p, (x - w / 2 - 0.06, F - 0.06, z + h), (x + w / 2 + 0.06, F + 0.02, z + h + 0.12), "plinth", b=0.02)
    if shutters:
        for s in (-1, 1):
            xa, xb = sorted((x + s * (w / 2 + 0.02), x + s * (w + 0.02)))
            bbox(p, (xa, F - 0.07, z), (xb, F - 0.01, z + h), "shutter", b=0.015)
            for zz in (z + 0.16, z + h - 0.22):
                bbox(p, (xa + 0.04, F - 0.1, zz), (xb - 0.04, F - 0.06, zz + 0.06), "shutter_dk")
    if flowers:
        bbox(p, (x - w / 2 - 0.04, F - 0.42, z - 0.06), (x + w / 2 + 0.04, F - 0.14, z + 0.14), "timber", b=0.02)
        bbox(p, (x - w / 2, F - 0.39, z + 0.1), (x + w / 2, F - 0.17, z + 0.24), "leaf", b=0.05)
        for k in range(4):
            fx, fy = x - w / 2 + 0.12 + k * (w - 0.24) / 3, F - 0.33 + 0.05 * (k % 2)
            bbox(p, (fx - 0.05, fy, z + 0.2), (fx + 0.05, fy + 0.1, z + 0.31), ("coral", "gold")[k % 2], b=0.02)


def awning(p, F, x, z0, w, out=0.95, drop=0.42, n=7):
    a, L = math.atan2(drop, out), math.hypot(out, drop)
    M = Matrix.Translation((0, F - 0.02, z0)) @ Matrix.Rotation(a, 4, "X")
    ws = w / n
    ey, ez = F - 0.02 - out, z0 - drop
    for k in range(n):
        xk = x - w / 2 + k * ws
        col = ("coral", "cream")[k % 2]
        bbox(p, (xk, -L, 0), (xk + ws, 0, 0.035), col, M=M)
        prism(p, (0, ey + 0.01, ez + 0.03), (1, 0, 0), (0, 0, 1),
              [(xk, 0), (xk, -0.15), (xk + ws / 2, -0.26), (xk + ws, -0.15), (xk + ws, 0)], 0.025, col)
    for s in (-1, 1):
        xb = x + s * (w / 2 - 0.12)
        H.tube(p, [(xb, F, z0 - 0.7), (xb, ey + 0.05, ez + 0.02)], [0.022, 0.022], 4, "iron", cap0="center", cap1="center")


def balcony(p, F, x, z, w=2.0, out=0.8):
    bbox(p, (x - w / 2, F - out, z - 0.16), (x + w / 2, F, z), {"*": "plinth", "+z": "pave"}, b=0.03)
    for s in (-1, 1):  # corbels
        prism(p, (x + s * (w / 2 - 0.25) - 0.08, F, z - 0.16), (0, -1, 0), (0, 0, -1),
              [(0, 0), (out * 0.75, 0), (0, 0.38)], 0.16, "plinth")
    yr = F - out + 0.06
    for k in range(7):
        xk = x - w / 2 + 0.06 + (w - 0.12) * k / 6
        bbox(p, (xk - 0.025, yr - 0.025, z), (xk + 0.025, yr + 0.025, z + 0.86), "iron")
    for s in (-1, 1):
        xs = x + s * (w / 2 - 0.06)
        bbox(p, (xs - 0.025, F - out * 0.45 - 0.025, z), (xs + 0.025, F - out * 0.45 + 0.025, z + 0.86), "iron")
        bbox(p, (xs - 0.06, F - out, z + 0.85), (xs + 0.06, F, z + 0.95), "timber", b=0.02)
    bbox(p, (x - w / 2, yr - 0.06, z + 0.85), (x + w / 2, yr + 0.06, z + 0.95), "timber", b=0.02)
    bbox(p, (x - w / 2, yr - 0.02, z + 0.12), (x + w / 2, yr + 0.02, z + 0.17), "iron")


def house_a():  # ridge along the lane, shop window under a striped awning
    def feats(p, F):
        door(p, F, -1.45)
        window(p, F, 0.95, 0.85, w=1.5, h=1.25, shutters=False)
        awning(p, F, 0.95, 2.45, 2.3)
        window(p, F, -1.45, 2.75, w=0.75, h=0.75)
        window(p, F, 1.1, 2.8, w=0.7, h=0.7, flowers=True)
    return house(5.0, 3.9, 28, False, feats)


def house_b():  # tall, gable to the camera, balcony over the door, round gable window
    def feats(p, F):
        door(p, F, 0.0, h=1.95)
        window(p, F, 1.42, 0.9, w=0.6, h=0.95, flowers=True)
        balcony(p, F, 0.0, 2.6)
        door(p, F, 0.0, w=0.9, h=1.7, z0=2.6, col=("shutter", "shutter_dk"), step=False)
        c = Vector((0, F, 4.72))
        ring = [(0.36 * math.cos(math.pi * k / 4 + math.pi / 8), 0.36 * math.sin(math.pi * k / 4 + math.pi / 8)) for k in range(8)]
        prism(p, c + Vector((0, 0.02, 0)), (1, 0, 0), (0, 0, 1), ring, 0.08, "plinth")
        prism(p, c + Vector((0, -0.04, 0)), (1, 0, 0), (0, 0, 1), [(x * 0.7, y * 0.7) for x, y in ring], 0.03, "glass")
    return house(4.2, 4.2, 35, True, feats)


def house_c():  # low and wide, teal door, chimney
    def feats(p, F):
        door(p, F, 0.3, col=("shutter", "shutter_dk"))
        window(p, F, -1.6, 1.0, w=0.9, h=1.0, flowers=True)
        window(p, F, 1.9, 1.0, w=0.7, h=1.0)
        bbox(p, (-1.9, 0.25, 3.0), (-1.3, 0.85, 4.75), "wall", b=0.03)
        bbox(p, (-1.95, 0.2, 4.5), (-1.25, 0.9, 4.75), "plinth", b=0.02)
        bbox(p, (-2.02, 0.13, 4.75), (-1.18, 0.97, 4.86), "roof_dk", b=0.02)
        cyl(p, (-1.6, 0.55, 4.86), (-1.6, 0.55, 5.05), 0.1, 6, "roof")
    return house(5.4, 3.2, 30, False, feats)


# ============================================================================= props
def crate():
    p = P()
    bbox(p, (-0.42, -0.42, 0.02), (0.42, 0.42, 0.86), "seam")
    for k in range(4):
        M = Matrix.Rotation(k * math.pi / 2, 4, "Z")
        bbox(p, (-0.45, -0.45, 0), (-0.33, -0.33, 0.9), "crate_dk", b=0.02, M=M)
        bbox(p, (-0.33, -0.45, 0), (0.33, -0.36, 0.12), "crate_dk", M=M)
        bbox(p, (-0.33, -0.45, 0.78), (0.33, -0.36, 0.9), "crate_dk", M=M)
        for j in range(3):
            z0 = 0.12 + j * 0.22
            bbox(p, (-0.33, -0.42, z0 + 0.01), (0.33, -0.36, z0 + 0.21), ("crate", "crate_b")[(j + k) % 2], M=M)
        if k % 2 == 0:  # diagonal brace on front/back
            L, th = math.hypot(0.62, 0.62), math.atan2(0.62, 0.62)
            Mb = M @ Matrix.Translation((0, -0.435, 0.45)) @ Matrix.Rotation(-th, 4, "Y")
            bbox(p, (-L / 2, -0.015, -0.055), (L / 2, 0.015, 0.055), "crate_dk", M=Mb)
    for j in range(3):
        y0 = -0.36 + j * 0.24
        bbox(p, (-0.36, y0 + 0.01, 0.8), (0.36, y0 + 0.23, 0.875), ("crate_b", "crate")[j % 2])
    return p


def barrel():
    p = P()
    rb = lambda z: 0.26 + 0.07 * math.sin(math.pi * z / 0.9)
    rings, cols = [(0.0, rb(0) - 0.02)], []
    z = 0.0
    for a, b in ((0.05, 0.13), (0.25, 0.32), (0.58, 0.65), (0.77, 0.85)):
        rings += [(a, rb(a)), (a + 0.004, rb(a) + 0.018), (b - 0.004, rb(b) + 0.018), (b, rb(b))]
        cols += ["staves", "iron", "iron", "iron"]
    rings.append((0.9, rb(0.9) - 0.02))
    cols.append("staves")
    n = 14

    def col(i, j):
        if i < 0 or i >= len(cols):
            return "oak_b"
        return ("oak", "oak_b")[j % 2] if cols[i] == "staves" else cols[i]
    H.tube(p, [(0, 0, zz) for zz, _ in rings], [r for _, r in rings], n, col, cap0="center", cap1=(0, 0, 0.86),
           phase=math.pi / n)
    # Bastian's cooper mark: a branded ring with a cross slot on the front staves
    yf = -rb(0.45) * math.cos(math.pi / n) - 0.004
    O, R0, R1 = Vector((0, yf, 0.45)), 0.075, 0.05
    for k in range(10):
        a0, a1 = 2 * math.pi * k / 10, 2 * math.pi * (k + 1) / 10
        q = lambda r, a: O + Vector((r * math.cos(a), 0, r * math.sin(a)))
        poly(p, (q(R1, a0), q(R0, a0), q(R0, a1), q(R1, a1)), "brand", O + Vector((0, 1, 0)))
    for ax in ((1, 0), (0, 1)):
        u, v = Vector((ax[0], 0, ax[1])), Vector((ax[1], 0, ax[0]))
        poly(p, [O + u * su * 0.045 + v * sv * 0.011 for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))], "brand",
             O + Vector((0, 1, 0)))
    return p


def rope_post():
    p = P()
    lathe(p, 0, 0, [(0, 0.125), (0.28, 0.125), (0.285, 0.137), (0.35, 0.137), (0.355, 0.125), (0.82, 0.125),
                    (0.87, 0.105), (0.9, 0.055)], 8, ["timber", "iron", "iron", "iron", "timber", "timber_dk", "timber_dk"])
    turns, m = 2.5, 31
    pts = [(0.152 * math.cos(2 * math.pi * turns * k / (m - 1)), 0.152 * math.sin(2 * math.pi * turns * k / (m - 1)),
            0.46 + 0.22 * k / (m - 1)) for k in range(m)]
    H.tube(p, pts, [0.032] * m, 6, lambda i, j: ("rope", "rope_dk")[(i + j) % 2], cap0="center", cap1="center")
    return p


def lamp_post():
    p = P()
    bbox(p, (-0.2, -0.2, 0), (0.2, 0.2, 0.22), {"*": "stone_b", "+z": "stone_c"}, b=0.03)
    lathe(p, 0, 0, [(0.2, 0.12), (0.36, 0.08), (0.5, 0.055), (1.6, 0.05), (1.63, 0.085), (1.69, 0.085),
                    (1.72, 0.05), (1.8, 0.07)], 8, ["iron", "iron", "iron", "iron", "brass", "iron", "iron"])
    bbox(p, (-0.17, -0.17, 1.8), (0.17, 0.17, 1.86), "iron", b=0.01)
    bbox(p, (-0.125, -0.125, 1.86), (0.125, 0.125, 2.16), "lamp")
    for sx in (-1, 1):
        for sy in (-1, 1):
            bbox(p, (sx * 0.13 - 0.02, sy * 0.13 - 0.02, 1.86), (sx * 0.13 + 0.02, sy * 0.13 + 0.02, 2.17), "iron")
    bbox(p, (-0.17, -0.17, 2.16), (0.17, 0.17, 2.2), "iron", b=0.01)
    H.tube(p, [(0, 0, 2.2), (0, 0, 2.33)], [0.25, 0.03], 4, "iron", cap0="center", cap1="center", phase=math.pi / 4)
    H.ellipsoid(p, (0, 0, 2.362), (0.038, 0.038, 0.038), 6, 4, "brass")
    return p


def bunting_5m():
    p = P()
    sag, span = 0.45, 5.0
    zf = lambda x: -sag * (1 - ((x - span / 2) / (span / 2)) ** 2)
    xs = [span * k / 20 for k in range(21)]
    H.tube(p, [(x, 0, zf(x)) for x in xs], [0.014] * 21, 4, "rope_dk", cap0="center", cap1="center")
    for i in range(13):
        xc = 0.25 + i * 0.375
        tri = [(xc - 0.13, zf(xc - 0.13) - 0.01), (xc, zf(xc) - 0.31), (xc + 0.13, zf(xc + 0.13) - 0.01)]
        prism(p, (0, 0.006, 0), (1, 0, 0), (0, 0, 1), tri, 0.012, ("coral", "gold", "teal", "cream")[i % 4])
    return p


def mast_sail():
    p = P()
    bbox(p, (-0.28, -0.28, 0), (0.28, 0.28, 0.25), "timber_dk", b=0.03)
    lathe(p, 0, 0, [(0, 0.17), (9.6, 0.11), (10.0, 0.08)], 8, ["timber", "timber_dk"])
    cyl(p, (-2.5, 0, 6.6), (2.5, 0, 6.6), 0.075, 8, "timber_dk")
    # furled sail: lumpy bundle under the yard, rope gaskets between the lumps
    fx = [-2.3, -1.85, -1.4, -1.36, -0.92, -0.48, -0.44, 0.0, 0.44, 0.48, 0.92, 1.36, 1.4, 1.85, 2.3]
    fr = [0.08, 0.27, 0.19, 0.19, 0.3, 0.19, 0.19, 0.29, 0.19, 0.19, 0.3, 0.19, 0.19, 0.27, 0.08]
    fc = ["sail_sh", "cream", "rope", "cream", "sail_sh", "rope", "cream", "sail_sh", "rope", "cream", "sail_sh", "rope",
          "cream", "sail_sh"]
    H.tube(p, [(x, -0.02, 6.36 - 0.05 * math.cos(math.pi * x / 4.6)) for x in fx], fr, 8, seg(fc),
           cap0="center", cap1="center", hint=Vector((0, 0, -1)))
    cup(p, (0, 0, 0), 0.52, 0.45, 8.2, 8.72, 12, "timber", "timber_dk")
    lathe(p, 0, 0, [(7.95, 0.15), (8.2, 0.52)], 12, ["timber_dk"])  # bracket cone under the nest
    prism(p, (0, 0.012, 0), (1, 0, 0), (0, 0, 1), [(0.09, 9.82), (0.09, 9.5), (1.0, 9.62)], 0.024, "coral")
    return p


def sloop():
    """The Brine Dream. Origin = waterline, hull centre. Bow +X."""
    p = P()
    x0, x1, NS = -4.3, 4.3, 18

    def beam(u):
        return 1.35 * (1 - 0.32 * ((0.42 - u) / 0.42) ** 2) if u <= 0.42 else 1.35 * math.sqrt(max(0.0, 1 - ((u - 0.42) / 0.58) ** 2))

    def sheer(u):
        return 0.9 + (0.3 * ((u - 0.45) / 0.55) ** 2 if u > 0.45 else 0.25 * ((0.45 - u) / 0.45) ** 2)

    def keel(u):
        return -1.0 + (1.25 * ((u - 0.6) / 0.4) ** 2 if u > 0.6 else (0.45 * (0.15 - u) / 0.15 if u < 0.15 else 0))

    rings = []
    for i in range(NS + 1):
        u = i / NS
        x = x0 + (x1 - x0) * u
        b, zs, zk = max(beam(u), 0.04), sheer(u), keel(u)
        w, hb = min(0.1, b * 0.45), 0.32
        side = [(b - w, zs + hb), (b * 1.03, zs + hb)]
        for t in (0.0, 0.36, 0.46, 0.68, 0.86):
            side.append((b * (1 - t ** 2.4) ** 0.5, zs + (zk - zs) * t))
        ring = ([(x, y, z) for y, z in side] + [(x, 0, zk)] + [(x, -y, z) for y, z in reversed(side)]
                + [(x, -(b - w), zs), (x, -(b - w) / 3, zs), (x, (b - w) / 3, zs), (x, b - w, zs)])
        rings.append([Vector(v) for v in reversed(ring)])
    seg_cols = ["timber_dk", "cream", "timber", "gold", "antifoul", "antifoul", "antifoul", "antifoul", "antifoul",
                "antifoul", "gold", "timber", "cream", "timber_dk", "timber_lt", "deck", "deck_b", "deck", "timber_lt"]
    N = len(seg_cols)
    H.loft(p, rings, lambda i, j: seg_cols[(N - 2 - j) % N], closed=True)
    poly(p, rings[0], "timber", (x0 + 1, 0, 0.3))
    poly(p, rings[-1], "timber_dk", (x1 - 1, 0, 0.3))
    zs_at = lambda x: sheer((x - x0) / (x1 - x0))
    xm, zm = 0.6, zs_at(0.6)
    # spars, rigging, deck furniture
    lathe(p, xm, 0, [(zm - 0.1, 0.13), (8.6, 0.08)], 8, ["timber"])
    cyl(p, (xm - 0.1, 0, zm + 1.25), (-3.6, 0, zm + 1.25), 0.065, 6, "timber_dk")
    cyl(p, (3.9, 0, 1.2), (5.45, 0, 1.58), 0.075, 6, "timber_dk", r1=0.05)
    for a, b in (((xm, 0, 8.45), (5.4, 0, 1.58)), ((xm, 0, 8.45), (-4.2, 0, 1.45)),
                 ((xm, 0, 7.6), (xm, -1.25, zm + 0.3)), ((xm, 0, 7.6), (xm, 1.25, zm + 0.3))):
        cyl(p, a, b, 0.018, 4, "rope_dk", phase=0)
    zc = zs_at(-1.75)
    bbox(p, (-2.5, -0.65, zc - 0.05), (-1.0, 0.65, zc + 0.55), {"*": "timber_lt", "+z": "cream"}, b=0.04)
    for xp in (-2.1, -1.4):
        bbox(p, (xp - 0.1, -0.68, zc + 0.2), (xp + 0.1, -0.6, zc + 0.38), "glass")
    zst = zs_at(-4.1)
    cyl(p, (-4.1, 0, zst + 0.25), (-3.25, 0, zst + 0.45), 0.035, 6, "timber_dk")
    bbox(p, (-4.48, -0.06, -0.75), (-4.26, 0.06, zst + 0.15), "timber_dk", b=0.02)
    prism(p, (0, 0.012, 0), (1, 0, 0), (0, 0, 1), [(xm - 0.05, 8.55), (xm - 0.05, 8.28), (xm - 1.1, 8.4)], 0.024, "gold")

    def sail(A, B, C, billow, col, n=6, emblem=None):
        det = (B[1] - C[1]) * (A[0] - C[0]) + (C[0] - B[0]) * (A[1] - C[1])

        def S(x, z, side, lift):
            l1 = ((B[1] - C[1]) * (x - C[0]) + (C[0] - B[0]) * (z - C[1])) / det
            l2 = ((C[1] - A[1]) * (x - C[0]) + (A[0] - C[0]) * (z - C[1])) / det
            return Vector((x, -billow * 27 * l1 * l2 * (1 - l1 - l2) + side * lift, z))

        def G(i, j, side):
            l1, l2 = i / n, j / n
            return S(A[0] * l1 + B[0] * l2 + C[0] * (1 - l1 - l2), A[1] * l1 + B[1] * l2 + C[1] * (1 - l1 - l2), side, 0.012)

        for side in (-1, 1):
            for i in range(n):
                for j in range(n - i):
                    tris = [(G(i, j, side), G(i + 1, j, side), G(i, j + 1, side))]
                    if i + j <= n - 2:
                        tris.append((G(i + 1, j, side), G(i + 1, j + 1, side), G(i, j + 1, side)))
                    for t in tris:
                        poly(p, t, col, sum(t, Vector()) / 3 - Vector((0, side, 0)))
        if emblem:  # Kito's sun-compass: 8-ray sun inside a ring, gold, both faces
            (cx, cz), R = emblem
            Q = lambda r, a: (cx + r * math.cos(a), cz + r * math.sin(a))
            for side in (-1, 1):
                F = lambda pts2: poly(p, [S(x, z, side, 0.03) for x, z in pts2], "gold",
                                      S(cx, cz, side, 0.03) - Vector((0, side, 0)))
                for k in range(24):
                    a0, a1 = 2 * math.pi * k / 24, 2 * math.pi * (k + 1) / 24
                    F([Q(R * 0.8, a0), Q(R, a0), Q(R, a1), Q(R * 0.8, a1)])
                F([Q(R * 0.32, 2 * math.pi * k / 12) for k in range(12)])
                for k in range(8):
                    a = 2 * math.pi * k / 8 + math.pi / 8
                    F([Q(R * 0.4, a - 0.2), Q(R * (0.7 if k % 2 == 0 else 0.6), a), Q(R * 0.4, a + 0.2)])

    zb = zm + 1.33
    sail((xm - 0.13, zb), (xm - 0.13, 7.8), (-3.3, zb), 0.3, "coral", emblem=((-0.86, zb + 1.36), 1.02))
    sail((5.0, 2.1), (1.32, 7.5), (2.3, 2.05), 0.2, "cream")
    return p


def ship_rail_2m():
    p = P()
    bbox(p, (-1, -0.075, 0.8), (1, 0.075, 0.9), {"*": "timber", "+z": "timber_lt"}, b=0.025, cut=("-x", "+x"))
    bbox(p, (-1, -0.05, 0.1), (1, 0.05, 0.18), "timber", b=0.015, cut=("-x", "+x"))
    bbox(p, (-1, -0.07, 0), (1, 0.07, 0.1), "timber_dk", b=0.015, cut=("-x", "+x"))
    for x in (-0.75, -0.25, 0.25, 0.75):
        lathe(p, x, 0, [(0.18, 0.035), (0.26, 0.05), (0.36, 0.03), (0.55, 0.045), (0.7, 0.03), (0.8, 0.04)], 8,
              ["cream"] * 5)
    return p


MODULES = [
    ("dock_2m", dock_2m), ("seawall_2m", seawall_2m), ("stone_block_1m", stone_block_1m), ("cave_rock_2m", cave_rock_2m),
    ("house_a", house_a), ("house_b", house_b), ("house_c", house_c),
    ("crate", crate), ("barrel", barrel), ("rope_post", rope_post), ("lamp_post", lamp_post),
    ("bunting_5m", bunting_5m), ("mast_sail", mast_sail), ("sloop", sloop), ("ship_rail_2m", ship_rail_2m),
]
BUDGET = {"house_a": 2500, "house_b": 2500, "house_c": 2500, "sloop": 4000,
          "dock_2m": 1000, "seawall_2m": 1000, "stone_block_1m": 1000, "cave_rock_2m": 1000, "ship_rail_2m": 1000}


# ============================================================================= build / export / previews
def make_obj(name, p, mat, coll=None):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in p.v], [], p.f)
    me.validate()
    me.update()
    H.assign_palette_uvs(me, p.c, PAL)
    me.polygons.foreach_set("use_smooth", p.s)
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob


def export(ob, path):
    for o in bpy.context.scene.objects:
        o.select_set(o == ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_yup=True,
                              export_apply=True, export_cameras=False, export_lights=False,
                              export_animations=False, export_materials="EXPORT")


def world_bbox(obs):
    pts = [o.matrix_world @ v.co for o in obs for v in o.data.vertices]
    return (Vector([min(q[k] for q in pts) for k in range(3)]), Vector([max(q[k] for q in pts) for k in range(3)]))


def look(cam, loc, target):
    cam.location = Vector(loc)
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()


def setup_lit(res, sky, ambient=0.5, sun=2.2):
    """EEVEE + sun + sky ambient (camera sees the sky at full strength), Standard view: palette colours stay true."""
    sc = bpy.context.scene
    cam = H.setup_render(res)
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.eevee.taa_render_samples = 16
    sc.view_settings.view_transform, sc.view_settings.look = "Standard", "None"
    nt = sc.world.node_tree if sc.world.use_nodes else None
    if nt is None:
        sc.world.use_nodes = True
        nt = sc.world.node_tree
        nt.nodes.clear()
        lp, mix = nt.nodes.new("ShaderNodeLightPath"), nt.nodes.new("ShaderNodeMixShader")
        b_amb, b_cam, out = nt.nodes.new("ShaderNodeBackground"), nt.nodes.new("ShaderNodeBackground"), nt.nodes.new("ShaderNodeOutputWorld")
        nt.links.new(lp.outputs["Is Camera Ray"], mix.inputs[0])
        nt.links.new(b_amb.outputs[0], mix.inputs[1])
        nt.links.new(b_cam.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], out.inputs[0])
    b_amb, b_cam = [n for n in nt.nodes if n.type == "BACKGROUND"]
    b_amb.inputs[0].default_value = b_cam.inputs[0].default_value = (*sky, 1)
    b_amb.inputs[1].default_value, b_cam.inputs[1].default_value = ambient, 1.0
    s = bpy.data.objects.get("Sun")
    if s is None:
        s = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
        sc.collection.objects.link(s)
    s.data.energy, s.data.angle = sun, math.radians(4)
    s.rotation_euler = (math.radians(50), 0, math.radians(-35))  # from front-left-above: lights tops + fronts
    return cam


def render_cells(objs, size, outdir):
    cam = setup_lit((size, size), (0.62, 0.7, 0.74))
    paths = []
    for name, ob in objs.items():
        for o in objs.values():
            o.hide_render = o is not ob
        lo, hi = world_bbox([ob])
        diag = (hi - lo).length
        path = os.path.join(outdir, f"{name}.png")
        H.render_view(path, cam, 28, target=(lo + hi) / 2, scale=diag * 0.95, pitch_deg=72, dist=60)
        paths.append(path)
    for o in objs.values():
        o.hide_render = False
    return paths


def palette_cell(img, size, path):
    """Last contact-sheet cell: the shared swatch atlas, nearest-upscaled."""
    import numpy as np
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    a = a.reshape(h, w, 4)[(np.arange(size) * h) // size][:, (np.arange(size) * w) // size]
    im = bpy.data.images.new("pal_cell", size, size)
    im.pixels.foreach_set(a.ravel())
    im.filepath_raw, im.file_format = path, "PNG"
    im.save()
    bpy.data.images.remove(im)
    return path


def render_tiling(objs, path):
    """QA only: 3x seawall | 3x dock | 3x cave rock butted along X, to eyeball the seams."""
    sc = bpy.context.scene
    tmp = []
    for k, name in enumerate(["seawall_2m"] * 3 + ["dock_2m"] * 3 + ["cave_rock_2m"] * 3):
        ob = bpy.data.objects.new(f"tile_{k}", objs[name].data)
        ob.location.x = -8 + 2 * k
        sc.collection.objects.link(ob)
        tmp.append(ob)
    for o in objs.values():
        o.hide_render = True
    cam = setup_lit((720, 260), (0.62, 0.7, 0.74))
    H.render_view(path, cam, 12, target=(0, 0, -0.9), scale=19.5, pitch_deg=74, dist=60)
    for o in tmp:
        bpy.data.objects.remove(o)
    for o in objs.values():
        o.hide_render = False


def harbor_mock(objs, mat):
    """Side-view arrangement in its own collection (linked duplicates of the kit meshes, offset in Y)."""
    sc = bpy.context.scene
    coll = bpy.data.collections.new("harbor_mock")
    sc.collection.children.link(coll)
    Y0 = 60.0  # keep the mock away from the kit row in the .blend

    def put(name, x, y, z=0.0, rz=0.0, s=(1, 1, 1)):
        ob = bpy.data.objects.new(f"mock_{name}", objs[name].data)
        ob.location, ob.rotation_euler, ob.scale = (x, Y0 + y, z), (0, 0, rz), s
        coll.objects.link(ob)
        return ob

    for k in range(6):
        put("seawall_2m", -12 + 2 * k, 0)
    for k in range(8):
        put("seawall_2m", -12 + 2 * k, 4)  # back quay the houses stand on
    for k in range(7):
        put("dock_2m", 2 * k, 0)
    put("stone_block_1m", -5.5, 0.5, 0.5, s=(1.0, 1.0, 0.5))  # Godot-style scaled block = half-height step
    put("stone_block_1m", -4.5, 0.5, 1.0)
    put("house_a", -11.0, 4.0)
    put("house_b", -5.8, 4.4)
    put("house_c", -0.4, 4.6)
    put("bunting_5m", -13.4, 2.4, 4.2)
    put("bunting_5m", -8.2, 2.6, 4.3)
    put("crate", -11.0, -0.3)
    put("crate", -11.0, -0.3, 0.9, rz=0.2)
    put("crate", -10.05, -0.6, rz=-0.15)
    put("barrel", -8.6, -0.5)
    put("barrel", -8.0, 0.1)
    put("lamp_post", -2.4, 1.2)
    for x in (1.0, 5.0, 9.0):
        put("rope_post", x, -1.7)
    put("barrel", 3.2, 0.2)
    put("crate", 7.0, 0.6, rz=0.4)
    put("sloop", 8.0, 6.6, -0.9)
    sea = P()
    poly(sea, [(-40, -30, -0.9), (40, -30, -0.9), (40, 80, -0.9), (-40, 80, -0.9)], "sea", (0, 0, -5))
    o = make_obj("mock_sea", sea, mat, coll)
    o.location.y = Y0
    ref = P()  # 1.5 m hero-height scale reference
    H.ellipsoid(ref, (-6.5, -0.2, 0.75), (0.28, 0.22, 0.75), 10, 8, "coral")
    o = make_obj("mock_hero_scale", ref, mat, coll)
    o.location.y = Y0
    return coll, Y0


def render_mock(coll, Y0, kit_objs, path):
    sc = bpy.context.scene
    for o in kit_objs:
        o.hide_render = True
    setup_lit((720, 405), (0.62, 0.84, 0.96), ambient=0.55, sun=2.4)
    cam = bpy.data.objects.new("MockCam", bpy.data.cameras.new("MockCam"))
    coll.objects.link(cam)
    cam.data.lens = 30
    look(cam, (-1.0, Y0 - 17.5, 4.2), (-1.0, Y0 + 2.5, 1.4))  # game-like: side view, slight perspective, ~8 deg down
    sc.camera = cam
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    for o in kit_objs:
        o.hide_render = False


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(PREV, exist_ok=True)
    pal_path = os.path.join(OUT, "env_palette.png")
    img = PAL.image("env_palette", pal_path)
    mat = PAL.material("env_palette", img)
    objs = {}
    for name, fn in MODULES:
        ob = make_obj(name, fn(), mat)
        objs[name] = ob
        export(ob, os.path.join(OUT, f"{name}.glb"))
        lo, hi = world_bbox([ob])
        t = H.tri_count(ob)
        over = "  OVER BUDGET" if t > BUDGET.get(name, 800) else ""
        print(f"[env] {name:15s} tris={t:5d} min=({lo.x:+.3f},{lo.y:+.3f},{lo.z:+.3f}) "
              f"max=({hi.x:+.3f},{hi.y:+.3f},{hi.z:+.3f}){over}")
    if "--no-render" not in ARGS:
        tmp = os.path.join(PREV, "_tmp_env")
        cells = render_cells(objs, 180, tmp)
        cells.append(palette_cell(img, 180, os.path.join(tmp, "zz_palette.png")))
        H.contact_sheet(cells, os.path.join(PREV, "env_kit_sheet.png"), 4)
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
        if "--qa" in ARGS:
            qa = ARGS[ARGS.index("--qa") + 1]
            render_cells(objs, 480, qa)
            render_tiling(objs, os.path.join(qa, "_tiling.png"))
        coll, Y0 = harbor_mock(objs, mat)
        render_mock(coll, Y0, list(objs.values()), os.path.join(PREV, "env_harbor_mock.png"))
    x = 0.0  # lay the kit out in a row for browsing the .blend (GLBs were exported at the origin)
    for name, ob in objs.items():
        lo, hi = world_bbox([ob])
        ob.location.x = x - lo.x
        x += (hi.x - lo.x) + 1.5
    img.filepath_raw = bpy.path.relpath(pal_path, start=os.path.dirname(BLEND))
    bpy.context.preferences.filepaths.save_version = 0  # no .blend1
    bpy.ops.wm.save_as_mainfile(filepath=BLEND)
    print("[env] saved", BLEND)


def verify():
    print("[verify] module          tris  mats | Blender Z-up bbox min / max | Godot Y-up bbox min / max")
    for name, _ in MODULES:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=os.path.join(OUT, f"{name}.glb"))
        obs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        bpy.context.view_layer.update()
        tris = sum(H.tri_count(o) for o in obs)
        mats = {m.name for o in obs for m in o.data.materials if m}
        lo, hi = world_bbox(obs)
        g = lambda v: f"({v[0]:+.2f},{v[1]:+.2f},{v[2]:+.2f})"
        print(f"[verify] {name:15s} {tris:5d}  {len(mats)}  {sorted(mats)} | {g(lo)} / {g(hi)} | "
              f"{g((lo.x, lo.z, -hi.y))} / {g((hi.x, hi.z, -lo.y))}")


if __name__ == "__main__":
    verify() if "--verify" in ARGS else build()
