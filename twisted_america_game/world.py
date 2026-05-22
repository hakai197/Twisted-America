"""Zones of Beckley.

Each Zone is a single-screen area with obstacles, NPCs, exits, decoration,
and ambient narration tied to entry / hunger level.

The map is 1280x720 minus a HUD strip at the bottom.
"""

import pygame
import random
from settings import *
from npc import NPC, Enemy
import assets


PLAY_W = WIDTH
PLAY_H = HEIGHT - 100  # bottom strip for HUD


class Decoration:
    """Static drawable — not interactive."""

    def __init__(self, rect, color, kind="rect", outline=None):
        self.rect = pygame.Rect(rect)
        self.color = color
        self.kind = kind  # "rect" | "tree" | "trailer" | "house" | "church" | "hospital" | "headstone" | "snowpile" | "sinkhole"
        self.outline = outline

    def draw(self, surf, cam=(0, 0)):
        r = self.rect.move(-cam[0], -cam[1])
        # Prefer a painted PNG when present. Stretches to fit the decoration rect.
        sp = assets.sprite("deco_" + self.kind)
        if sp is not None:
            if sp.get_size() != (r.w, r.h):
                sp = pygame.transform.smoothscale(sp, (r.w, r.h))
            surf.blit(sp, (r.x, r.y))
            return
        if self.kind == "tree":
            pygame.draw.rect(surf, WOOD_DARK, (r.x + r.w // 2 - 2, r.y + r.h - 12, 4, 12))
            pygame.draw.polygon(
                surf,
                self.color,
                [(r.x, r.y + r.h - 12), (r.x + r.w, r.y + r.h - 12), (r.x + r.w // 2, r.y)],
            )
        elif self.kind == "house":
            pygame.draw.rect(surf, self.color, r)
            pygame.draw.polygon(surf, ROOF, [(r.x - 4, r.y), (r.x + r.w + 4, r.y), (r.x + r.w // 2, r.y - 18)])
            # boarded windows
            for wx in (r.x + 8, r.x + r.w - 22):
                pygame.draw.rect(surf, WINDOW, (wx, r.y + 14, 14, 14))
                pygame.draw.line(surf, WOOD, (wx, r.y + 21), (wx + 14, r.y + 21), 2)
            # door
            pygame.draw.rect(surf, WOOD_DARK, (r.x + r.w // 2 - 6, r.y + r.h - 22, 12, 22))
            pygame.draw.rect(surf, BLACK, r, 1)
        elif self.kind == "church":
            pygame.draw.rect(surf, self.color, r)
            pygame.draw.polygon(surf, (28, 28, 38), [(r.x - 6, r.y), (r.x + r.w + 6, r.y), (r.x + r.w // 2, r.y - 30)])
            # cross
            pygame.draw.rect(surf, BONE, (r.x + r.w // 2 - 2, r.y - 50, 4, 22))
            pygame.draw.rect(surf, BONE, (r.x + r.w // 2 - 8, r.y - 42, 16, 4))
            # door
            pygame.draw.rect(surf, WOOD_DARK, (r.x + r.w // 2 - 10, r.y + r.h - 28, 20, 28))
            pygame.draw.rect(surf, BLACK, r, 1)
        elif self.kind == "hospital":
            pygame.draw.rect(surf, self.color, r)
            # windows
            for wy in range(r.y + 10, r.y + r.h - 16, 24):
                for wx in range(r.x + 10, r.x + r.w - 16, 24):
                    pygame.draw.rect(surf, WINDOW, (wx, wy, 14, 14))
            # red cross
            pygame.draw.rect(surf, BLOOD_RED, (r.x + r.w // 2 - 3, r.y + 4, 6, 22))
            pygame.draw.rect(surf, BLOOD_RED, (r.x + r.w // 2 - 11, r.y + 12, 22, 6))
            pygame.draw.rect(surf, BLACK, r, 1)
        elif self.kind == "trailer":
            pygame.draw.rect(surf, self.color, r)
            pygame.draw.rect(surf, ROOF, (r.x - 2, r.y - 4, r.w + 4, 6))
            for wx in (r.x + 8, r.x + r.w - 22):
                pygame.draw.rect(surf, WINDOW, (wx, r.y + 8, 14, 10))
            # door
            door_col = self.outline or WOOD_DARK
            pygame.draw.rect(surf, door_col, (r.x + r.w // 2 - 5, r.y + r.h - 20, 10, 20))
            pygame.draw.rect(surf, BLACK, r, 1)
        elif self.kind == "headstone":
            pygame.draw.rect(surf, self.color, r)
            pygame.draw.rect(surf, BLACK, r, 1)
        elif self.kind == "sinkhole":
            # dark concentric ovals
            pygame.draw.ellipse(surf, (28, 24, 30), r)
            inner = r.inflate(-r.w // 4, -r.h // 4)
            pygame.draw.ellipse(surf, (16, 12, 18), inner)
            core = inner.inflate(-inner.w // 2, -inner.h // 2)
            pygame.draw.ellipse(surf, SINKHOLE, core)
        elif self.kind == "snowpile":
            pygame.draw.ellipse(surf, self.color, r)
        else:
            pygame.draw.rect(surf, self.color, r)
            if self.outline:
                pygame.draw.rect(surf, self.outline, r, 1)


class Exit:
    def __init__(self, rect, target_zone, spawn_xy, label,
                 requires_visited=None, locked_message=None):
        self.rect = pygame.Rect(rect)
        self.target_zone = target_zone
        self.spawn_xy = spawn_xy
        self.label = label
        # List of zone keys that must be marked visited before this exit unlocks.
        self.requires_visited = list(requires_visited or [])
        self.locked_message = locked_message or "Not yet. There are still names you don't know."

    def is_locked(self, zones):
        for zk in self.requires_visited:
            z = zones.get(zk)
            if z is None or not z.visited:
                return True
        return False


class Zone:
    def __init__(self, key, name, ground_color):
        self.key = key
        self.name = name
        self.ground_color = ground_color
        self.decorations = []      # drawn under entities
        self.obstacles = []        # rects (collision)
        self.foreground = []       # drawn after entities (rare)
        self.npcs = []
        self.enemies = []
        self.exits = []
        self.entry_narration = ""  # shown once on entry
        self.visited = False
        # Lighting: None disables the darkness layer (e.g. open outdoor zones
        # in daylight). A positive int is the nominal light radius in pixels.
        self.darkness_radius = None
        # Lamps: list of (x, y, radius, (r, g, b)). Drawn additively over
        # the darkness so they brighten dim areas.
        self.lamps = []
        # Atmospheric particles + fog.
        self.particle_kind = "snow"   # "snow" | "ash" | "dust" | None
        self.fog_density = 0.0        # 0.0 .. 1.0
        # (legacy: kept so any persisted save references don't crash; unused)
        self.snow_specks = []

    def add_house(self, x, y, w=64, h=56, color=ROOF):
        self.decorations.append(Decoration((x, y, w, h), color, "house"))
        self.obstacles.append(pygame.Rect(x, y, w, h))

    def add_trailer(self, x, y, door_color=WOOD_DARK):
        self.decorations.append(Decoration((x, y, 84, 36), TRAILER, "trailer", outline=door_color))
        self.obstacles.append(pygame.Rect(x, y, 84, 36))

    def add_tree(self, x, y):
        self.decorations.append(Decoration((x, y, 26, 38), TREE, "tree"))
        self.obstacles.append(pygame.Rect(x + 10, y + 28, 6, 8))

    def add_wall(self, x, y, w, h, color=GRAY):
        self.decorations.append(Decoration((x, y, w, h), color, "rect", outline=BLACK))
        self.obstacles.append(pygame.Rect(x, y, w, h))

    def add_snowpile(self, x, y, w=40, h=14):
        self.decorations.append(Decoration((x, y, w, h), SNOW, "snowpile"))

    def draw_ground(self, surf, cam=(0, 0)):
        surf.fill(self.ground_color)
        # specks of snow / static
        for sx, sy, size, alpha in self.snow_specks:
            pygame.draw.rect(surf, SNOW, (sx, sy, 2, 2))


# ----------------------------------------------------------------------
def build_zones():
    zones = {}

    # =========================================================== MAIN STREET
    z = Zone("main_street", "Main Street", SNOW_DEEP)
    z.entry_narration = "Main Street. Beckley, West Virginia. The shops are dark. Nobody clears the snow."
    z.darkness_radius = 380
    z.particle_kind = "snow"
    z.fog_density = 0.3
    # Sodium street lamps along the road
    for lx in (160, 380, 600, 820, 1040):
        z.lamps.append((lx, PLAY_H // 2 - 80, 70, (180, 140, 70)))
    # road down the middle
    z.decorations.append(Decoration((0, PLAY_H // 2 - 60, PLAY_W, 120), ASPHALT, "rect"))
    for cx in range(40, PLAY_W, 80):
        z.decorations.append(Decoration((cx, PLAY_H // 2 - 2, 30, 4), (90, 80, 60), "rect"))
    # church on the left
    z.add_house(80, 100, 140, 110, color=CHURCH)
    z.decorations[-2 if False else -1]  # noop
    # replace last entry with church variant: rebuild
    z.decorations.pop(); z.obstacles.pop()
    z.decorations.append(Decoration((80, 100, 140, 110), CHURCH, "church"))
    z.obstacles.append(pygame.Rect(80, 100, 140, 110))
    # diner
    z.add_house(280, 110, 130, 90, color=(64, 56, 50))
    # boarded shop
    z.add_house(460, 110, 110, 90, color=(60, 52, 46))
    # alley between shops (Cory)
    z.add_house(640, 110, 80, 90, color=(54, 48, 44))
    z.add_house(740, 110, 80, 90, color=(54, 48, 44))
    # apothecary
    z.add_house(860, 110, 110, 90, color=(58, 50, 46))
    # bus stop bench
    z.decorations.append(Decoration((1020, 200, 100, 14), WOOD_DARK, "rect", outline=BLACK))
    z.obstacles.append(pygame.Rect(1020, 200, 100, 14))
    # trees south
    for tx in range(20, PLAY_W, 90):
        z.add_tree(tx, PLAY_H - 80)
    z.add_snowpile(360, PLAY_H - 120, 60, 18)
    z.add_snowpile(900, PLAY_H - 130, 50, 16)

    z.npcs.append(NPC("Cory", 700, 230, (80, 64, 60), "cory", label="Cory"))
    z.exits.append(Exit((PLAY_W - 30, PLAY_H // 2 - 30, 30, 60), "hollows", (40, PLAY_H // 2), "The Hollows >"))
    z.exits.append(Exit((0, PLAY_H // 2 - 30, 30, 60), "hospital", (PLAY_W - 60, PLAY_H // 2), "< Hospital"))
    # Chapel entrance — over the church door at (140, 182, 20, 28)
    z.exits.append(Exit((140, 182, 20, 28), "chapel",
                        (PLAY_W // 2 - 11, PLAY_H - 80), "Chapel"))
    # Sheriff's office — repurpose the diner doorway at (280, 110, 130, 90)
    z.exits.append(Exit((335, 178, 20, 22), "sheriff",
                        (PLAY_W // 2, PLAY_H - 80), "Sheriff"))
    # Highway 19 Motel — north exit off Main Street
    z.exits.append(Exit((PLAY_W // 2 - 30, 0, 60, 30), "motel",
                        (PLAY_W // 2, PLAY_H - 80), "Motel ^"))
    # Woods is gated: Maya must walk the town first.
    z.exits.append(Exit(
        (PLAY_W // 2 - 30, PLAY_H - 30, 60, 30), "woods", (PLAY_W // 2, 40), "Woods v",
        requires_visited=["hollows", "trailer_park", "hospital", "chapel",
                          "sheriff", "motel", "school", "mine"],
        locked_message="Not yet. The woods can wait. The town can't.",
    ))
    zones[z.key] = z

    # =========================================================== HOLLOWS
    z = Zone("hollows", "The Hollows", SNOW_DEEP)
    z.entry_narration = "The Hollows. Houses leaning into each other for warmth. Henderson's porch light is on."
    z.darkness_radius = 360
    z.particle_kind = "snow"
    z.fog_density = 0.4
    # Henderson's porch light — single warm lamp, the only working one
    z.lamps.append((510, 190, 75, (210, 140, 60)))
    # one cold dim lamp at the far end
    z.lamps.append((1020, 130, 45, (130, 130, 150)))
    z.decorations.append(Decoration((0, PLAY_H // 2 - 40, PLAY_W, 80), ASPHALT, "rect"))
    # row of houses
    z.add_house(100, 90, 110, 80)
    z.add_house(260, 90, 110, 80)
    # Henderson — slightly larger, lighter
    z.add_house(440, 80, 130, 100, color=(76, 56, 48))
    z.add_house(620, 90, 110, 80)
    z.add_house(780, 90, 110, 80)
    z.add_house(940, 90, 110, 80)
    # back row
    z.add_house(180, 380, 110, 80)
    z.add_house(360, 380, 110, 80)
    z.add_house(540, 380, 110, 80)
    z.add_house(720, 380, 110, 80)
    z.add_house(900, 380, 110, 80)
    # trees
    for tx in (40, 1100):
        for ty in range(40, PLAY_H - 80, 80):
            z.add_tree(tx, ty)
    # snowpile in the middle
    z.add_snowpile(580, PLAY_H - 90, 80, 16)

    # Henderson NPC — on the porch
    z.npcs.append(NPC("Old Man Henderson", 500, 200, (110, 90, 70), "henderson", label="Henderson"))

    z.exits.append(Exit((0, PLAY_H // 2 - 30, 30, 60), "main_street", (PLAY_W - 60, PLAY_H // 2), "< Main St."))
    z.exits.append(Exit((PLAY_W - 30, PLAY_H // 2 - 30, 30, 60), "trailer_park", (40, PLAY_H // 2), "Trailer Park >"))
    # Schoolhouse — north exit
    z.exits.append(Exit((PLAY_W // 2 - 30, 0, 60, 30), "school",
                        (PLAY_W // 2, PLAY_H - 80), "Schoolhouse ^"))
    zones[z.key] = z

    # =========================================================== TRAILER PARK
    z = Zone("trailer_park", "The Trailer Park", DEAD_GRASS)
    z.entry_narration = "The trailer park. Dogs that don't bark. A blue door at the north end."
    z.darkness_radius = 340
    z.particle_kind = "snow"
    z.fog_density = 0.5
    # Sickly yellow-green vapor lamps. One is over the blue-door trailer.
    z.lamps.append((442, 100, 55, (150, 170, 70)))
    z.lamps.append((200, 280, 50, (140, 150, 80)))
    z.lamps.append((900, 320, 50, (140, 150, 80)))
    z.decorations.append(Decoration((0, PLAY_H // 2 - 30, PLAY_W, 60), ASPHALT_CRK, "rect"))
    # row of trailers
    z.add_trailer(120, 110)
    z.add_trailer(260, 110)
    z.add_trailer(400, 110, door_color=(40, 80, 130))  # blue door — dealer
    z.add_trailer(540, 110)
    z.add_trailer(680, 110)
    z.add_trailer(820, 110)
    z.add_trailer(960, 110)
    # south row
    z.add_trailer(120, 400)
    z.add_trailer(260, 400)
    z.add_trailer(400, 400)
    z.add_trailer(540, 400)
    z.add_trailer(680, 400)
    z.add_trailer(820, 400)
    # Leah's trailer — paint marks
    z.decorations.append(Decoration((820, 396, 84, 4), DULL_RED, "rect"))
    # dead trees
    for tx in (40, 1180):
        for ty in range(40, PLAY_H - 80, 90):
            z.add_tree(tx, ty)
    z.add_snowpile(600, PLAY_H - 100, 60, 14)

    # Leah outside her trailer
    z.npcs.append(NPC("Leah", 840, 360, (90, 70, 84), "leah", label="Leah"))
    # Dealer is inside blue-door trailer — interact spot
    z.npcs.append(NPC("The Dealer", 432, 152, (60, 70, 90), "dealer", label="Dealer"))

    z.exits.append(Exit((0, PLAY_H // 2 - 30, 30, 60), "hollows", (PLAY_W - 60, PLAY_H // 2), "< Hollows"))
    # Coal Mine — east exit
    z.exits.append(Exit((PLAY_W - 30, PLAY_H // 2 - 30, 30, 60), "mine",
                        (40, PLAY_H // 2), "Coal Mine >"))
    zones[z.key] = z

    # =========================================================== HOSPITAL
    z = Zone("hospital", "Beckley General", DARK_GRAY)
    z.entry_narration = "The hospital lights buzz. Half are out. Jared is in 204."
    z.darkness_radius = 280
    z.particle_kind = "dust"
    z.fog_density = 0.0
    # Fluorescent ceiling fixtures. Pale, cold. Several are dead — we just
    # don't place them. The remaining ones flicker (handled per-lamp).
    for lx, ly in ((220, 130), (640, 130), (1060, 130),
                   (220, 380), (640, 380), (1060, 380)):
        z.lamps.append((lx, ly, 50, (170, 180, 200)))
    # tile floor checker
    for tx in range(0, PLAY_W, 64):
        for ty in range(0, PLAY_H, 64):
            if (tx // 64 + ty // 64) % 2 == 0:
                z.decorations.append(Decoration((tx, ty, 64, 64), (44, 44, 50), "rect"))
    # walls
    z.add_wall(0, 0, PLAY_W, 30, GRAY)
    z.add_wall(0, PLAY_H - 30, PLAY_W, 30, GRAY)
    # central reception desk
    z.add_wall(540, 240, 200, 40, (54, 48, 44))
    # patient rooms (right side)
    z.add_wall(900, 70, 30, 200, GRAY)
    z.add_wall(900, 320, 30, 270, GRAY)
    # bed in 204
    z.decorations.append(Decoration((1000, 200, 90, 40), BONE, "rect", outline=BLACK))
    z.obstacles.append(pygame.Rect(1000, 200, 90, 40))
    # IV stand
    z.decorations.append(Decoration((1100, 210, 4, 50), LIGHT_GRAY, "rect"))
    z.decorations.append(Decoration((1094, 200, 16, 12), (90, 130, 100), "rect"))

    # Jared lies in bed
    z.npcs.append(NPC("Jared Blake", 1024, 178, (80, 76, 82), "jared", label="Jared"))

    # Hollowed patient enemy roaming
    z.enemies.append(Enemy("Hollowed Patient", 360, 340, (96, 80, 80), hp=18, attack=6, can_parley=True, encounter_id="hollowed"))

    z.exits.append(Exit((PLAY_W - 30, PLAY_H // 2 - 30, 30, 60), "main_street", (40, PLAY_H // 2), "Main St. >"))
    zones[z.key] = z

    # =========================================================== CHAPEL
    z = Zone("chapel", "The Chapel", (24, 22, 26))
    z.entry_narration = "The chapel. Half the candles still burn. The Reverend has not left."
    z.darkness_radius = 220
    z.particle_kind = "dust"
    z.fog_density = 0.08

    # boundary walls
    z.add_wall(0, 0, PLAY_W, 30, (40, 36, 38))
    z.add_wall(0, PLAY_H - 30, PLAY_W, 30, (40, 36, 38))
    z.add_wall(0, 30, 30, PLAY_H - 60, (40, 36, 38))
    z.add_wall(PLAY_W - 30, 30, 30, PLAY_H - 60, (40, 36, 38))

    # altar at the north
    altar_x = PLAY_W // 2 - 60
    altar_y = 80
    z.decorations.append(Decoration((altar_x, altar_y, 120, 30), (54, 44, 36), "rect", outline=BLACK))
    z.obstacles.append(pygame.Rect(altar_x, altar_y, 120, 30))
    # cross above the altar
    z.decorations.append(Decoration((PLAY_W // 2 - 2, altar_y - 50, 4, 40), BONE, "rect"))
    z.decorations.append(Decoration((PLAY_W // 2 - 12, altar_y - 36, 24, 4), BONE, "rect"))

    # pews flanking the central aisle (6 rows, two columns)
    aisle_left = PLAY_W // 2 - 50
    aisle_right = PLAY_W // 2 + 50
    for row in range(6):
        py = 180 + row * 60
        z.decorations.append(Decoration((aisle_left - 240, py, 220, 22), WOOD, "rect", outline=WOOD_DARK))
        z.obstacles.append(pygame.Rect(aisle_left - 240, py, 220, 22))
        z.decorations.append(Decoration((aisle_right + 20, py, 220, 22), WOOD, "rect", outline=WOOD_DARK))
        z.obstacles.append(pygame.Rect(aisle_right + 20, py, 220, 22))

    # stained-glass panels — the only saturated color in the game
    for sy, col in ((140, BLOOD_RED), (300, (160, 130, 60)), (460, BLOOD_RED)):
        z.decorations.append(Decoration((4, sy, 26, 60), col, "rect", outline=BLACK))
        z.decorations.append(Decoration((PLAY_W - 30, sy, 26, 60), col, "rect", outline=BLACK))

    # The Reverend at the altar
    z.npcs.append(NPC("The Reverend", PLAY_W // 2 - 11, altar_y + 32,
                      (40, 28, 48), "reverend", label="Reverend"))

    # candles — two small warm pinpoints at the altar corners
    z.lamps.append((altar_x + 10, altar_y + 14, 26, (220, 180, 110)))
    z.lamps.append((altar_x + 110, altar_y + 14, 26, (220, 180, 110)))

    # exit at the south, back to Main Street, just below the church door
    z.exits.append(Exit((PLAY_W // 2 - 30, PLAY_H - 30, 60, 30), "main_street",
                        (140, 230), "v Main St."))
    zones[z.key] = z

    # =========================================================== SHERIFF'S OFFICE
    z = Zone("sheriff", "Sheriff's Office", (28, 26, 24))
    z.entry_narration = "Sheriff's office. Boarded glass. The chair behind the desk is overturned."
    z.particle_kind = "dust"
    z.fog_density = 0.0

    z.add_wall(0, 0, PLAY_W, 30, (44, 38, 36))
    z.add_wall(0, PLAY_H - 30, PLAY_W, 30, (44, 38, 36))
    z.add_wall(0, 30, 30, PLAY_H - 60, (44, 38, 36))
    z.add_wall(PLAY_W - 30, 30, 30, PLAY_H - 60, (44, 38, 36))

    # overturned desk + chair on the floor
    z.decorations.append(Decoration((PLAY_W // 2 - 80, 200, 160, 50), (62, 48, 36), "rect", outline=BLACK))
    z.obstacles.append(pygame.Rect(PLAY_W // 2 - 80, 200, 160, 50))
    z.decorations.append(Decoration((PLAY_W // 2 + 60, 260, 30, 14), WOOD_DARK, "rect"))

    # file cabinets along the back wall
    for cx in range(120, PLAY_W - 120, 70):
        z.decorations.append(Decoration((cx, 50, 44, 70), (60, 60, 64), "rect", outline=BLACK))
        z.obstacles.append(pygame.Rect(cx, 50, 44, 70))

    # evidence-room door — sealed in red paint, decorative
    ev_x = PLAY_W - 90
    z.decorations.append(Decoration((ev_x, 200, 50, 90), (40, 30, 24), "rect", outline=BLACK))
    z.obstacles.append(pygame.Rect(ev_x, 200, 50, 90))
    z.decorations.append(Decoration((ev_x + 10, 270, 30, 4), BLOOD_RED, "rect"))

    # Deputy Hollis's office door (west wall)
    dep_door = pygame.Rect(40, 380, 50, 90)
    z.decorations.append(Decoration(dep_door, (40, 30, 24), "rect", outline=BLACK))
    z.obstacles.append(dep_door)
    # NPC stands just east of the door (the player knocks; Hollis answers through it)
    z.npcs.append(NPC("Deputy Hollis", 100, 405, (60, 50, 50), "hollis", label="Deputy Hollis (through the door)"))

    # cold desk lamp
    z.lamps.append((PLAY_W // 2, 220, 50, (160, 170, 180)))

    z.exits.append(Exit((PLAY_W // 2 - 30, PLAY_H - 30, 60, 30), "main_street",
                        (345, 230), "v Main St."))
    zones[z.key] = z

    # =========================================================== MOTEL
    z = Zone("motel", "Highway 19 Motel", (140, 144, 152))
    z.entry_narration = "Highway 19 Motel. The vacancy sign is on. Most of the doors are open."
    z.particle_kind = "snow"
    z.fog_density = 0.4

    z.add_wall(0, 0, PLAY_W, 30, (44, 42, 44))
    z.add_wall(0, PLAY_H - 30, PLAY_W, 30, (44, 42, 44))
    z.add_wall(0, 30, 30, PLAY_H - 60, (44, 42, 44))
    z.add_wall(PLAY_W - 30, 30, 30, PLAY_H - 60, (44, 42, 44))

    # row of 7 motel rooms along the top
    for room_idx in range(7):
        rx = 80 + room_idx * 160
        z.decorations.append(Decoration((rx, 80, 140, 60), (72, 64, 56), "rect", outline=BLACK))
        z.obstacles.append(pygame.Rect(rx, 80, 140, 60))
        # door — open (void) for some, shut (wood) for others. Room 7 (index 6) is open.
        if room_idx in (1, 3, 5, 6):
            z.decorations.append(Decoration((rx + 60, 120, 20, 20), (8, 8, 10), "rect"))
        else:
            z.decorations.append(Decoration((rx + 60, 120, 20, 20), WOOD_DARK, "rect", outline=BLACK))
        # window + room-number plate
        z.decorations.append(Decoration((rx + 10, 100, 30, 20), WINDOW, "rect"))
        z.decorations.append(Decoration((rx + 100, 90, 12, 12), (180, 160, 80), "rect"))

    # vacancy sign with a buzzing yellow lamp
    z.decorations.append(Decoration((PLAY_W - 150, 200, 100, 60), (60, 50, 40), "rect", outline=BLACK))
    z.obstacles.append(pygame.Rect(PLAY_W - 150, 200, 100, 60))
    z.decorations.append(Decoration((PLAY_W - 140, 220, 80, 8), (180, 160, 80), "rect"))
    z.decorations.append(Decoration((PLAY_W - 140, 240, 80, 8), (180, 160, 80), "rect"))
    z.lamps.append((PLAY_W - 100, 230, 70, (200, 170, 60)))

    # abandoned car
    z.decorations.append(Decoration((280, 380, 120, 50), (52, 50, 48), "rect", outline=BLACK))
    z.obstacles.append(pygame.Rect(280, 380, 120, 50))
    z.decorations.append(Decoration((290, 388, 20, 14), WINDOW, "rect"))
    z.decorations.append(Decoration((370, 388, 20, 14), WINDOW, "rect"))

    # The Guest, standing in the open door of Room 7
    guest_x = 80 + 6 * 160 + 60
    z.npcs.append(NPC("Hotel Guest", guest_x, 138, (90, 60, 60), "motel_guest", label="The Guest"))

    z.exits.append(Exit((PLAY_W // 2 - 30, PLAY_H - 30, 60, 30), "main_street",
                        (PLAY_W // 2, 60), "v Main St."))
    zones[z.key] = z

    # =========================================================== SCHOOLHOUSE
    z = Zone("school", "The Schoolhouse", (40, 32, 26))
    z.entry_narration = "Schoolhouse. Empty desks. Chalk on the board: SHE IS COMING. SHE IS COMING."
    z.particle_kind = "dust"
    z.fog_density = 0.0

    z.add_wall(0, 0, PLAY_W, 30, (54, 44, 38))
    z.add_wall(0, PLAY_H - 30, PLAY_W, 30, (54, 44, 38))
    z.add_wall(0, 30, 30, PLAY_H - 60, (54, 44, 38))
    z.add_wall(PLAY_W - 30, 30, 30, PLAY_H - 60, (54, 44, 38))

    # chalkboard
    z.decorations.append(Decoration((PLAY_W // 2 - 180, 50, 360, 80), (24, 28, 28), "rect", outline=BLACK))

    # rows of small desks
    for row in range(4):
        for col in range(5):
            dx = 280 + col * 140
            dy = 200 + row * 90
            z.decorations.append(Decoration((dx, dy, 60, 30), WOOD, "rect", outline=WOOD_DARK))
            z.obstacles.append(pygame.Rect(dx, dy, 60, 30))

    # children's drawings on the side walls (the only saturated color)
    for sy, col in ((100, BLOOD_RED), (220, (160, 130, 60)), (340, BLOOD_RED), (460, (160, 130, 60))):
        z.decorations.append(Decoration((40, sy, 30, 30), col, "rect", outline=BLACK))
        z.decorations.append(Decoration((PLAY_W - 70, sy, 30, 30), col, "rect", outline=BLACK))

    # the janitor with his broom
    z.npcs.append(NPC("The Janitor", PLAY_W // 2 - 11, 480, (66, 58, 50), "janitor", label="Janitor"))

    # overhead fluorescents
    z.lamps.append((PLAY_W // 2 - 280, 60, 45, (170, 180, 200)))
    z.lamps.append((PLAY_W // 2 + 280, 60, 45, (170, 180, 200)))

    z.exits.append(Exit((PLAY_W // 2 - 30, PLAY_H - 30, 60, 30), "hollows",
                        (PLAY_W // 2, 60), "v Hollows"))
    zones[z.key] = z

    # =========================================================== COAL MINE
    z = Zone("mine", "Coal Mine Entrance", (32, 28, 24))
    z.entry_narration = "Coal mine entrance. The lift cage is gone. Wind comes out of the dark."
    z.particle_kind = "ash"
    z.fog_density = 0.5

    z.add_wall(0, 0, PLAY_W, 30, (40, 36, 32))
    z.add_wall(0, PLAY_H - 30, PLAY_W, 30, (40, 36, 32))
    z.add_wall(0, 30, 30, PLAY_H - 60, (40, 36, 32))
    z.add_wall(PLAY_W - 30, 30, 30, PLAY_H - 60, (40, 36, 32))

    # the mine mouth — black void at the north
    mouth_rect = (PLAY_W // 2 - 180, 60, 360, 140)
    z.decorations.append(Decoration(mouth_rect, (8, 6, 8), "rect", outline=BLACK))
    z.obstacles.append(pygame.Rect(mouth_rect))
    z.decorations.append(Decoration((PLAY_W // 2 - 140, 90, 280, 80), (4, 4, 6), "rect"))

    # rusted mine cart + tracks
    z.decorations.append(Decoration((280, 360, 100, 50), (66, 38, 28), "rect", outline=BLACK))
    z.obstacles.append(pygame.Rect(280, 360, 100, 50))
    for tx in range(80, PLAY_W - 80, 40):
        z.decorations.append(Decoration((tx, 415, 30, 4), (44, 38, 32), "rect"))

    # scattered boulders
    for bx, by in [(160, 240), (940, 280), (240, 480), (1000, 480), (700, 250)]:
        z.decorations.append(Decoration((bx, by, 50, 36), (42, 38, 36), "rect", outline=BLACK))
        z.obstacles.append(pygame.Rect(bx, by, 50, 36))

    # broken floodlight — pole + busted lamp head (still half-flickering)
    z.decorations.append(Decoration((PLAY_W - 240, 260, 6, 100), (60, 60, 64), "rect"))
    z.decorations.append(Decoration((PLAY_W - 256, 248, 38, 18), (60, 60, 64), "rect"))
    z.lamps.append((PLAY_W - 237, 268, 80, (180, 180, 180)))

    # The Miner — near the mine mouth, whose voice doesn't match his lips
    z.npcs.append(NPC("The Miner", 600, 230, (80, 60, 40), "miner", label="The Miner"))

    z.exits.append(Exit((0, PLAY_H // 2 - 30, 30, 60), "trailer_park",
                        (PLAY_W - 60, PLAY_H // 2), "< Trailer Park"))
    zones[z.key] = z

    # =========================================================== WOODS
    z = Zone("woods", "The Woods", (22, 28, 24))
    z.entry_narration = "The woods. Trees standing closer than they should. The sinkhole is south."
    z.darkness_radius = 240
    z.particle_kind = "ash"
    z.fog_density = 0.7
    # Distant fires through the trees. Heavy flicker, deep orange.
    z.lamps.append((140, 480, 60, (190, 70, 30)))
    z.lamps.append((1080, 420, 60, (190, 70, 30)))
    # scatter of trees forming corridors
    random.seed(7)
    for _ in range(80):
        tx = random.randint(0, PLAY_W - 30)
        ty = random.randint(0, PLAY_H - 50)
        # leave central path
        if 540 < tx < 760 and ty < PLAY_H - 220:
            continue
        z.add_tree(tx, ty)
    # sinkhole at the south
    sink_rect = (PLAY_W // 2 - 110, PLAY_H - 200, 220, 160)
    z.decorations.append(Decoration(sink_rect, SINKHOLE, "sinkhole"))
    # snow stops at the edge — outline ring
    z.foreground.append(Decoration(sink_rect, BLACK, "rect", outline=NEAR_BLACK))
    # Mother Ash is at the sinkhole rim
    z.npcs.append(NPC("Mother Ash", PLAY_W // 2 - 11, PLAY_H - 232, (44, 22, 38), "mother_ash", label="Mother Ash"))

    # Shadow enemies in the woods
    z.enemies.append(Enemy("Shadow", 220, 200, (24, 24, 30), hp=14, attack=5, can_parley=False, encounter_id="shadow"))
    z.enemies.append(Enemy("Shadow", 980, 220, (24, 24, 30), hp=14, attack=5, can_parley=False, encounter_id="shadow"))

    z.exits.append(Exit((PLAY_W // 2 - 30, 0, 60, 30), "main_street", (PLAY_W // 2, PLAY_H - 60), "^ Main St."))
    zones[z.key] = z

    return zones
