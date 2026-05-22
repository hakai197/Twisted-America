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

import math
import random
import pygame
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


# Peripheral shadow shape presets — (anchor, w, h, draw_fn)
# anchor: "L"/"R"/"T"/"B" — which edge the shape sits flush against.
def _shape_vertical_smear(surf, x, y, w, h, alpha):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    s.fill((0, 0, 0, alpha))
    # roughen the inner edge
    for yy in range(0, h, 4):
        cut = random.randint(0, w // 3)
        pygame.draw.rect(s, (0, 0, 0, 0), (w - cut, yy, cut, 4),
                         special_flags=pygame.BLEND_RGBA_SUB)
    surf.blit(s, (x, y))


def _shape_half_figure(surf, x, y, w, h, alpha):
    # bottom-anchored elongated silhouette
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    body = pygame.Rect(2, h - 32, w - 4, 32)
    pygame.draw.rect(s, (0, 0, 0, alpha), body)
    head = pygame.Rect(w // 2 - 4, h - 46, 8, 10)
    pygame.draw.rect(s, (0, 0, 0, alpha), head)
    surf.blit(s, (x, y))


_PERIPHERAL_SHAPES = (_shape_vertical_smear, _shape_half_figure)


class HungerFx:
    def __init__(self):
        self.time = 0.0
        self.flicker_timer = 0.0
        self.whisper_timer = random.uniform(6, 12)
        self.active_whisper = None
        self.active_whisper_time = 0.0
        self._tile_overlay = pygame.Surface((WIDTH, HEIGHT - 100), pygame.SRCALPHA)
        self._heartbeat = pygame.Surface((WIDTH, HEIGHT - 100), pygame.SRCALPHA)
        self._ab_left = pygame.Surface((28, HEIGHT - 100), pygame.SRCALPHA)
        self._ab_right = pygame.Surface((28, HEIGHT - 100), pygame.SRCALPHA)

        # peripheral shadow state
        self._shadow_cooldown = random.uniform(8, 16)
        self._shadow_visible_t = 0.0
        self._shadow_total = 0.0
        self._shadow_rect = None
        self._shadow_draw = None

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

        # peripheral shadow cadence
        if self._shadow_visible_t > 0:
            self._shadow_visible_t -= dt
        elif hunger >= 60:
            self._shadow_cooldown -= dt
            if self._shadow_cooldown <= 0:
                self._spawn_peripheral_shadow(hunger)

    def _spawn_peripheral_shadow(self, hunger):
        # frequency: every ~8s at hunger 60 → ~1.5s at hunger 100
        scale = max(0.0, (hunger - 60) / 40.0)
        mean = 8.0 - scale * 6.0
        self._shadow_cooldown = random.uniform(mean * 0.6, mean * 1.4)
        # pick edge + shape
        edge = random.choice(("L", "R"))
        shape_fn = random.choice(_PERIPHERAL_SHAPES)
        h = random.randint(60, 220)
        w = random.randint(28, 70)
        if edge == "L":
            x = 0
        else:
            x = WIDTH - w
        y = random.randint(40, HEIGHT - 200 - h)
        self._shadow_rect = pygame.Rect(x, y, w, h)
        self._shadow_draw = shape_fn
        # visible time short — these are flickers, not lingering ghosts
        self._shadow_total = random.uniform(0.18, 0.45)
        self._shadow_visible_t = self._shadow_total

    def draw_overlay(self, surf, hunger, font):
        """Painted on top of the play area each frame."""
        h = hunger

        # Heartbeat pulse — starts at Hunger 25, quickens with the meter.
        self._draw_heartbeat(surf, h)

        if h <= 25:
            return

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

        # Chromatic aberration bands at the screen edges (cheap fake)
        if h > 60:
            self._draw_aberration_edges(surf, h)

        # Peripheral shadow flicker
        if self._shadow_visible_t > 0:
            self._draw_peripheral_shadow(surf)

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
            jx = random.randint(-2, 2)
            jy = random.randint(-2, 2)
            wx = random.randint(80, WIDTH - 200)
            wy = random.randint(40, HEIGHT - 200)
            surf.blit(s, (wx + jx, wy + jy))

    # ---------------- heartbeat ----------------
    def _draw_heartbeat(self, surf, hunger):
        if hunger < 25:
            return
        # period: 1.4s at hunger 25, 0.55s at hunger 100
        period = max(0.55, 1.4 - (hunger - 25) / 100.0)
        phase = (self.time % period) / period * math.pi * 2
        # double-thump shape: dominant beat + smaller second beat
        pulse = 0.5 + 0.5 * math.sin(phase)
        pulse += 0.25 * max(0.0, math.sin(phase - 0.6))
        # intensity scales with hunger
        base = 6 + (hunger - 25) * 0.32
        a = int(base * min(1.4, pulse))
        if a <= 0:
            return
        self._heartbeat.fill((0, 0, 0, a))
        surf.blit(self._heartbeat, (0, 0))

    # ---------------- chromatic aberration ----------------
    def _draw_aberration_edges(self, surf, hunger):
        intensity = min(72, int((hunger - 60) * 2.0))
        if intensity <= 0:
            return
        self._ab_left.fill((180, 20, 20, intensity))
        self._ab_right.fill((40, 40, 200, int(intensity * 0.8)))
        surf.blit(self._ab_left, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        surf.blit(self._ab_right, (WIDTH - self._ab_right.get_width(), 0),
                  special_flags=pygame.BLEND_RGB_ADD)

    # ---------------- peripheral shadow ----------------
    def _draw_peripheral_shadow(self, surf):
        if not self._shadow_rect or not self._shadow_draw:
            return
        # ease in / ease out: peak alpha at middle of life
        if self._shadow_total <= 0:
            return
        t_norm = self._shadow_visible_t / self._shadow_total
        env = 1.0 - abs(2 * t_norm - 1)  # triangle
        alpha = int(220 * env)
        if alpha <= 0:
            return
        r = self._shadow_rect
        self._shadow_draw(surf, r.x, r.y, r.w, r.h, alpha)

    def _draw_vignette(self, surf, alpha):
        # cheap vignette: four darkening edges
        s = pygame.Surface((WIDTH, HEIGHT - 100), pygame.SRCALPHA)
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
