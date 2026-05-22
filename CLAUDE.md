# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**Twisted America: Hunger** — a 2D survival-horror RPG prototype built on **pygame** (Python 3.10+).
Setting: Beckley, West Virginia. Player is Dr. Maya Chen. ~15–20 min play length, four reachable endings.
The tone is intentionally bleak; tonal choices (no cute UI, muted palette, no jump scares) are deliberate.

## Run / test

All commands run from the `twisted_america_game/` subdirectory.

```bash
pip install pygame
python main.py        # play the game
python _smoketest.py  # headless: walks dialogue trees, combat, save/load, ending. Prints PASS lines.
```

There is no unit test framework. `_smoketest.py` is the entire test suite — it uses `SDL_VIDEODRIVER=dummy` and drives the `Game` API directly (no input simulation). After non-trivial logic changes, run it and confirm `All smoke tests passed.`

For graphics changes that the smoke test doesn't exercise (rendering, lighting, atmosphere), the standard manual check is a headless multi-zone render — set `SDL_VIDEODRIVER=dummy`, instantiate `Game`, `start_new_game()`, `begin_play()`, then iterate `g.zones`, call `g._enter_zone_effects()`, push `g.player.hunger` through 10/40/65/85/99, and `g.update(dt) + g.draw()` a few frames each. If it doesn't raise, the draw pipeline is wired correctly.

`save.json` is written next to `main.py` on F5/save. Delete it to force a fresh new-game path on next launch.

## Architecture

### State machine drives everything

`Game` in [main.py](twisted_america_game/main.py) owns one of these states at a time: `STATE_MENU`, `STATE_INTRO`, `STATE_PLAYING`, `STATE_DIALOGUE`, `STATE_COMBAT`, `STATE_INVENTORY`, `STATE_ENDING`, `STATE_GAME_OVER`. The main loop is `handle_events → update(dt) → draw()` per frame. Input dispatch (`handle_key`) and render dispatch (`draw`) both branch on `self.state`. **Always route new screens / modal flows through the state machine** — do not branch render logic inside `_draw_world`.

### Data model is shallow and direct

There is no entity-component system, no scene graph, no event bus. Game objects are plain Python classes with `rect`, `update(dt, ...)`, and `draw(surf, cam)` methods. Collision is AABB-against-obstacle-rects in `Player.update`. Cameras are hard-coded to `(0, 0)` (single-screen zones). Don't introduce abstractions to "fix" this — single-screen zones with shape-drawn primitives is the design.

### World is data, not code

`world.build_zones()` returns a `dict[str, Zone]`. Each `Zone` holds `decorations`, `obstacles`, `npcs`, `enemies`, `exits`, plus rendering metadata: `darkness_radius`, `lamps`, `particle_kind`, `fog_density`. Adding a new area means appending to that function, not subclassing anything. The same is true of dialogue: `dialogue_data.DIALOGUES` is a `dict[str, fn(game) -> tree]` registered at module bottom; each tree-builder may return different nodes based on `player.flags`.

### Rendering pipeline (in `Game._draw_world`)

Order matters — these layers are cooperative, not independent:

```
ground fill → atmosphere.draw_particles → decorations → npcs → enemies →
exits → player → foreground → atmosphere.draw_fog →
lighting.draw (darkness) → lighting.draw_lamps (additive) →
ui.draw_diegetic_edges → fx.draw_overlay (hunger effects)
```

- **`lighting.py`** punches a circular hole in a dark overlay around the player; lamps then ADD warm light back on top. Hunger above 50 tightens the hole.
- **`hunger_effects.py`** owns every effect tied to the Hunger meter (vignette, drips, whispers, heartbeat pulse, chromatic aberration edges, peripheral shadow flickers, pixel-shift bands). New hunger-driven effects belong here, gated on `hunger > threshold`.
- **`atmosphere.py`** owns drifting particles and fog. Per-zone config via `zone.particle_kind` and `zone.fog_density`. `setup_zone()` is called from `_enter_zone_effects` and short-circuits if the zone didn't change.

### Asset pipeline is graceful fallback

`assets.py` walks `twisted_america_game/assets/{sprites,decorations,overlays}/` once at boot. Missing PNGs return `None`, and every draw site falls back to its procedural silhouette/shape. **The game runs with zero assets.** Sprite keys are derived deterministically:

- Player: `maya` (`maya_0.png`, `maya_1.png`, … for animation frames)
- NPC: `npc_<slug(name)>` (lowercase, non-alphanumerics → `_`)
- Enemy: `enemy_<encounter_id>` (not enemy name — same encounter_id shares sprite)
- Decoration: `deco_<kind>` (kind is the `Decoration(...)` constructor's `kind` arg)

See [twisted_america_game/assets/MANIFEST.md](twisted_america_game/assets/MANIFEST.md) for the full list, sizes, and style notes.

### The Hunger meter is the central mechanic

It climbs passively, faster after ugly choices. It drives:
- Visual effects (in `hunger_effects.HungerFx` — thresholds at 25/50/60/75/80/90)
- Lighting (radius shrinks above 50, in `lighting.Lighting.draw`)
- Player sprite (coat / skin darken above 76, in `player.Player._draw_silhouette`)
- Combat (`parley` only available when `hunger < 50`, in `combat.Combat`)
- Endings (`hunger >= 100` triggers "Consumption" in `Game.check_endings`)

When extending hunger behavior, search for the threshold constants in `settings.py` (`HUNGER_NORMAL`, `HUNGER_UNEASE`, `HUNGER_WARPED`, `HUNGER_UNRAVEL`) and the literal numbers in `hunger_effects.py`.

### Saves are a thin JSON snapshot

`save_system.py` persists `player.{x, y, hp, hunger, corruption, inventory, key_items, flags}` and `current_zone_key`. **It does NOT persist zone state** — defeated enemies, picked-up items, and dialogue progress live in `Player.flags` and `Player.key_items` strings. When adding a new "consumed" world interaction, add a flag to `player.flags` and check it in the relevant `dialogue_data` tree or in `world.build_zones` setup — don't try to mutate-then-save the zone.

`load_game` merges flags: keys present in the save file overwrite, keys added since the save was made keep their defaults. New flags don't break old saves.

## Conventions in this codebase

- Every module does `from settings import *`. This is the project's chosen pattern — IDE warnings about wildcard imports are acknowledged and ignored. Don't change this without coordinating.
- Colors live in `settings.py` as module-level constants (`BLOOD_RED`, `COAT_BROWN`, `SNOW`, …). Add new palette entries there rather than inlining tuples.
- Drawing functions take `(surf, cam=(0, 0))` even though cam is always `(0, 0)` today. Preserve the signature.
- Sprite-or-fallback pattern: try `assets.sprite(key, frame)`, blit foot-aligned if not None, otherwise call `_draw_silhouette` / shape primitives. Follow this when adding new entity types.

## Important deliberate-bleakness notes

- No cute or cartoonish elements anywhere — sprites, UI, dialogue, narration. If a change would make the game look friendlier, that's a regression.
- No vibrant colors. Accent palette is restricted to blood red and jaundiced yellow.
- "Kindness is the cheat code" — the two reconciliation quests (Henderson↔Jared, Leah↔Jared) are the only non-pill source of Hunger relief in the prototype. Don't add other relief sources without checking with the project owner.
- Combat is intentionally light (4 actions, no positioning). Don't expand it into a tactical layer.
