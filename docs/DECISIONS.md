# Decisions

| Date | Area | Decision | Why |
|---|---|---|---|
| 2026-10-30 | Engine | **Godot 4.7.2-stable** (winget `GodotEngine.GodotEngine` 4.7.2), standard (non-.NET) build. Pinned in `tools/godot.cmd`. | Latest stable available; GDScript only. |
| 2026-10-30 | Renderer | **GL Compatibility** for desktop + mobile settings. | Keeps the web export path open. Verified running on AMD Radeon iGPU (OpenGL 3.3). |
| 2026-10-30 | Physics | **Jolt** with `areas_detect_static_bodies=true`. | 4.7 default. Without the flag, Area3D slash hitboxes ignore StaticBody crates (caught by tests). |
| 2026-10-30 | Scale | 1 unit = 1 m. Hero 1.5 m. Gameplay plane z=0, clamped for every actor each physics tick. | Brief §12. |
| 2026-10-30 | Feel | Run 5.5 m/s; jump 2.4 m / 0.4 s apex → g=30, v0=12; fall gravity ×1.6; jump cut ×0.45 on release; double jump 1.6 m; coyote 0.10 s; buffer 0.12 s. | Brief targets; derived so height/apex stay consistent. Tunable in `resources/tuning/player_tuning.tres`. |
| 2026-10-30 | Combat | Slash = 0.06 startup / 0.10 active / 0.16 recovery; attacker tracks hit set per swing ID; hit-stop 0.05 s via `Engine.time_scale` restored by a real-time timer. | One hit per target per swing; hit-stop can't stick. |
| 2026-10-30 | Camera | Fixed side camera, FOV 38, distance 12.5, height +2.8, pitch −11°, look-ahead 2 m, dead zone 0.5 m, vertical re-centre only on ground or outside a band, room limits. | Readable landings without chasing every hop. |
| 2026-10-30 | Input | Actions registered in code (`InputSetup`) with keyboard + gamepad. Touch uses `TouchScreenButton` (per-finger index tracking) firing the same actions. | Version-proof; touch shares actions. |
| 2026-10-30 | Save | `user://save.json`, schema `version` 1, write to `.tmp` then rename, previous good save kept as `.bak`; future versions rejected. | Brief §15. |
| 2026-10-30 | Levels | Blockout rooms generated from `tools/rooms/build_rooms.py` → `.tscn`. | Fast, reproducible iteration while geometry is proxy. |
| 2026-10-30 | Audio | Temporary procedural SFX synthesized at runtime (`scripts/world/sfx.gd`). | Honest placeholders, zero licensing risk. |
| 2026-10-30 | Codex | `codex exec -m gpt-6-astra --sandbox workspace-write --skip-git-repo-check -` with stdin task files. | User's global default model (`gpt-6.1-sol`) is rejected for ChatGPT-account auth; per-run override, global config untouched. |
| 2026-10-30 | Vendor tools | Installed Godot-relevant agents/skills from claude-code-game-studios (no hooks/settings). godot-mcp in `.mcp.json`. UnrealClaude not used (Unreal-only). ACE-Step not run (needs Python 3.11+, GPU; this machine: iGPU 512 MB, Python 3.10). | Fit the fixed Godot stack. |
| 2026-10-30 | Naming | Working title **Barrelborn**; hero **Kito Brineheart**; navigator **Marisol "Sol" Quill**; mentor **Bastian Gull**; boss **Captain Varga Chainhook**; enemies **Bilge Brute**, **Powder Gull**; island **Gullhaven**; ship **The Brine Dream**. | Working names; may change. |
| 2026-10-30 | Tuning (tested) | Slash knockback 6 → **3 m/s**; camera distance 12.5 → **10.5 m**; boss fight frames the player–boss midpoint, distance up to 17 m. Basic gaps ≤ 3 m (single jump measured ≈ 3.9 m flat); "double-jump only" spaces ≥ 7.9 m are treated as unreachable. | From the visual tours and tests. |
| 2026-10-30 | Chapter layout | 4 spaces instead of 6–8: prologue, harbor (arrival + town + fight + lookout + secret alcove), cave (power + 3-step teaching + puzzle + shortcut), boss deck (fight + recruit + flag + departure). | Brief allows combining rooms; less transition overhead. |
| 2026-10-30 | Boss rules | Chainhook is armored except while STUCK (after a sweep) or STUNNED (reflected shot). Phase 2 at ≤ 50%: alternating low/high sweeps, 3-shot fan, shorter recovery. | Readable windows; the Gale slash and reflection are both relevant. |
| 2026-10-30 | Persistence | Story rewards save on pickup; boss defeat saves immediately; chapter completion saves before the departure cutscene; the post-chapter checkpoint is Gullhaven's pier. | Death right after a pickup, or skipping the cutscene, can't lose progress. |
