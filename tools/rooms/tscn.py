"""Tiny .tscn writer for blockout rooms. Layouts are data; this turns them into Godot scenes.

Gameplay plane is z=0. Solid boxes get collision (StaticBody3D + BoxShape3D); decor has none.
Re-run the layout script after edits; hand edits to generated .tscn files will be overwritten.
"""
from __future__ import annotations

import math
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

# Environment kit (tools/blender/build_env_kit.py). Used automatically once the GLBs exist.
KIT_TILES = {"timber": "dock_2m", "timber_light": "dock_2m", "sandstone": "seawall_2m", "cave": "cave_rock_2m", "moss": "cave_rock_2m"}
KIT_BLOCK_MATS = {"sandstone", "stone_dark", "moss", "cliff"}


def kit_path(module: str) -> str:
    return f"res://assets/environment/{module}.glb"


def kit_exists(module: str) -> bool:
    return (ROOT / "assets" / "environment" / f"{module}.glb").exists()

MATS = {
    # name: (albedo hex, roughness)
    "timber": ("8a5a36", 0.9),
    "timber_light": ("b07a4a", 0.9),
    "sandstone": ("cfa874", 0.95),
    "stone_dark": ("9c8a72", 0.95),
    "roof": ("c8573a", 0.8),
    "wall_white": ("cbbba0", 0.95),
    "awning": ("2f8f8a", 0.9),
    "rope": ("c9a66b", 1.0),
    "cliff": ("8f7a5a", 1.0),
    "grass": ("6f9a4a", 1.0),
    "sail": ("f3e7c9", 0.9),
    "cave": ("2c4e55", 1.0),
    "moss": ("4f7b4a", 1.0),
    "iron": ("3a3a42", 0.5),
    "gold": ("d9a531", 0.4),
    "coral": ("e2483d", 0.8),
}


def c(hexs: str) -> str:
    r, g, b = (int(hexs[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return f"Color({r:.3f}, {g:.3f}, {b:.3f}, 1)"


def xf(x=0.0, y=0.0, z=0.0, sx=1.0, sy=1.0, sz=1.0) -> str:
    return f"Transform3D({sx}, 0, 0, 0, {sy}, 0, 0, 0, {sz}, {x:.3f}, {y:.3f}, {z:.3f})"


class Scene:
    def __init__(self, root_name: str, root_type: str = "Node3D", script: str | None = None):
        self.ext: list[tuple[str, str, str]] = []  # (type, path, id)
        self.sub: list[str] = []
        self.nodes: list[str] = []
        self._n = 0
        self._mat_ids: dict[str, str] = {}
        self._box_meshes: dict[tuple, str] = {}
        self._box_shapes: dict[tuple, str] = {}
        props = {}
        if script:
            props["script"] = f'ExtResource("{self.ext_res("Script", script)}")'
        self.root_props = props
        self.root_name, self.root_type = root_name, root_type

    # --- resources ---
    def ext_res(self, typ: str, path: str) -> str:
        for t, p, i in self.ext:
            if p == path:
                return i
        i = str(len(self.ext) + 1)
        self.ext.append((typ, path, i))
        return i

    def _sub(self, typ: str, body: str) -> str:
        self._n += 1
        rid = f"{typ}_{self._n}"
        self.sub.append(f'[sub_resource type="{typ}" id="{rid}"]\n{body}\n')
        return rid

    def mat(self, name: str) -> str:
        if name not in self._mat_ids:
            col, rough = MATS[name]
            self._mat_ids[name] = self._sub("StandardMaterial3D", f"albedo_color = {c(col)}\nroughness = {rough}")
        return self._mat_ids[name]

    def box_mesh(self, size, mat) -> str:
        key = (tuple(round(v, 3) for v in size), mat)
        if key not in self._box_meshes:
            self._box_meshes[key] = self._sub(
                "BoxMesh", f'material = SubResource("{self.mat(mat)}")\nsize = Vector3({size[0]:.3f}, {size[1]:.3f}, {size[2]:.3f})')
        return self._box_meshes[key]

    def box_shape(self, size) -> str:
        key = tuple(round(v, 3) for v in size)
        if key not in self._box_shapes:
            self._box_shapes[key] = self._sub("BoxShape3D", f"size = Vector3({size[0]:.3f}, {size[1]:.3f}, {size[2]:.3f})")
        return self._box_shapes[key]

    # --- nodes ---
    def node(self, name: str, typ: str | None, parent: str = ".", instance: str | None = None,
             groups: list[str] | None = None, **props) -> str:
        head = f'[node name="{name}"'
        if typ:
            head += f' type="{typ}"'
        head += f' parent="{parent}"'
        if instance:
            head += f' instance=ExtResource("{self.ext_res("PackedScene", instance)}")'
        if groups:
            head += " groups=[" + ", ".join(f'"{g}"' for g in groups) + "]"
        head += "]"
        lines = [head] + [f"{k} = {v}" for k, v in props.items()]
        self.nodes.append("\n".join(lines) + "\n")
        return name if parent == "." else f"{parent}/{name}"

    def solid(self, name: str, x0: float, x1: float, top: float, depth: float = 1.0, mat="timber",
              z=0.0, zsize=4.0, parent="Level"):
        """Collidable box spanning x0..x1 with its top surface at `top`.
        Visuals use environment-kit tiles when the kit GLB exists, else a flat box (blockout)."""
        size = (x1 - x0, depth, zsize)
        cx, cy = (x0 + x1) / 2, top - depth / 2
        p = self.node(name, "StaticBody3D", parent, transform=xf(cx, cy, z))
        self.node("Shape", "CollisionShape3D", p, shape=f'SubResource("{self.box_shape(size)}")')
        tile = KIT_TILES.get(mat)
        if tile and kit_exists(tile) and zsize >= 3.9 and depth >= 0.9:
            # Ground run: repeat a 2 m tile, stretched slightly so the run fits exactly.
            n = max(1, math.ceil((x1 - x0) / 2.0 - 0.01))
            sx = (x1 - x0) / (2.0 * n)
            for i in range(n):
                tx = x0 + (i + 0.5) * 2.0 * sx - cx
                self.node(f"Kit{i}", None, p, instance=kit_path(tile),
                          transform=xf(tx, depth / 2, 0, sx, 1, 1))
        elif mat in KIT_BLOCK_MATS and kit_exists("stone_block_1m"):
            # Steps / ledges: one stone block scaled to the solid (1 x 1 x 3 m source).
            self.node("Kit", None, p, instance=kit_path("stone_block_1m"),
                      transform=xf(0, depth / 2, 0, x1 - x0, depth, zsize / 3.0))
        else:
            self.node("Mesh", "MeshInstance3D", p, mesh=f'SubResource("{self.box_mesh(size, mat)}")')

    def prop(self, name: str, module: str, pos, scale=1.0, parent="Decor", fallback=None) -> bool:
        """Place a kit module (origin bottom-centre); returns False (and draws `fallback` box) if missing."""
        if kit_exists(module):
            self.node(name, None, parent, instance=kit_path(module),
                      transform=xf(*pos, scale, scale, scale))
            return True
        if fallback:
            self.decor(name, *fallback, parent=parent)
        return False

    def decor(self, name: str, pos, size, mat, parent="Decor"):
        self.node(name, "MeshInstance3D", parent, transform=xf(*pos),
                  mesh=f'SubResource("{self.box_mesh(size, mat)}")')

    def write(self, rel_path: str):
        out = ["[gd_scene format=3]\n"]
        out += [f'[ext_resource type="{t}" path="{p}" id="{i}"]' for t, p, i in self.ext]
        out.append("")
        out += self.sub
        root = f'[node name="{self.root_name}" type="{self.root_type}"]'
        out.append("\n".join([root] + [f"{k} = {v}" for k, v in self.root_props.items()]) + "\n")
        out += self.nodes
        path = ROOT / rel_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(out), encoding="utf-8")
        print("wrote", rel_path)


def standard_room(s: Scene, cam_min=(-2.0, -1.0), cam_max=(60.0, 6.0), sky="harbor"):
    """Player, camera, HUD, light, environment, sea and kill-water shared by every room."""
    skies = {
        "harbor": ("6fb6e8", "cfe9f2", "f2d49b", 1.0, (-45, -68, 0)),
        "storm": ("1d2f4a", "3c5873", "3c5873", 0.45, (-60, 20, 0)),
        "cave": ("4a8a96", "2c4e55", "1f4b55", 0.6, (-55, -60, 0)),
        "sunset": ("7a5a9a", "ff8a3d", "ffb070", 1.1, (-30, -70, 0)),
    }
    top, horizon, ground, energy, rot = skies[sky]
    skymat = s._sub("ProceduralSkyMaterial",
                    f"sky_top_color = {c(top)}\nsky_horizon_color = {c(horizon)}\n"
                    f"ground_bottom_color = {c(ground)}\nground_horizon_color = {c(horizon)}")
    skyres = s._sub("Sky", f'sky_material = SubResource("{skymat}")')
    env = s._sub("Environment",
                 f'background_mode = 2\nsky = SubResource("{skyres}")\nambient_light_source = 2\n'
                 f"reflected_light_source = 1\nambient_light_color = {c(top)}\nambient_light_energy = 0.42\ntonemap_mode = 3\n"
                 f"tonemap_exposure = 1.0\nfog_enabled = true\nfog_light_color = {c(horizon)}\n"
                 "fog_density = 0.0015\nadjustment_enabled = true\nadjustment_saturation = 1.1")
    s.node("WorldEnvironment", "WorldEnvironment", environment=f'SubResource("{env}")')
    s.node("Sun", "DirectionalLight3D",
           transform=_rot_xf(*rot), light_energy=energy * 0.85, shadow_enabled="true",
           directional_shadow_max_distance=40.0)
    s.node("Player", None, instance="res://scenes/player/player.tscn", transform=xf(0, 0.5, 0))
    s.node("Camera", "Camera3D", script=f'ExtResource("{s.ext_res("Script", "res://scripts/world/side_camera.gd")}")',
           fov=38.0, current="true", target_path='NodePath("../Player")',
           limit_min=f"Vector2({cam_min[0]}, {cam_min[1]})", limit_max=f"Vector2({cam_max[0]}, {cam_max[1]})")
    s.node("HUD", None, instance="res://scenes/ui/hud.tscn")
    s.node("Level", "Node3D")
    s.node("Decor", "Node3D")
    s.node("SpawnPoints", "Node3D")
    # Sea surface (visual) + kill water (hazard) under the whole room.
    if sky != "cave":
        sea = s._sub("PlaneMesh", f'material = ExtResource("{s.ext_res("Material", "res://resources/materials/sea.tres")}")\n'
                                  "size = Vector2(400, 120)\nsubdivide_width = 160\nsubdivide_depth = 48")
        s.node("Sea", "MeshInstance3D", transform=xf(cam_min[0] + 60, -0.9, -45), mesh=f'SubResource("{sea}")')
    width = cam_max[0] - cam_min[0] + 60
    hz = s.node("KillWater", "Area3D", collision_layer=0, collision_mask=6,
                script=f'ExtResource("{s.ext_res("Script", "res://scripts/world/hazard.gd")}")')
    s.node("Shape", "CollisionShape3D", hz, transform=xf((cam_min[0] + cam_max[0]) / 2, -2.2, 0),
           shape=f'SubResource("{s.box_shape((width, 2.0, 6.0))}")')


def _rot_xf(rx_deg: float, ry_deg: float, _rz: float) -> str:
    import math
    rx, ry = math.radians(rx_deg), math.radians(ry_deg)
    # R = Ry * Rx
    cx, sx, cy, sy = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry)
    m = [[cy, sy * sx, sy * cx], [0, cx, -sx], [-sy, cy * sx, cy * cx]]
    return ("Transform3D(" + ", ".join(f"{m[r][col]:.4f}" for r in range(3) for col in range(3))
            + ", 0, 10, 0)")
