"""Maya Chen — protagonist."""

import math
import random
import pygame
from settings import *
import assets


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

        # idle animation state
        self._idle_t = 0.0
        self._jitter = (0, 0)
        self._jitter_clock = 0.0
        self._frame_clock = 0.0
        self._frame_idx = 0
        self._is_moving = False

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
            if dx and dy:
                dx *= 0.7071
                dy *= 0.7071
            self.facing = (dx, dy)
            self._is_moving = True
        else:
            self._is_moving = False

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

        # idle jitter & frame animation
        self._idle_t += dt
        self._jitter_clock -= dt
        if self._jitter_clock <= 0:
            # idle is twitchier than walking — twitch a bit either way
            self._jitter_clock = random.uniform(0.18, 0.42)
            mag = 1 if self._is_moving else 1
            self._jitter = (random.randint(-mag, mag), random.randint(-mag, mag))
        self._frame_clock += dt
        frame_period = 0.14 if self._is_moving else 0.22
        if self._frame_clock >= frame_period:
            self._frame_clock = 0.0
            self._frame_idx += 1

    def draw(self, surf, cam=(0, 0)):
        jx, jy = self._jitter
        x = self.rect.x - cam[0] + jx
        y = self.rect.y - cam[1] + jy

        sp = assets.sprite("maya", self._frame_idx)
        if sp is not None:
            sw, sh = sp.get_size()
            blit_x = x + (self.rect.w - sw) // 2
            blit_y = y + self.rect.h - sh  # foot-aligned
            surf.blit(sp, (blit_x, blit_y))
            return

        self._draw_silhouette(surf, x, y)

    def _draw_silhouette(self, surf, x, y):
        w, h = self.rect.w, self.rect.h
        bottom = y + h
        # subtle ground shadow
        shadow = pygame.Rect(x - 2, bottom - 3, w + 4, 5)
        pygame.draw.ellipse(surf, (0, 0, 0), shadow)

        sway = math.sin(self._idle_t * 1.4) * 0.6
        coat = COAT_BROWN if self.hunger < 76 else (40, 20, 22)
        head_col = SKIN if self.hunger < 76 else (130, 100, 96)

        # legs
        pygame.draw.rect(surf, (24, 18, 14), (x + 6, bottom - 12, 4, 12))
        pygame.draw.rect(surf, (24, 18, 14), (x + w - 10, bottom - 12, 4, 12))
        # coat — flared at base, narrower at shoulders (gaunt)
        pygame.draw.polygon(surf, coat, [
            (x + 5, bottom - 22),
            (x + w - 5, bottom - 22),
            (x + w - 1, bottom - 4),
            (x + 1, bottom - 4),
        ])
        # collar
        pygame.draw.rect(surf, (24, 16, 12), (x + 6, bottom - 22, w - 12, 2))
        # neck (elongates above the rect)
        nx = int(x + w // 2 - 2 + sway)
        pygame.draw.rect(surf, head_col, (nx, bottom - 28, 4, 6))
        # head — sits above rect top (elongation)
        head_w, head_h = 8, 9
        hx = int(x + w // 2 - head_w // 2 + sway)
        pygame.draw.rect(surf, head_col, (hx, bottom - 38, head_w, head_h))
        # hair / hood
        pygame.draw.rect(surf, (16, 12, 10), (hx, bottom - 38, head_w, 3))
        # darken eyes — just a horizontal shadow band
        pygame.draw.rect(surf, (28, 22, 22), (hx + 1, bottom - 34, head_w - 2, 1))
