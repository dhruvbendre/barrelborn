# Gullhaven environment kit

Rebuild everything (GLBs, palette, .blend, previews) from the project root, headless and deterministic (re-runs give byte-identical GLBs):

    & "C:\Program Files\Blender Foundation\Blender 4.5\blender.exe" -b --factory-startup --python tools/blender/build_env_kit.py
    # -- --no-render   GLBs + .blend only (the .blend then lacks the harbor_mock collection)
    # -- --verify      re-import every GLB in a fresh scene; prints tris, material count, bbox (Blender + Godot axes)
    # -- --qa <dir>    also writes 480 px per-module renders + a tiling strip into <dir>

Outputs: `assets/environment/<module>.glb`, `assets/environment/env_palette.png`, `art_source/blender/env_kit.blend`,
`art_source/blender/previews/env_kit_sheet.png` (row-major in the table order below; last cell = palette),
`art_source/blender/previews/env_harbor_mock.png`.

## Conventions
- Meters. Built in Blender with X = gameplay lane, -Y = toward the camera, Z = up; exported `+Y up` so in Godot
  **X = lane, Y = up, +Z = toward the camera**. Object transforms are identity; geometry sits at the contract origin.
- Each GLB is one static mesh with one material, `env_palette`: a 128x96 flat-swatch atlas (16 px cells) with nearest
  filtering; every face's UVs are collapsed onto its swatch (same approach as `humanoid.Palette`). Each GLB embeds its own copy
  of the PNG. To share one resource in Godot, set the material to an external `env_palette.tres` in the import settings, and
  turn off mipmaps or use nearest filtering on the texture so swatches don't bleed at distance.
- No collision and no LODs. Walkable tops use the lightest, warmest swatches (`pave`, `deck`, `rock_top`, `moss_top`).
- Tiles repeat every 2.0 m along X with no visible seam. Chamfers are dropped on blocks that cross a tile edge, and the cave
  noise has a 2 m period. Checked visually with the `--qa` tiling strip.

## Modules
Bbox = verified after re-import, in **Godot axes** (x, y up, z toward camera), min / max.

| Module | Origin | Tris | Godot bbox min / max | Notes |
|---|---|---|---|---|
| `dock_2m` | top-center (deck top y=0) | 848 | (-1.00, -2.60, -2.00) / (1.00, 0.00, 2.00) | 8 planks of 0.25 m across the lane, 2 butt joints, 2 worn planks. Fascia beam (-0.10..-0.42), lower beam to -1.20, X-brace, 2 piles at x=±0.5 down to -2.6 (algae foot, rope lashing) at the front edge |
| `seawall_2m` | top-center | 600 | (-1.00, -1.40, -2.00) / (1.00, 0.00, 2.00) | Overhanging coping and paving on top. 3 staggered block courses on the front face, down to -1.40 |
| `stone_block_1m` | top-center | 44 | (-0.50, -1.00, -1.50) / (0.50, 0.00, 1.50) | Bevelled sandstone with a light top. Scale x/y in Godot for steps and ledges (the bevels stretch too) |
| `cave_rock_2m` | top-center | 236 | (-1.00, -1.20, -2.00) / (1.00, 0.00, 2.00) | Flat teal-grey top, moss strip and drip lip at the front edge, faceted front face with a jagged bottom (-1.08..-1.20) |
| `house_a` | bottom-center of footprint | 1982 | (-2.84, 0.00, -1.86) / (2.84, 4.87, 2.49) | Walls 5.0 w x 3.9 h x 3.0 d, ridge along the lane. Door, shop window under a **striped awning**, 2 upper windows (shutters, flower box) |
| `house_b` | bottom-center | 1918 | (-2.46, 0.00, -1.84) / (2.46, 5.84, 2.30) | Walls 4.2 x 4.2 x 3.0, gable faces the camera. **Balcony** with a teal door, round gable window, door, 1 window |
| `house_c` | bottom-center | 1786 | (-3.04, 0.00, -1.86) / (3.04, 5.05, 1.95) | Walls 5.4 x 3.2 x 3.0, ridge along the lane, teal door, 2 shuttered windows, **chimney** |
| `crate` | bottom-center | 488 | (-0.45, 0.00, -0.45) / (0.45, 0.90, 0.45) | Frame, plank panels, diagonal brace |
| `barrel` | bottom-center | 528 | (-0.34, 0.00, -0.33) / (0.34, 0.90, 0.33) | Two-tone staves, 4 iron hoops, Bastian's branded mark on the front (-Y / +Z) |
| `rope_post` | bottom-center | 500 | (-0.18, 0.00, -0.18) / (0.18, 0.90, 0.18) | 0.25 m post. The rope coil makes the bbox 0.37 wide |
| `lamp_post` | bottom-center | 372 | (-0.20, 0.00, -0.20) / (0.20, 2.40, 0.20) | Stone base, iron shaft, lantern with warm glass. Not emissive (one material) |
| `bunting_5m` | left anchor | 272 | (0.00, -0.76, -0.01) / (5.00, 0.01, 0.01) | Right anchor at (5, 0, 0); 0.45 m sag. 13 flags cycling coral, gold, teal, cream |
| `mast_sail` | bottom-center (mast foot) | 512 | (-2.50, 0.00, -0.52) / (2.50, 10.00, 0.52) | 10 m mast, yard at 6.6 with a furled cream sail, crow's nest at 8.2-8.7, coral pennant |
| `sloop` | waterline, hull center | 1282 | (-4.48, -1.00, -1.39) / (5.46, 8.60, 1.39) | *The Brine Dream*. Hull 8.6 m (+X = bow) plus bowsprit; draft 1.0, deck about +0.9. Coral main with a gold 8-ray sun-in-ring on both faces, cream jib, cabin, tiller |
| `ship_rail_2m` | bottom-center | 444 | (-1.00, 0.00, -0.08) / (1.00, 0.90, 0.08) | Cap rail at 0.9, turned cream balusters every 0.5 m (x = ±0.25, ±0.75), tiles along X |

Budgets: tiles ≤ 1k, houses ≤ 2.5k, props ≤ 800, sloop ≤ 4k. All modules are within budget; the build prints `OVER BUDGET` if one goes over.
