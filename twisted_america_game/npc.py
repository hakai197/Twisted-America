"""NPC base class — used for talking characters and enemy spawners."""

import pygame
from settings import *


class NPC:
    def __init__(self, name, x, y, color, dialogue_key, w=22, h=30, label=None):
        self.name = name
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.dialogue_key = dialogue_key  # key into dialogue_data
        self.label = label or name
        self.gone = False  # NPC removed from world

    def interact_rect(self):
        r = self.rect.copy()
        r.inflate_ip(30, 30)
        return r

    def draw(self, surf, cam=(0, 0)):
        if self.gone:
            return
        x = self.rect.x - cam[0]
        y = self.rect.y - cam[1]
        # body
        pygame.draw.rect(surf, self.color, (x, y + 9, self.rect.w, self.rect.h - 9))
        # head
        pygame.draw.rect(surf, SKIN, (x + 6, y + 1, self.rect.w - 12, 9))
        pygame.draw.rect(surf, (20, 16, 14), (x + 6, y, self.rect.w - 12, 3))
        pygame.draw.rect(surf, BLACK, (x, y, self.rect.w, self.rect.h), 1)


class Enemy(NPC):
    """An NPC the player must fight or flee on contact."""

    def __init__(self, name, x, y, color, hp, attack, can_parley, encounter_id):
        super().__init__(name, x, y, color, dialogue_key=None, w=24, h=30, label=name)
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.can_parley = can_parley
        self.encounter_id = encounter_id  # marks combat encounter type

    def draw(self, surf, cam=(0, 0)):
        if self.gone:
            return
        x = self.rect.x - cam[0]
        y = self.rect.y - cam[1]
        pygame.draw.rect(surf, self.color, (x, y + 9, 24, 21))
        # head — sickly, sunken
        pygame.draw.rect(surf, (110, 96, 86), (x + 6, y + 1, 12, 9))
        # hollow eyes
        pygame.draw.rect(surf, BLACK, (x + 8, y + 4, 2, 2))
        pygame.draw.rect(surf, BLACK, (x + 14, y + 4, 2, 2))
        pygame.draw.rect(surf, BLACK, (x, y, 24, 30), 1)
