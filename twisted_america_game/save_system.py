"""JSON save / load.

Stores a single slot in `save.json` next to main.py.
"""

import json
import os
from settings import SAVE_PATH


def save_game(game, path=SAVE_PATH):
    p = game.player
    data = {
        "version": 1,
        "zone": game.current_zone_key,
        "player": {
            "x": p.rect.x,
            "y": p.rect.y,
            "hp": p.hp,
            "hunger": p.hunger,
            "corruption": p.corruption,
            "inventory": p.inventory,
            "key_items": sorted(p.key_items),
            "flags": p.flags,
        },
    }
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except OSError:
        return False


def has_save(path=SAVE_PATH):
    return os.path.exists(path)


def load_game(game, path=SAVE_PATH):
    if not os.path.exists(path):
        return False
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return False

    p = game.player
    pd = data.get("player", {})
    p.rect.x = pd.get("x", p.rect.x)
    p.rect.y = pd.get("y", p.rect.y)
    p.hp = pd.get("hp", p.hp)
    p.hunger = pd.get("hunger", 0)
    p.corruption = pd.get("corruption", 0)
    p.inventory = pd.get("inventory", p.inventory)
    p.key_items = set(pd.get("key_items", []))
    saved_flags = pd.get("flags", {})
    # merge — keep new flags that didn't exist when save was made
    for k, v in saved_flags.items():
        if k in p.flags:
            p.flags[k] = v
    game.current_zone_key = data.get("zone", game.current_zone_key)
    return True
