"""Reusable helpers for procedural, game-ready humanoids (Blender 4.5, headless-safe).

Pipeline: build geometry into `Part`s (plain Python verts/faces + a palette color per face
+ a bone-candidate spec) -> `build_body()` joins them into ONE mesh, collapses each face's
UVs onto its palette swatch, and writes explicit vertex weights -> `key_clip()` authors
actions -> `export_glb()`.

Conventions (shared by every character script):
  * meters, feet at origin, character faces -Y (glTF +Z after Y-up conversion)
  * bones: STANDARD_BONES (+ optional extras), .L = +X
  * pose values are degrees in the ARMATURE REST frame, anatomical for both sides:
      limbs:  x<0 swing forward, y<0 raise sideways/abduct, z<0 rotate toward the front
      spine/neck/head: x>0 bend forward, y>0 lean to own left, z>0 turn to own left
    .R values are mirrored automatically, so write both sides with the same meaning.
"""
import math
import os
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler
from mathutils.bvhtree import BVHTree

STANDARD_BONES = [
    "root", "hips", "spine", "chest", "neck", "head",
    "shoulder.L", "upper_arm.L", "forearm.L", "hand.L",
    "shoulder.R", "upper_arm.R", "forearm.R", "hand.R",
    "thigh.L", "shin.L", "foot.L", "thigh.R", "shin.R", "foot.R",
]
STANDARD_CLIPS = ["idle", "run", "jump", "fall", "land", "slash", "air_slash",
                  "cast", "hurt", "death", "interact", "victory"]
FPS = 30


# ----------------------------------------------------------------------------- palette
def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


class Palette:
    """Flat swatch atlas: `cols` x rows grid of `cell`-pixel squares."""

    def __init__(self, colors, cols=8, cell=8):
        self.colors, self.cols, self.cell = dict(colors), cols, cell
        self.names = list(self.colors)
        self.rows = math.ceil(len(self.names) / cols)

    def uv(self, name):
        i = self.names.index(name)
        return ((i % self.cols + 0.5) / self.cols, (i // self.cols + 0.5) / self.rows)

    def image(self, name, path):
        w, h = self.cols * self.cell, self.rows * self.cell
        img = bpy.data.images.new(name, w, h, alpha=False)
        px = [0.5, 0.5, 0.5, 1.0] * (w * h)
        for i, n in enumerate(self.names):
            r, g, b = hex_rgb(self.colors[n])
            cx, cy = (i % self.cols) * self.cell, (i // self.cols) * self.cell
            for y in range(cy, cy + self.cell):
                for x in range(cx, cx + self.cell):
                    k = (y * w + x) * 4
                    px[k:k + 3] = (r, g, b)
        img.pixels[:] = px
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        return img

    def material(self, name, img):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = nt.nodes["Principled BSDF"]
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image, tex.interpolation = img, "Closest"
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = 0.85
        bsdf.inputs["Specular IOR Level"].default_value = 0.2
        return mat


# ----------------------------------------------------------------------------- parts
class Part:
    """Geometry chunk with one weight spec. bones: list of name or (name, fn(v)->mult)."""

    def __init__(self, bones, smooth=True):
        self.v, self.f, self.c, self.s = [], [], [], []
        self.bones, self.smooth = bones, smooth

    def vert(self, p):
        self.v.append(Vector(p))
        return len(self.v) - 1

    def face(self, idx, color, smooth=None):
        self.f.append(tuple(idx))
        self.c.append(color)
        self.s.append(self.smooth if smooth is None else smooth)

    def recolor(self, f0, fn):
        """fn(face_center, face_normal)->color or None, for faces added since index f0."""
        from mathutils.geometry import normal
        for k in range(f0, len(self.f)):
            vs = [self.v[i] for i in self.f[k]]
            self.c[k] = fn(sum(vs, Vector()) / len(vs), normal(vs)) or self.c[k]

    def bvh(self, f0=0, f1=None):
        return BVHTree.FromPolygons(self.v, self.f[f0:f1])


def frame(d, hint=Vector((0, -1, 0))):
    """Orthonormal u, v with u x v = d (ring points c+u*cos+v*sin wind outward)."""
    d = Vector(d).normalized()
    h = Vector(hint) - d * Vector(hint).dot(d)
    if h.length < 1e-6:
        h = Vector((1, 0, 0)) - d * d.x
        if h.length < 1e-6:
            h = Vector((0, 1, 0)) - d * d.y
    u = h.normalized()
    return u, d.cross(u)


def ring(c, d, rx, ry, n, hint=Vector((0, -1, 0)), phase=0.0):
    u, v = frame(d, hint)
    return [Vector(c) + u * (rx * math.cos(phase + 2 * math.pi * j / n))
            + v * (ry * math.sin(phase + 2 * math.pi * j / n)) for j in range(n)]


def loft(part, rings, color, closed=True, cap0=None, cap1=None, wrap_path=False):
    """Connect rings with quads. color: name or fn(i, j)->name. cap: Vector pole or 'center'."""
    col = color if callable(color) else (lambda i, j: color)
    grid = [[part.vert(p) for p in r] for r in rings]
    n = len(rings[0])
    jn = n if closed else n - 1
    rn = len(grid) if wrap_path else len(grid) - 1
    for i in range(rn):
        a, b = grid[i], grid[(i + 1) % len(grid)]
        for j in range(jn):
            k = (j + 1) % n
            part.face((a[j], a[k], b[k], b[j]), col(i, j))
    for cap, ring_idx, rev in ((cap0, 0, False), (cap1, -1, True)):
        if cap is None:
            continue
        r = grid[ring_idx]
        pole = sum((part.v[x] for x in r), Vector()) / n if cap == "center" else Vector(cap)
        pi = part.vert(pole)
        cc = col(-1 if not rev else len(grid), 0)
        for j in range(jn):
            k = (j + 1) % n
            part.face((pi, r[k], r[j]) if not rev else (pi, r[j], r[k]), cc)
    return grid


def tube(part, pts, radii, n, color, hint=Vector((0, -1, 0)), cap0=None, cap1=None,
         closed_path=False, phase=0.0):
    """Rings perpendicular to a polyline. radii: per point r or (rx, ry)."""
    pts = [Vector(p) for p in pts]
    rings = []
    m = len(pts)
    for i, p in enumerate(pts):
        if closed_path:
            t = pts[(i + 1) % m] - pts[i - 1]
        else:
            t = pts[min(i + 1, m - 1)] - pts[max(i - 1, 0)]
        r = radii[i]
        rx, ry = (r, r) if isinstance(r, (int, float)) else r
        rings.append(ring(p, t, rx, ry, n, hint, phase))
    if cap0 == "tip":
        cap0 = pts[0] - (pts[1] - pts[0]).normalized() * 0.001
    if cap1 == "tip":
        cap1 = pts[-1] + (pts[-1] - pts[-2]).normalized() * 0.001
    return loft(part, rings, color, True, cap0, cap1, wrap_path=closed_path)


def sphere(part, fn, nu, nv, color):
    """Closed UV sphere; fn(unit Vector)->world Vector shapes it. color: name or fn(i, j)."""
    rings = []
    for i in range(1, nv):
        th = math.pi - math.pi * i / nv  # bottom -> top
        rings.append([fn(Vector((math.sin(th) * math.cos(2 * math.pi * j / nu),
                                 math.sin(th) * math.sin(2 * math.pi * j / nu),
                                 math.cos(th)))) for j in range(nu)])
    return loft(part, rings, color, True, fn(Vector((0, 0, -1))), fn(Vector((0, 0, 1))))


def ellipsoid(part, c, r, nu, nv, color, basis=None, exp=1.0):
    """basis: 3x3 Matrix whose columns are the local X, Y, Z axes. exp<1 -> boxier."""
    B = (basis or Matrix.Identity(3)).copy()
    if B.determinant() < 0:  # keep winding outward for left-handed bases
        B.col[0] = -B.col[0]
    c = Vector(c)

    def fn(u):
        q = Vector([math.copysign(abs(x) ** exp, x) for x in u])
        return c + B @ Vector((q.x * r[0], q.y * r[1], q.z * r[2]))
    return sphere(part, fn, nu, nv, color)


def axes(x, y, z):
    return Matrix((tuple(x), tuple(y), tuple(z))).transposed()


def sheet(part, P, thick, outer, inner, edges):
    """Thicken a rows x cols point grid into a closed slab.
    outer: fn(r, c)->color; inner: color; edges: dict top/bottom/left/right -> color."""
    R, C = len(P), len(P[0])
    N = [[None] * C for _ in range(R)]
    for r in range(R):
        for c in range(C):
            tr = P[min(r + 1, R - 1)][c] - P[max(r - 1, 0)][c]
            tc = P[r][min(c + 1, C - 1)] - P[r][max(c - 1, 0)]
            N[r][c] = tr.cross(tc).normalized()
    O = [[part.vert(P[r][c]) for c in range(C)] for r in range(R)]
    I = [[part.vert(P[r][c] - N[r][c] * thick) for c in range(C)] for r in range(R)]
    for r in range(R - 1):
        for c in range(C - 1):
            part.face((O[r][c], O[r + 1][c], O[r + 1][c + 1], O[r][c + 1]), outer(r, c))
            part.face((I[r][c], I[r][c + 1], I[r + 1][c + 1], I[r + 1][c]), inner)
    for c in range(C - 1):
        part.face((O[0][c], O[0][c + 1], I[0][c + 1], I[0][c]), edges["top"])
        part.face((O[R - 1][c + 1], O[R - 1][c], I[R - 1][c], I[R - 1][c + 1]), edges["bottom"])
    for r in range(R - 1):
        part.face((O[r + 1][0], O[r][0], I[r][0], I[r + 1][0]), edges["left"])
        part.face((O[r][C - 1], O[r + 1][C - 1], I[r + 1][C - 1], I[r][C - 1]), edges["right"])
    return O, I, N


def decal(part, bvh, origin, right, up, outline, color, offset, rings=2):
    """Project a star-shaped 2D outline [(s, t)...] (CCW seen from the viewer) along
    -(right x up)... i.e. from the viewer side onto `bvh`, lifted `offset` along the normal."""
    O, Rv, Uv = Vector(origin), Vector(right), Vector(up)
    D = Uv.cross(Rv).normalized()  # into the surface (viewer looks along D)
    cs = sum(s for s, _ in outline) / len(outline)
    ct = sum(t for _, t in outline) / len(outline)

    def proj(s, t):
        start = O + Rv * s + Uv * t - D * 0.5
        hit, nrm, _, _ = bvh.ray_cast(start, D, 2.0)
        if hit is None:
            return start + D * 0.5
        if nrm.dot(D) > 0:
            nrm = -nrm
        return hit + nrm * offset
    idx = []
    for k in range(rings, 0, -1):
        f = k / rings
        idx.append([part.vert(proj(cs + (s - cs) * f, ct + (t - ct) * f)) for s, t in outline])
    center = part.vert(proj(cs, ct))
    n = len(outline)
    for a, b in zip(idx, idx[1:]):
        for j in range(n):
            k = (j + 1) % n
            part.face((a[j], a[k], b[k], b[j]), color)
    last = idx[-1]
    for j in range(n):
        part.face((center, last[j], last[(j + 1) % n]), color)


def decal_strip(part, bvh, origin, right, up, top, bottom, color, offset):
    """Quad strip between two 2D polylines (same length, left->right)."""
    O, Rv, Uv = Vector(origin), Vector(right), Vector(up)
    D = Uv.cross(Rv).normalized()

    def proj(s, t):
        start = O + Rv * s + Uv * t - D * 0.5
        hit, nrm, _, _ = bvh.ray_cast(start, D, 2.0)
        if hit is None:
            return start + D * 0.5
        if nrm.dot(D) > 0:
            nrm = -nrm
        return hit + nrm * offset
    T = [part.vert(proj(*p)) for p in top]
    Bt = [part.vert(proj(*p)) for p in bottom]
    for j in range(len(top) - 1):
        part.face((Bt[j], Bt[j + 1], T[j + 1], T[j]), color)


def ellipse_pts(cx, cy, rx, ry, n, rot=0.0):
    out = []
    for j in range(n):
        a = 2 * math.pi * j / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * math.cos(rot) - y * math.sin(rot), cy + x * math.sin(rot) + y * math.cos(rot)))
    return out


def fist(part, wrist, a, g, p, color="skin", size=1.0, thumb_color=None):
    """Closed fist. a: along forearm (toward fingers), g: knuckle row (grip axis), p: palm normal."""
    a, g, p = Vector(a).normalized(), Vector(g).normalized(), Vector(p).normalized()
    B = axes(g, p, a)
    c = Vector(wrist) + a * 0.044 * size
    ellipsoid(part, c, (0.045 * size, 0.037 * size, 0.047 * size), 12, 8, color, B, exp=0.8)
    for k in range(4):
        kc = c + g * ((k - 1.5) * 0.022 * size) + a * (0.03 * size) - p * (0.02 * size)
        ellipsoid(part, kc, (0.012 * size, 0.014 * size, 0.016 * size), 6, 4, color, B)
    tc = c + p * (0.026 * size) + g * (0.03 * size) - a * (0.004 * size)
    ellipsoid(part, tc, (0.026 * size, 0.014 * size, 0.016 * size), 8, 5, thumb_color or color, B)
    return c


# ----------------------------------------------------------------------------- skeleton
def mirror(p):
    return Vector((-p[0], p[1], p[2]))


def standard_skeleton(J, extras=()):
    """J: joint positions (L side for limbs). Returns [(name, head, tail, parent)]."""
    V = lambda k: Vector(J[k])
    b = [("root", Vector((0, 0, 0)), Vector((0, 0, 0.12)), None),
         ("hips", V("hips"), V("spine"), "root"),
         ("spine", V("spine"), V("chest"), "hips"),
         ("chest", V("chest"), V("neck"), "spine"),
         ("neck", V("neck"), V("head"), "chest"),
         ("head", V("head"), V("head_top"), "neck")]
    for s, m in (("L", lambda x: x), ("R", mirror)):
        b += [(f"shoulder.{s}", m(V("shoulder")), m(V("arm")), "chest"),
              (f"upper_arm.{s}", m(V("arm")), m(V("elbow")), f"shoulder.{s}"),
              (f"forearm.{s}", m(V("elbow")), m(V("wrist")), f"upper_arm.{s}"),
              (f"hand.{s}", m(V("wrist")), m(V("hand_end")), f"forearm.{s}")]
    for s, m in (("L", lambda x: x), ("R", mirror)):
        b += [(f"thigh.{s}", m(V("hip")), m(V("knee")), "hips"),
              (f"shin.{s}", m(V("knee")), m(V("ankle")), f"thigh.{s}"),
              (f"foot.{s}", m(V("ankle")), m(V("toe")), f"shin.{s}")]
    b += [(n, Vector(h), Vector(t), p) for n, h, t, p in extras]
    return b


def build_armature(bones, name="Armature"):
    data = bpy.data.armatures.new(name)
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.mode_set(mode="EDIT")
    eb = {}
    for n, h, t, p in bones:
        e = data.edit_bones.new(n)
        e.head, e.tail, e.roll = h, t, 0.0
        if p:
            e.parent = eb[p]
            e.use_connect = (eb[p].tail - e.head).length < 1e-5
        eb[n] = e
    bpy.ops.object.mode_set(mode="OBJECT")
    data.display_type = "STICK"
    return ob


def seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (p - (a + ab * t)).length


def weights_for(v, spec, segs, power=4.0, maxinf=4):
    w = {}
    for item in spec:
        name, fn = (item, None) if isinstance(item, str) else item
        m = 1.0 if fn is None else fn(v)
        if m <= 0:
            continue
        a, b = segs[name]
        w[name] = m / max(seg_dist(v, a, b), 0.004) ** power
    top = sorted(w.items(), key=lambda kv: -kv[1])[:maxinf]
    s = sum(x for _, x in top)
    top = [(n, x / s) for n, x in top if x / s > 0.01]
    s = sum(x for _, x in top)
    return [(n, x / s) for n, x in top]


def smoothstep(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


# ----------------------------------------------------------------------------- body mesh
def build_body(name, parts, palette, material, arm_ob, bones):
    verts, faces, cols, smooth, owner = [], [], [], [], []
    for pi, p in enumerate(parts):
        off = len(verts)
        verts += [tuple(x) for x in p.v]
        faces += [tuple(i + off for i in f) for f in p.f]
        cols += p.c
        smooth += p.s
        owner += [pi] * len(p.v)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    assign_palette_uvs(me, cols, palette)
    me.polygons.foreach_set("use_smooth", smooth)
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    segs = {n: (Vector(h), Vector(t)) for n, h, t, _ in bones}
    groups = {n: ob.vertex_groups.new(name=n) for n, *_ in bones}
    for i, co in enumerate(verts):
        for bn, w in weights_for(Vector(co), parts[owner[i]].bones, segs):
            groups[bn].add([i], w, "REPLACE")
    ob.parent = arm_ob
    mod = ob.modifiers.new("Armature", "ARMATURE")
    mod.object = arm_ob
    return ob


def assign_palette_uvs(me, cols, palette):
    uv = me.uv_layers.new(name="UVMap")
    for poly, c in zip(me.polygons, cols):
        u = palette.uv(c)
        for li in poly.loop_indices:
            uv.data[li].uv = u


def bone_attached_mesh(name, part, palette, material, arm_ob, bone):
    """Separate rigid mesh parented to `bone` (exports as a child node of that joint)."""
    b = arm_ob.data.bones[bone]
    tail = arm_ob.matrix_world @ b.matrix_local @ Matrix.Translation((0, b.length, 0))
    inv = tail.inverted()
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(inv @ v) for v in part.v], [], part.f)
    me.update()
    assign_palette_uvs(me, part.c, palette)
    me.polygons.foreach_set("use_smooth", part.s)
    me.materials.append(material)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.parent, ob.parent_type, ob.parent_bone = arm_ob, "BONE", bone
    ob.matrix_parent_inverse = Matrix.Identity(4)
    ob.matrix_basis = Matrix.Identity(4)
    return ob


def tri_count(ob):
    ob.data.calc_loop_triangles()
    return len(ob.data.loop_triangles)


# ----------------------------------------------------------------------------- animation
def local_quat(arm_ob, bone, euler_deg):
    x, y, z = euler_deg
    if bone.endswith(".R"):
        y, z = -y, -z
    q = Euler((math.radians(x), math.radians(y), math.radians(z)), "XYZ").to_quaternion()
    m = arm_ob.data.bones[bone].matrix_local.to_quaternion()
    return m.inverted() @ q @ m


def local_loc(arm_ob, bone, loc):
    return arm_ob.data.bones[bone].matrix_local.to_3x3().inverted() @ Vector(loc)


def key_clip(arm_ob, name, keys, loop=False):
    """keys: [(frame, pose)], pose = {bone: (x, y, z) deg, 'hips_loc': (x, y, z) m}.
    Every bone is keyed on every key so clips never leak pose into each other."""
    act = bpy.data.actions.new(name)
    act.use_fake_user = True
    if arm_ob.animation_data is None:
        arm_ob.animation_data_create()
    arm_ob.animation_data.action = act
    prev = {}
    for f, pose in keys:
        for pb in arm_ob.pose.bones:
            pb.rotation_mode = "QUATERNION"
            q = local_quat(arm_ob, pb.name, pose.get(pb.name, (0, 0, 0)))
            if pb.name in prev and prev[pb.name].dot(q) < 0:
                q.negate()
            prev[pb.name] = q
            pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=f, group=pb.name)
        hb = arm_ob.pose.bones["hips"]
        hb.location = local_loc(arm_ob, "hips", pose.get("hips_loc", (0, 0, 0)))
        hb.keyframe_insert("location", frame=f, group="hips")
    act.use_frame_range = True
    act.frame_start, act.frame_end = keys[0][0], keys[-1][0]
    act.use_cyclic = loop
    return act


def reset_pose(arm_ob):
    if arm_ob.animation_data:
        arm_ob.animation_data.action = None
    for pb in arm_ob.pose.bones:
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = Quaternion()
        pb.location = Vector()
    bpy.context.view_layer.update()


def sym(pose, part, l, r=None):
    pose[f"{part}.L"] = l
    pose[f"{part}.R"] = l if r is None else r
    return pose


# ----------------------------------------------------------------------------- export / render
def export_glb(path, objects):
    for ob in bpy.context.scene.objects:
        ob.select_set(ob in objects)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True, export_yup=True,
        export_apply=False, export_cameras=False, export_lights=False,
        export_skins=True, export_animations=True, export_animation_mode="ACTIONS",
        export_anim_single_armature=True, export_force_sampling=True,
        export_reset_pose_bones=True, export_def_bones=False, export_materials="EXPORT")


def setup_render(res=(720, 960), bg=0.42):
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sh = sc.display.shading
    sh.light, sh.color_type = "STUDIO", "TEXTURE"
    sh.show_backface_culling = True
    sh.show_object_outline, sh.object_outline_color = True, (0.08, 0.08, 0.1)
    sh.show_cavity = False
    sc.display.render_aa = "8"
    w = sc.world or bpy.data.worlds.new("World")
    sc.world = w
    w.color = (bg, bg, bg)
    sc.view_settings.view_transform = "Standard"
    cam = bpy.data.objects.get("PreviewCam")
    if cam is None:
        cam = bpy.data.objects.new("PreviewCam", bpy.data.cameras.new("PreviewCam"))
        sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    sc.camera = cam
    return cam


def render_view(path, cam, yaw_deg, target=(0, 0, 0.78), scale=1.75, pitch_deg=90.0, dist=6.0):
    """yaw 0 = looking at the character's face (camera on -Y)."""
    yaw = math.radians(yaw_deg)
    pitch = math.radians(pitch_deg)
    t = Vector(target)
    d = Vector((math.sin(yaw) * math.sin(pitch), -math.cos(yaw) * math.sin(pitch), math.cos(pitch)))
    cam.location = t + d * dist
    cam.rotation_euler = (pitch, 0.0, yaw)
    cam.data.ortho_scale = scale
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def contact_sheet(paths, out, cols):
    import numpy as np
    imgs = [bpy.data.images.load(p, check_existing=False) for p in paths]
    w, h = imgs[0].size
    rows = math.ceil(len(imgs) / cols)
    sheet_px = np.ones((rows * h, cols * w, 4), dtype=np.float32)
    sheet_px[..., :3] = 0.3
    for k, im in enumerate(imgs):
        a = np.empty(w * h * 4, dtype=np.float32)
        im.pixels.foreach_get(a)
        r, c = rows - 1 - k // cols, k % cols  # pixel rows start at the bottom
        sheet_px[r * h:(r + 1) * h, c * w:(c + 1) * w] = a.reshape(h, w, 4)
    out_img = bpy.data.images.new("contact", cols * w, rows * h)
    out_img.pixels.foreach_set(sheet_px.ravel())
    out_img.filepath_raw = out
    out_img.file_format = "PNG"
    out_img.save()
    for im in imgs:
        bpy.data.images.remove(im)


# ============================================================================= shared character kit
# Added for the enemy/NPC scripts. Additive only: nothing above changed, build_kito.py keeps its own copies.
def lerp(a, b, t):
    return a + (b - a) * t


# Bone families written once as `name=` (same value both sides) or `name=((L), (R))`.
# Scripts with extra mirrored bones extend it: H.PAIRED.add("coat_tail").
PAIRED = {"upper_arm", "forearm", "hand", "thigh", "shin", "foot", "shoulder"}


def pose(**kw):
    """pose(spine=(..), upper_arm=((L), (R)), thigh=(..), hand_R=(..), hips_loc=(x, y, z))."""
    out = {}
    for k, v in kw.items():
        if k == "hips_loc":
            out[k] = tuple(v)
        elif k in PAIRED:
            l, r = (v if isinstance(v[0], (tuple, list)) else (v, v))
            out[f"{k}.L"], out[f"{k}.R"] = tuple(l), tuple(r)
        elif k.endswith(("_L", "_R")):
            out[k[:-2] + "." + k[-1]] = tuple(v)
        else:
            out[k] = tuple(v)
    return out


def mix(a, b, t):
    return {k: tuple(lerp(x, y, t) for x, y in zip(a.get(k, (0, 0, 0)), b.get(k, (0, 0, 0))))
            for k in set(a) | set(b)}


def over(base, **kw):
    d = dict(base)
    d.update(pose(**kw))
    return d


def head_shape(HC, HR, jaw=0.42, jaw_back=0.35, jaw_front=0.12, jaw_z=0.88, front=0.94, rear=1.05, jaw_pow=1.6):
    """Kito's skull as a reusable fn(unit Vector, scale=1)->world point. jaw<0 widens the jaw (brutes)."""
    HC = Vector(HC)

    def fn(u, scale=1.0):
        x, y, z = u.x * HR[0], u.y * HR[1], u.z * HR[2]
        if u.z < 0:
            t = (-u.z) ** jaw_pow
            x *= 1 - jaw * t
            y *= 1 - (jaw_front if u.y < 0 else jaw_back) * t
            z *= jaw_z
        y *= front if u.y < 0 else rear
        return HC + Vector((x, y, z)) * scale
    return fn


FACE = (Vector((0, -0.3, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)))  # decal origin/right/up for a -Y face


def anime_eye(part, bvh, ex, ez, s, k=1.0, iris="amber", iris_dk="amber_dk", white="eye_white", pupil="pupil",
              lash="lash", hi="white", brow="hair", lid_col="skin", brow_spec=(0.042, 0.013, 0.016),
              lid=0.0, lid_tilt=0.0):
    """Kito-style decal eye projected onto `bvh` from the front (-Y).
    ex: |x| of the eye centre, s: +1 left eye (+X) / -1 right eye. k scales the whole eye.
    brow_spec: (height above centre, rise toward the outer end [negative = scowl], thickness) or None.
    lid: 0..1 drops a skin-coloured upper lid over the eye (sly/sleepy/angry); lid_tilt>0 drops the inner corner."""
    O, R, U = FACE
    rx, ry = 0.025 * k, 0.031 * k
    cx = ex * s

    def E(dx, dy, ax, ay, n=16, flat=1.0):
        pts = []
        for j in range(n):
            a = 2 * math.pi * j / n
            yy = ay * math.sin(a) * (flat if math.sin(a) < 0 else 1.0)
            pts.append((cx + s * (dx * k + ax * k * math.cos(a)), ez + dy * k + yy * k))
        return pts if s > 0 else pts[::-1]
    decal(part, bvh, O, R, U, E(0, 0, 0.025, 0.031, 18, 0.88), white, 0.0015)
    decal(part, bvh, O, R, U, E(-0.002, -0.002, 0.0175, 0.025), iris_dk, 0.0026)
    decal(part, bvh, O, R, U, E(-0.002, -0.009, 0.015, 0.015), iris, 0.0034)
    decal(part, bvh, O, R, U, E(-0.002, -0.002, 0.0072, 0.011, 12), pupil, 0.0042)
    decal(part, bvh, O, R, U, E(0.006, 0.01, 0.0055, 0.0055, 8), hi, 0.005, 1)
    decal(part, bvh, O, R, U, E(-0.008, -0.013, 0.003, 0.003, 6), hi, 0.005, 1)
    if lid > 0:
        # lid line in eye-local x (x<0 = inner corner, toward the nose); lid_tilt>0 drops the inner end
        h = ry * (1 - 2 * lid)
        line = lambda lx: h + lid_tilt * ry * (lx / rx)
        ell = [(rx * 1.12 * math.cos(2 * math.pi * j / 40), ry * 1.12 * math.sin(2 * math.pi * j / 40))
               for j in range(40)]
        poly = []
        for j in range(40):
            (x0, y0), (x1, y1) = ell[j], ell[(j + 1) % 40]
            a0, a1 = y0 - line(x0), y1 - line(x1)
            if a0 >= 0:
                poly.append((x0, y0))
            if (a0 >= 0) != (a1 >= 0):
                t = a0 / (a0 - a1)
                poly.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
        if len(poly) >= 3:
            pts = [(cx + s * x, ez + y) for x, y in poly]
            decal(part, bvh, O, R, U, pts if s > 0 else pts[::-1], lid_col, 0.0048)
        xs = [-rx * 1.1 + 2.2 * rx * j / 8 for j in range(9)]
        top = [(cx + s * x, ez + line(x) + 0.0045 * k) for x in xs]
        bot = [(cx + s * x, ez + line(x) - 0.002 * k) for x in xs]
        if s < 0:
            top, bot = top[::-1], bot[::-1]
        decal_strip(part, bvh, O, R, U, top, bot, lash, 0.0054)
    else:
        ths = [math.radians(a) for a in range(185, -20, -15)]
        if s < 0:
            ths = ths[::-1]
        top, bot = [], []
        for a in ths:
            flick = 0.004 * k if math.cos(a) > 0.8 else 0.0
            top.append((cx + s * ((rx + 0.006 * k + flick) * math.cos(a)), ez + (ry + 0.007 * k) * math.sin(a) + flick))
            bot.append((cx + s * (0.024 * k * math.cos(a)), ez + 0.029 * k * math.sin(a)))
        decal_strip(part, bvh, O, R, U, top, bot, lash, 0.0032)
    if brow_spec:
        bz, rise, th0 = brow_spec
        xs = [-0.032 * k + 0.07 * k * j / 6 for j in range(7)]
        top, bot = [], []
        for x in xs:
            t = (x + 0.032 * k) / (0.07 * k)
            zc = ez + bz * k + rise * k * t + 0.005 * k * math.sin(math.pi * t)
            th = (th0 * (1 - t) + th0 * 0.5 * t) * k
            top.append((cx + s * x, zc + th / 2))
            bot.append((cx + s * x, zc - th / 2))
        if s < 0:
            top, bot = top[::-1], bot[::-1]
        decal_strip(part, bvh, O, R, U, top, bot, brow, 0.004)


def run_character(cid, palette, bones, build_parts, build_actions, weapon=None, height=1.5, shots=(),
                  poses_cols=3, args=(), root=None, extra_meshes=()):
    """Shared main(): palette material -> armature -> skinned body (+ `Weapon` on hand.R) -> actions ->
    GLB -> 3 small previews (<= 720 px) -> .blend.
    build_parts() -> [Part]; weapon() -> Part in world space at rest pose; build_actions(arm) -> {name: Action};
    shots: [(action, frame)] for the poses sheet; extra_meshes: [(name, fn()->Part, bone)] more rigid props."""
    root = root or os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    blend = os.path.join(root, "art_source", "blender", f"{cid}.blend")
    prev = os.path.join(root, "art_source", "blender", "previews")
    out = os.path.join(root, "assets", "characters", cid)
    glb = os.path.join(out, f"{cid}.glb")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    os.makedirs(out, exist_ok=True)
    os.makedirs(prev, exist_ok=True)

    img = palette.image(f"{cid}_palette", os.path.join(out, f"{cid}_palette.png"))
    mat = palette.material(f"{cid}_mat", img)
    arm = build_armature(bones)
    body = build_body(cid.capitalize(), build_parts(), palette, mat, arm, bones)
    objs = [arm, body]
    if weapon:
        objs.append(bone_attached_mesh("Weapon", weapon(), palette, mat, arm, "hand.R"))
    for name, fn, bone in extra_meshes:
        objs.append(bone_attached_mesh(name, fn(), palette, mat, arm, bone))
    acts = build_actions(arm)
    reset_pose(arm)
    arm.animation_data.action = acts["idle"]
    sc.frame_start, sc.frame_end, sc.frame_current = 0, int(acts["idle"].frame_range[1]), 0

    tris = {o.name: tri_count(o) for o in objs[1:]}
    zs = [v.co.z for v in body.data.vertices]
    print(f"[{cid}] tris={tris} total={sum(tris.values())} materials={len(bpy.data.materials)} "
          f"height={max(zs) - min(zs):.3f} minz={min(zs):.3f}")
    for n, a in acts.items():
        print(f"[{cid}] action {n}: frames {a.frame_range[0]:.0f}-{a.frame_range[1]:.0f} "
              f"({(a.frame_range[1] - a.frame_range[0]) / FPS:.2f}s){' loop' if a.use_cyclic else ''}")
    export_glb(glb, objs)
    print(f"[{cid}] exported", glb)

    if "--no-render" not in args:
        cam = setup_render((540, 720))
        reset_pose(arm)
        tz = height * 0.5
        render_view(os.path.join(prev, f"{cid}_3q.png"), cam, 35, target=(0, 0, tz), scale=height * 1.2)
        render_view(os.path.join(prev, f"{cid}_side.png"), cam, 90, target=(0, 0, tz), scale=height * 1.2)
        shots = list(shots) or [(n, int(a.frame_range[1] // 2)) for n, a in acts.items()]
        cell = 720 // max(poses_cols, math.ceil(len(shots) / poses_cols))
        sc.render.resolution_x = sc.render.resolution_y = cell
        tmp = os.path.join(prev, f"_tmp_{cid}")
        paths = []
        for name, f in shots:
            arm.animation_data.action = acts[name]
            sc.frame_set(f)
            p = os.path.join(tmp, f"{name}_{f:02d}.png")
            render_view(p, cam, 35, target=(0, 0, tz * 0.95), scale=height * 1.45, pitch_deg=84)
            paths.append(p)
        contact_sheet(paths, os.path.join(prev, f"{cid}_poses.png"), poses_cols)
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    reset_pose(arm)
    arm.animation_data.action = acts["idle"]
    sc.frame_set(0)
    bpy.context.preferences.filepaths.save_version = 0  # no .blend1 backups
    bpy.ops.wm.save_as_mainfile(filepath=blend)
    print(f"[{cid}] saved", blend)
    return arm, body, acts
