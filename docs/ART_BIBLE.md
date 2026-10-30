# Art Bible — BARRELBORN (working title)

All names are **working names** and may change. Original cast; no franchise characters, logos, or fonts.

## Visual identity
- Expressive anime pirate adventure in compact 3D. Chunky readable silhouettes, big hands/feet, clear faces at gameplay scale.
- Materials: flat/painted albedo + soft toon-ish lighting. No photoreal texture noise. 1–3 materials per character.
- Shape language: heroes = round + upward triangles; villains = sharp hooks, downward wedges, heavy shoulders.
- Lines/outlines: none required (Compatibility renderer); rely on value contrast and rim light.

## Color script (opening chapter)
| Beat | Key colors | Notes |
|---|---|---|
| Prologue sea | storm blue `#1d2f4a`, slate `#3c5873`, foam `#d8eef2` | barrel is the warmest object on screen |
| Harbor | sunlit sand `#f2d49b`, terracotta roofs `#c8573a`, turquoise sea `#2fb3b8`, timber `#8a5a36` | warm key light, cool shadows |
| Cave / power room | cool teal `#1f4b55`, moss `#4f7b4a`, wind-glow cyan `#7ff3ff` | single warm torch accents |
| Boss deck | sunset orange `#ff8a3d`, bruise purple `#4a2a5a`, iron `#3a3a42` | boss telegraphs in hot orange |
| Gameplay readability | landing surfaces lighter/warmer than background; hazards red-orange; reflectable shots teal-white with ring |

## Proportions
- Hero ≈ 1.5 m tall, **4.5 heads**. Youthful: large eyes, short torso, long-ish legs, oversized hands for sword readability.
- Adults 5–6 heads. Boss ≈ 2.6 m, 6 heads, very broad shoulders.

---

## Cast

### Kito Brineheart — playable child captain
- **Role**: 14-year-old castaway who floats ashore in a barrel, declares he'll be Pirate King, ends the campaign as Pirate King.
- **Personality**: loud optimism, stubborn, impulsive, laughs at his own mistakes; inexperienced (stumbles on landing early on).
- **Shape language**: upward triangle — spiky hair rising up, coat flaring down-out. Leans forward in idle (eager).
- **Skin / hair**: warm tan-brown skin; spiky black hair with dark-teal sheen, tied into a short upward **topknot bound with a red cord**.
- **Face**: big amber eyes, thick expressive brows, small band-aid on the **bridge of his nose**. No scars under the eyes.
- **Signature costume feature**: an **oversized coral-red captain's coat** (clearly too big — hem reaches his calves), gold piping, with a hand-painted **gold sun-compass emblem on the back** (an eight-ray sun inside a ring).
- **Asymmetry (fixed)**: coat's **LEFT sleeve full length, rolled once at the cuff**; **RIGHT sleeve torn off at the elbow**, right forearm wrapped in white bandage. Sword held in the **RIGHT** hand.
- **Under-layer**: cream short-sleeve shirt, navy knee-length shorts, wide brown belt with brass buckle, sturdy brown sea boots with rolled tops.
- **Keepsake**: the **brass bung-plug of his barrel** worn on a cord around his neck (round brass disc with a cross-slot). Story: the barrel he floated in; the plug is stamped with Bastian's cooperage mark.
- **Weapon**: short **cutlass** — curved 55 cm blade, brass knuckle-bow guard, **rope-wrapped grip**, **sea-glass green pommel**.
- **Palette**: coral `#e2483d`, gold `#f2b630`, cream `#f3e7c9`, navy `#26365e`, boot brown `#6b4126`, skin `#b9794f`, hair `#15202a`.
- **Animation attitude**: snappy anticipation, overshoot on landings, wide-arc slashes, fist-pump victory.
- **Required clips**: idle, run, jump, fall, land, slash, air_slash, cast (wind slash), hurt, death, interact, victory. Later: carry_idle, carry_move, throw, double_jump.
- **Gameplay readability**: red coat vs. blue/teal backgrounds; topknot + coat flare readable at 60 px tall.

### Marisol "Sol" Quill — navigator
- **Role**: 16-year-old chartmaker kept by Chainhook's crew to plot routes; skeptical of Kito; joins after the boss.
- **Personality**: dry, observant, numbers-first, secretly romantic about the sea.
- **Shape language**: vertical rectangle — tall, narrow, straight lines; contrasts Kito's flare.
- **Look**: pale freckled skin, auburn hair in a single long braid; round **brass navigator goggles** pushed up on her forehead; teal waistcoat over a white long-sleeve blouse; dark-grey trousers tucked into tall boots; **map-tube slung across her back**; **brass compass worn on a leather wrist gauntlet (LEFT wrist)**; pencil behind the right ear.
- **Palette**: teal `#2f8f8a`, brass `#c79a3b`, white `#f5f2ea`, auburn `#9a3f22`, charcoal `#3a3d44`.
- **Poses**: idle (arms crossed, weight on one leg), talk (gesturing with pencil), departure (pointing to horizon with compass arm).

### Bastian Gull — harbor shipwright / mentor
- **Role**: old cooper-shipwright. Recognizes his own mark on Kito's barrel plug; gives him the cutlass ("it was going to rust anyway") and later the small ship.
- **Personality**: gruff, few words, teaches by handing you a job.
- **Shape language**: square/barrel — short, very wide, low center of gravity.
- **Look**: weathered ruddy skin, bald head, enormous white walrus mustache, bushy brows; leather carpenter apron with tools; **peg leg on the LEFT**; striped blue/white sailor shirt with rolled sleeves; a **big wooden mallet** on his shoulder.
- **Palette**: apron brown `#7a4a2a`, stripe blue `#3c6fb0`, white `#f0f0ea`, skin `#c98a6a`.

### Captain Varga Chainhook — first boss
- **Role**: theatrical tyrant who "taxes" the harbor and keeps Sol prisoner; fought on the deck of his ship *The Gilded Gullet*.
- **Personality**: vain showman; monologues mid-fight; furious when his hat is touched.
- **Shape language**: inverted triangle — huge shoulders, tiny waist, tall plumed hat; everything ends in hooks.
- **Look**: 2.6 m; long **plum-purple coat** with spiked gold epaulettes, tall tricorn with a white plume, gold teeth, curled black mustache; **right arm replaced by an iron winch-gauntlet** that fires a **giant anchor-hook on a chain**.
- **Attacks (gameplay-bound)**:
  1. **Hook Sweep** — telegraph: winds the chain overhead, hook glows hot orange and he plants his feet (0.8 s); sweeps a low arc across the deck. Jump it.
  2. **Chain Shot** — telegraph: aims gauntlet, a teal ring appears on the muzzle (0.6 s); fires a teal-white **reflectable** ball. Slash it back to stun him.
  3. **Recovery** — after a sweep the hook bites into the deck; he strains to pull it free (1.6 s, vulnerable, sweat drops).
  - **Phase 2 (≤50% HP)**: sweep alternates **low then high** (duck-free: high sweep is dodged by staying grounded), chain shot fires a 3-shot fan, shorter recovery.
- **Palette**: plum `#5b2a6e`, gold `#d9a531`, iron `#3a3a42`, telegraph orange `#ff7a2f`, reflect teal `#7ff3ff`.

### Enemy 1 — Bilge Brute (melee deckhand)
- Short, very wide, hunched; striped red/white shirt, sleeveless; bandana; **belaying-pin club**. Waddling approach, rhythm: slow walk → stop → **raises club high (0.5 s, flashes)** → slam → 0.7 s recovery stuck.
- Palette: red stripe `#b83a2e`, off-white, bandana olive `#6f7a3a`.

### Enemy 2 — Powder Gull (ranged gunner)
- Tall, skinny, long-legged, long navy coat, wide floppy hat with a gull feather; **long flintlock musket**. Keeps distance, hops back when approached; **aim cue**: lifts musket, a teal sight-line flickers (0.7 s); fires a teal-white reflectable shot; 1.4 s reload.
- Palette: navy `#2a3350`, hat tan `#b48a5a`, musket wood `#6b4126`.

---

## Environment kit (opening island: Gullhaven)
Worn timber docks (plank width 0.25 m), stone sea walls (warm sandstone blocks), rope posts, barrels (Bastian-mark stamped), crates (breakable variant has painted X), modest whitewashed port houses with terracotta roofs, striped awnings, sails, bunting flags, cliffs, cave modules, small sloop (Kito's first ship, *The Brine Dream*). Ladders only if implemented.

## Asset standards
- Units: meters. Gameplay plane Z = 0. Characters face +X/−X in game (model authored facing +Z, rotated by controller).
- Hero ~6k–12k tris target, ≤3 materials. Enemies ≤6k. Props ≤1.5k.
- Blender sources in `art_source/blender/`, runtime GLB in `assets/`.
- Concept/reference rasters in `art_source/concepts/`; generation records in `art_source/generation_records/`.
- No text, logos, or watermarks baked into images. UI text lives in Godot.
- Every asset is listed in `docs/ASSET_MANIFEST.json` with status: `proxy` | `generated` | `accepted` | `integrated`.
