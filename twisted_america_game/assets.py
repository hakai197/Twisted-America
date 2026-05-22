"""Asset loader.

Walks `assets/` once at startup and caches every PNG it finds. Missing
assets return `None` so every draw site can fall back to a procedural
silhouette. The game is playable with zero PNGs — assets are additive.

Folder layout (under twisted_america_game/assets/):
    sprites/      characters, enemies, the player
    decorations/  world props (trees, houses, sinkhole, ...)
    overlays/     full-screen textures (paper, grain, fog, ...)

Animation: a stem suffixed with `_0`, `_1`, ... groups into a frame list.
A bare `<key>.png` is a single-frame sprite. See assets/MANIFEST.md.
"""

import os
import re
import pygame


_SLUG_RE = re.compile(r"[^a-z0-9]+")
_FRAME_RE = re.compile(r"^(?P<stem>.*?)_(?P<idx>\d+)$")


def slug(name):
    return _SLUG_RE.sub("_", name.lower()).strip("_")


class Assets:
    def __init__(self, base_dir):
        self.base = base_dir
        self._cache = {}        # key -> list[Surface]
        self._missing_logged = set()

    def load_all(self):
        if not os.path.isdir(self.base):
            return
        for sub in ("sprites", "decorations", "overlays"):
            d = os.path.join(self.base, sub)
            if not os.path.isdir(d):
                continue
            grouped = {}  # key -> list[(idx, path)]
            for fname in os.listdir(d):
                if not fname.lower().endswith(".png"):
                    continue
                stem = fname[:-4].lower()
                m = _FRAME_RE.match(stem)
                if m:
                    key, idx = m.group("stem"), int(m.group("idx"))
                else:
                    key, idx = stem, 0
                grouped.setdefault(key, []).append((idx, os.path.join(d, fname)))
            for key, items in grouped.items():
                items.sort()
                surfs = []
                for _, path in items:
                    try:
                        surfs.append(pygame.image.load(path).convert_alpha())
                    except pygame.error as e:
                        print(f"[assets] failed to load {path}: {e}")
                if surfs:
                    self._cache[key] = surfs

    def get(self, key, frame=0):
        frames = self._cache.get(key)
        if not frames:
            return None
        return frames[frame % len(frames)]

    def has(self, key):
        return key in self._cache

    def frame_count(self, key):
        return len(self._cache.get(key, ()))


_ASSETS = None


def init(base_dir):
    global _ASSETS
    _ASSETS = Assets(base_dir)
    _ASSETS.load_all()
    return _ASSETS


def sprite(key, frame=0):
    if _ASSETS is None:
        return None
    return _ASSETS.get(key, frame)


def frame_count(key):
    if _ASSETS is None:
        return 0
    return _ASSETS.frame_count(key)
