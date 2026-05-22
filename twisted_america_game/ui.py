"""HUD, dialogue box, menus, ending screens."""

import math
import random
import pygame
import textwrap
from settings import *


def draw_text(surf, font, text, x, y, color=TEXT, max_w=None, line_spacing=2):
    if max_w is None:
        s = font.render(text, True, color)
        surf.blit(s, (x, y))
        return s.get_height()
    # word-wrap
    words = text.split(" ")
    line = ""
    h = 0
    line_h = font.get_linesize() + line_spacing
    for w in words:
        test = (line + " " + w).strip()
        if font.size(test)[0] <= max_w:
            line = test
        else:
            surf.blit(font.render(line, True, color), (x, y + h))
            h += line_h
            line = w
    if line:
        surf.blit(font.render(line, True, color), (x, y + h))
        h += line_h
    return h


def wrap_with_newlines(text):
    """Yield lines, preserving explicit newlines."""
    for raw in text.split("\n"):
        yield raw


class UI:
    def __init__(self):
        self.font = pygame.font.SysFont("consolas", 16)
        self.font_sm = pygame.font.SysFont("consolas", 14)
        self.font_md = pygame.font.SysFont("consolas", 20)
        self.font_big = pygame.font.SysFont("consolas", 32, bold=True)
        self.font_title = pygame.font.SysFont("consolas", 56, bold=True)
        # Diegetic indicator state — drifts the marks slightly per second.
        self._diegetic_t = 0.0

    # -------------------------------------------------- DIEGETIC CARVED EDGES
    def draw_diegetic_edges(self, surf, player, dt=0.016):
        """Carved HP tally on the left, blood streak on the right.

        Drawn on the play area edges, always visible, between the darkness
        layer and the hunger FX layer.
        """
        self._diegetic_t += dt
        play_h = HEIGHT - 100

        # --- Left edge: HP tally ---
        # Faint backing strip
        strip = pygame.Surface((10, play_h), pygame.SRCALPHA)
        strip.fill((0, 0, 0, 90))
        surf.blit(strip, (0, 0))

        n_marks = 14
        cy_start = 60
        cy_step = (play_h - 120) / max(1, n_marks - 1)
        hp_pct = player.hp / player.max_hp
        lit_count = int(round(hp_pct * n_marks))
        # Marks fill from the bottom up — more lit marks = healthier.
        for i in range(n_marks):
            mark_y = int(cy_start + i * cy_step)
            is_lit = (n_marks - 1 - i) < lit_count
            col = BONE if is_lit else (38, 36, 36)
            wobble = int(math.sin(self._diegetic_t * 1.1 + i * 0.7) * 1.5)
            # ragged scratch — varying length, slight angle
            length = 9 + (i * 13) % 5 + wobble
            pygame.draw.line(surf, col, (2, mark_y), (2 + length, mark_y + (i % 2)), 1)
            if is_lit and i % 4 == 0:
                # cross-tick on every fourth healthy mark
                pygame.draw.line(surf, col, (4, mark_y - 2), (4, mark_y + 2), 1)

        # --- Right edge: Hunger blood streak ---
        streak_x = WIDTH - 10
        backing = pygame.Surface((10, play_h), pygame.SRCALPHA)
        backing.fill((0, 0, 0, 90))
        surf.blit(backing, (WIDTH - 10, 0))

        h_pct = player.hunger / player.max_hunger
        col_top = 30
        col_bottom = play_h - 30
        col_h = col_bottom - col_top
        fill_h = int(h_pct * col_h)
        fill_top = col_bottom - fill_h
        # base dark channel
        pygame.draw.rect(surf, (28, 8, 10), (streak_x + 2, col_top, 6, col_h))
        # blood column
        if fill_h > 0:
            pygame.draw.rect(surf, BLOOD_RED, (streak_x + 2, fill_top, 6, fill_h))
            # uneven dripping tendrils at the top of the fill
            random.seed(int(self._diegetic_t * 0.5) + int(player.hunger))
            for _ in range(min(4, fill_h // 18)):
                dx = random.choice((-1, 1, 1))
                drip_h = random.randint(3, 10)
                pygame.draw.rect(surf, BLOOD_RED, (streak_x + 2 + dx, fill_top + random.randint(0, 4), 2, drip_h))
            random.seed()

        # --- Corruption: short carved nicks near the center of the left strip ---
        if player.corruption > 0:
            corruption_pct = player.corruption / 100.0
            nicks = int(corruption_pct * 6)
            cy = HEIGHT // 2 - 100
            for i in range(nicks):
                ny = cy + i * 8
                pygame.draw.line(surf, CORRUPT_BAR, (1, ny), (5, ny + 2), 1)

    # ---------------------------------------------------------------- HUD
    def draw_hud(self, surf, game):
        # bottom strip
        strip_h = 100
        pygame.draw.rect(surf, NEAR_BLACK, (0, HEIGHT - strip_h, WIDTH, strip_h))
        pygame.draw.line(surf, BLACK, (0, HEIGHT - strip_h), (WIDTH, HEIGHT - strip_h), 2)

        p = game.player
        # Hunger bar
        bar_x, bar_y = 24, HEIGHT - strip_h + 16
        bar_w, bar_h = 360, 20
        pygame.draw.rect(surf, HUNGER_BG, (bar_x, bar_y, bar_w, bar_h))
        fill = int(bar_w * (p.hunger / p.max_hunger))
        # color shifts as it climbs
        col = (140 + min(80, p.hunger), 30, 30)
        pygame.draw.rect(surf, col, (bar_x, bar_y, fill, bar_h))
        pygame.draw.rect(surf, BLACK, (bar_x, bar_y, bar_w, bar_h), 1)
        surf.blit(self.font_sm.render(f"HUNGER {p.hunger}/100", True, TEXT), (bar_x + 6, bar_y + 3))

        # HP bar
        hp_y = bar_y + 30
        pygame.draw.rect(surf, HP_BG, (bar_x, hp_y, bar_w, bar_h))
        hp_fill = int(bar_w * (p.hp / p.max_hp))
        pygame.draw.rect(surf, HP_BAR, (bar_x, hp_y, hp_fill, bar_h))
        pygame.draw.rect(surf, BLACK, (bar_x, hp_y, bar_w, bar_h), 1)
        surf.blit(self.font_sm.render(f"HP {p.hp}/{p.max_hp}", True, TEXT), (bar_x + 6, hp_y + 3))

        # Corruption bar
        co_y = hp_y + 24
        co_w = 200
        pygame.draw.rect(surf, (24, 14, 30), (bar_x, co_y, co_w, 8))
        co_fill = int(co_w * (p.corruption / 100))
        pygame.draw.rect(surf, CORRUPT_BAR, (bar_x, co_y, co_fill, 8))
        surf.blit(self.font_sm.render(f"corruption {p.corruption}", True, TEXT_DIM), (bar_x + co_w + 8, co_y - 4))

        # Inventory glance
        inv_x = 460
        surf.blit(self.font_sm.render("ITEMS", True, TEXT_DIM), (inv_x, bar_y - 2))
        ix = inv_x
        iy = bar_y + 14
        for name, count in p.inventory.items():
            line = f"{name} x{count}"
            surf.blit(self.font_sm.render(line, True, TEXT), (ix, iy))
            iy += 16
        # key items
        if p.key_items:
            kx = 640
            surf.blit(self.font_sm.render("KEY", True, TEXT_DIM), (kx, bar_y - 2))
            ky = bar_y + 14
            for k in sorted(p.key_items):
                surf.blit(self.font_sm.render(k, True, TEXT_WARN), (kx, ky))
                ky += 16

        # Zone label + controls
        right_x = WIDTH - 280
        surf.blit(self.font_md.render(game.zone.name.upper(), True, TEXT), (right_x, bar_y - 4))
        ctrl_lines = [
            "WASD move    E interact",
            "I inventory  ESC menu",
            "F5 save      F9 load",
        ]
        cy = bar_y + 22
        for ln in ctrl_lines:
            surf.blit(self.font_sm.render(ln, True, TEXT_DIM), (right_x, cy))
            cy += 16

    # ---------------------------------------------------------------- INTERACT PROMPT
    def draw_interact_prompt(self, surf, label):
        text = f"E — {label}"
        s = self.font.render(text, True, TEXT)
        pad = 8
        box = pygame.Rect(0, 0, s.get_width() + pad * 2, s.get_height() + pad)
        box.midbottom = (WIDTH // 2, HEIGHT - 110)
        bg = pygame.Surface((box.w, box.h), pygame.SRCALPHA)
        bg.fill((10, 10, 14, 200))
        surf.blit(bg, box.topleft)
        pygame.draw.rect(surf, BLACK, box, 1)
        surf.blit(s, (box.x + pad, box.y + pad // 2))

    # ---------------------------------------------------------------- NOTIFICATION
    def draw_notification(self, surf, text):
        s = self.font.render(text, True, TEXT_WARN)
        pad = 10
        box = pygame.Rect(0, 0, s.get_width() + pad * 2, s.get_height() + pad)
        box.midtop = (WIDTH // 2, 30)
        bg = pygame.Surface((box.w, box.h), pygame.SRCALPHA)
        bg.fill((10, 10, 14, 220))
        surf.blit(bg, box.topleft)
        pygame.draw.rect(surf, TEXT_WARN, box, 1)
        surf.blit(s, (box.x + pad, box.y + pad // 2))

    # ---------------------------------------------------------------- ENTRY NARRATION
    def draw_entry_narration(self, surf, text):
        # centered italic-ish narration
        pad = 14
        max_w = WIDTH - 200
        lines = self._wrap(self.font_md, text, max_w)
        line_h = self.font_md.get_linesize() + 4
        h = pad * 2 + line_h * len(lines)
        w = min(max_w + pad * 2, WIDTH - 40)
        box = pygame.Rect(0, 0, w, h)
        box.midtop = (WIDTH // 2, 80)
        bg = pygame.Surface((box.w, box.h), pygame.SRCALPHA)
        bg.fill((6, 6, 10, 200))
        surf.blit(bg, box.topleft)
        pygame.draw.rect(surf, NEAR_BLACK, box, 1)
        y = box.y + pad
        for ln in lines:
            s = self.font_md.render(ln, True, TEXT)
            surf.blit(s, (box.centerx - s.get_width() // 2, y))
            y += line_h

    # ---------------------------------------------------------------- DIALOGUE
    def draw_dialogue(self, surf, dialogue):
        # box at bottom of play area
        box_h = 220
        box = pygame.Rect(40, HEIGHT - 100 - box_h - 16, WIDTH - 80, box_h)
        bg = pygame.Surface((box.w, box.h), pygame.SRCALPHA)
        bg.fill((6, 6, 10, 230))
        surf.blit(bg, box.topleft)
        pygame.draw.rect(surf, GRAY, box, 1)

        node = dialogue.current_node()
        if not node:
            return

        speaker = node.get("speaker", "")
        text = node.get("text", "")

        ty = box.y + 14
        if speaker:
            if speaker == "NARRATION":
                s = self.font_sm.render("— narration —", True, TEXT_DIM)
            else:
                s = self.font_md.render(speaker.upper(), True, TEXT_WARN)
            surf.blit(s, (box.x + 18, ty))
            ty += s.get_height() + 6

        # text — preserve newlines, wrap within
        max_w = box.w - 36
        line_h = self.font.get_linesize() + 4
        for raw_line in text.split("\n"):
            for wrapped in self._wrap(self.font, raw_line, max_w):
                col = TEXT_DIM if speaker == "NARRATION" else TEXT
                s = self.font.render(wrapped, True, col)
                surf.blit(s, (box.x + 18, ty))
                ty += line_h

        # choices or continue prompt
        choices = node.get("choices")
        if choices:
            ty += 8
            for i, (label, _next, _eff) in enumerate(choices):
                prefix = ">" if i == dialogue.choice_index else " "
                col = TEXT if i == dialogue.choice_index else TEXT_DIM
                s = self.font.render(f"{prefix} {i+1}. {label}", True, col)
                surf.blit(s, (box.x + 28, ty))
                ty += line_h
        else:
            prompt = "Press E to continue" if node.get("next") else "Press E to close"
            s = self.font_sm.render(prompt, True, TEXT_DIM)
            surf.blit(s, (box.right - s.get_width() - 18, box.bottom - s.get_height() - 10))

    # ---------------------------------------------------------------- COMBAT
    def draw_combat(self, surf, combat, player):
        # full-screen overlay
        bg = pygame.Surface((WIDTH, HEIGHT - 100), pygame.SRCALPHA)
        bg.fill((6, 6, 10, 230))
        surf.blit(bg, (0, 0))

        # enemy "sprite"
        ex = WIDTH // 2 - 40
        ey = 160
        # color flickers
        col = (90, 70, 80)
        pygame.draw.rect(surf, col, (ex, ey, 80, 120))
        pygame.draw.rect(surf, BLACK, (ex, ey, 80, 120), 1)
        # name + hp
        s = self.font_big.render(combat.name, True, TEXT)
        surf.blit(s, (WIDTH // 2 - s.get_width() // 2, ey - 50))
        # hp bar
        hp_w = 240
        hp_ratio = max(0, combat.enemy_hp) / combat.enemy_max
        pygame.draw.rect(surf, (30, 14, 14), (WIDTH // 2 - hp_w // 2, ey + 130, hp_w, 12))
        pygame.draw.rect(surf, HUNGER_BAR, (WIDTH // 2 - hp_w // 2, ey + 130, int(hp_w * hp_ratio), 12))
        pygame.draw.rect(surf, BLACK, (WIDTH // 2 - hp_w // 2, ey + 130, hp_w, 12), 1)

        # log
        log_x = 60
        log_y = 380
        for i, line in enumerate(combat.log[-5:]):
            s = self.font.render(line, True, TEXT)
            surf.blit(s, (log_x, log_y + i * 22))

        # menu
        if not combat.over:
            menu_x = WIDTH - 280
            menu_y = 380
            s = self.font_md.render("ACTIONS", True, TEXT_DIM)
            surf.blit(s, (menu_x, menu_y - 28))
            for i, c in enumerate(combat.choices):
                prefix = ">" if i == combat.menu_index else " "
                col = TEXT if i == combat.menu_index else TEXT_DIM
                s = self.font_md.render(f"{prefix} {c}", True, col)
                surf.blit(s, (menu_x, menu_y + i * 28))
        else:
            s = self.font_md.render("...", True, TEXT_DIM)
            surf.blit(s, (WIDTH - 200, 380))

    # ---------------------------------------------------------------- MENU
    def draw_menu(self, surf, options, index, title="TWISTED AMERICA: HUNGER", subtitle="A horror RPG of the dying town."):
        surf.fill(BLACK)
        # title
        t = self.font_title.render(title, True, TEXT)
        surf.blit(t, (WIDTH // 2 - t.get_width() // 2, 140))
        sub = self.font_md.render(subtitle, True, TEXT_DIM)
        surf.blit(sub, (WIDTH // 2 - sub.get_width() // 2, 210))
        # blood smear
        pygame.draw.rect(surf, BLOOD_RED, (WIDTH // 2 - 200, 250, 400, 2))
        # options
        y = 340
        for i, opt in enumerate(options):
            prefix = ">  " if i == index else "   "
            col = TEXT if i == index else TEXT_DIM
            s = self.font_md.render(prefix + opt, True, col)
            surf.blit(s, (WIDTH // 2 - 200, y))
            y += 44

        # content warning
        warn = self.font_sm.render("Content warning: addiction, body horror, violence.", True, TEXT_DIM)
        surf.blit(warn, (WIDTH // 2 - warn.get_width() // 2, HEIGHT - 60))

    # ---------------------------------------------------------------- INVENTORY
    def draw_inventory(self, surf, player):
        bg = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        bg.fill((6, 6, 10, 220))
        surf.blit(bg, (0, 0))
        s = self.font_big.render("MAYA — FIELD KIT", True, TEXT)
        surf.blit(s, (80, 60))

        y = 130
        surf.blit(self.font_md.render("Consumables", True, TEXT_WARN), (80, y))
        y += 32
        for name, count in player.inventory.items():
            line = f"{name:<14} x{count}"
            surf.blit(self.font.render(line, True, TEXT), (100, y))
            y += 22

        y += 20
        surf.blit(self.font_md.render("Key items", True, TEXT_WARN), (80, y))
        y += 32
        if player.key_items:
            for k in sorted(player.key_items):
                surf.blit(self.font.render(k, True, TEXT), (100, y))
                y += 22
        else:
            surf.blit(self.font.render("— none —", True, TEXT_DIM), (100, y))
            y += 22

        # notebook hints
        y += 30
        surf.blit(self.font_md.render("Notebook", True, TEXT_WARN), (80, y))
        y += 32
        notes = self._notebook_lines(player)
        for n in notes:
            for ln in self._wrap(self.font_sm, "- " + n, WIDTH - 200):
                surf.blit(self.font_sm.render(ln, True, TEXT_DIM), (100, y))
                y += 18

        prompt = self.font_sm.render("I or ESC — close", True, TEXT_DIM)
        surf.blit(prompt, (WIDTH - prompt.get_width() - 60, HEIGHT - 60))

    def _notebook_lines(self, p):
        out = []
        if not p.flags["talked_henderson"]:
            out.append("Visit Old Man Henderson in The Hollows.")
        if not p.flags["talked_jared"]:
            out.append("Jared Blake is at the hospital, west of Main Street.")
        if not p.flags["talked_leah"]:
            out.append("Leah is at the trailer park, east of The Hollows.")
        if "Old Man's Note" in p.key_items:
            out.append("Bring Henderson's note to Jared.")
        if "Leah's Photo" in p.key_items:
            out.append("Bring Leah's photo back to her.")
        if p.flags["delivered_note"] and p.flags["delivered_photo"]:
            out.append("They might reconcile. Mother Ash still calls from the woods.")
        if "Cult Symbol" in p.key_items and not p.flags["talked_mother_ash"]:
            out.append("Carry the symbol into the woods.")
        if not out:
            out.append("Find the sinkhole. Decide.")
        return out

    # ---------------------------------------------------------------- ENDING
    def draw_ending(self, surf, ending):
        surf.fill(BLACK)
        title_map = {
            "consumption": ("CONSUMPTION", TEXT_BLOOD),
            "hollow_crown": ("THE HOLLOW CROWN", CORRUPT_BAR),
            "forgiveness": ("FORGIVENESS", BONE),
            "witness": ("THE WITNESS", TEXT),
        }
        body_map = {
            "consumption": [
                "The meter in your chest hits the last notch and tips.",
                "Your name does not unmake itself — Maya, Maya — but it",
                "is no longer yours to wear. The town has another mouth now.",
                "",
                "You will see Beckley again. From the inside out.",
            ],
            "hollow_crown": [
                "You step forward. Mother Ash opens. You open.",
                "The sinkhole closes around what was Maya and chooses",
                "a new throat. The wind in the woods slows.",
                "",
                "Years from now a doctor will come from up north.",
                "You will call her daughter. You will call her bright with hunger.",
            ],
            "forgiveness": [
                "Henderson opens his door. Jared sits on the porch.",
                "Neither of them says anything for a long time.",
                "Leah is two streets away, holding a photograph.",
                "",
                "The Hunger does not leave Beckley. But it has,",
                "for one winter, lost some of its appetite.",
                "",
                "You drive north. The road is plowed.",
            ],
            "witness": [
                "You turn your back on the sinkhole and walk.",
                "Behind you something laughs, then weeps, then is silent.",
                "",
                "You will write the report. They will not believe it.",
                "But you will remember. You will recognize the pattern",
                "the next time a small town stops answering its phones.",
            ],
        }
        title, col = title_map.get(ending, ("END", TEXT))
        body = body_map.get(ending, [""])

        t = self.font_title.render(title, True, col)
        surf.blit(t, (WIDTH // 2 - t.get_width() // 2, 120))
        pygame.draw.rect(surf, col, (WIDTH // 2 - 220, 200, 440, 2))

        y = 260
        for line in body:
            s = self.font_md.render(line, True, TEXT)
            surf.blit(s, (WIDTH // 2 - s.get_width() // 2, y))
            y += 36
        prompt = self.font_sm.render("Press ENTER to return to menu.", True, TEXT_DIM)
        surf.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT - 80))

    # ---------------------------------------------------------------- GAME OVER
    def draw_game_over(self, surf, message):
        surf.fill(BLACK)
        t = self.font_title.render("YOU DIED", True, TEXT_BLOOD)
        surf.blit(t, (WIDTH // 2 - t.get_width() // 2, 160))
        pygame.draw.rect(surf, BLOOD_RED, (WIDTH // 2 - 200, 240, 400, 2))
        for i, ln in enumerate(message.split("\n")):
            s = self.font_md.render(ln, True, TEXT)
            surf.blit(s, (WIDTH // 2 - s.get_width() // 2, 300 + i * 36))
        prompt = self.font_sm.render("ENTER — return to menu      F9 — load save", True, TEXT_DIM)
        surf.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT - 80))

    # ---------------------------------------------------------------- INTRO
    def draw_intro(self, surf, lines, line_index):
        surf.fill(BLACK)
        # show up to line_index lines centered
        y = 200
        for i, ln in enumerate(lines[: line_index + 1]):
            col = TEXT if i == line_index else TEXT_DIM
            s = self.font_md.render(ln, True, col)
            surf.blit(s, (WIDTH // 2 - s.get_width() // 2, y))
            y += 38
        prompt = self.font_sm.render("SPACE — next      ESC — skip", True, TEXT_DIM)
        surf.blit(prompt, (WIDTH // 2 - prompt.get_width() // 2, HEIGHT - 60))

    # ---------------------------------------------------------------- helpers
    def _wrap(self, font, text, max_w):
        words = text.split(" ")
        lines = []
        cur = ""
        for w in words:
            test = (cur + " " + w).strip() if cur else w
            if font.size(test)[0] <= max_w:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        return lines
