# Blender character pipeline

Rebuild Kito (mesh, rig, 12 clips, GLB, previews), headless, from the project root:

    & "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" -b --factory-startup --python tools/blender/build_kito.py
    # add  -- --no-render  to skip the preview renders (~2x faster)

Outputs: `assets/characters/kito/kito.glb` + `kito_palette.png`, `art_source/blender/kito.blend`,
`art_source/blender/previews/kito_{front,side,back,3q,face}.png`, `kito_pose_{slash,run,victory}.png`, `kito_poses.png` (contact sheet).

Conventions (`humanoid.py`, reuse for enemies):
- Meters, feet at origin, character faces Blender -Y (glTF/Godot +Z). Everything is built in place; no object transforms.
- One skinned mesh + one material: a flat-swatch palette PNG, each face's UVs collapsed onto its swatch (`Palette`).
- Geometry is assembled from `Part`s; each Part lists candidate bones (optionally with a multiplier fn) and weights are
  inverse-distance-to-bone-segment, max 4 influences. No auto-weights, so it is deterministic and headless-safe.
- Armature object `Armature`, bones `STANDARD_BONES` (+ extras such as `topknot`, `coat_tail.L/.R`); `.L` = +X.
- Props are separate meshes bone-parented with `bone_attached_mesh()` (exported as a child of the joint -> BoneAttachment3D).
- Clips (`STANDARD_CLIPS`) are 30 fps actions, in place (root never moves; only `hips` bobs), every bone keyed on every key.
  Pose values are degrees in the armature rest frame with anatomical signs (see `humanoid.py` docstring); `.R` is auto-mirrored.
- Loop flags are not stored in glTF: set loop mode for `idle`, `run`, `fall` in Godot's import settings.

## Enemies, boss, NPCs

Same pipeline; each script ends with `humanoid.run_character()` (palette -> armature -> skinned body ->
optional `Weapon` on `hand.R` -> actions -> GLB -> 3 previews <= 720 px -> .blend). From the project root:

    $B = "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"
    & $B -b --factory-startup --python tools/blender/build_brute.py      # Bilge Brute
    & $B -b --factory-startup --python tools/blender/build_gunner.py     # Powder Gull
    & $B -b --factory-startup --python tools/blender/build_chainhook.py  # Captain Varga Chainhook (boss)
    & $B -b --factory-startup --python tools/blender/build_bastian.py    # Bastian Gull (NPC)
    & $B -b --factory-startup --python tools/blender/build_sol.py        # Marisol "Sol" Quill (NPC)
    # each accepts  -- --no-render

Outputs per `<id>`: `assets/characters/<id>/<id>.glb` + `<id>_palette.png`, `art_source/blender/<id>.blend`,
`art_source/blender/previews/<id>_{3q,side,poses}.png` (3q/side show the rest pose).

| id | Actions (loop in Godot import settings: *) | Weapon (`hand.R`) | Extra bones |
|---|---|---|---|
| brute | idle*, walk*, windup, strike, recover, hurt, death | belaying-pin club | - |
| gunner | idle*, aim, fire, reload, hop, hurt, death | musket (two-handed) | coat_tail.L/.R |
| chainhook | idle*, walk*, sweep_tell, sweep, stuck*, shot_tell, shot, stunned*, death | - (winch-gauntlet is body; game draws hook + chain) | hat, plume, coat_tail.L/.R |
| bastian | idle*, talk* | mallet | - |
| sol | idle*, talk*, point | - | braid.1, braid.2, index.L |

Clip lengths are whole frames at 30 fps (the glTF exporter samples integer frames): `strike` is 4 f (0.133 s) and
`sweep` 13 f (0.433 s) instead of 0.15 s / 0.45 s; scale playback in Godot if exact timing matters.
`humanoid.py` shared kit (additive, Kito unaffected): `pose/over/mix` pose DSL (`PAIRED` set for mirrored bone
families), `head_shape()`, `anime_eye()` (decal eye with optional lid/scowl), `run_character()`.
