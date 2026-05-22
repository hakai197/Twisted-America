"""Headless smoke test — walks through dialogue, combat, save/load.

Not part of the shipped game. Run with:
    python _smoketest.py
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
pygame.init()
pygame.display.set_mode((1280, 720))

import main
import dialogue_data
from save_system import save_game, load_game


def header(t):
    print("\n=== " + t + " ===")


def main_test():
    g = main.Game()
    g.start_new_game()
    g.begin_play()

    header("Dialogue: Henderson")
    tree = dialogue_data.get("henderson", g)
    d = main.Dialogue(tree, g)
    while not d.closed:
        node = d.current_node()
        if node and node.get("choices"):
            d.pick(0)
        else:
            d.advance()
    print("flags after henderson:", g.player.flags["talked_henderson"], "| has note:", "Old Man's Note" in g.player.key_items)

    header("Dialogue: Cory")
    d = main.Dialogue(dialogue_data.get("cory", g), g)
    while not d.closed:
        node = d.current_node()
        if node and node.get("choices"):
            d.pick(1)  # ask about the woods
        else:
            d.advance()
    print("has symbol:", "Cult Symbol" in g.player.key_items)

    header("Dialogue: Jared then deliver note")
    d = main.Dialogue(dialogue_data.get("jared", g), g)
    while not d.closed:
        node = d.current_node()
        if node and node.get("choices"):
            d.pick(0)
        else:
            d.advance()
    print("photo:", "Leah's Photo" in g.player.key_items, "talked:", g.player.flags["talked_jared"])
    # second visit — deliver note
    d = main.Dialogue(dialogue_data.get("jared", g), g)
    while not d.closed:
        node = d.current_node()
        if node and node.get("choices"):
            d.pick(0)
        else:
            d.advance()
    print("delivered note:", g.player.flags["delivered_note"], "henderson forgave:", g.player.flags["henderson_forgave"])

    header("Combat: Hollowed")
    g.start_combat("hollowed")
    safety = 60
    while g.combat and not g.combat.over and safety > 0:
        g.combat.act_fight()
        safety -= 1
    print("combat over:", g.combat.over if g.combat else "yes", "victory:", g.combat.victory if g.combat else "?")
    g.end_combat()

    header("Save / Load")
    g.player.hunger = 42
    g.player.add_corruption(15)
    save_game(g, path="_test_save.json")
    g2 = main.Game()
    g2.player = main.Player(0, 0)
    g2.zones = main.build_zones()
    g2.current_zone_key = "main_street"
    load_game(g2, path="_test_save.json")
    print("loaded hunger:", g2.player.hunger, "corruption:", g2.player.corruption, "flags talked_henderson:", g2.player.flags["talked_henderson"])
    os.remove("_test_save.json")

    header("Mother Ash: refuse")
    d = main.Dialogue(dialogue_data.get("mother_ash", g), g)
    while not d.closed:
        node = d.current_node()
        if node and node.get("choices"):
            d.pick(1)  # refuse
        else:
            d.advance()
    g.check_endings()
    print("ending state:", g.state, "ending:", g.ending)

    header("All smoke tests passed.")


if __name__ == "__main__":
    main_test()
