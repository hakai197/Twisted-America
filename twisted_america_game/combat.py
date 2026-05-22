"""Turn-based combat — Fight / Run / Item / Parley.

Encounters are short, punishing. Death is permanent (reload save).
"""

import random
from settings import *


ENCOUNTERS = {
    "hollowed": {
        "name": "Hollowed Patient",
        "hp": 18,
        "attack": (5, 9),
        "can_parley": True,
        "flee_chance": 0.6,
        "intro": "It rises from the gurney. Its mouth is wrong.",
        "death": "It folds. Quiet. Almost grateful.",
        "parley_text": "You speak its old name. It remembers. It walks away.",
        "win_hunger": 4,
    },
    "shadow": {
        "name": "Shadow",
        "hp": 14,
        "attack": (6, 10),
        "can_parley": False,
        "flee_chance": 0.4,
        "intro": "A shape that does not cast itself.",
        "death": "The shape unspools and is taken back into the snow.",
        "parley_text": "",
        "win_hunger": 3,
    },
    "dealer": {
        "name": "The Dealer",
        "hp": 36,
        "attack": (7, 12),
        "can_parley": False,
        "flee_chance": 0.25,
        "intro": "He's already reaching for the knife on the table.",
        "death": "He drops. The trailer is suddenly very quiet.",
        "parley_text": "",
        "win_hunger": 0,
    },
}


class Combat:
    def __init__(self, game, encounter_id, enemy_ref=None):
        self.game = game
        self.enemy_ref = enemy_ref  # the world Enemy instance (or None for forced fights)
        data = ENCOUNTERS[encounter_id]
        self.encounter_id = encounter_id
        self.name = data["name"]
        self.enemy_hp = data["hp"]
        self.enemy_max = data["hp"]
        self.attack_low, self.attack_high = data["attack"]
        self.can_parley = data["can_parley"]
        self.flee_chance = data["flee_chance"]
        self.win_hunger = data["win_hunger"]
        self.death_text = data["death"]
        self.parley_text = data["parley_text"]

        self.log = [data["intro"]]
        self.choices = self.menu_choices()
        self.menu_index = 0
        self.over = False
        self.victory = False
        self.player_turn = True
        self.message_timer = 0.0

    def menu_choices(self):
        base = ["Fight", "Run", "Item"]
        if self.can_parley and self.game.player.hunger < 50:
            base.append("Parley")
        return base

    def push(self, line):
        self.log.append(line)
        if len(self.log) > 6:
            self.log = self.log[-6:]

    # ---- actions ----
    def act_fight(self):
        dmg = random.randint(6, 12)
        # corruption sharpens the knife
        dmg += self.game.player.corruption // 25
        self.enemy_hp -= dmg
        self.push(f"You strike. -{dmg}.")
        if self.enemy_hp <= 0:
            self.win()
            return
        self.enemy_attack()

    def act_run(self):
        if random.random() < self.flee_chance:
            self.push("You break away into the snow.")
            self.end(victory=False, fled=True)
        else:
            self.push("You can't get clear.")
            self.enemy_attack()

    def act_item(self):
        inv = self.game.player.inventory
        if inv.get("Coffee", 0) > 0:
            inv["Coffee"] -= 1
            self.game.player.heal(8)
            self.game.player.add_hunger(-2)
            self.push("Coffee. Bitter. HP +8, Hunger -2.")
        elif inv.get("Pill", 0) > 0:
            inv["Pill"] -= 1
            self.game.player.add_hunger(-5)
            self.game.player.add_corruption(5)
            self.push("Pill. The fight slows. Hunger -5, Corruption +5.")
        else:
            self.push("Nothing in your bag worth using.")
            self.enemy_attack()
            return
        self.enemy_attack()

    def act_parley(self):
        if not self.can_parley:
            self.push("It will not listen.")
            self.enemy_attack()
            return
        if self.game.player.hunger >= 50:
            self.push("The hunger is too loud. You can't find words.")
            self.enemy_attack()
            return
        self.push(self.parley_text)
        self.end(victory=False, parleyed=True)

    def enemy_attack(self):
        dmg = random.randint(self.attack_low, self.attack_high)
        self.game.player.damage(dmg)
        self.push(f"{self.name} strikes. -{dmg} HP.")
        if self.game.player.hp <= 0:
            self.game.trigger_game_over("You fall in the snow. The hunger takes its time.")
            self.over = True

    # ---- end states ----
    def win(self):
        self.push(self.death_text)
        if self.enemy_ref is not None:
            self.enemy_ref.gone = True
        if self.encounter_id == "dealer":
            self.game.player.flags["killed_dealer"] = True
            self.game.player.add_corruption(10)
        self.game.player.add_hunger(self.win_hunger)
        self.end(victory=True)

    def end(self, victory=False, fled=False, parleyed=False):
        self.over = True
        self.victory = victory
        if parleyed and self.enemy_ref is not None:
            self.enemy_ref.gone = True
        self.message_timer = 1.5  # short pause before returning to play

    # ---- input ----
    def handle_key(self, key):
        if self.over:
            return
        import pygame
        if key in (pygame.K_w, pygame.K_UP):
            self.menu_index = (self.menu_index - 1) % len(self.choices)
        elif key in (pygame.K_s, pygame.K_DOWN):
            self.menu_index = (self.menu_index + 1) % len(self.choices)
        elif key in (pygame.K_RETURN, pygame.K_e, pygame.K_SPACE):
            choice = self.choices[self.menu_index]
            if choice == "Fight":
                self.act_fight()
            elif choice == "Run":
                self.act_run()
            elif choice == "Item":
                self.act_item()
            elif choice == "Parley":
                self.act_parley()
            # recompute parley availability
            self.choices = self.menu_choices()
            self.menu_index = min(self.menu_index, len(self.choices) - 1)

    def update(self, dt):
        if self.over:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.game.end_combat()
