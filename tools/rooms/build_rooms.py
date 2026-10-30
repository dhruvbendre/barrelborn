"""Generate blockout room scenes. Run: python tools/rooms/build_rooms.py"""
from tscn import Scene, standard_room, xf

CRATE = "res://scenes/interactables/crate.tscn"
BRUTE = "res://scenes/enemies/bilge_brute.tscn"
CHECKPOINT = "res://scenes/interactables/checkpoint.tscn"
ROOM = "res://scripts/world/room.gd"


def house(s, name, x, w, h, z=-10.0, roof="roof"):
    variant = "house_" + "abc"[sum(map(ord, name)) % 3]
    if s.prop(name, variant, (x, 0, z), scale=max(0.8, min(1.3, w / 5.0))):
        return
    s.decor(f"{name}Wall", (x, h / 2, z), (w, h, 3), "wall_white")
    s.decor(f"{name}Roof", (x, h + 0.35, z), (w + 0.6, 0.7, 3.4), roof)
    s.decor(f"{name}Door", (x, 0.8, z + 1.52), (0.8, 1.6, 0.05), "timber")


def dock_test():
    """Milestone A test strip: run, jump, gap over water, crate, checkpoint, brute,
    moving platform, ledge and low ceiling."""
    s = Scene("DockTest", script=ROOM)
    s.root_props["objective"] = '"Reach the far end of the dock"'
    s.root_props["room_id"] = '"dock_test"'
    standard_room(s, cam_min=(-2, 0), cam_max=(62, 4))
    # Ground segments (top surface y=0 unless noted).
    s.solid("DockA", -8, 18, 0.0, depth=1.2)
    s.solid("Step1", 11.5, 12.5, 1.0, depth=1.0, mat="timber_light", zsize=1.6)
    s.solid("Ledge1", 13.5, 15.5, 2.0, depth=2.0, mat="sandstone", zsize=3)
    s.solid("DockB", 21, 40, 0.0, depth=1.2)
    s.solid("DockC", 48, 64, 0.0, depth=1.2)
    s.solid("Ceiling", 50, 52.5, 3.4, depth=0.5, mat="stone_dark", zsize=3)
    s.solid("LedgeC", 55, 64, 2.0, depth=2.0, mat="sandstone", zsize=3)
    s.solid("WallL", -8.5, -7.5, 6.0, depth=7.0, mat="cliff")
    s.solid("WallR", 64, 65, 8.0, depth=9.0, mat="cliff")
    # Piers under docks (decor).
    for i, x in enumerate(range(-6, 64, 3)):
        if 18 < x < 21 or 40 < x < 48:
            continue
        s.decor(f"Pile{i}", (x, -1.5, 1.6), (0.3, 2.4, 0.3), "timber")
    # Moving platform across the second gap.
    mp = s.node("MovingPlatform", "AnimatableBody3D", "Level", transform=xf(41.5, -0.2, 0),
                script=f'ExtResource("{s.ext_res("Script", "res://scripts/world/moving_platform.gd")}")',
                offset="Vector3(5, 0, 0)", period=4.5)
    s.node("Mesh", "MeshInstance3D", mp, mesh=f'SubResource("{s.box_mesh((2.2, 0.4, 2.4), "timber_light")}")')
    s.node("Shape", "CollisionShape3D", mp, shape=f'SubResource("{s.box_shape((2.2, 0.4, 2.4))}")')
    # Gameplay objects.
    s.node("Crate1", None, "Level", instance=CRATE, transform=xf(6, 0, 0))
    s.node("Crate2", None, "Level", instance=CRATE, transform=xf(7, 0, 0))
    s.node("Crate3", None, "Level", instance=CRATE, transform=xf(6.5, 0.9, 0))
    s.node("Checkpoint", None, "Level", instance=CHECKPOINT, transform=xf(24, 0, 0))
    s.node("Brute", None, "Level", instance=BRUTE, transform=xf(33, 0.1, 0))
    s.node("Start", "Marker3D", "SpawnPoints", transform=xf(0, 0.2, 0))
    # Harbor dressing behind the lane.
    for i, (x, w, h) in enumerate([(-2, 5, 4), (5, 4, 5), (12, 6, 3.5), (27, 5, 4.5), (35, 4, 3.8), (52, 6, 5)]):
        house(s, f"House{i}", x, w, h)
    s.decor("SeaWall", (28, -0.4, -2.8), (80, 1.6, 1.2), "sandstone")
    s.decor("Cliff", (68, 4, -8), (16, 16, 10), "cliff")
    s.decor("CliffGrass", (68, 12.2, -8), (16.4, 0.4, 10.4), "grass")
    for i, x in enumerate([3, 9, 26, 31, 37]):
        s.decor(f"Post{i}", (x, 0.45, 1.5), (0.22, 0.9, 0.22), "rope")
    s.write("scenes/rooms/dock_test.tscn")


if __name__ == "__main__":
    dock_test()
