# BARRELBORN — project instructions (Claude Code)

2.5D pirate action-adventure. Godot **4.7.2-stable**, typed GDScript, **Compatibility** renderer, Jolt physics.
Full brief: `docs/MASTER_BRIEF.md`. Read `docs/RESUME.md` first when starting a session.

## Run / check
- Godot binary: `tools\godot.cmd` (pinned path; override with `GODOT` env var).
- Import: `tools\godot.cmd --headless --path . --import`
- Logic tests: `tools\godot.cmd --headless --path . res://tests/test_runner.tscn` (exit 0 = pass)
- Visual QA tour (windowed, writes `qa/screens/*.png`): `tools\godot.cmd --path . res://tests/visual_tour.tscn`
- Play: `tools\godot.cmd --path .` (title) or append a room path, e.g. `res://scenes/rooms/dock_test.tscn`.
- Rooms are generated: edit `tools/rooms/build_rooms.py`, run `python tools/rooms/build_rooms.py`. Don't hand-edit generated room `.tscn`.
- Hero model: `tools/blender/build_kito.py` (Blender 4.5 LTS, headless). Codex image tasks: `python tools/asset_tasks/run_codex_task.py <task.md>` (run from PowerShell; needs `node` on PATH).

## Conventions
- World X = horizontal, Y = up, gameplay plane Z = 0 (clamped every physics frame for actors).
- Models authored facing +Z; controllers yaw them to ±X.
- Layers: 1 world, 2 player, 3 enemies, 4 interact, 5 hazard.
- Damage: targets implement `apply_hit(hit: Hit) -> bool`. One hit per target per swing (attacker tracks).
- Progress: `Game.grant(id)` is idempotent — use stable string IDs for every reward/ability/story beat.
- Tuning numbers live in `resources/tuning/*.tres`, not scattered literals.
- UI listens to `Game` signals; never poll the scene tree from UI.
- Mark temporary art `PROXY` (node `editor_description` + `docs/ASSET_MANIFEST.json`).

## Working docs (keep current)
`docs/BUILD_STATUS.md`, `docs/DECISIONS.md`, `docs/ART_BIBLE.md`, `docs/ASSET_MANIFEST.json`, `docs/QA.md`, `docs/RESUME.md`.
Never claim engine-tested/visually-reviewed without a real run recorded in `docs/QA.md`.

## Agents & skills
`.claude/agents/` and `.claude/skills/` include a Godot-relevant subset of
[claude-code-game-studios](https://github.com/donchitos/claude-code-game-studios) (MIT). Where they mention
`design/gdd/` or `production/`, use this repo's `docs/` instead. Its hooks/settings were intentionally not installed.
`.mcp.json` registers godot-mcp (available after a Claude Code restart).
