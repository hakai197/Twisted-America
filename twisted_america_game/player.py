"""Maya Chen — protagonist."""

import pygame
from settings import *


class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 22, 30)
        self.speed = 180  # px / sec
        self.max_hp = 100
        self.hp = 100
        self.hunger = 0
        self.max_hunger = 100
        self.corruption = 0
        self.facing = (0, 1)

        self.inventory = {
            "Coffee": 2,
            "Pill": 0,
            "Cigarette": 1,
        }
        self.key_items = set()

        self.flags = {
            "talked_henderson": False,
            "talked_jared": False,
            "talked_leah": False,
            "talked_cory": False,
            "talked_dealer": False,
            "talked_mother_ash": False,
            "henderson_forgave": False,
            "took_dealer_pills": False,
            "killed_dealer": False,
            "fed_hunger": False,
            "refused_hunger": False,
            "delivered_note": False,
            "delivered_photo": False,
            "reconciled": False,
            "saw_intro": False,
        }

        # passive hunger tick
        self._hunger_clock = 0.0
        self._hunger_period = 7.0  # seconds per +1 hunger

    # ---- stat helpers ----
    def add_hunger(self, n):
        self.hunger = max(0, min(self.max_hunger, self.hunger + n))

    def add_corruption(self, n):
        self.corruption = max(0, min(100, self.corruption + n))

    def damage(self, n):
        self.hp = max(0, self.hp - n)

    def heal(self, n):
        self.hp = min(self.max_hp, self.hp + n)

    # ---- update / draw ----
    def update(self, dt, obstacles):
        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1

        if dx or dy:
            # normalize
            if dx and dy:
                dx *= 0.7071
                dy *= 0.7071
            self.facing = (dx, dy)

        move_x = dx * self.speed * dt
        move_y = dy * self.speed * dt

        self.rect.x += round(move_x)
        for o in obstacles:
            if self.rect.colliderect(o):
                if move_x > 0:
                    self.rect.right = o.left
                elif move_x < 0:
                    self.rect.left = o.right
        self.rect.y += round(move_y)
        for o in obstacles:
            if self.rect.colliderect(o):
                if move_y > 0:
                    self.rect.bottom = o.top
                elif move_y < 0:
                    self.rect.top = o.bottom

        # passive hunger
        self._hunger_clock += dt
        while self._hunger_clock >= self._hunger_period:
            self._hunger_clock -= self._hunger_period
            self.add_hunger(1)

    def draw(self, surf, cam=(0, 0)):
        x = self.rect.x - cam[0]
        y = self.rect.y - cam[1]
        # coat
        coat = COAT_BROWN
        if self.hunger >= 76:
            coat = (40, 20, 22)  # darkening
        pygame.draw.rect(surf, coat, (x, y + 9, 22, 21))
        # collar
        pygame.draw.rect(surf, (40, 26, 18), (x + 4, y + 9, 14, 3))
        # head
        head_col = SKIN
        if self.hunger >= 76:
            head_col = (130, 100, 96)
        pygame.draw.rect(surf, head_col, (x + 6, y + 1, 10, 9))
        # hair
        pygame.draw.rect(surf, (20, 16, 14), (x + 6, y, 10, 3))
        # outline
        pygame.draw.rect(surf, BLACK, (x, y, 22, 30), 1)
