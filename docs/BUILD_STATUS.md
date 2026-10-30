# Build status — 2026-10-30

## What runs
`tools\godot.cmd --path .` → Title → **New Game** → storm prologue (skippable) → Gullhaven harbor → cave → back via the shortcut → the Gilded Gullet boss deck → Sol joins → raise the flag → departure → **Chapter 1 complete** screen. **Continue** resumes from the last checkpoint.

| Milestone | State |
|---|---|
| **A — executable foundation** | **Complete and engine-tested.** Movement, variable/double jump, coyote and buffer, camera, cutlass combat, Bilge Brute, damage/hurt/invulnerability, hazards, checkpoint + death respawn, pause menu, save. Test room `scenes/rooms/dock_test.tscn`. |
| B — character and art integration | **Partial.** All six main characters are rigged Blender GLBs integrated in game with state-driven clips (Kito, Bilge Brute, Powder Gull, Chainhook, Bastian, Sol). Old Fisher is still a proxy. Environment kit (15 Blender modules) integrated: docks, sea walls, houses, props and the Brine Dream render as real modelled art; puzzle props and signs are still proxies; large stone ledges look stretched and too pale. Codex concept art queued (usage limit). |
| C — opening playable loop | **Code-complete and engine-tested by scripts:** prologue + skip, arrival, cutlass, barricade, first fight, chest, treasure promise, Gale Conch wind slash (boulder → switch → ranged enemy), barrel/pressure-plate puzzle, shortcut, secret treasure, checkpoints, save. Not human-playtested. |
| D — representative chapter | **Code-complete; partly verified.** Chainhook boss (sweep/shot, recovery, phase 2), Sol recruit, flag, departure, completion state are verified by flow tests; the boss fight has not been played by a human. No music. No browser export. |
| E — repair and acceptance | Not started (needs a human playthrough). |

## Proxy / temporary content
- Old Fisher NPC: primitive proxy. All other characters are rigged models.
- Rooms: kit-dressed; collision is generated boxes. Signs, gates, plates, switches, chests and the Old Fisher are proxies.
- SFX: procedural placeholder synth. Music: none.
- No dialogue portraits yet.

## Blockers
1. **Codex image generation:** ChatGPT Codex usage limit hit at 17:0x; resets 20:38. Batch is auto-queued for 20:40 (tasks 01, 04–08), then 02–03 with the 3D Kito as reference.
2. **Browser export:** templates not installed (~1 GB); free space on C: is now ~3 GB.
3. **ACE-Step music:** insufficient disk, no CUDA GPU, Python 3.10.

## Next executable step
1. Art pass on large ledges (a 2 m stone tile instead of a stretched block), darker whitewash, and modelled puzzle props.
2. Human playthrough of the full chapter (keyboard + gamepad), then tune boss timings and the gaps.
3. Review the Codex sheets → environment kit pass for the harbor (Milestone B).
4. Free disk space → install 4.7.2 export templates → Web export smoke test.
