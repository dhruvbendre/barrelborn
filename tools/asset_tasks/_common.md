# Codex asset task — BARRELBORN (Godot 2.5D pirate adventure)

Use $imagegen (the built-in image_gen tool) to create actual raster concept/reference assets for our Godot 2.5D pirate adventure. Read docs/ART_BIBLE.md first; it is the source of truth for every character's identity.

Rules for this task:
- You own art outputs only. Do NOT edit gameplay scripts, scenes, project.godot, docs/ASSET_MANIFEST.json, or any file outside the allowed output directory named below.
- Match the game's expressive anime pirate-adventure direction: bold readable silhouettes, appealing proportions, clean painted cel-shaded rendering, restrained material complexity, side-view readability. Original designs only.
- No logos, watermarks, signatures, fake UI, speech bubbles, labels, or decorative text anywhere in the image.
- Generate with the built-in image_gen tool. Do not use the CLI/API fallback and do not substitute SVG, HTML, ASCII, or a prompt-only answer.
- After generation, copy the final image(s) from $CODEX_HOME/generated_images/... into the workspace at the exact EXPECT paths below (PNG). Never overwrite an existing file; if one exists use a -v2 suffix and say so.
- Inspect each result yourself (view_image). If there is an obvious identity/anatomy failure (wrong sleeve asymmetry, extra fingers, text in image), do ONE targeted regeneration and keep the better one.
- Finish with a short completion report: actual saved paths, generation status per file, the final prompt used per file, visible defects, and any tool limitation. If image generation was unavailable, say so plainly and do not claim success.
