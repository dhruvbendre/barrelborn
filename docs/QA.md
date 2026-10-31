# QA record

Machine: Windows 11, AMD Radeon iGPU (OpenGL 3.3 Compatibility), 15 GB RAM. Engine: Godot 4.7.2-stable.
All results below were produced by actually running the commands on 2026-10-30.

## Automated checks

| Check | Command | Result |
|---|---|---|
| Import / parse | `tools\godot.cmd --headless --path . --import` | PASS, no errors |
| Scene smoke (prologue, harbor, cave, boss_deck, title, chapter_complete) | `tools\godot.cmd --headless --path . res://scenes/<scene>.tscn --quit-after 240` | PASS, no script errors |
| Logic tests | `tools\godot.cmd --headless --path . res://tests/test_runner.tscn` | **22/22 PASS** |
| Chapter flow tests | `tools\godot.cmd --headless --path . res://tests/chapter_flow.tscn` | **30/30 PASS** |
| Milestone A visual tour (input-driven) | `tools\godot.cmd --path . res://tests/visual_tour.tscn` | PASS: full dock_test route, crates, checkpoint, brute killed, moving platform, far ledge |
| Chapter visual tour | `tools\godot.cmd --path . res://tests/chapter_tour.tscn` | PASS: harbor opening played with real input actions up to the 4.6 m lookout; later beats visited; 21 screenshots |

| Boss bot (real input actions, reacts to telegraphs only) | `tools\godot.cmd --headless --path . res://tests/boss_bot.tscn` | PASS: won in 20.7 s, 0 hits taken, reached phase 2 (at 12 HP it won in 8.8 s, so HP was raised to 30) |
| Performance probe (this dev machine only) | `tools\godot.cmd --path . res://tests/perf_probe.tscn` → `qa/perf.txt` | AMD Radeon iGPU, GL 3.3, 1280x720, vsync off: harbor 164 fps avg / 17.5 ms worst; cave 234 fps / 33.6 ms worst (one hitch, likely a first-use shader compile, uninvestigated); boss deck 190 fps / 7.5 ms; ≤ 81 draw calls; ~75 MB static memory |

| Web build (CI) | `.github/workflows/deploy.yml`: Godot 4.7.2 on ubuntu-latest → import → both test suites → `--export-release "Web"` → GitHub Pages | PASS (run 41172503323): build + deploy succeeded |
| Web build in browser | gstack `browse` (headless Chromium, WebGL2) at https://dhruvbendre.github.io/barrelborn/ | PASS: title loads (Continue disabled with no save, Quit hidden on web), New Game → prologue renders, Esc skip → harbor renders with HUD; no console errors (only GPU-stall perf warnings from the screenshot readback). Files: index.wasm 39.5 MB, index.pck 1.7 MB. |

### What the logic tests cover
- Jump math (g = 30, v0 = 12, simulated apex 2.30 m), buffered jump on landing, coyote jump at 0.05 s, no jump after coyote expiry, double jump.
- One hit per target per swing (exactly 1, then 2 after a second swing); Bilge Brute dies in 3 slashes.
- Reward idempotency (grant twice refused; reward crate pays once and doesn't respawn).
- Save: write/load, corrupt main save falls back to `.bak`, future schema rejected, Continue disabled without a save.

### What the chapter flow tests cover
- Prologue skipped == watched (identical flags, checkpoint, objective, destination; lands at harbor Arrival).
- No sword before the cutlass; the boss pier is locked before the wind slash; cutlass survives death/reload and never respawns.
- Wind slash at zero Spirit refused; Spirit regenerates to castable in ~3 s (no softlock); Gale slash trips the distant bridge switch; the bridge rises; a cutlass cannot trip a wind switch.
- Barrel lost below the room returns home; barrel on the plate opens the tunnel; the gate stays open on revisit.
- Boss ignores hits before the fight and is armored outside recovery; damage only while STUCK; phase 2 at half HP; defeat flag + reward once; no respawn and no duplicate reward on reload; the cage stays open; Sol recruit; flag-raise unlock; chapter completion saved **before** the departure cutscene; Continue afterwards resumes at Gullhaven with completion kept.

## Bugs found by these checks and fixed
1. Jolt `Area3D` ignored StaticBody crates, so slashes hit nothing. Enabled `areas_detect_static_bodies`.
2. A 4 m dock gap exceeded the measured single-jump range (~3.9 m). Narrowed to 3 m.
3. 6 m/s slash knockback pushed the brute out of reach between swings. Reduced to 3 m/s plus faster hurt-slide stop.
4. Godot tried to import `.blend` sources (no Blender path set), which aborted the GLB import. Added `.gdignore` to `art_source/`, `tools/`, `qa/`, `docs/`.
5. Boss deck sat 0.6 m above the gangplank, so the player could not reach the arena (blocker). Flattened.
6. Boss camera framed a fixed point, so the player was off-screen. Now frames the player–boss midpoint and zooms out to fit.
7. Hero showed the cutlass before acquiring it. Hidden until `item_cutlass`.
8. Room objectives didn't update on first visit. Now set on the first visit per room.
10. Powder Gull fired horizontally from its shelf, so it could never hit a grounded player. It now aims at the player; reflects return along the incoming line (tested).
11. Room generator passed resolved resource IDs as instance paths (broke the rigged-NPC scenes). Fixed in `tscn.py`/`build_props.py`.
9. Scene lighting overexposed (sky ambient). Switched to colour ambient, ACES tonemap, retuned.

## Screenshots reviewed (actual engine frames)
`qa/screens/*.png` (dock test) and `qa/screens/chapter/*.png`: prologue storm, harbor arrival, Bastian dialogue, cutlass, barricade, brute fight, chest, checkpoint, lookout and treasure promise, cave conch, gale slash, bridge, Powder Gull, barrel puzzle, drawbridge switch, boss idle / sweep telegraph / stuck / chain shot, pause menu, narrow aspect (720x900).

## NOT performed (with reason)
- **A human playthrough.** All play here is scripted. Feel, difficulty and first-time comprehension are unverified.
- **Human boss fight.** The bot proves the fight is winnable with the intended reads, but it reads state perfectly. Human difficulty and timing are unverified.
- **Moving-platform boarding by a human; carry/throw by hand** (puzzle logic is tested by placing the barrel).
- **Touch on a real device; gamepad disconnect; focus loss.** Code paths exist (TouchScreenButton per-finger, focus-out pause and release) but no device/gamepad was available.
- **Performance profiling on a target device.** Not measured; no claims made.
- **Old-schema migration beyond v1.** Only v1 exists; future-version rejection is tested.
- **Music.** None yet (ACE-Step blocked; see the asset manifest).
