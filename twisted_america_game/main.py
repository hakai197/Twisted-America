"""Twisted America: Hunger — entry point.

Run:   python main.py

Controls:
    WASD / Arrows  — move
    E              — interact / advance dialogue
    1-4            — choose dialogue option (also W/S + Enter)
    I              — open inventory / notebook
    ESC            — back / menu
    F5 / F9        — save / load
"""

import sys
import os
import pygame
import random

from settings import *
from player import Player
from world import build_zones, PLAY_W, PLAY_H
from npc import NPC, Enemy
from ui import UI
from combat import Combat, ENCOUNTERS
from hunger_effects import HungerFx
from save_system import save_game, load_game, has_save
import dialogue_data


# ============================================================ DIALOGUE RUNNER
class Dialogue:
    """Walks through a dialogue node tree."""

    def __init__(self, tree, game, on_close=None):
        self.tree = tree
        self.game = game
        self.node_key = "start"
        self.choice_index = 0
        self.closed = False
        self.on_close = on_close
        self._fired_effects = set()
        self._enter_node()

    def current_node(self):
        return self.tree.get(self.node_key)

    def _enter_node(self):
        node = self.current_node()
        if node is None:
            self.close()
            return
        # one-shot effect
        eff = node.get("effect")
        if eff and id(node) not in self._fired_effects:
            self._fired_effects.add(id(node))
            try:
                eff(self.game)
            except Exception as e:
                print(f"[dialogue effect error] {e}")
        self.choice_index = 0

    def advance(self):
        """Called when player presses E with no visible choices."""
        if self.closed:
            return
        node = self.current_node()
        if node is None:
            self.close()
            return
        nxt = node.get("next")
        if nxt is None:
            self.close()
        else:
            self.node_key = nxt
            self._enter_node()

    def pick(self, idx):
        node = self.current_node()
        if not node or not node.get("choices"):
            return
        choices = node["choices"]
        if idx < 0 or idx >= len(choices):
            return
        label, next_key, eff = choices[idx]
        if eff:
            try:
                eff(self.game)
            except Exception as e:
                print(f"[choice effect error] {e}")
        if next_key is None:
            self.close()
        else:
            self.node_key = next_key
            self._enter_node()

    def move_cursor(self, delta):
        node = self.current_node()
        if not node or not node.get("choices"):
            return
        n = len(node["choices"])
        self.choice_index = (self.choice_index + delta) % n

    def close(self):
        self.closed = True
        if self.on_close:
            try:
                self.on_close()
            except Exception as e:
                print(f"[on_close error] {e}")


# ============================================================ GAME
INTRO_LINES = [
    "BECKLEY, WEST VIRGINIA — JANUARY",
    "",
    "Three weeks ago, the calls stopped.",
    "The state police drove in. They drove back out.",
    "They said the town was fine. The town was not fine.",
    "",
    "Dr. Maya Chen, forensic psychologist, was sent in.",
    "Her first field investigation.",
    "",
    "Her notes — left in the car at the edge of town —",
    "would later be read aloud at a closed hearing in Charleston.",
    "",
    "She walked the rest of the way.",
    "",
    "It was snowing.",
]


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Twisted America: Hunger")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.running = True

        self.ui = UI()
        self.fx = HungerFx()

        self.state = STATE_MENU
        self.menu_index = 0
        self.menu_options = self._menu_options()

        # placeholders until New Game / Load is chosen
        self.player = None
        self.zones = None
        self.current_zone_key = None
        self.dialogue = None
        self.combat = None
        self.ending = None
        self.game_over_msg = ""
        self.intro_index = 0
        self.intro_timer = 0.0

        # notification
        self.notification = None
        self.notification_timer = 0.0

        # zone entry narration
        self.entry_text = None
        self.entry_text_timer = 0.0

        # font for fx whispers
        self.fx_font = pygame.font.SysFont("consolas", 18, italic=True)

    # ---------- menu ----------
    def _menu_options(self):
        opts = ["NEW GAME"]
        if has_save():
            opts.append("CONTINUE")
        opts.append("QUIT")
        return opts

    # ---------- properties ----------
    @property
    def zone(self):
        return self.zones[self.current_zone_key]

    # ---------- lifecycle ----------
    def start_new_game(self):
        self.player = Player(WIDTH // 2 - 20, PLAY_H // 2)
        self.zones = build_zones()
        self.current_zone_key = "main_street"
        self.dialogue = None
        self.combat = None
        self.ending = None
        self.state = STATE_INTRO
        self.intro_index = 0
        self.intro_timer = 0.0

    def begin_play(self):
        self.state = STATE_PLAYING
        self._enter_zone_effects()

    def load(self):
        # need player + zones to exist before loading state into them
        if not has_save():
            return False
        self.player = Player(0, 0)
        self.zones = build_zones()
        self.current_zone_key = "main_street"
        ok = load_game(self)
        if ok:
            self.state = STATE_PLAYING
            self.show_message("Loaded.")
            self._enter_zone_effects()
        return ok

    def save(self):
        if save_game(self):
            self.show_message("Saved.")
            self.menu_options = self._menu_options()

    # ---------- zone transitions ----------
    def change_zone(self, key, spawn=None):
        self.current_zone_key = key
        if spawn:
            self.player.rect.x, self.player.rect.y = spawn
        self._enter_zone_effects()

    def _enter_zone_effects(self):
        z = self.zone
        if not z.visited:
            z.visited = True
            if z.entry_narration:
                self.entry_text = z.entry_narration
                self.entry_text_timer = 4.5

    # ---------- messaging ----------
    def show_message(self, text, duration=2.5):
        self.notification = text
        self.notification_timer = duration

    # ---------- combat ----------
    def start_combat(self, encounter_id, enemy_ref=None):
        self.combat = Combat(self, encounter_id, enemy_ref=enemy_ref)
        self.state = STATE_COMBAT

    def end_combat(self):
        self.combat = None
        if self.player.hp > 0:
            self.state = STATE_PLAYING

    # ---------- game over ----------
    def trigger_game_over(self, message):
        self.game_over_msg = message
        self.state = STATE_GAME_OVER

    # ---------- ending check ----------
    def check_endings(self):
        p = self.player
        if p.hunger >= 100 and self.state == STATE_PLAYING:
            self.trigger_ending("consumption")
            return
        if p.flags["fed_hunger"] and self.state == STATE_PLAYING:
            self.trigger_ending("hollow_crown")
            return
        if p.flags["refused_hunger"] and self.state == STATE_PLAYING:
            if p.flags["reconciled"]:
                self.trigger_ending("forgiveness")
            else:
                self.trigger_ending("witness")

    def trigger_ending(self, key):
        self.ending = key
        self.state = STATE_ENDING

    # ============================================================ EVENTS
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)

    def handle_key(self, key):
        if self.state == STATE_MENU:
            self._key_menu(key)
        elif self.state == STATE_INTRO:
            self._key_intro(key)
        elif self.state == STATE_PLAYING:
            self._key_play(key)
        elif self.state == STATE_DIALOGUE:
            self._key_dialogue(key)
        elif self.state == STATE_COMBAT:
            self._key_combat(key)
        elif self.state == STATE_INVENTORY:
            self._key_inventory(key)
        elif self.state == STATE_ENDING:
            self._key_ending(key)
        elif self.state == STATE_GAME_OVER:
            self._key_game_over(key)

    def _key_menu(self, key):
        if key in (pygame.K_w, pygame.K_UP):
            self.menu_index = (self.menu_index - 1) % len(self.menu_options)
        elif key in (pygame.K_s, pygame.K_DOWN):
            self.menu_index = (self.menu_index + 1) % len(self.menu_options)
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            choice = self.menu_options[self.menu_index]
            if choice == "NEW GAME":
                self.start_new_game()
            elif choice == "CONTINUE":
                self.load()
            elif choice == "QUIT":
                self.running = False

    def _key_intro(self, key):
        if key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
            self.intro_index += 1
            if self.intro_index >= len(INTRO_LINES):
                self.begin_play()
        elif key == pygame.K_ESCAPE:
            self.intro_index = len(INTRO_LINES)
            self.begin_play()

    def _key_play(self, key):
        if key == pygame.K_e:
            self.try_interact()
        elif key == pygame.K_i:
            self.state = STATE_INVENTORY
        elif key == pygame.K_ESCAPE:
            # back to menu (but keep run going)
            self.state = STATE_MENU
            self.menu_options = self._menu_options()
            self.menu_index = 0
        elif key == pygame.K_F5:
            self.save()
        elif key == pygame.K_F9:
            self.load()
        elif key == pygame.K_c:
            # debug: use coffee
            if self.player.inventory.get("Coffee", 0) > 0:
                self.player.inventory["Coffee"] -= 1
                self.player.heal(5)
                self.player.add_hunger(-2)
                self.show_message("Coffee. -2 Hunger.")
        elif key == pygame.K_x:
            # use cigarette - reveals hidden paths (cosmetic for now)
            if self.player.inventory.get("Cigarette", 0) > 0:
                self.player.inventory["Cigarette"] -= 1
                self.show_message("You light up. The trees lean back a little.")
                self.player.add_hunger(-1)
        elif key == pygame.K_p:
            # use a pill
            if self.player.inventory.get("Pill", 0) > 0:
                self.player.inventory["Pill"] -= 1
                self.player.add_hunger(-5)
                self.player.add_corruption(8)
                self.show_message("Pill. Hunger -5. Corruption +8.")

    def _key_dialogue(self, key):
        d = self.dialogue
        if not d:
            self.state = STATE_PLAYING
            return
        node = d.current_node()
        choices = node.get("choices") if node else None
        if choices:
            if key in (pygame.K_w, pygame.K_UP):
                d.move_cursor(-1)
            elif key in (pygame.K_s, pygame.K_DOWN):
                d.move_cursor(1)
            elif key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE):
                d.pick(d.choice_index)
            elif key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                d.pick(key - pygame.K_1)
        else:
            if key in (pygame.K_e, pygame.K_RETURN, pygame.K_SPACE):
                d.advance()
        if d.closed:
            self.dialogue = None
            self.state = STATE_PLAYING
            self.check_endings()

    def _key_combat(self, key):
        if self.combat:
            self.combat.handle_key(key)

    def _key_inventory(self, key):
        if key in (pygame.K_i, pygame.K_ESCAPE):
            self.state = STATE_PLAYING
        elif key == pygame.K_c:
            if self.player.inventory.get("Coffee", 0) > 0:
                self.player.inventory["Coffee"] -= 1
                self.player.heal(5)
                self.player.add_hunger(-2)
                self.show_message("Coffee. -2 Hunger.")
        elif key == pygame.K_p:
            if self.player.inventory.get("Pill", 0) > 0:
                self.player.inventory["Pill"] -= 1
                self.player.add_hunger(-5)
                self.player.add_corruption(8)
                self.show_message("Pill. Hunger -5. Corruption +8.")

    def _key_ending(self, key):
        if key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            # back to title — game over
            self.state = STATE_MENU
            self.menu_options = self._menu_options()
            self.menu_index = 0

    def _key_game_over(self, key):
        if key == pygame.K_F9:
            self.load()
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
            self.state = STATE_MENU
            self.menu_options = self._menu_options()

    # ---------- interaction ----------
    def try_interact(self):
        # check exits first
        for ex in self.zone.exits:
            if self.player.rect.colliderect(ex.rect.inflate(20, 20)):
                self.change_zone(ex.target_zone, ex.spawn_xy)
                return
        # NPC?
        for npc in self.zone.npcs:
            if npc.gone:
                continue
            if self.player.rect.colliderect(npc.interact_rect()):
                tree = dialogue_data.get(npc.dialogue_key, self)
                self.dialogue = Dialogue(tree, self)
                self.state = STATE_DIALOGUE
                if self.dialogue.closed:
                    self.dialogue = None
                    self.state = STATE_PLAYING
                    self.check_endings()
                return
        # enemy?
        for en in self.zone.enemies:
            if en.gone:
                continue
            if self.player.rect.colliderect(en.interact_rect()):
                self.start_combat(en.encounter_id, enemy_ref=en)
                return

    # ============================================================ UPDATE
    def update(self, dt):
        if self.state == STATE_PLAYING:
            self.fx.update(dt, self.player.hunger)
            self.player.update(dt, self.zone.obstacles)
            self._check_enemy_collisions()
            self.check_endings()
        elif self.state == STATE_COMBAT:
            self.fx.update(dt, self.player.hunger)
            if self.combat:
                self.combat.update(dt)
        elif self.state == STATE_INTRO:
            self.intro_timer += dt
            if self.intro_timer > 1.2 and self.intro_index < len(INTRO_LINES) - 1:
                self.intro_timer = 0.0
                self.intro_index += 1
        # notification timer
        if self.notification_timer > 0:
            self.notification_timer -= dt
            if self.notification_timer <= 0:
                self.notification = None
        if self.entry_text_timer > 0:
            self.entry_text_timer -= dt
            if self.entry_text_timer <= 0:
                self.entry_text = None

    def _check_enemy_collisions(self):
        for en in self.zone.enemies:
            if en.gone:
                continue
            if self.player.rect.colliderect(en.rect):
                self.start_combat(en.encounter_id, enemy_ref=en)
                return

    # ============================================================ DRAW
    def draw(self):
        screen = self.screen
        if self.state == STATE_MENU:
            self.ui.draw_menu(screen, self.menu_options, self.menu_index)
        elif self.state == STATE_INTRO:
            self.ui.draw_intro(screen, INTRO_LINES, min(self.intro_index, len(INTRO_LINES) - 1))
        elif self.state == STATE_ENDING:
            self.ui.draw_ending(screen, self.ending)
        elif self.state == STATE_GAME_OVER:
            self.ui.draw_game_over(screen, self.game_over_msg)
        elif self.state == STATE_COMBAT:
            self._draw_world()
            self.ui.draw_combat(screen, self.combat, self.player)
            self.ui.draw_hud(screen, self)
        elif self.state == STATE_INVENTORY:
            self._draw_world()
            self.ui.draw_hud(screen, self)
            self.ui.draw_inventory(screen, self.player)
        else:
            # playing or dialogue
            self._draw_world()
            if self.state == STATE_DIALOGUE and self.dialogue:
                self.ui.draw_dialogue(screen, self.dialogue)
            elif self.state == STATE_PLAYING:
                self._draw_interact_prompt()
                if self.entry_text:
                    self.ui.draw_entry_narration(screen, self.entry_text)
            self.ui.draw_hud(screen, self)

        if self.notification:
            self.ui.draw_notification(screen, self.notification)

        pygame.display.flip()

    def _draw_world(self):
        z = self.zone
        # ground
        self.screen.fill(z.ground_color, rect=(0, 0, WIDTH, HEIGHT - 100))
        # snow specks for atmosphere
        for sx, sy, *_ in z.snow_specks:
            self.screen.set_at((int(sx), int(sy)), SNOW)
        # decorations
        for d in z.decorations:
            d.draw(self.screen, (0, 0))
        # NPCs
        for n in z.npcs:
            n.draw(self.screen, (0, 0))
        # Enemies
        for e in z.enemies:
            e.draw(self.screen, (0, 0))
        # Exits — small arrows / labels
        self._draw_exit_markers()
        # Player
        self.player.draw(self.screen, (0, 0))
        # foreground (e.g. sinkhole rim)
        for f in z.foreground:
            f.draw(self.screen, (0, 0))
        # Hunger effects on top
        self.fx.draw_overlay(self.screen, self.player.hunger, self.fx_font)

    def _draw_exit_markers(self):
        font = self.ui.font_sm
        for ex in self.zone.exits:
            r = ex.rect
            # darker tile to indicate exit
            pygame.draw.rect(self.screen, (60, 60, 70), r)
            pygame.draw.rect(self.screen, BLACK, r, 1)
            label = font.render(ex.label, True, TEXT_DIM)
            # position label nearby
            if r.x < 32:  # left edge
                self.screen.blit(label, (r.right + 8, r.centery - label.get_height() // 2))
            elif r.right > WIDTH - 32:  # right edge
                self.screen.blit(label, (r.left - label.get_width() - 8, r.centery - label.get_height() // 2))
            elif r.y < 32:
                self.screen.blit(label, (r.centerx - label.get_width() // 2, r.bottom + 4))
            else:
                self.screen.blit(label, (r.centerx - label.get_width() // 2, r.top - label.get_height() - 4))

    def _draw_interact_prompt(self):
        # show prompt if near an interactable
        for ex in self.zone.exits:
            if self.player.rect.colliderect(ex.rect.inflate(20, 20)):
                self.ui.draw_interact_prompt(self.screen, ex.label.strip("<>v^ "))
                return
        for npc in self.zone.npcs:
            if npc.gone:
                continue
            if self.player.rect.colliderect(npc.interact_rect()):
                self.ui.draw_interact_prompt(self.screen, f"Talk to {npc.label}")
                return
        for en in self.zone.enemies:
            if en.gone:
                continue
            if self.player.rect.colliderect(en.interact_rect()):
                self.ui.draw_interact_prompt(self.screen, f"Engage {en.label}")
                return

    # ============================================================ MAIN LOOP
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit()


def main():
    # make sure we run from this directory so save.json lands next to it
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    Game().run()


if __name__ == "__main__":
    main()
