# Twisted America: Hunger

A 2D survival-horror RPG prototype set in Beckley, West Virginia. You play
**Dr. Maya Chen**, a forensic psychologist sent to investigate a series of
disappearances in a town that has stopped answering its phones.

The longer you stay in Beckley, the louder the **Hunger** becomes.

> **Content warning:** addiction, body horror, violence, abuse, religious horror.
> The tone is intentionally bleak. Take breaks if you need them.

---

## Setup

Requires **Python 3.10+** and **pygame**.

```bash
pip install pygame
cd twisted_america_game
python main.py
```

That's the entire install. The prototype draws everything with shapes — no
external image, font, or audio assets are needed. A `save.json` file will be
created next to `main.py` the first time you save.

---

## Controls

| Key            | Action                                        |
| -------------- | --------------------------------------------- |
| WASD / Arrows  | Move                                          |
| E              | Interact / advance dialogue / pick choice     |
| W / S          | Move cursor in dialogue and combat menus      |
| 1 – 4          | Pick numbered dialogue choice                 |
| I              | Inventory + notebook                          |
| C              | Use Coffee (in field) — small Hunger relief   |
| P              | Use Pill (in field) — bigger relief, Corruption|
| X              | Light a cigarette — minor Hunger relief       |
| F5 / F9        | Save / Load                                   |
| ESC            | Back to menu                                  |

---

## The Hunger Meter

A second life bar. It climbs passively, faster when you make ugly choices,
slower in safe rooms.

| Range  | State          | What happens                                                |
| ------ | -------------- | ----------------------------------------------------------- |
| 0–25   | Normal         | The town looks like a town.                                 |
| 26–50  | Unease         | Vignette darkens. Edges of the world tighten.               |
| 51–75  | Warped         | Static pixels. Whispered words drift across the screen.     |
| 76–99  | Unraveling     | Blood drips from the top. Pixel-shift bands roll past.      |
| 100    | **Consumption**| You are no longer Maya. Game over.                          |

Parley in combat only works at **Hunger < 50** — past that point, words fail.

---

## Endings

There are **four** endings, all reachable on a first playthrough:

| Ending           | How to get it                                                                |
| ---------------- | ---------------------------------------------------------------------------- |
| **Consumption** | Let Hunger reach 100.                                                         |
| **Hollow Crown** | Reach Mother Ash in the woods and step forward to feed her.                   |
| **Forgiveness** | Deliver Henderson's note to Jared **and** Leah's photo to Leah, then refuse Ash. |
| **The Witness** | Turn your back on Mother Ash without reconciling the others. Sets up the next case. |

---

## Walkthrough (no spoilers for tone, just routing)

1. Start on Main Street. Talk to **Cory** in the alley — he'll hand you the **Cult Symbol** if you ask about the woods.
2. Head east to **The Hollows**. Talk to **Old Man Henderson** on his porch. He gives you the **Old Man's Note**.
3. Continue east to **The Trailer Park**. Talk to **Leah**, then go inside the blue-door trailer to face **The Dealer**.
4. Return west to Main Street, then north to **Beckley General Hospital**. Talk to **Jared** — he gives you **Leah's Photo**. (A Hollowed Patient roams the halls. Parley works while your Hunger is low.)
5. Return Henderson's note to Jared. Return Leah's photo to Leah.
6. Go south from Main Street into **The Woods**. Pass the Shadows. Find the sinkhole. Choose.

The whole arc is ~15–20 minutes on a clean run.

---

## Project Layout

```
twisted_america_game/
├── main.py            # Game loop, state machine, orchestration
├── settings.py        # Constants — palette, screen size, state names
├── player.py          # Maya — movement, stats, hunger tick
├── world.py           # Zones (Main Street, Hollows, Trailer Park, Hospital, Woods)
├── npc.py             # NPC + Enemy base classes
├── dialogue_data.py   # All dialogue trees
├── combat.py          # Turn-based Fight / Run / Item / Parley
├── ui.py              # HUD, dialogue box, menus, ending screens
├── hunger_effects.py  # Screen distortion, whispers, vignette
├── save_system.py     # JSON save / load
└── assets/            # Empty placeholder for future graphics / SFX
```

---

## Extending the game

### Add a new zone
1. Open `world.py`.
2. Inside `build_zones()`, create a new `Zone(...)` and append decorations,
   obstacles, exits and NPCs.
3. Add `Exit(...)` objects to neighbour zones pointing at your new zone key.

### Add a new NPC
1. Add a function to `dialogue_data.py` returning a dialogue tree.
2. Register it in the `DIALOGUES` dict at the bottom of that file.
3. Place an `NPC(name, x, y, color, dialogue_key)` inside whichever zone in
   `world.py` should contain them.

### Add a new ending
1. Add a flag to `Player.flags` in `player.py`.
2. Add the trigger logic to `Game.check_endings()` in `main.py`.
3. Add a title + body to the `title_map` and `body_map` in `UI.draw_ending`.

### Add real audio
`hunger_effects.py` contains the intended audio atmosphere as comments:

- Low droning wind (constant loop)
- Distant intermittent scratching
- Heartbeat that quickens as Hunger rises
- A second voice humming under everything above 75
- Whispered phrases above 90

Drop `.ogg` files into `assets/`, call `pygame.mixer.init()` from `main.py`,
and trigger them inside `HungerFx.update`.

### Add custom sprites
Every NPC, the player, and every decoration are drawn from `pygame.draw.rect`
and friends. To replace one with a sprite:

1. Add the PNG to `assets/`.
2. Load it once with `pygame.image.load(...).convert_alpha()`.
3. Replace the `draw()` method on the corresponding class with a `surf.blit`.

The data model (rects, collision, dialogue trees) does not need to change.

---

## Design notes

- **Combat is a tax, not a fantasy.** Most enemies are avoidable. Parley
  is the cheapest path out, but only while Maya is still herself.
- **Pills are the obvious answer to the Hunger meter.** They are also the
  Corruption pipeline. The Dealer ending and the Hollow Crown ending both
  feed off this trap.
- **The two reconciliation quests (Henderson ↔ Jared, Leah ↔ Jared) each
  drop Maya's Hunger meaningfully** — they are the only non-pill source of
  relief in the prototype. This is intentional: kindness is the cheat code.
- **The opening narration positions this as a prequel** to a longer story
  about pattern recognition in dying towns. The Witness ending leaves the
  door open.

---

## Known prototype limitations

- One save slot.
- No mouse input — keyboard only.
- No audio (commented stubs are in `hunger_effects.py`).
- Combat is intentionally light (4 actions, no positioning).
- Enemies do not respawn or chase between zones.

Patches welcome.
