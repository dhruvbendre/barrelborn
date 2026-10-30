# Resume here

1. Read `CLAUDE.md` (commands and conventions) and `docs/BUILD_STATUS.md` (where things stand).
2. Sanity check: `tools\godot.cmd --headless --path . --import`, then both test suites:
   - `tools\godot.cmd --headless --path . res://tests/test_runner.tscn` (expect 22/22)
   - `tools\godot.cmd --headless --path . res://tests/chapter_flow.tscn` (expect 28/28)
3. Codex outputs: check `art_source/generation_records/*.report.md` and `art_source/concepts/**`. Review each image. Update `docs/ASSET_MANIFEST.json` (queued → generated → accepted/rejected).
4. Blender characters: `tools/blender/README.md`. GLBs live in `assets/characters/<id>/`.
5. Rooms: edit `tools/rooms/build_chapter1.py` → `python tools/rooms/build_chapter1.py` (from `tools/rooms/`). Don't hand-edit generated rooms.
6. Visual QA: `tools\godot.cmd --path . res://tests/chapter_tour.tscn` → look at `qa/screens/chapter/`.

Story flags (stable IDs): `story_prologue_seen`, `item_cutlass`, `harbor_chest_fisher`, `ability_wind_slash`, `cave_boulder`,
`cave_bridge_switch`, `cave_shortcut_plate`, `harbor_drawbridge_switch`, `harbor_secret_chest`,
`boss_chainhook_defeated`, `crew_sol`, `flag_raised`, `chapter1_complete`, `visited_<room>`.

Debug: open any room directly (`tools\godot.cmd --path . res://scenes/rooms/cave.tscn`). The player's `force_sword` export enables the sword without the pickup.
