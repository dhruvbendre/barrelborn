BEGIN MASTER PROMPT

## 1. Your role and the outcome

You are the lead game engineer, game designer, art director, level designer, and integration owner for this project. Work as a practical small game studio. Use Codex as your asset-generation and specialist implementation collaborator when available.

BUILD THE GAME. Do not respond with only a plan, architecture diagram, asset wish list, or tutorial. Inspect the actual environment, choose reasonable defaults, create the project, implement it, generate assets with Codex where supported, run checks, and deliver a playable milestone. A short plan should lead directly into implementation.

The game is a single-player 2.5D pirate action-adventure inspired by Swordigo's responsive platforming, simple sword-and-power combat, connected exploration, hidden treasure, upgrades, and boss fights. Its setting and emotional tone draw on One Piece: adventurous islands, unusual pirates, expressive characters, crew loyalty, humor, and an enormous dream.

The story begins with a kid floating at sea inside a barrel, dreaming of becoming Pirate King. The complete campaign must eventually show the protagonist becoming Pirate King. Preserve both endpoints. The first implementation milestone is the opening island and first ship departure, not the whole campaign.

Use original characters designed by you unless existing project materials explicitly provide canonical characters. Preserve the anime pirate identity. Do not drift into a generic medieval dungeon game. Create original code, levels, music, and assets; do not extract Swordigo's proprietary content or claim franchise licensing we do not have.

Choose a provisional game title and cast names autonomously. Record them as working names that can change later. Do not ask me to name everyone, supply character pictures, or decide every costume detail.

## 2. Technology decision: implement this stack

- Engine: a supported stable Godot 4 release available in the environment. Record and pin the exact version. Avoid preview/nightly releases.
- Language: typed GDScript where practical.
- Renderer: Compatibility, selected from the beginning to keep a browser export path viable.
- Presentation: actual 3D characters, props, and environments; side-scrolling gameplay constrained to a plane.
- Character movement: CharacterBody3D, authored velocity, simple capsule collision, game-specific jump rules.
- Assets: Blender source and exported GLB/glTF for characters, rigs, animation, and reusable environment meshes.
- Runtime interface: Godot Control nodes and theme resources.
- Targets: get a desktop development build running first, then validate a browser export early. Keep mobile touch support in the input architecture from the start.
- Persistence: Godot user:// with a versioned save format and a previous-valid-save recovery strategy.
- Codex delegation: use an already available supported integration or verified local CLI workflow. Verify actual capabilities before depending on them.

Do not replace the game with a React website, a static HTML mockup, a video, a scrolling illustration, or a Three.js scene. The engine decision is already made. If Godot cannot execute here, still produce a valid Godot project and clearly distinguish generated files from engine-tested files.

Keep Godot, Blender, and Codex version differences in mind. Check current official documentation for unfamiliar APIs. Do not copy outdated flags or configure a nonexistent tool endpoint.

## 3. Inspect the environment and begin without a questionnaire

First inspect the repository, existing instructions, user changes, operating system, available commands, and connected tools. Prefer existing work over recreating it. Do not overwrite unrelated files.

Check the available Godot executable, Blender executable, Python, Git, Codex, and any existing Godot/Blender automation tools. Use platform-appropriate commands. For example, where available inspect godot --version, blender --version, codex --version, and codex exec --help. Discover alternate executable names or installation paths when necessary.

Produce a brief capability table: available, unavailable, not yet verified. Check whether Codex can actually generate images in its current runtime. The presence of an imagegen skill name alone is not proof a generation call will work.

Make normal design and implementation choices yourself. Ask only for a real dependency you cannot resolve, such as account authentication, a missing executable you cannot install within the permitted environment, or access to a service the task truly needs. Never ask me to paste secrets into a chat. Do not purchase services, incur a separate unapproved paid API workflow, or disable permission controls to get past a blocker.

When one tool is unavailable, continue independent work. A missing image tool should not prevent implementing movement and combat. A missing Blender executable should not become a reason to substitute a different game engine.

## 4. Persistent project instructions and session continuity

Create or amend a concise CLAUDE.md and a concise AGENTS.md so Claude and Codex share the project's core conventions. Preserve any existing instructions. Keep the master brief in docs/MASTER_BRIEF.md instead of copying this entire document into every always-loaded instruction file.

Maintain these working documents as implementation evolves:

- docs/BUILD_STATUS.md: what runs, what is incomplete, blockers, and the next executable step.
- docs/DECISIONS.md: engine/version, scale, controls, camera, visual identity, and meaningful changes.
- docs/ART_BIBLE.md: character identities, palette, proportions, lighting, and asset standards.
- docs/ASSET_MANIFEST.json: each asset's stable ID, source, prompt/task, path, intended use, review status, and integration status.
- docs/QA.md: actual commands/results, observed behavior, and checks not performed.
- docs/RESUME.md: short instructions to continue after a new session.

Do not claim a milestone is complete while its critical path depends on TODO functions, missing assets, a fake screenshot, or a scene that has never been imported. Distinguish code-complete, engine-tested, visually reviewed, and device-tested.

## 5. Product pillars

1. Movement must feel good before the world becomes large.
2. A small input vocabulary must support satisfying combat.
3. New abilities must unlock both combat options and exploration.
4. The child must feel like an expressive pirate character at normal gameplay scale.
5. Each island must offer an understandable local problem and a meaningful payoff.
6. The player must see progress toward a crew, a ship, and Pirate King.
7. Every mechanic should work on keyboard/gamepad and be expressible with practical touch controls.

Prioritize these over a large skill tree, many currencies, collectible character rosters, procedural worlds, or extensive dialogue.

## 6. Art direction: make concrete choices yourself

Use an expressive anime pirate adventure aesthetic in a compact 3D platformer. Favor memorable silhouettes, appealing proportions, readable faces, painted or simplified materials, strong anticipation poses, tropical color, dramatic seas, and charming architectural shapes.

Aim for roughly four to five heads in the hero's height, then verify the actual silhouette in gameplay. The child should look youthful and brave, not like an adult scaled down. Avoid a baby-like mascot, anonymous mannequin, or a head-and-limbs assembly presented as final art.

Create a specific color script for the opening: storm-blue sea, warm harbor sunlight, cool cave interior, and a dramatic boss-deck scene. Use enough contrast that the hero and landing surfaces remain readable.

Choose your own costume, hair, face, accent color, emblem, and weapon identity. Build an original recognizable combination. Avoid accidentally reproducing the exact outfit and silhouette of a famous character. The project is pirate-themed; it is not automatically tied to another organization's branding or fonts.

Create a coherent environment kit: worn timber docks, stone sea walls, rope posts, barrels, crates, modest port houses, sails, ladders only if implemented, flags, cliffs, cave modules, and a small ship. Use simple geometry intentionally, with designed proportions and materials.

Temporary primitives are fine for validating mechanics. They must remain labeled as blockout or proxy assets until replaced or polished. Attractive concept art must not be used to disguise an unpolished playable scene.

## 7. Design the cast autonomously

Design and name the following characters yourself. Decide their appearance, personality, silhouette, materials, and animation attitude, and write a compact specification for each.

### Playable child captain

Age impression approximately 13–16; energetic, stubborn, optimistic, visibly inexperienced at first. Uses a short cutlass. Include one memorable costume feature and one personal keepsake that can connect to the opening. Express the dream through posture, not just dialogue. Keep costume asymmetry clear enough to enforce in later reference views and models.

### Navigator

An original character who contrasts with the hero: practical, observant, skeptical, eventually loyal. Their costume and props should communicate navigation. They need dialogue portraits, simple idle/talk poses, and the ship-departure moment; no complex companion pathfinding is required initially.

### Harbor mentor or shipwright

A supporting character with a compact silhouette and a believable reason to help. Avoid long tutorial speeches. They should teach through a short task, an object, or a visible event.

### Chainhook Captain

The first boss: a theatrical pirate controlling the harbor. Design a readable large weapon, clear windup silhouette, and vulnerable recovery pose. Their hook/chain identity must support the actual attacks, not remain decorative.

### Two ordinary enemies

One close-range deckhand and one ranged attacker. Different silhouettes, threat cues, and movement rhythms. Reuse an appropriate humanoid rig where it genuinely helps; keep the visible behaviors distinct.

For every major character record name, story role, shape language, palette, clothing, weapon/props, personality, fixed identity details, required poses/animations, and gameplay-scale readability. Self-select a coherent direction; do not stop to request a character-design vote.

## 8. Mandatory Codex image-generation workflow

You are responsible for orchestrating Codex, not merely telling me to generate assets myself.

First determine whether an existing supported integration can delegate a workspace task to Codex. Otherwise inspect the local Codex CLI. Use its actual installed help and current official documentation. Do not assume that the old codex mcp-server command is available, or that Codex's app server can be connected as a generic MCP server.

Where the installed CLI supports it, a project-local task-file pattern is appropriate:

    codex exec --sandbox workspace-write - < tools/asset_tasks/hero_concepts.md

Run from the intended repository. Verify syntax on the installed version. Use a subprocess argument array and stdin when writing a wrapper, rather than interpolating prompts into shell commands. Keep $imagegen literal in task files. Do not use --full-auto, bypass flags, or global permission changes as an assumed setup recipe.

Give each Codex assignment explicit inputs, reference paths, allowed output paths, expected output files, quality criteria, and a completion report. Codex should not edit gameplay or project configuration during an image-only task. Serialize edits to shared files; avoid Claude and Codex modifying the same asset or manifest simultaneously.

For raster tasks, explicitly ask Codex to use its available image-generation capability and the $imagegen skill. Ask for real generated files saved into the project. Do not accept an image prompt, a filename claim, a Markdown image tag, an SVG substitute, or ASCII art as proof that raster generation happened.

Prefer available built-in image generation. Do not assume every Codex surface or account exposes it. If it is unavailable, capture the specific capability failure, prepare exact reusable task files, and continue the game with clearly labeled proxies. A separately billed API route requires appropriate existing authorization and credentials. Do not silently switch to it.

### Initial generation batch

Keep the initial batch bounded: around eight generation jobs, not the full campaign. Exact image counts may vary with the exposed tool.

1. One comparable concept sheet showing three candidate child-captain designs.
2. One consistent front/side/back reference sheet for the direction you select.
3. One hero expression sheet: determined, cheerful, curious, hurt, surprised, victorious.
4. One compact supporting-cast concept sheet for the navigator and mentor.
5. One boss concept/reference sheet with attack anticipation and recovery poses.
6. One ordinary-enemy sheet containing the melee and ranged archetypes.
7. One side-view harbor environment keyframe, composed for real platformer gameplay.
8. One ship-and-barrel prop sheet, with consistent scale and materials.

Treat these as a starting scope, not eight mandatory calls when one already available asset can be reused. Make a bounded correction pass for obvious identity or anatomy failures; do not iterate indefinitely or generate unnecessary variants.

### Identity and output rules

After selecting the hero, reuse that selected image as a reference for later views when the tool supports reference input. Keep skin tone, hair, costume, emblem, proportions, weapon, and left/right asymmetry stable. A requested turnaround is not automatically geometrically consistent; inspect and correct mismatches.

Use a plain neutral background for modeling references. Use actual transparent-background generation only for assets that need cutouts, and validate alpha; do not assume transparency from a checkerboard-looking image. If the tool does not support the requested output mode, record it and follow its documented workflow.

Generate no important UI copy or dialogue as pixels. Keep titles, labels, subtitles, and numbers editable in Godot.

Save source prompts and generation records. Confirm files exist and can be decoded. Inspect them visually before accepting them. Record rejected outputs separately from accepted references, and record exactly which files are integrated into the game.

### Codex image task template you must expand

"Use $imagegen to create actual raster concept/reference assets for our Godot 2.5D pirate adventure. Read docs/ART_BIBLE.md and the supplied character brief. You own art outputs only for this task. Preserve the selected identity and references. Produce [specified asset], composed for [modeling reference / portrait / environment reference]. Match the game's expressive anime pirate direction, restrained material complexity, and side-view readability. Keep [fixed identity details]. Use [background requirement]. No logos, watermarks, fake UI, or decorative text. Save actual generated image files to [allowed output directory]. Inspect the result and return actual paths, generation status, visible defects, and any tool limitation. Do not claim image generation succeeded if the tool was unavailable. Do not edit gameplay scripts."

## 9. Turn references into real game characters

Generated character pictures are not rigged 3D characters. Do not rename a PNG to GLB, put a portrait on a cube, or present a billboard as the finished playable hero.

Use Blender, either through an available automation tool or reproducible Blender Python scripts. Codex can implement a bounded Blender asset-generation script while you own integration. Scripts should be repeatable, use predictable object and bone names, avoid editing unrelated source files, and export to specified paths.

Build the strongest character model the environment can support: intentional silhouette, modeled face and hair shapes, coherent costume, separate cutlass, manageable materials, and a skeleton with deforming geometry. Apply correct scale/transforms and validate orientation. An initial practical target is approximately 6k–12k triangles for the hero, with a small material count; tune based on actual appearance and device profiling rather than treating this as a certification.

Create a real armature, bind the mesh, define a weapon attachment, and animate with readable key poses. Start with in-place animation. Keep controller movement authoritative, including lunges and knockback.

Do not wrap an unrelated generated portrait across a face mesh and call it a matched texture. Build textures and UVs for the actual geometry. If a dedicated image-to-3D service is already available and authorized, evaluate its output for topology, rigging, scale, and animation suitability before using it; do not invent access to one.

Initially implement idle, run, jump, fall, land, slash, air slash, cast, hurt, death, interact, and victory. Add carry-idle, carry-move, throw, and double-jump presentation as those interactions are integrated. Reuse clips only where the result remains convincing.

Store Blender sources outside runtime assets and export runtime GLBs. Import into Godot and inspect at gameplay scale. Verify mesh deformation, weapon grip, foot contact, facing direction, materials, and animation names. If the best available model remains a proxy, call it a proxy and keep the replacement path clean. Do not claim commercial character quality without a visual review.

## 10. Opening chapter: specific playable sequence

Target approximately 10–15 minutes for a first playthrough once the representative chapter is complete. Build this over milestones; do not fabricate completion in one session.

### Prologue: barrel at sea

Create an in-engine stormy ocean opening with a floating barrel. Use inexpensive stylized water, foam, bobbing, clouds, and a controlled camera. The kid's ambition should be established in one or two short lines. Show the character inside or emerging from the barrel in a readable way. Reach player control quickly. Make the opening skippable; skipping must grant the same story state and safe starting location.

### Harbor arrival

The barrel reaches a small harbor. The player learns moving, short/high jumping, and interacting in a safe section. The port should immediately look inhabited through architecture, flags, ropes, and one or two ambient characters or animations.

### First weapon and fight

Acquire the cutlass, break a crate, fight one melee deckhand, receive a modest reward, and see a clear next objective. Use sound, reaction animation, a restrained slash trail, and brief impact feedback.

### Exploration promise

Show an optional treasure route the player cannot yet open. Make the reason legible: a distant mechanism accessible with the upcoming wind slash. Keep the main route obvious.

### Wind-slash acquisition

Award the ranged power through a compact narrative event. Teach it first against a stationary target, then a distant switch, then a ranged enemy. Teach each use clearly instead of introducing all challenges simultaneously.

### Shortcut and optional return

Open a shortcut back toward the visible treasure. The player should understand that a new ability changes earlier space. Include a simple carry/place or pressure-switch puzzle with a reset path.

### Chainhook Captain

Enter a short boss encounter on a ship deck or harbor platform. Use a checkpoint immediately before it. Telegraph a hook sweep and a marked projectile attack. Include a readable recovery window. A second phase should alter a known pattern, not introduce unreadable chaos. Make one tool relevant without requiring a scarce consumable.

### First flag and departure

After victory, free or recruit the navigator, raise the protagonist's first flag, obtain the small ship, and show a short departure. Save the completed chapter. A post-victory reload must not respawn the defeated boss or replay rewards incorrectly. End with a real chapter-complete state and a clear next destination, not a fake button promising an unbuilt island.

Use roughly 6–8 compact rooms/scenes: arrival dock, town, cliff/warehouse approach, power room, puzzle/shortcut area, optional treasure pocket, boss deck, and departure space. Combine small spaces where it improves pacing and production effort.

## 11. Complete-campaign direction, without scope creep

Keep a campaign outline for five or six island chapters: first ship; broken lighthouse and grapple; blockade and reputation; hidden reef and discovery power; capture/crew rescue; final passage and Pirate King ending.

The ship begins as a safe hub and destination selector. Later upgrades can change its appearance. Crew begin as story/hub characters and occasional authored assistance. Reputation changes wanted posters and NPC reactions. Do not implement a seamless ocean, naval simulation, multiplayer, playable crew roster, complex crafting, random loot treadmill, or procedural main campaign in the opening milestone.

The final story must eventually pay off the legendary route/treasure, major antagonist, crew journey, and Pirate King recognition. Keep the original barrel in the captain's cabin in the ending. Do not build the final cutscene before the first chapter's core loop works.

## 12. Movement and camera specification

Use world X for horizontal movement, Y for height, and a fixed Z gameplay plane. Decorative scenery can occupy other depths. Enforce the plane on player, enemies, projectiles, and interactions where relevant; do not let physical contact gradually push actors out of the lane.

Use a stable side camera with enough perspective for visible 3D depth. Start with restrained perspective and inspect landing clarity. Use horizontal look-ahead, a dead zone, bounded vertical tracking, room limits, and boss framing. Avoid free orbit, constant zooming, excessive camera lag, and tracking every tiny jump motion.

Use a 60 Hz physics update initially. Rendering may vary without changing game speed. Keep input, physics, animation timing, and pause behavior coherent. Expose tuning through resources/inspector settings rather than scattered magic numbers.

Initial tuning targets, to be tested rather than represented as Swordigo measurements:

- Run speed approximately 5.5 m/s with a roughly 1.5 m hero; adjust to scene scale.
- First jump height approximately 2.4 m and time to apex approximately 0.4 s; derive gravity and launch velocity consistently.
- Variable jump height by release handling; a second jump available early.
- Coyote time about 0.10 s and input buffering about 0.12 s.
- Controlled air steering, prompt braking, reliable slope handling, and moving-platform support.
- Detect ceiling contact; avoid corner snagging and uncontrolled wall climbing.

Test the controller before committing level gaps. Support movement and attack in air, with explicit action-cancellation and facing rules. Do not let a purely visual animation event unexpectedly change collision or physics ownership.

## 13. Combat, enemies, and interactions

Implement a simple satisfying cutlass strike first. Give attacks startup, an active interval, recovery, damage, knockback, and target filtering. Use a unique swing ID to prevent one swing damaging the same target every physics frame. Use swept tests or suitable sampling for fast moving weapons and projectiles.

Ground and air attacks need clear poses. Add a combo only if it improves play without undermining the compact control scheme. Do not make a large combo tree a dependency for the opening.

Wind slash consumes Spirit but Spirit recovers or is readily refillable. Gates must not softlock when the meter is empty. Mark reflectable projectiles visually; make reflection timing understandable. Differentiate damage, blocking, reflection, and invulnerability feedback.

Use restrained hit pause, enemy flinch, hit particles, audio, and optional shake. Initial hit pause around 0.05 s and hurt invulnerability around 0.8 s are starting points. Ensure timers behave correctly while paused and time scaling does not corrupt cooldowns.

Enemy states: idle/patrol, detect, approach or aim, telegraph, attack, recover, hurt, dead. Keep detection and attacks constrained by walls, distance, and platform edges unless intentionally authored otherwise.

Melee deckhand: approach, clear windup, short strike, recovery. Ranged enemy: aim cue, marked projectile, reposition or cooldown. Boss: two readable patterns, recovery, meaningful second-phase change, reliable defeat transition.

Interactions: cutlass pickup, breakable crates/barrels, carry/place/throw where implemented, chest, switch, pressure plate, checkpoint, NPC dialogue, room exits, and departure interaction. Every puzzle object needs predictable reset/recovery behavior.

## 14. Architecture and content organization

Use Godot scenes, signals, resources, and composition. Avoid an unnecessary custom framework, huge singleton, or general-purpose ECS project. Keep the first milestone small while preserving sensible boundaries.

Suggested organization; adapt to the repository if existing conventions are better:

- scenes/player/, enemies/, bosses/, interactables/, rooms/, cinematics/, ui/
- scripts/player/, combat/, ai/, world/, progression/, save/, ui/
- resources/tuning/, characters/, attacks/, abilities/, encounters/
- assets/characters/, environments/, props/, textures/, portraits/, ui/, audio/
- art_source/concepts/, blender/, generation_records/
- tools/asset_tasks/, blender/, validation/
- tests/ and docs/

Separate locomotion from action state so jumping, attacking, and being hurt do not create one giant combinatorial state machine. Use dedicated damage/hit interfaces, enemy configurations, room spawn IDs, and stable reward IDs.

Keep managers focused: overall state, room transitions, story/progression, saving, and audio as needed. UI should listen to state changes rather than scan the scene tree every frame. Use explicit node references or exports and verify scene paths after edits.

Prefer reusable authored rooms and configured enemy scenes. Load only needed content and unload old scenes cleanly. Prevent projectiles, signals, or stale references from surviving room changes unintentionally.

## 15. Progression and saving

Implement health, Spirit, XP, coins, equipment/ability unlocks, opened treasure, completed quests, boss state, checkpoint, and recruited navigator as needed for the slice. Keep story reputation distinct from spendable money. Use clear progression feedback and meaningful rewards rather than a large inventory.

Save data must include a schema version and stable content IDs. Use safe writes and a previous valid save where supported. Verify persistence on the actual target; browser user:// storage has platform-specific behavior. Saving in a scene script alone is not proof persistence works.

Make reward events idempotent. Permanent story rewards should remain granted after death. A boss reward, acquired power, and recruited crew member must not duplicate on reload. Do not save a temporary impossible position during a cutscene and then reload into water.

Provide New Game, Continue when valid, pause, restart from checkpoint, and a clear recovery for missing/corrupt data. Keep destructive reset separate from Continue. Include debug reset and jump-to-room options in development builds.

## 16. Controls, HUD, and audio

Create action mappings for move left/right, jump, attack, power, interact, pause, and any power selection that is actually implemented. Provide keyboard and gamepad support first, then touch via the same actions.

Touch must support simultaneous movement, jump, and attack. Track touch IDs independently; releasing one button must not release every action. Handle canceled pointers, window focus loss, and pause without stuck movement. Allow practical control sizing and safe-area layout.

Keep HUD concise: health, Spirit, selected power, contextual interaction, and brief objective feedback. Put detailed XP/equipment/quest information in menus where needed. Use readable typography, adequate contrast, scalable controls, non-color-only attack cues, separate music/effects levels, subtitle sizing, and reduced/off shake.

Audio should include footsteps, jump/land, sword swing/contact, damage, power, reflection, pickup, chest, UI, ocean, and a small musical set. Use original or appropriately licensed sources and record provenance. If authored audio is not available, use honest temporary sound effects rather than copyrighted soundtrack extraction. Browser audio should start after the intended user gesture.

## 17. Performance and browser export

Profile actual content; do not promise mobile performance from triangle counts alone. Start with simple materials, few active lights, limited shadow casters, pooled projectiles/effects, bounded particles, sensible textures, and reusable environment meshes.

Aim for 60 fps on the chosen midrange device with a stable lower-quality/30 fps fallback where appropriate. Keep gameplay speed consistent across refresh rates. Pick and record actual test devices; never invent device test results.

Export a tiny browser build early to check loading, rendering, audio, input, and save behavior. Start with a single-threaded Godot web export. Keep Compatibility-compatible materials and effects; avoid accidentally introducing a feature that only works in another renderer.

Measure the real initial payload, startup time, memory, room transition cost, and sustained combat behavior. Do not download the full campaign at boot. A PWA is optional later, not proof that the game works offline. Configure hosting and MIME/compression correctly; keep names of exported runtime files coherent.

Prepare local run/export instructions and a browser test build if supported. Do not publicly deploy or buy hosting unless separately authorized.

## 18. Implementation milestones and session behavior

Work in small runnable increments. Keep the project parseable and inspectable after each substantial change. Documentation supports execution; it must not consume the session while the game remains empty.

### Milestone A: executable foundation

Create/import the Godot project, input actions, player controller, camera, a real test room, hazards/respawn, and one enemy/damage loop. Establish Codex asset delegation and start the hero concepts. Deliver a scene where the player can move, jump, attack, be hurt, and restart. This is the minimum useful first coding-session result if later work cannot fit.

### Milestone B: character and art integration

Finish selected references, model/rig, core clips, hero import, environment kit, and one attractive harbor room. Replace or clearly label proxies. Test gameplay at the final camera scale.

### Milestone C: opening playable loop

Implement the barrel prologue, arrival, cutlass pickup, wind slash, simple puzzle, secret, checkpoint, and basic saving. Ensure cutscene skipping and revisiting rooms work.

### Milestone D: representative chapter

Add the boss, navigator recruitment, departure, completion state, readable UI, sound, and a stable browser export. Refine pacing and first-time comprehension.

### Milestone E: repair and acceptance

Play through the chapter, repair issues, repeat the critical path after repairs, check persistence and input edge cases, review screenshots, and report actual results. Do not expand into later islands until this chapter passes.

Continue autonomously through milestones while the environment and session permit. Do not stop after planning to ask whether to start coding. If a session limit interrupts work, leave the largest coherent runnable milestone, update the status/resume documents, and state exactly where implementation stopped. Do not pretend later milestones are complete.

## 19. Validation requirements

Use the actual Godot binary for import/parse checks and scene smoke tests. Verify the installed version's command syntax. Headless checks can establish importing and logic; they do not establish visual quality or physical touch usability.

Add focused deterministic checks for important logic: one hit per target per swing, jump buffering and reset rules, reward idempotency, save recovery, and progression gates. Prefer small useful tests over a large test framework. Use separate test-save locations so tests do not erase a player's real progress.

Exercise these cases:

- New Game, Continue, death/retry, and checkpoint reload.
- Prologue watched versus skipped produces equivalent starting progress.
- Short jump, full jump, double jump, platform edges, ceiling contact.
- Moving-platform boarding, riding, and jumping off.
- Attack while airborne, repeated attack input, reflection, hurt protection.
- Wind slash at zero Spirit and mandatory-puzzle recovery.
- Carry/throw puzzle object lost or dropped in an awkward location.
- Room re-entry, treasure already opened, boss already defeated.
- Power pickup immediately followed by death or restart.
- Post-boss cutscene skipped or interrupted; rewards and departure state remain correct.
- Touch multi-input, canceled touches, gamepad disconnect, focus loss.
- Browser refresh, storage failure, and old save schema handling.

For visual QA capture actual game screenshots of the harbor, hero close view, normal gameplay, attack contact, power, boss, pause/HUD, and narrow aspect ratio where supported. Inspect them; fix unreadable silhouettes, excessive dark areas, clipping, wrong scale, broken material imports, and obscured platforms. Do not supply generated concept images as gameplay screenshots.

Track tests as passed, failed, or not performed, with reasons. If no display/browser/device is available, mark those tests unperformed and provide the exact follow-up steps. Never invent performance, playtest, generation, or export success.

## 20. Definition of done and your immediate instruction

The representative chapter is complete only when a player can start at the barrel, reach the harbor, move and fight, obtain and use the wind slash, solve the simple puzzle, optionally discover the secret, beat the boss, recruit the navigator, depart on the ship, and resume saved progress.

It also requires actual character/art integration or explicit proxy labels, readable feedback, working controls, no known progression blocker, real engine import checks, a concise run guide, and an honest QA record. A beautiful reference sheet alone is not a completed game milestone.

At the end of each substantial working session report briefly:

1. What is playable now and how to run it.
2. Which milestone is actually complete.
3. Which real assets Codex generated and which are integrated.
4. Which models/animations exist and which remain proxies.
5. Actual checks performed and unresolved failures.
6. The next concrete implementation step.

START NOW. Inspect the workspace and tools, establish the chosen Godot project, write the short persistent instructions, prepare the first bounded Codex character-generation task, and implement Milestone A. Continue toward the representative chapter without waiting for routine design approvals. Make deliberate creative decisions and show progress through actual working files and verified behavior.

END MASTER PROMPT
