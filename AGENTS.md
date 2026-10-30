# BARRELBORN — agent instructions (Codex and others)

Godot 4.7.2 / GDScript / Compatibility renderer 2.5D pirate platformer. Claude Code owns integration;
Codex owns bounded asset tasks handed to it via `tools/asset_tasks/*.md`.

- Identity source of truth: `docs/ART_BIBLE.md`. Keep each character's fixed details (asymmetry, colors, props).
- During an art task, write ONLY inside the task's allowed output directory. Do not edit `scripts/`, `scenes/`,
  `project.godot`, or `docs/ASSET_MANIFEST.json` (Claude updates the manifest after reviewing outputs).
- Raster art: use `$imagegen` (built-in image_gen). Copy finals from `$CODEX_HOME/generated_images` into the
  workspace. No text/logos/watermarks in images. Never claim generation succeeded if the tool failed.
- Never overwrite an existing asset; add a `-v2` suffix.
- End every task with a report: saved paths, status, prompts used, visible defects, tool limits.
- Full brief: `docs/MASTER_BRIEF.md`.
