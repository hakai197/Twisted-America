# Asset Manifest — Twisted America: Hunger

The game runs with **zero** PNGs (procedural silhouettes draw automatically).
Drop PNGs into the folders below and they replace the fallbacks one-by-one.

All PNGs must be **32-bit RGBA** with transparency.

## Style guide

- **Tone:** muted, desaturated. No saturated hues. Blood-red and jaundiced
  yellow are the only accent colors and must be sparingly applied.
- **Texture:** stained, scratched, water-damaged. Use noise overlays, slight
  vertical streaks, blotchy edges. Avoid clean vector / cell shaded looks.
- **Sprites:** distorted humanoid silhouettes — elongated necks, narrow
  shoulders, gaunt proportions. Faces are suggested, not detailed.
- **Decorations:** look abandoned. Broken windows, missing tiles, leaning
  geometry. No clean signage or fresh paint.
- **Frames:** for animated assets, draw 2–4 frames named `<key>_0.png`,
  `<key>_1.png`, etc. Frames cycle at ~5 fps. A single `<key>.png` is fine
  for static props or one-frame idle.

## Folder layout

    assets/
    ├── sprites/        characters (player, NPCs, enemies)
    ├── decorations/    world props
    └── overlays/       reserved for screen-space textures (future)

---

## sprites/ — characters

Recommended canvas: **32 × 48 RGBA**, foot-aligned (bottom row = ground
contact). The game blits foot-aligned and centered horizontally onto a
22×30 (player/NPC) or 24×30 (enemy) collision box, so anything above pixel
row 30 from the bottom appears as elongation above the rect — exactly what
you want.

| File                       | Subject              | Notes                                                     |
| -------------------------- | -------------------- | --------------------------------------------------------- |
| `maya.png`                 | Dr. Maya Chen        | Heavy coat, scarf, gaunt. 2–3 idle frames encouraged.     |
| `maya_0.png` .. `maya_3.png` | Maya idle anim (opt) | Sub-pixel sway is added in code — keep frames near-static.|
| `npc_cory.png`             | Cory                 | Hoodie, hands in pockets. Pale.                           |
| `npc_old_man_henderson.png`| Old Man Henderson    | Wool jacket, hunched, snow on shoulders.                  |
| `npc_leah.png`             | Leah                 | Thin sweater, sunken eyes.                                |
| `npc_the_dealer.png`       | The Dealer           | Long coat, taller than the rest. Half-shadowed face.      |
| `npc_jared_blake.png`      | Jared (in bed)       | Lying down — bottom-aligned. Bandages visible.            |
| `npc_mother_ash.png`       | Mother Ash           | Robed figure, head obscured, very tall. Stand-out asset.  |
| `enemy_hollowed.png`       | Hollowed Patient     | Hospital gown, broken posture, mouth open.                |
| `enemy_shadow.png`         | Shadow               | Silhouette only — no features. Edges fray to transparent. |
| `enemy_dealer.png`         | Dealer (combat)      | Same figure as `npc_the_dealer` but mid-attack pose.      |

**Sprite key derivation** (so you can preview without reading code):

- Player: `maya`
- NPC: `npc_` + lowercase name with non-alphanumerics → `_`
- Enemy: `enemy_` + the encounter_id from world.py (`hollowed`, `shadow`, `dealer`)

---

## decorations/ — world props

Each is stretched to fit the decoration rect at draw time (using
`pygame.transform.smoothscale`), so the **aspect ratio** of your PNG should
match the rect size used in world.py — listed below.

| File                  | Drawn rect (W × H)      | Notes                                                  |
| --------------------- | ----------------------- | ------------------------------------------------------ |
| `deco_tree.png`       | 26 × 38                 | Bare branches, leaning. Trunk at center-bottom.        |
| `deco_house.png`      | varies (110×80 typical) | Boarded windows, drooping roof. Asymmetric.            |
| `deco_church.png`     | 140 × 110               | Steeple included in the upper canvas. Cross.           |
| `deco_hospital.png`   | varies                  | Grid of dim windows, rusted red cross.                 |
| `deco_trailer.png`    | 84 × 36                 | Streaked siding, sagging roof, single door.            |
| `deco_headstone.png`  | varies                  | Tilted slab. Single carved letter or symbol.           |
| `deco_sinkhole.png`   | 220 × 160               | **Critical asset.** Concentric pit, near-black core.   |
| `deco_snowpile.png`   | varies (40-80 wide)     | Trampled, gray-tinged.                                 |

If a `deco_<kind>.png` is missing, the existing shape draw is used. You can
ship one decoration at a time.

---

## overlays/ — screen-space textures (reserved)

Not yet consumed by code. Filenames you can place here for future use:

- `paper.png` — full-screen weathered paper (for diegetic UI later)
- `grain.png` — 256×256 tiling noise (for stained-glass overlay)
- `fog.png` — 1024×512 soft cloud noise (for drift effect later)

---

## Testing your asset

1. Drop the PNG into the right subfolder.
2. Run `python main.py` from `twisted_america_game/`.
3. Visit the relevant zone. The sprite/decoration replaces its placeholder.
4. If nothing changes, check the filename is **lowercase**, has the right
   prefix, and the file is a valid PNG. Errors print to stdout at startup.
