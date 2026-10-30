# Barrelborn (working title)

A 2.5D pirate action-adventure in Godot 4.7.2. A kid floats ashore in a barrel, declares he'll be Pirate King, and takes on his first island. Chapter 1 (Gullhaven) is playable from start to finish with blockout art and a real rigged hero.

## Play
```
tools\godot.cmd --path .
```
(Or open `project.godot` in Godot 4.7.2 and press F5.) **New Game** starts the prologue; **Continue** resumes from your checkpoint.

| Action | Keyboard | Gamepad |
|---|---|---|
| Move | A / D or ← / → | Left stick / D-pad |
| Jump (hold = higher, again in the air = double jump) | Space / W / ↑ / K | A |
| Slash (also throws a carried barrel; times a reflect) | J / X | X |
| Gale Slash (after the cave) | L / C | Y |
| Use / talk / lift | E / S / ↓ | B |
| Pause (skips cutscenes) | Esc / P | Start |

On a touchscreen, on-screen buttons appear automatically. Dev builds: F1–F4 jump to rooms, F5 grants the cutlass and Gale Slash.

## Check
```
tools\godot.cmd --headless --path . res://tests/test_runner.tscn    # 22 logic tests
tools\godot.cmd --headless --path . res://tests/chapter_flow.tscn   # 28 progression tests
tools\godot.cmd --headless --path . res://tests/boss_bot.tscn       # bot beats the boss with real inputs
tools\godot.cmd --path . res://tests/chapter_tour.tscn              # screenshots -> qa/screens/chapter/
```

Status, decisions, art bible, asset manifest and QA live in `docs/`. Start with `docs/BUILD_STATUS.md`.
