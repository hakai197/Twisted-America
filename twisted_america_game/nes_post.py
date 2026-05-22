"""NES-style post-process: ordered-Bayer dither helpers + palette quantize.

The render pipeline (in main.py) draws the world at WIDTH x HEIGHT, then
downsamples to RENDER_W x RENDER_H with nearest-neighbor sampling. Any
4x4 dither pattern drawn at world resolution becomes a 1x1 pattern in the
downsampled image, matching the NES PPU's per-pixel cadence.

All drawing helpers here operate at world resolution and align to a
PIXEL_SCALE-pixel grid so the downsample preserves them exactly.
"""

import pygame

from settings import PIXEL_SCALE, NES_PALETTE, RENDER_W, RENDER_H

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    np = None
    _HAS_NUMPY = False


# Bayer threshold matrix, normalized to 0..1. Used for ordered dither in
# effects code below. Falls back to a plain nested list when numpy is absent.
if _HAS_NUMPY:
    BAYER_4 = np.array(
        [
            [0, 8, 2, 10],
            [12, 4, 14, 6],
            [3, 11, 1, 9],
            [15, 7, 13, 5],
        ],
        dtype=np.float32,
    ) / 16.0
else:
    BAYER_4 = [
        [v / 16.0 for v in row]
        for row in (
            (0, 8, 2, 10),
            (12, 4, 14, 6),
            (3, 11, 1, 9),
            (15, 7, 13, 5),
        )
    ]


_PALETTE_LUT = None
_QUANTIZE_WARNED = False


def _build_palette_lut(palette):
    """Map every (r>>4, g>>4, b>>4) triple to its nearest palette color."""
    pal = np.array(palette, dtype=np.int32)
    coords = np.indices((16, 16, 16), dtype=np.int32).reshape(3, -1).T
    full = coords * 17  # promote 0..15 to 0..255
    diffs = full[:, None, :] - pal[None, :, :]
    dist2 = (diffs ** 2).sum(axis=2)
    idx = np.argmin(dist2, axis=1)
    return pal[idx].reshape(16, 16, 16, 3).astype(np.uint8)


def quantize(surf):
    """Snap every pixel of `surf` to its nearest NES palette entry.

    Requires numpy. If numpy is not installed, this is a no-op (the
    pipeline still pixelates via downsample+upscale, just without the
    limited-palette snap).
    """
    global _PALETTE_LUT, _QUANTIZE_WARNED
    if not _HAS_NUMPY:
        if not _QUANTIZE_WARNED:
            print("[nes_post] numpy not installed — palette quantize disabled. "
                  "Run `pip install numpy` for full NES palette snap.")
            _QUANTIZE_WARNED = True
        return
    if _PALETTE_LUT is None:
        _PALETTE_LUT = _build_palette_lut(NES_PALETTE)
    arr = pygame.surfarray.pixels3d(surf)
    high = arr >> 4
    arr[...] = _PALETTE_LUT[high[..., 0], high[..., 1], high[..., 2]]
    del arr


def _bayer(y, x):
    """Threshold lookup that works with numpy 2D array or list-of-lists."""
    return BAYER_4[y & 3][x & 3]


def dither_fill(surf, rect, color, alpha):
    """Bayer-dither a colored block over `rect` with apparent `alpha` (0..255).

    Operates at PIXEL_SCALE granularity so each Bayer cell survives the
    nearest-neighbor downsample to RENDER_W x RENDER_H as a single pixel.
    """
    if alpha <= 0:
        return
    if alpha >= 255:
        pygame.draw.rect(surf, color, rect)
        return
    bx, by, bw, bh = rect
    ps = PIXEL_SCALE
    threshold = alpha / 255.0
    sx = bx // ps
    sy = by // ps
    ex = (bx + bw) // ps
    ey = (by + bh) // ps
    for cy in range(sy, ey):
        my = cy & 3
        py = cy * ps
        for cx in range(sx, ex):
            if BAYER_4[my][cx & 3] < threshold:
                pygame.draw.rect(surf, color, (cx * ps, py, ps, ps))


def dither_mask_surface(width, height, alpha, color=(0, 0, 0)):
    """Return a pre-baked dithered alpha-fill surface at world resolution.

    Use when you need to blit the same dithered fill many times per frame.
    The result is SRCALPHA; opaque cells are `color`, off cells are clear.
    """
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    if alpha <= 0:
        return surf
    if alpha >= 255:
        surf.fill((*color, 255))
        return surf
    ps = PIXEL_SCALE
    threshold = alpha / 255.0
    cells_x = width // ps
    cells_y = height // ps
    for cy in range(cells_y):
        my = cy & 3
        py = cy * ps
        for cx in range(cells_x):
            if BAYER_4[my][cx & 3] < threshold:
                pygame.draw.rect(surf, (*color, 255), (cx * ps, py, ps, ps))
    return surf


def dither_radial_dark(surf, cx, cy, inner_r, outer_r, max_alpha):
    """Dithered radial darkness — clear at `inner_r`, alpha `max_alpha` at `outer_r`.

    Operates on `surf` directly (which should have SRCALPHA). Used by lighting
    to punch a player-centered hole in the darkness overlay without needing
    a pre-built smooth-gradient disk.
    """
    if outer_r <= inner_r or max_alpha <= 0:
        return
    ps = PIXEL_SCALE
    w, h = surf.get_size()
    x0 = max(0, (cx - outer_r) // ps)
    y0 = max(0, (cy - outer_r) // ps)
    x1 = min(w // ps, (cx + outer_r) // ps + 1)
    y1 = min(h // ps, (cy + outer_r) // ps + 1)
    span = max(1, outer_r - inner_r)
    for gy in range(y0, y1):
        py = gy * ps
        dy = py + ps // 2 - cy
        my = gy & 3
        for gx in range(x0, x1):
            px = gx * ps
            dx = px + ps // 2 - cx
            dist = (dx * dx + dy * dy) ** 0.5
            if dist <= inner_r:
                continue
            t = min(1.0, (dist - inner_r) / span)
            if BAYER_4[my][gx & 3] < t:
                pygame.draw.rect(surf, (0, 0, 0, max_alpha), (px, py, ps, ps))
