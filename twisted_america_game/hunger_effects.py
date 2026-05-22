"""Visual / atmospheric effects driven by the Hunger meter.

Intended audio atmosphere (no sound files used in prototype — wire in later):
  - Low, droning ambient wind (constant)
  - Distant intermittent scratching (random every 20-40s)
  - Heartbeat that quickens as Hunger rises (loop tempo scales with meter)
  - At Hunger > 75: a second voice that hums under everything
  - At Hunger > 90: occasional whispered "daughter", "open your mouth"

To add sound, load mixer assets and play them inside `apply_hunger_effects`
based on hunger thresholds.
"""

import pygame
import random
import math
from settings import *


WHISPERS = [
    "daughter",
    "open your mouth",
    "the hole is older than the town",
    "you smell like winter",
    "stay",
    "come closer",
    "she remembers your name",
    "you were always coming",
]


class HungerFx:
    def __init__(self):
        self.time = 0.0
        self.flicker_timer = 0.0
        self.whisper_timer = random.uniform(6, 12)
        self.active_whisper = None
        self.active_whisper_time = 0.0
        self._tile_overlay = pygame.Surface((WIDTH, HEIGHT - 100), pygame.SRCALPHA)
        self._vignette = self._build_vignette()

    def _build_vignette(self):
        s = pygame.Surface((WIDTH, HEIGHT - 100), pygame.SRCALPHA)
        # darker corners — drawn each frame because alpha varies
        return s

    def update(self, dt, hunger):
        self.time += dt
        self.flicker_timer -= dt
        self.whisper_timer -= dt
        if self.active_whisper:
            self.active_whisper_time -= dt
            if self.active_whisper_time <= 0:
                self.active_whisper = None
        # spawn whispers more often as hunger climbs
        if hunger >= 50 and self.whisper_timer <= 0:
            cadence = max(2.5, 12 - hunger / 12)
            self.whisper_timer = random.uniform(cadence * 0.6, cadence * 1.4)
            if random.random() < min(0.95, hunger / 100 + 0.2):
                self.active_whisper = random.choice(WHISPERS)
                self.active_whisper_time = random.uniform(1.4, 2.4)

    def draw_overlay(self, surf, hunger, font):
        """Painted on top of the play area each frame."""
        h = hunger
        play_rect = pygame.Rect(0, 0, WIDTH, HEIGHT - 100)

        if h <= 25:
            return  # no effect

        # Desaturation tint (subtle gray wash)
        if h > 25:
            tint = min(60, (h - 25) * 1.2)
            self._tile_overlay.fill((40, 40, 50, int(tint)))
            surf.blit(self._tile_overlay, (0, 0))

        # Edge darkening / vignette
        if h > 25:
            vig_alpha = min(180, int((h - 25) * 2.4))
            self._draw_vignette(surf, vig_alpha)

        # Random pixel shift / noise — pixel dust
        if h > 50:
            count = int((h - 50) * 4)
            for _ in range(count):
                x = random.randint(0, WIDTH - 1)
                y = random.randint(0, HEIGHT - 101)
                c = random.choice([(20, 20, 24), (180, 180, 180), (50, 12, 12)])
                surf.set_at((x, y), c)

        # Stretched shadows around the player position — drawn elsewhere.

        # Blood drips at the top edge
        if h > 75:
            self._draw_drips(surf, h)

        # Pixel shift bands
        if h > 80:
            band_y = int((self.time * 80) % (HEIGHT - 100))
            band_h = 6
            band = surf.subsurface(pygame.Rect(0, band_y, WIDTH, band_h)).copy()
            shift = random.randint(-10, 10)
            surf.blit(band, (shift, band_y))

        # whisper text
        if self.active_whisper:
            s = font.render(self.active_whisper, True, (160, 40, 40))
            # position drifts
            jx = random.randint(-2, 2)
            jy = random.randint(-2, 2)
            wx = random.randint(80, WIDTH - 200)
            wy = random.randint(40, HEIGHT - 200)
            surf.blit(s, (wx + jx, wy + jy))

    def _draw_vignette(self, surf, alpha):
        # cheap vignette: four darkening edges
        s = pygame.Surface((WIDTH, HEIGHT - 100), pygame.SRCALPHA)
        # corners
        margin = 220
        for i in range(margin):
            a = int(alpha * (i / margin) ** 2)
            if a <= 0:
                continue
            pygame.draw.rect(s, (0, 0, 0, a), (0, i, WIDTH, 1))
            pygame.draw.rect(s, (0, 0, 0, a), (0, HEIGHT - 100 - i - 1, WIDTH, 1))
            pygame.draw.rect(s, (0, 0, 0, a), (i, 0, 1, HEIGHT - 100))
            pygame.draw.rect(s, (0, 0, 0, a), (WIDTH - i - 1, 0, 1, HEIGHT - 100))
        surf.blit(s, (0, 0))

    def _draw_drips(self, surf, hunger):
        # vertical reddish streaks from the top
        random.seed(int(self.time * 1.5))
        count = int((hunger - 75) / 2) + 1
        for _ in range(count):
            x = random.randint(0, WIDTH - 1)
            length = random.randint(20, 80)
            for y in range(length):
                a = max(0, 200 - y * 4)
                surf.set_at((x, y), (100 + random.randint(0, 30), 10, 10))
        random.seed()  # restore entropy
