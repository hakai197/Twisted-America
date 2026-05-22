"""NPC base class — used for talking characters and enemy spawners."""

import math
import random
import pygame
from settings import *
import assets


class NPC:
    def __init__(self, name, x, y, color, dialogue_key, w=22, h=30, label=None):
        self.name = name
        self.rect = pygame.Rect(x, y, w, h)
        self.color = color
        self.dialogue_key = dialogue_key
        self.label = label or name
        self.gone = False

        # idle anim state (lazy — only used by draw)
        self._t = random.uniform(0, 6.28)  # random phase so NPCs don't sway in sync
        self._jitter = (0, 0)
        self._jitter_clock = random.uniform(0.0, 0.3)
        self._frame_clock = random.uniform(0.0, 0.2)
        self._frame_idx = random.randint(0, 3)
        self._sprite_key = "npc_" + assets.slug(name)

    def interact_rect(self):
        r = self.rect.copy()
        r.inflate_ip(30, 30)
        return r

    def _tick_anim(self, dt=1 / 60.0, jitter_mag=1, frame_period=0.22):
        # Driven from draw because NPCs don't have an update() in this prototype.
        self._t += dt
        self._jitter_clock -= dt
        if self._jitter_clock <= 0:
            self._jitter_clock = random.uniform(0.20, 0.55)
            self._jitter = (random.randint(-jitter_mag, jitter_mag),
                            random.randint(-jitter_mag, jitter_mag))
        self._frame_clock += dt
        if self._frame_clock >= frame_period:
            self._frame_clock = 0.0
            self._frame_idx += 1

    def draw(self, surf, cam=(0, 0)):
        if self.gone:
            return
        self._tick_anim()
        jx, jy = self._jitter
        x = self.rect.x - cam[0] + jx
        y = self.rect.y - cam[1] + jy

        sp = assets.sprite(self._sprite_key, self._frame_idx)
        if sp is not None:
            sw, sh = sp.get_size()
            surf.blit(sp, (x + (self.rect.w - sw) // 2, y + self.rect.h - sh))
            return

        self._draw_silhouette(surf, x, y)

    def _draw_silhouette(self, surf, x, y):
        w, h = self.rect.w, self.rect.h
        bottom = y + h
        sway = math.sin(self._t * 1.1) * 0.7

        # ground shadow
        pygame.draw.ellipse(surf, (0, 0, 0), (x - 2, bottom - 3, w + 4, 5))
        # legs
        pygame.draw.rect(surf, (22, 18, 16), (x + 5, bottom - 12, 4, 12))
        pygame.draw.rect(surf, (22, 18, 16), (x + w - 9, bottom - 12, 4, 12))
        # body — slightly tapered
        pygame.draw.polygon(surf, self.color, [
            (x + 4, bottom - 22),
            (x + w - 4, bottom - 22),
            (x + w - 1, bottom - 4),
            (x + 1, bottom - 4),
        ])
        # neck
        nx = int(x + w // 2 - 2 + sway)
        pygame.draw.rect(surf, SKIN, (nx, bottom - 28, 4, 6))
        # head — above rect (elongation)
        head_w, head_h = 8, 9
        hx = int(x + w // 2 - head_w // 2 + sway)
        pygame.draw.rect(surf, SKIN, (hx, bottom - 38, head_w, head_h))
        pygame.draw.rect(surf, (18, 14, 12), (hx, bottom - 38, head_w, 3))
        # eye line
        pygame.draw.rect(surf, (38, 28, 26), (hx + 1, bottom - 34, head_w - 2, 1))


class Enemy(NPC):
    """An NPC the player must fight or flee on contact."""

    def __init__(self, name, x, y, color, hp, attack, can_parley, encounter_id):
        super().__init__(name, x, y, color, dialogue_key=None, w=24, h=30, label=name)
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.can_parley = can_parley
        self.encounter_id = encounter_id
        self._sprite_key = "enemy_" + assets.slug(encounter_id)

    def draw(self, surf, cam=(0, 0)):
        if self.gone:
            return
        # Enemies twitch harder and snap frames faster — wrongness.
        self._tick_anim(jitter_mag=2, frame_period=0.16)
        jx, jy = self._jitter
        x = self.rect.x - cam[0] + jx
        y = self.rect.y - cam[1] + jy

        sp = assets.sprite(self._sprite_key, self._frame_idx)
        if sp is not None:
            sw, sh = sp.get_size()
            surf.blit(sp, (x + (self.rect.w - sw) // 2, y + self.rect.h - sh))
            return

        self._draw_enemy_silhouette(surf, x, y)

    def _draw_enemy_silhouette(self, surf, x, y):
        w, h = self.rect.w, self.rect.h
        bottom = y + h
        # Strong elongation: head sits ~20px above the rect.
        sway = math.sin(self._t * 0.8) * 1.6
        bob = math.sin(self._t * 2.7) * 0.6  # subtle vertical pulse

        # ground shadow
        pygame.draw.ellipse(surf, (0, 0, 0), (x - 3, bottom - 3, w + 6, 6))
        # spindly legs
        pygame.draw.rect(surf, (14, 12, 14), (x + 6, bottom - 14, 3, 14))
        pygame.draw.rect(surf, (14, 12, 14), (x + w - 9, bottom - 14, 3, 14))
        # gaunt elongated torso — narrows at the shoulders
        pygame.draw.polygon(surf, self.color, [
            (x + 5, bottom - 28),
            (x + w - 5, bottom - 28),
            (x + w - 2, bottom - 6),
            (x + 2, bottom - 6),
        ])
        # long neck (stretched)
        nx = int(x + w // 2 - 2 + sway)
        pygame.draw.rect(surf, (96, 84, 78), (nx, bottom - 40 + int(bob), 4, 12))
        # small sunken head sitting well above the rect — elongation
        head_w, head_h = 9, 9
        hx = int(x + w // 2 - head_w // 2 + sway)
        hy = bottom - 50 + int(bob)
        pygame.draw.rect(surf, (96, 84, 78), (hx, hy, head_w, head_h))
        # hollow eyes
        pygame.draw.rect(surf, (0, 0, 0), (hx + 1, hy + 3, 2, 3))
        pygame.draw.rect(surf, (0, 0, 0), (hx + head_w - 3, hy + 3, 2, 3))
        # mouth slit
        pygame.draw.rect(surf, (40, 10, 10), (hx + 2, hy + 7, head_w - 4, 1))
