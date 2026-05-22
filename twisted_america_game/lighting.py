"""Darkness-radius lighting.

Composites a play-area-sized dark overlay each frame, then subtracts a
precomputed soft circular disk centered on the player. No raycasting,
no shadow casters — just a tightening dark vignette that follows Maya.

Cost: one fill + one subtractive blit + one normal blit per frame on a
1280x620 SRCALPHA surface. ~1ms total on integrated graphics.
"""

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
