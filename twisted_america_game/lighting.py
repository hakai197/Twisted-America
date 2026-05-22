"""Darkness-radius lighting + flickering lamp pools.

Two systems on one surface:

  - Darkness overlay: dark layer over the play area with a soft circular
    hole centered on the player. Hunger above 50 tightens the hole.
  - Lamp pools: small additive warm-light disks at static positions, with
    per-lamp flicker. Drawn on top of the darkness so they brighten dark
    areas, never the player's lit region (which is already cleared).
"""

import math
import pygame
from settings import WIDTH, HEIGHT


PLAY_H = HEIGHT - 100


class Lighting:
    def __init__(self):
        self._overlay = pygame.Surface((WIDTH, PLAY_H), pygame.SRCALPHA)
        self._disks = {}  # (radius, dark_alpha) -> Surface

    def _disk(self, radius, dark_alpha):
        key = (radius, dark_alpha)
        d = self._disks.get(key)
        if d is not None:
            return d
        size = radius * 2 + 4
        d = pygame.Surface((size, size), pygame.SRCALPHA)
        steps = 48
        cx = cy = size // 2
        for i in range(steps, 0, -1):
            r = max(1, int(radius * (i / steps)))
            a = int(dark_alpha * (i / steps) ** 1.6)
            if a <= 0:
                continue
            pygame.draw.circle(d, (0, 0, 0, a), (cx, cy), r)
        self._disks[key] = d
        return d

    def draw(self, screen, player_rect, base_radius, hunger=0, dark_alpha=205):
        """Darken the play area with a soft hole centered on the player.

        `base_radius` is the zone's nominal light radius. Hunger above 50
        tightens the radius progressively, up to ~40% smaller at 100.
        """
        if base_radius is None or base_radius <= 0:
            return
        shrink = 1.0
        if hunger > 50:
            shrink = max(0.6, 1.0 - (hunger - 50) / 125.0)
        radius = max(40, int(base_radius * shrink))

        disk = self._disk(radius, dark_alpha)
        self._overlay.fill((0, 0, 0, dark_alpha))
        dx = player_rect.centerx - disk.get_width() // 2
        dy = player_rect.centery - disk.get_height() // 2
        self._overlay.blit(disk, (dx, dy), special_flags=pygame.BLEND_RGBA_SUB)
        screen.blit(self._overlay, (0, 0))

    def draw_lamps(self, screen, lamps, t):
        """Additive warm pools at static lamp positions with per-lamp flicker.

        Each lamp is a tuple: (x, y, radius, (r, g, b)).
        """
        if not lamps:
            return
        for (lx, ly, radius, color) in lamps:
            # Smooth oscillation + occasional hard dip — looks like a bad bulb.
            flicker = 0.78 + 0.22 * math.sin(t * 6.0 + lx * 0.013 + ly * 0.017)
            tick = int(t * 14 + lx * 0.7 + ly * 0.3)
            if tick % 71 == 0:
                flicker *= 0.45
            elif tick % 53 == 0:
                flicker *= 0.7
            r0 = int(color[0] * flicker)
            g0 = int(color[1] * flicker)
            b0 = int(color[2] * flicker)

            size = radius * 2 + 4
            disk = pygame.Surface((size, size), pygame.SRCALPHA)
            cx = cy = size // 2
            # Pre-multiplied additive: outer rings have near-zero RGB so the
            # BLEND_RGB_ADD blit is invisible outside the glow.
            steps = 18
            for i in range(steps, 0, -1):
                ring_r = max(1, int(radius * (i / steps)))
                curve = (i / steps) ** 2.0
                rgb = (int(r0 * curve), int(g0 * curve), int(b0 * curve))
                pygame.draw.circle(disk, (*rgb, 255), (cx, cy), ring_r)
            screen.blit(disk, (int(lx - cx), int(ly - cy)),
                        special_flags=pygame.BLEND_RGB_ADD)
