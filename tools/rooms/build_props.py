"""Generate small PROXY prop/NPC scenes. Run: python tools/rooms/build_props.py"""
from tscn import Scene, c, xf

ROT_X90 = "Transform3D(1, 0, 0, 0, -4.37114e-08, -1, 0, 1, -4.37114e-08, {x}, {y}, {z})"


def mat(s: Scene, hexs: str, extra: str = "") -> str:
    return s._sub("StandardMaterial3D", f"albedo_color = {c(hexs)}" + (("\n" + extra) if extra else ""))


def mesh(s: Scene, typ: str, m: str, **props) -> str:
    body = f'material = SubResource("{m}")\n' + "\n".join(f"{k} = {v}" for k, v in props.items())
    return s._sub(typ, body)


def shape(s: Scene, typ: str, **props) -> str:
    return s._sub(typ, "\n".join(f"{k} = {v}" for k, v in props.items()))


def mi(s: Scene, name: str, m: str, t: str, parent: str = ".", note: str | None = None):
    kw = {"transform": t, "mesh": f'SubResource("{m}")'}
    if note:
        kw["editor_description"] = f'"{note}"'
    s.node(name, "MeshInstance3D", parent, **kw)


def col(s: Scene, sh: str, t: str, parent: str = "."):
    s.node("Shape", "CollisionShape3D", parent, transform=t, shape=f'SubResource("{sh}")')


def pickup():
    s = Scene("Pickup", "Area3D", "res://scripts/interact/pickup.gd")
    glow = mat(s, "ffd966", "emission_enabled = true\nemission = Color(1, 0.75, 0.25, 1)\nemission_energy_multiplier = 0.8")
    steel = mat(s, "d9e0ea", "metallic = 0.6\nroughness = 0.3")
    col(s, shape(s, "SphereShape3D", radius=1.0), xf(0, 0.8, 0))
    mi(s, "Icon", mesh(s, "BoxMesh", steel, size="Vector3(0.06, 0.6, 0.03)"), xf(0, 1.0, 0), note="PROXY item icon")
    mi(s, "Halo", mesh(s, "TorusMesh", glow, inner_radius=0.42, outer_radius=0.48), ROT_X90.format(x=0, y=1.0, z=0))
    s.write("scenes/interactables/pickup.tscn")


def chest():
    s = Scene("Chest", "Area3D", "res://scripts/interact/chest.gd")
    wood, gold = mat(s, "7a4a26"), mat(s, "d9a531", "metallic = 0.7\nroughness = 0.35")
    col(s, shape(s, "BoxShape3D", size="Vector3(1.6, 1.6, 2)"), xf(0, 0.6, 0))
    mi(s, "Base", mesh(s, "BoxMesh", wood, size="Vector3(0.9, 0.5, 0.6)"), xf(0, 0.25, -0.3))
    band = mesh(s, "BoxMesh", gold, size="Vector3(0.1, 0.52, 0.62)")
    mi(s, "BandL", band, xf(-0.28, 0.26, -0.3))
    mi(s, "BandR", band, xf(0.28, 0.26, -0.3))
    s.node("Lid", "Node3D", transform=xf(0, 0.5, -0.6))
    mi(s, "Mesh", mesh(s, "BoxMesh", wood, size="Vector3(0.92, 0.18, 0.62)"), xf(0, 0.09, 0.31), parent="Lid")
    s.write("scenes/interactables/chest.tscn")


def wind_switch():
    s = Scene("WindSwitch", "StaticBody3D", "res://scripts/interact/switch.gd")
    s.root_props["wind_only"] = "true"
    iron = mat(s, "3a3a42", "metallic = 0.6")
    col(s, shape(s, "BoxShape3D", size="Vector3(0.7, 1.0, 1.0)"), xf(0, 0.9, 0))
    mi(s, "Post", mesh(s, "BoxMesh", iron, size="Vector3(0.5, 1.6, 0.5)"), xf(0, 0.6, -0.1))
    gem = s._sub("SphereMesh", "radius = 0.28\nheight = 0.56")
    s.node("Gem", "MeshInstance3D", transform=xf(0, 1.1, 0.12), mesh=f'SubResource("{gem}")')
    s.write("scenes/interactables/wind_switch.tscn")


def barrel():
    s = Scene("Barrel", "RigidBody3D", "res://scripts/interact/carryable.gd")
    oak, hoop = mat(s, "9a6133"), mat(s, "3f3f46", "metallic = 0.6")
    col(s, shape(s, "CylinderShape3D", height=0.9, radius=0.36), xf(0, 0.45, 0))
    mi(s, "Body", mesh(s, "CylinderMesh", oak, top_radius=0.33, bottom_radius=0.36, height=0.9), xf(0, 0.45, 0))
    ring = mesh(s, "CylinderMesh", hoop, top_radius=0.37, bottom_radius=0.37, height=0.06)
    mi(s, "Ring1", ring, xf(0, 0.2, 0))
    mi(s, "Ring2", ring, xf(0, 0.7, 0))
    s.write("scenes/interactables/barrel.tscn")


def pressure_plate():
    s = Scene("PressurePlate", "Area3D", "res://scripts/interact/pressure_plate.gd")
    brass = mat(s, "c79a3b", "metallic = 0.6\nroughness = 0.4")
    col(s, shape(s, "BoxShape3D", size="Vector3(1.2, 0.6, 1.6)"), xf(0, 0.3, 0))
    mi(s, "Top", mesh(s, "BoxMesh", brass, size="Vector3(1.2, 0.12, 1.2)"), xf(0, 0.0, 0))
    s.write("scenes/interactables/pressure_plate.tscn")


def room_exit():
    s = Scene("RoomExit", "Area3D", "res://scripts/interact/room_exit.gd")
    s.root_props["monitorable"] = "false"
    col(s, shape(s, "BoxShape3D", size="Vector3(1, 3, 3)"), xf(0, 1.5, 0))
    s.write("scenes/interactables/room_exit.tscn")


def gate():
    s = Scene("Gate", "AnimatableBody3D", "res://scripts/interact/gate.gd")
    iron = mat(s, "3f3d44", "metallic = 0.5")
    col(s, shape(s, "BoxShape3D", size="Vector3(0.6, 3.2, 3)"), xf(0, 1.6, 0))
    mi(s, "Mesh", mesh(s, "BoxMesh", iron, size="Vector3(0.5, 3.2, 2.6)"), xf(0, 1.6, 0))
    s.write("scenes/interactables/gate.tscn")


def boulder():
    s = Scene("Boulder", "StaticBody3D", "res://scripts/world/breakable.gd")
    s.root_props["wind_only"] = "true"
    s.root_props["coins"] = "0"
    rock = mat(s, "6e7f7c")
    crack = mat(s, "7ff3ff", "emission_enabled = true\nemission = Color(0.5, 0.95, 1, 1)\nemission_energy_multiplier = 0.6")
    col(s, shape(s, "BoxShape3D", size="Vector3(1.4, 2.4, 3)"), xf(0, 1.2, 0))
    mi(s, "Rock", mesh(s, "SphereMesh", rock, radius=0.9, height=2.4), xf(0, 1.2, 0, 1.0, 1.0, 1.4))
    mi(s, "Crack", mesh(s, "BoxMesh", crack, size="Vector3(0.06, 1.4, 0.05)"), xf(0.1, 1.3, 0.9))
    s.write("scenes/interactables/boulder.tscn")


def sign():
    """Readable sign / inspect point (Npc with no speaker)."""
    s = Scene("Sign", "Area3D", "res://scripts/interact/npc.gd")
    s.root_props["speaker"] = '""'
    wood = mat(s, "8a5a36")
    col(s, shape(s, "BoxShape3D", size="Vector3(1.4, 2, 2)"), xf(0, 1, 0))
    mi(s, "Post", mesh(s, "BoxMesh", wood, size="Vector3(0.12, 1.2, 0.12)"), xf(0, 0.6, -0.4))
    mi(s, "Board", mesh(s, "BoxMesh", wood, size="Vector3(0.8, 0.45, 0.06)"), xf(0, 1.15, -0.36))
    s.write("scenes/interactables/sign.tscn")


def model_path(cid: str):
    """Rigged character GLB from tools/blender/build_<id>.py, if it has been built."""
    import pathlib
    root = pathlib.Path(__file__).resolve().parents[2]
    return f"res://assets/characters/{cid}/{cid}.glb" if (root / "assets/characters" / cid / f"{cid}.glb").exists() else None


def npc(name: str, path: str, parts: list, speaker: str, model: str | None = None):
    """parts: (name, mesh_type, hex, props, transform) - proxy used only when no rigged model exists."""
    s = Scene(name, "Area3D", "res://scripts/interact/npc.gd")
    s.root_props["speaker"] = f'"{speaker}"'
    col(s, shape(s, "BoxShape3D", size="Vector3(2, 2.4, 2)"), xf(0, 1.2, 0))
    glb = model_path(model) if model else None
    if glb:
        # Three-quarter turn toward an approaching player (who arrives from the left).
        s.node("Visual", "Node3D", transform="Transform3D(0.825, 0, -0.565, 0, 1, 0, 0.565, 0, 0.825, 0, 0, 0)")
        s.node("Model", None, "Visual", instance=glb)
        s.write(path)
        return
    s.node("Visual", "Node3D", editor_description=f'"PROXY blockout of {speaker}"')
    for pname, typ, hexs, props, t in parts:
        mi(s, pname, mesh(s, typ, mat(s, hexs), **props), t, parent="Visual")
    s.write(path)


def door():
    s = Scene("Door", "Area3D", "res://scripts/interact/door.gd")
    dark = mat(s, "141c22")
    col(s, shape(s, "BoxShape3D", size="Vector3(1.6, 2.6, 2.4)"), xf(0, 1.3, 0))
    mi(s, "Mouth", mesh(s, "BoxMesh", dark, size="Vector3(1.6, 2.4, 0.1)"), xf(0, 1.2, -1.3))
    s.write("scenes/interactables/door.tscn")


def chainhook():
    s = Scene("Chainhook", "CharacterBody3D", "res://scripts/bosses/chainhook.gd")
    s.root_props["collision_layer"] = "4"
    col(s, shape(s, "CapsuleShape3D", radius=0.6, height=2.6), xf(0, 1.3, 0))
    plum, gold, iron, skin, black = mat(s, "5b2a6e"), mat(s, "d9a531", "metallic = 0.6"), mat(s, "3a3a42", "metallic = 0.6"), mat(s, "c98a6a"), mat(s, "1a1a22")
    glb = model_path("chainhook")
    s.node("Visual", "Node3D", editor_description='"' + ("Rigged Chainhook model" if glb else "PROXY blockout of Captain Varga Chainhook") + '"')
    if glb:
        s.node("Model", None, "Visual", instance=glb)
    else:
        proxy_chainhook(s, plum, gold, iron, skin, black)
    ring = mat(s, "7ff3ff", "emission_enabled = true\nemission = Color(0.5, 0.95, 1, 1)")
    mi(s, "AimRing", mesh(s, "TorusMesh", ring, inner_radius=0.3, outer_radius=0.38), ROT_X90.format(x=-0.75, y=1.6, z=0.6), parent="Visual")
    s.node("Hook", "Area3D", collision_layer=0, collision_mask=2, monitorable="false")
    col(s, shape(s, "SphereShape3D", radius=0.55), xf(0, 0, 0), parent="Hook")
    mi(s, "Mesh", mesh(s, "TorusMesh", iron, inner_radius=0.22, outer_radius=0.45), xf(0, 0, 0), parent="Hook")
    mi(s, "Chain", mesh(s, "BoxMesh", iron, size="Vector3(0.09, 1, 0.09)"), xf(0, 1.5, 0))
    s.write("scenes/bosses/chainhook.tscn")


def proxy_chainhook(s, plum, gold, iron, skin, black):
    mi(s, "Legs", mesh(s, "BoxMesh", black, size="Vector3(0.5, 0.9, 0.35)"), xf(0, 0.45, 0), parent="Visual")
    mi(s, "Coat", mesh(s, "CylinderMesh", plum, top_radius=0.75, bottom_radius=0.35, height=1.4), xf(0, 1.55, 0), parent="Visual")
    mi(s, "Tail", mesh(s, "BoxMesh", plum, size="Vector3(0.7, 1.0, 0.1)"), xf(0, 0.9, -0.3), parent="Visual")
    mi(s, "EpL", mesh(s, "BoxMesh", gold, size="Vector3(0.35, 0.12, 0.35)"), xf(0.62, 2.22, 0), parent="Visual")
    mi(s, "EpR", mesh(s, "BoxMesh", gold, size="Vector3(0.35, 0.12, 0.35)"), xf(-0.62, 2.22, 0), parent="Visual")
    mi(s, "Head", mesh(s, "SphereMesh", skin, radius=0.25, height=0.5), xf(0, 2.5, 0.05), parent="Visual")
    mi(s, "Hat", mesh(s, "CylinderMesh", black, top_radius=0.3, bottom_radius=0.55, height=0.35), xf(0, 2.85, 0), parent="Visual")
    mi(s, "Plume", mesh(s, "SphereMesh", mat(s, "f5f2ea"), radius=0.12, height=0.6), xf(0.2, 3.15, -0.1), parent="Visual")
    mi(s, "Gauntlet", mesh(s, "CylinderMesh", iron, top_radius=0.2, bottom_radius=0.24, height=0.7), xf(-0.75, 1.6, 0.1), parent="Visual")


def bastian():
    npc("Bastian", "scenes/npcs/bastian.tscn", [
        ("Body", "SphereMesh", "3c6fb0", {"radius": 0.45, "height": 0.9}, xf(0, 0.75, 0, 1.15, 1.0, 1.0)),
        ("Apron", "BoxMesh", "7a4a2a", {"size": "Vector3(0.7, 0.7, 0.05)"}, xf(0, 0.65, 0.42)),
        ("Head", "SphereMesh", "c98a6a", {"radius": 0.22, "height": 0.44}, xf(0, 1.32, 0.05)),
        ("Mustache", "BoxMesh", "f0f0ea", {"size": "Vector3(0.42, 0.08, 0.1)"}, xf(0, 1.25, 0.27)),
        ("Peg", "CylinderMesh", "8a5a36", {"top_radius": 0.05, "bottom_radius": 0.04, "height": 0.35}, xf(0.15, 0.17, 0)),
        ("Boot", "BoxMesh", "4a2f1c", {"size": "Vector3(0.16, 0.3, 0.26)"}, xf(-0.15, 0.15, 0.04)),
        ("Mallet", "CylinderMesh", "8a5a36", {"top_radius": 0.12, "bottom_radius": 0.12, "height": 0.35}, xf(-0.4, 1.55, -0.1)),
    ], "Bastian", model="bastian")


def sol():
    npc("Sol", "scenes/npcs/sol.tscn", [
        ("Body", "CapsuleMesh", "2f8f8a", {"radius": 0.2, "height": 1.0}, xf(0, 0.95, 0)),
        ("Legs", "BoxMesh", "3a3d44", {"size": "Vector3(0.3, 0.6, 0.18)"}, xf(0, 0.3, 0)),
        ("Head", "SphereMesh", "f0c8a8", {"radius": 0.17, "height": 0.34}, xf(0, 1.58, 0)),
        ("Braid", "CylinderMesh", "9a3f22", {"top_radius": 0.05, "bottom_radius": 0.03, "height": 0.6}, xf(0, 1.3, -0.17)),
        ("Goggles", "TorusMesh", "c79a3b", {"inner_radius": 0.12, "outer_radius": 0.15}, xf(0, 1.72, 0.05)),
        ("MapTube", "CylinderMesh", "7a4a2a", {"top_radius": 0.06, "bottom_radius": 0.06, "height": 0.8}, "Transform3D(0.7, 0.7, 0, -0.7, 0.7, 0, 0, 0, 1, 0, 1.1, -0.2)"),
    ], "Sol", model="sol")


def fisher():
    npc("Fisher", "scenes/npcs/fisher.tscn", [
        ("Body", "CapsuleMesh", "b07a4a", {"radius": 0.24, "height": 0.9}, xf(0, 0.75, 0)),
        ("Head", "SphereMesh", "a8714f", {"radius": 0.18, "height": 0.36}, xf(0, 1.35, 0)),
        ("Hat", "CylinderMesh", "e2c28f", {"top_radius": 0.05, "bottom_radius": 0.32, "height": 0.18}, xf(0, 1.55, 0)),
        ("Rod", "CylinderMesh", "6b4126", {"top_radius": 0.01, "bottom_radius": 0.025, "height": 2.0}, "Transform3D(0.5, 0.87, 0, -0.87, 0.5, 0, 0, 0, 1, -0.6, 1.4, 0.3)"),
    ], "Old Fisher")


if __name__ == "__main__":
    for f in (chainhook, door, pickup, chest, wind_switch, barrel, pressure_plate, room_exit, gate, boulder, sign, bastian, sol, fisher):
        f()
