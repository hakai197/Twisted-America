"""Drifting particles and fog mist.

One Atmosphere instance per game. It rebuilds its state when the player
enters a new zone, reading two optional fields off the zone:

    zone.particle_kind: "snow" | "ash" | "dust" | None
    zone.fog_density:   0.0 ... 1.0

Cost: ~80 particle position updates + ~12 fog-blob blits per frame on the
play surface. Cheaper than the previous static `set_at` snow loop.
"""

import math
import random
import pygame
from settings import WIDTH, HEIGHT, PIXEL_SCALE
from nes_post import BAYER_4


PLAY_H = HEIGHT - 100


# Per-kind visual + motion presets.
# `size` is in world pixels and is snapped up to PIXEL_SCALE so particles
# survive the downsample to 320x240 as solid 1-pixel specks.
_PRESETS = {
    "snow": {
        "color": (175, 180, 188),
        "vx_range": (-8, 8),
        "vy_range": (10, 26),
        "size": PIXEL_SCALE,
        "count": 90,
        "wobble": 0.4,
    },
    "ash": {
        "color": (90, 86, 82),
        "vx_range": (-14, 6),
        "vy_range": (14, 30),
        "size": PIXEL_SCALE,
        "count": 80,
        "wobble": 0.9,
    },
    "dust": {
        "color": (110, 100, 92),
        "vx_range": (-4, 4),
        "vy_range": (-3, 8),
        "size": PIXEL_SCALE,
        "count": 60,
        "wobble": 1.4,
    },
}


def _build_fog_blob(radius=180):
    """Bayer-dithered radial fog blob — densest near center, scattered at edge.

    NES PPUs couldn't alpha-blend; horror games (Sweet Home, Uninvited)
    faked translucent fog with ordered dither. Each lit cell here is a
    PIXEL_SCALE-sized block so it survives the downsample as one pixel.
    """
    ps = PIXEL_SCALE
    # Round radius to PIXEL_SCALE so the blob aligns with the dither grid.
    radius = (radius // ps) * ps
    size = radius * 2
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    color = (180, 182, 188, 255)
    cells = size // ps
    cx_world = cy_world = radius
    for cy in range(cells):
        py = cy * ps
        my = cy & 3
        dy = py + ps // 2 - cy_world
        for cx in range(cells):
            px = cx * ps
            dx = px + ps // 2 - cx_world
            dist = math.hypot(dx, dy)
            if dist >= radius:
                continue
            # density: ~32% at the center, falling off as a soft curve.
            density = (1.0 - dist / radius) ** 1.6 * 0.32
            if BAYER_4[my][cx & 3] < density:
                pygame.draw.rect(s, color, (px, py, ps, ps))
    return s


class Atmosphere:
    def __init__(self):
        self._zone_key = None
        self._kind = None
        self._particles = []          # [x, y, vx, vy]
        self._t = 0.0
        self._fog_blob = _build_fog_blob(180)
        self._fog_blobs = []          # [x, y, vx, drift_phase]
        self._fog_density = 0.0

    def setup_zone(self, zone):
        if self._zone_key == zone.key:
            return  # already initialized for this zone
        self._zone_key = zone.key
        self._kind = getattr(zone, "particle_kind", "snow")
        self._fog_density = max(0.0, min(1.0, getattr(zone, "fog_density", 0.0)))

        self._particles = []
        if self._kind in _PRESETS:
            preset = _PRESETS[self._kind]
            for _ in range(preset["count"]):
                self._particles.append([
                    random.uniform(0, WIDTH),
                    random.uniform(0, PLAY_H),
                    random.uniform(*preset["vx_range"]),
                    random.uniform(*preset["vy_range"]),
                ])

        self._fog_blobs = []
        if self._fog_density > 0:
            count = int(4 + self._fog_density * 12)
            blob_w = self._fog_blob.get_width()
            for _ in range(count):
                self._fog_blobs.append([
                    random.uniform(-blob_w, WIDTH + blob_w),
                    random.uniform(-blob_w // 2, PLAY_H - blob_w // 4),
                    random.uniform(6, 20),
                    random.uniform(0, math.pi * 2),
                ])

    def update(self, dt):
        self._t += dt

        if self._kind in _PRESETS:
            preset = _PRESETS[self._kind]
            wobble = preset["wobble"]
            for p in self._particles:
                p[0] += p[2] * dt + math.sin(self._t * 1.2 + p[1] * 0.01) * wobble
                p[1] += p[3] * dt
                if p[1] > PLAY_H:
                    p[1] = -2
                    p[0] = random.uniform(0, WIDTH)
                if p[0] < -8:
                    p[0] = WIDTH + 4
                elif p[0] > WIDTH + 8:
                    p[0] = -4

        if self._fog_blobs:
            blob_w = self._fog_blob.get_width()
            for b in self._fog_blobs:
                b[0] += b[2] * dt
                # gentle vertical wobble
                b[3] += dt * 0.6
                if b[0] - blob_w > WIDTH:
                    b[0] = -blob_w
                    b[1] = random.uniform(-blob_w // 2, PLAY_H - blob_w // 4)

    def draw_particles(self, surf):
        if not self._kind or self._kind not in _PRESETS:
            return
        preset = _PRESETS[self._kind]
        color = preset["color"]
        size = preset["size"]
        ps = PIXEL_SCALE
        # Snap each particle to the pixel grid so it survives the downsample
        # as a solid block. Drifting still updates floating-point position;
        # only the rendered rectangle is grid-aligned.
        for p in self._particles:
            x = int(p[0]) // ps * ps
            y = int(p[1]) // ps * ps
            pygame.draw.rect(surf, color, (x, y, size, size))

    def draw_fog(self, surf):
        if not self._fog_blobs:
            return
        blob = self._fog_blob
        bw = blob.get_width()
        bh = blob.get_height()
        half_w = bw // 2
        half_h = bh // 2
        for b in self._fog_blobs:
            wobble_y = math.sin(b[3]) * 6
            surf.blit(blob, (int(b[0] - half_w), int(b[1] - half_h + wobble_y)))
