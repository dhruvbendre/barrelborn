"""Chapter 1 (Gullhaven) blockout rooms. Run: python tools/rooms/build_chapter1.py

Measured controller limits (tests/visual_tour): single jump ~3.9 m flat / 2.4 m high,
double jump ~4.0 m high / ~6-7 m flat. Gaps and heights below are chosen against those.
"""
import json

from tscn import Scene, standard_room, xf
from build_rooms import house

R = "res://scenes/"
ROOMS = {"harbor": R + "rooms/harbor.tscn", "cave": R + "rooms/cave.tscn", "boss": R + "rooms/boss_deck.tscn"}


def q(v) -> str:
    """Godot literal for a Python value (strings JSON-escaped, which Godot's parser accepts)."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return json.dumps(v)
    return str(v)


def inst(s: Scene, name: str, scene: str, x: float, y: float = 0.0, parent="Level", **props):
    s.node(name, None, parent, instance=R + scene, transform=xf(x, y, 0), **{k: q(v) for k, v in props.items()})


def lines(*ls: str) -> str:
    return "\n".join(ls)


def spawn(s: Scene, name: str, x: float, y: float):
    s.node(name, "Marker3D", "SpawnPoints", transform=xf(x, y, 0))


def mover(s: Scene, name: str, flag: str, x0: float, x1: float, top: float, lift: float, depth=0.4, mat="timber_light"):
    """Bridge/platform that moves by `lift` (meters, Y) once `flag` is set (Gate script)."""
    size = (x1 - x0, depth, 2.6)
    p = s.node(name, "AnimatableBody3D", "Level", transform=xf((x0 + x1) / 2, top - depth / 2, 0),
               script=f'ExtResource("{s.ext_res("Script", "res://scripts/interact/gate.gd")}")',
               flag=q(flag), lift=lift, open_time=1.0)
    s.node("Mesh", "MeshInstance3D", p, mesh=f'SubResource("{s.box_mesh(size, mat)}")')
    s.node("Shape", "CollisionShape3D", p, shape=f'SubResource("{s.box_shape(size)}")')


def ferry(s: Scene, name: str, x: float, offset: float, period: float, y=-0.2):
    mp = s.node(name, "AnimatableBody3D", "Level", transform=xf(x, y, 0),
                script=f'ExtResource("{s.ext_res("Script", "res://scripts/world/moving_platform.gd")}")',
                offset=f"Vector3({offset}, 0, 0)", period=period)
    s.node("Mesh", "MeshInstance3D", mp, mesh=f'SubResource("{s.box_mesh((2.4, 0.4, 2.4), "timber_light")}")')
    s.node("Shape", "CollisionShape3D", mp, shape=f'SubResource("{s.box_shape((2.4, 0.4, 2.4))}")')


def bunting(s: Scene, x0: float, x1: float, y: float, z: float = -1.6):
    if s.prop(f"Bunting{x0:.0f}", "bunting_5m", (x0, y, z)):
        for k in range(1, int((x1 - x0) / 5.0)):
            s.prop(f"Bunting{x0:.0f}_{k}", "bunting_5m", (x0 + 5.0 * k, y, z))
        return
    cols = ["coral", "gold", "awning", "sail"]
    n = int((x1 - x0) / 0.8)
    for i in range(n):
        s.decor(f"Flag{x0:.0f}_{i}", (x0 + i * 0.8, y - (0.25 if i % 2 else 0.1), z), (0.35, 0.35, 0.03), cols[i % 4])


# ---------------------------------------------------------------------------

def harbor():
    s = Scene("Harbor", script="res://scripts/world/room.gd")
    s.root_props["objective"] = q("Explore Gullhaven harbor")
    s.root_props["room_id"] = q("harbor")
    standard_room(s, cam_min=(-3, 0), cam_max=(72, 7))
    # Arrival beach + safe teaching section.
    s.solid("Beach", -8, 9, 0.0, depth=1.4, mat="sandstone")
    s.solid("WallL", -9, -8, 9.0, depth=10, mat="cliff")
    s.solid("StepBox", 5, 6.2, 1.0, depth=1.0, mat="timber_light", zsize=1.4)
    if not s.prop("WashedBarrel", "barrel", (0.6, -0.2, 0.9)):
        s.decor("WashedBarrel", (0.6, 0.25, 0.9), (0.7, 0.9, 0.7), "timber")
        s.decor("WashedBarrelHoop", (0.6, 0.45, 0.9), (0.74, 0.08, 0.74), "iron")
    for i, (x, z) in enumerate([(8.2, -1.4), (24.5, -1.5), (35.2, -1.4), (63, -1.5)]):
        s.prop(f"Barrel{i}", "barrel", (x, 0, z))
        s.prop(f"Crate{i}", "crate", (x + 0.9, 0, z - 0.2))
    for i, x in enumerate([12.5, 31.5, 70.0]):
        s.prop(f"Lamp{i}", "lamp_post", (x, 0, -1.7))
    inst(s, "Sign", "interactables/sign.tscn", 3.0,
         lines=lines("GULLHAVEN", "By order of Captain Chainhook: all catches, coins and complaints are TAXED."))
    # Dock 1: Bastian, cutlass, crate wall, first brute, fisher, chest.
    s.solid("Dock1", 9, 30, 0.0, depth=1.2)
    inst(s, "Bastian", "npcs/bastian.tscn", 11.5,
         lines=lines(
             "...That plug round your neck. That's my cooper's gull. I made that barrel.",
             "Kito: I floated in it for nine days! Next I'm getting a ship, a crew, and the title of Pirate King!",
             "Bastian: Hah. Start with a sword. There's an old cutlass on my bench - it was going to rust anyway.",
             "Bastian: Chainhook's thugs have barricaded the dock. Crates break easier than heads.",
         ),
         after_flag="item_cutlass",
         after_lines=lines("Bastian: Swing with your whole arm, boy. Up past the crates.",
                           "Bastian: When you're done, the old cave above the cliffs hums on stormy nights. Might suit a dreamer."))
    s.solid("Bench", 13.6, 15.4, 0.8, depth=0.8, mat="timber", zsize=1.2, z=-0.9)
    inst(s, "Cutlass", "interactables/pickup.tscn", 14.5, 0.0, flag="item_cutlass", toast_text="Got Bastian's Cutlass!",
         hint=lines("Press J / X / gamepad X to slash. Slash in the air too.",
                    "Hold Jump for a high jump, tap it for a short hop. Jump again in mid-air."),
         objective_after="Break through the crate barricade")
    house(s, "Workshop", 13, 6, 4.2, z=-5.0)
    for i, y in enumerate([0.0, 0.9, 1.8]):
        inst(s, f"Barricade{i}", "interactables/crate.tscn", 18.0, y)
    s.solid("Awning", 16.6, 19.4, 3.2, depth=0.45, mat="awning", zsize=3.0)
    inst(s, "Fisher", "npcs/fisher.tscn", 21.5,
         lines=lines("Old Fisher: Chainhook's brute took my whole catch again.",
                     "Old Fisher: Teach him some manners and the chest by the water is yours. I hid it from the tax."))
    inst(s, "Brute1", "enemies/bilge_brute.tscn", 26.0, 0.1, patrol_range=2.0)
    inst(s, "Chest1", "interactables/chest.tscn", 28.5, reward_id="harbor_chest_fisher", coins=15,
         objective_after="Head east along the docks")
    # Water gap 30..33 (3 m).
    s.solid("Dock2", 33, 52, 0.0, depth=1.2)
    inst(s, "Checkpoint1", "interactables/checkpoint.tscn", 34.0)
    # Stairs up to the lookout; route continues over the treasure alcove roof.
    s.solid("Stair1", 37, 39, 1.6, depth=1.6, mat="sandstone", zsize=3)
    s.solid("Stair2", 39, 41, 3.2, depth=3.2, mat="sandstone", zsize=3)
    s.solid("Lookout", 41, 44, 4.6, depth=4.6, mat="sandstone", zsize=3)
    s.solid("AlcoveRoof", 44, 49.6, 4.6, depth=0.4, mat="stone_dark", zsize=3)
    s.solid("Lintel", 49.0, 49.6, 4.2, depth=1.0, mat="stone_dark", zsize=3)
    inst(s, "TreasureGate", "interactables/gate.tscn", 49.3, flag="harbor_drawbridge_switch", lift=3.0)
    inst(s, "SecretChest", "interactables/chest.tscn", 46.5, reward_id="harbor_secret_chest", coins=40,
         heart_upgrade=True, toast_text="Secret treasure! +40 coins and a new heart!")
    inst(s, "LookoutSign", "interactables/sign.tscn", 42.5, 4.6,
         lines=lines("An old winch-lock on the mast out there controls the gate below.",
                     "Far too far to reach with any blade... you'd need to throw the wind itself."))
    # The distant mechanism: crow's nest over water (unreachable: 7.9 m gap at 4.6 m height).
    s.solid("CrowsNest", 57.5, 58.5, 4.6, depth=0.5, mat="timber", zsize=1.6)
    s.decor("Mast", (58.0, 1.8, -0.4), (0.25, 5.6, 0.25), "timber")
    inst(s, "DrawbridgeSwitch", "interactables/wind_switch.tscn", 58.0, 4.6, flag="harbor_drawbridge_switch",
         toast_text="Clunk! Something opened below the lookout.")
    # Ferry across 52..61 (water below the nest).
    ferry(s, "Ferry", 53.8, 5.4, 5.0)
    s.solid("Dock3", 61, 76, 0.0, depth=1.2)
    s.solid("WallR", 76, 77, 10.0, depth=11, mat="cliff")
    s.decor("CliffFace", (68.5, 5, -4.5), (15, 10, 4), "cliff")
    s.decor("CliffGrass", (68.5, 10.2, -4.5), (15.4, 0.4, 4.4), "grass")
    inst(s, "CaveDoor", "interactables/door.tscn", 65.0, target_room=ROOMS["cave"], target_spawn="FromHarbor",
         prompt="Enter the cave")
    inst(s, "PierDoor", "interactables/door.tscn", 74.0, target_room=ROOMS["boss"], target_spawn="Start",
         prompt="Board the Gilded Gullet", requires="ability_wind_slash",
         locked_text="Chainhook's ship. You'll need more than a cutlass to take it.")
    spawn(s, "Start", 1.5, 0.1)
    spawn(s, "Arrival", 1.5, 0.1)
    spawn(s, "FromCave", 63.5, 0.1)
    spawn(s, "FromShortcut", 46.0, 4.7)
    spawn(s, "FromBoss", 72.0, 0.1)
    # Dressing: town behind the lane.
    for i, (x, w, h) in enumerate([(-3, 5, 4), (4, 4, 5.5), (22, 5, 4.5), (28, 4, 3.8), (36, 6, 5), (64, 5, 4)]):
        house(s, f"House{i}", x, w, h)
    s.decor("SeaWall", (30, -0.4, -2.8), (80, 1.6, 1.2), "sandstone")
    for i, x in enumerate([10, 16, 23, 27, 35, 62, 70]):
        s.prop(f"Post{i}", "rope_post", (x, 0, 1.5), fallback=((x, 0.45, 1.5), (0.22, 0.9, 0.22), "rope"))
    bunting(s, 20, 31, 3.6)
    bunting(s, 61, 72, 3.4)
    s.decor("GulletHull", (84, 1.0, -3), (14, 3.5, 4), "iron")
    s.decor("GulletSail", (84, 6.0, -3), (6, 5, 0.1), "sail")
    s.write("scenes/rooms/harbor.tscn")


def cave():
    s = Scene("Cave", script="res://scripts/world/room.gd")
    s.root_props["objective"] = q("Find what hums inside the cave")
    s.root_props["room_id"] = q("cave")
    standard_room(s, cam_min=(-1, 0), cam_max=(80, 4), sky="cave")
    s.solid("Floor1", -4, 28, 0.0, depth=1.2, mat="cave")
    s.solid("WallL", -5, -4, 8.0, depth=9, mat="cave")
    s.solid("Roof", -5, 84, 8.0, depth=1.0, mat="cave", zsize=4)
    inst(s, "BackDoor", "interactables/door.tscn", 0.0, target_room=ROOMS["harbor"], target_spawn="FromCave",
         prompt="Back to the harbor")
    spawn(s, "FromHarbor", 1.5, 0.1)
    spawn(s, "Start", 1.5, 0.1)
    # Shrine + the Gale Conch.
    s.solid("Pedestal", 7.4, 8.6, 0.7, depth=0.7, mat="moss", zsize=1.4)
    inst(s, "GaleConch", "interactables/pickup.tscn", 8.0, 0.7, flag="ability_wind_slash", toast_text="Gale Conch! Wind Slash learned!",
         hint=lines("The conch hums with a captured storm wind.",
                    "Press L / C / gamepad Y to loose a Gale Slash. It costs Spirit, which refills over time.",
                    "It flies far, breaks cracked stone and trips distant switches."),
         objective_after="Break the cracked boulder with a Gale Slash")
    inst(s, "Checkpoint", "interactables/checkpoint.tscn", 4.0)
    # Teach 1: stationary target.
    inst(s, "Boulder", "interactables/boulder.tscn", 15.0, reward_id="cave_boulder")
    # Teach 2: distant switch raises a bridge across the pit (28..36).
    inst(s, "PitSign", "interactables/sign.tscn", 24.0,
         lines=lines("A rope bridge lies sunk in the pit. Its winch-switch is on the far side."))
    mover(s, "Bridge", "cave_bridge_switch", 28, 36, -2.6, 2.6)
    s.solid("Floor2a", 36, 60, 0.0, depth=1.2, mat="cave")
    s.solid("Floor2b", 62, 84, 0.0, depth=1.2, mat="cave")
    inst(s, "BridgeSwitch", "interactables/wind_switch.tscn", 37.5, flag="cave_bridge_switch",
         toast_text="The bridge rises!")
    # Teach 3: ranged enemy on a raised shelf.
    s.solid("Shelf", 46, 54, 1.5, depth=1.5, mat="moss", zsize=3)
    inst(s, "Gunner", "enemies/powder_gull.tscn", 50.5, 1.6)
    inst(s, "Checkpoint2", "interactables/checkpoint.tscn", 56.0)
    # Puzzle: carry the barrel over a small channel, up onto the shelf, onto the plate.
    inst(s, "Barrel", "interactables/barrel.tscn", 58.5, 0.1)
    s.decor("ChannelWater", (61, -0.9, 0), (2, 0.2, 2.6), "awning")
    s.solid("PlateShelf", 64, 69, 2.0, depth=2.0, mat="moss", zsize=3)
    inst(s, "Plate", "interactables/pressure_plate.tscn", 66.5, 2.0, flag="cave_shortcut_plate",
         toast_text="Click! The tunnel gate grinds open.")
    inst(s, "PuzzleSign", "interactables/sign.tscn", 57.0,
         lines=lines("Bastian's old smuggler tunnel. The gate opens when the plate on the shelf is weighed down.",
                     "Use: lift / put down.  Slash while carrying: throw."))
    inst(s, "TunnelGate", "interactables/gate.tscn", 72.0, flag="cave_shortcut_plate", lift=3.0)
    inst(s, "Shortcut", "interactables/door.tscn", 76.0, target_room=ROOMS["harbor"], target_spawn="FromShortcut",
         prompt="Take the tunnel to the harbor lookout")
    s.solid("WallR", 80, 81, 8.0, depth=9, mat="cave")
    # Glow crystals.
    for i, (x, y) in enumerate([(6, 3), (12, 5), (31, 4), (44, 5.5), (63, 4.5), (75, 3.5)]):
        s.decor(f"Crystal{i}", (x, y, -1.8), (0.4, 0.9, 0.4), "awning")
    s.write("scenes/rooms/cave.tscn")


def boss_deck():
    s = Scene("BossDeck", script="res://scripts/world/boss_deck.gd")
    s.root_props["objective"] = q("Defeat Captain Chainhook")
    s.root_props["room_id"] = q("boss_deck")
    standard_room(s, cam_min=(4, 0.5), cam_max=(34, 2.5), sky="sunset")
    s.solid("Gangplank", -4, 4, 0.0, depth=0.4, mat="timber_light", zsize=2)
    s.solid("Deck", 4, 34, 0.0, depth=1.0, mat="timber_light")
    s.decor("Hull", (19, -1.2, 0), (32, 2.6, 5), "iron")
    s.solid("Stern", 33, 34.5, 4.0, depth=4.0, mat="timber", zsize=3)
    s.solid("WallL", -5, -4, 8.0, depth=9, mat="cliff")
    for i, x in enumerate([12, 24]):
        s.decor(f"Mast{i}", (x, 5, -3.2), (0.35, 10, 0.35), "timber")
        s.decor(f"Sail{i}", (x, 7.6, -3.0), (5, 4.0, 0.08), "sail")
    inst(s, "Checkpoint", "interactables/checkpoint.tscn", 2.5)
    spawn(s, "Start", 0.0, 0.1)
    s.node("Boss", None, "Level", instance=R + "bosses/chainhook.tscn", transform=xf(26, 0.1, 0))
    trig = s.node("ArenaTrigger", "Area3D", "Level", transform=xf(9, 0.0, 0), collision_layer=0, collision_mask=2)
    s.node("Shape", "CollisionShape3D", trig, shape=f'SubResource("{s.box_shape((1, 3, 3))}")')
    # Arena wall behind the player; boss_deck.gd enables it while the fight runs.
    s.solid("ArenaWall", 4.6, 5.0, 4.0, depth=4.0, mat="iron", zsize=3)
    # Sol's cage near the stern.
    inst(s, "Sol", "npcs/sol.tscn", 31.6, 0.0,
         lines=lines(
             "Sol: You actually beat him. With a cutlass, a gust of wind and absolutely no plan.",
             "Kito: I had a plan! Win, then get a navigator. You're a navigator, right?",
             "Sol: ...I chart his routes. Charted. Past tense.",
             "Sol: Fine. Bastian finished the Brine Dream - she's moored alongside. Raise your flag and I'll plot us a course.",
         ),
         after_flag="crew_sol",
         after_lines=lines("Sol: The flag, captain. Unless you want to sail without colours."),
         grant_on_talk="crew_sol")
    inst(s, "CageGate", "interactables/gate.tscn", 30.5, 0.0, flag="boss_chainhook_defeated", lift=3.2)
    s.solid("CageRoof", 30.2, 33, 4.0, depth=0.3, mat="iron", zsize=3)
    # The Brine Dream alongside (departure).
    if s.prop("Brine", "sloop", (40, -0.6, -1.5)):
        pass  # boss_deck.gd sails every Decor/Brine* node
    else:
        s.decor("BrineHull", (40, -0.4, -1.5), (9, 1.6, 3.5), "timber")
        s.decor("BrineMast", (40, 3.4, -1.5), (0.25, 6.4, 0.25), "timber")
        s.decor("BrineSail", (40, 4.2, -1.3), (3.2, 3.4, 0.06), "coral")
    inst(s, "RaiseFlag", "interactables/sign.tscn", 28.0, 0.0, prompt="Raise your flag",
         lines=lines("Kito: Sun and compass. My flag. Gullhaven, remember it!",
                     "Sol: Course plotted: north-east, to the Broken Lighthouse."),
         grant_on_talk="flag_raised")
    s.write("scenes/rooms/boss_deck.tscn")


if __name__ == "__main__":
    harbor()
    cave()
    boss_deck()
