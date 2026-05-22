"""All dialogue trees.

Format:
    node_key -> {
        "speaker": str,
        "text": str,
        "choices": [(label, next_key_or_None, effect_fn_or_None), ...]   (optional)
        "next": next_key_or_None     (used when 'choices' is absent)
        "effect": fn(game)            (called once on entry, optional)
    }

A 'next' of None ends the dialogue.
Effect functions receive the Game instance.
"""


def _give(game, item_name, message=None):
    game.player.key_items.add(item_name)
    game.show_message(message or f"Received: {item_name}")


def _consume_item(game, name):
    if game.player.inventory.get(name, 0) > 0:
        game.player.inventory[name] -= 1
        return True
    return False


# ---------------------------------------------------------------- HENDERSON
def henderson(game):
    p = game.player
    if p.flags["henderson_forgave"]:
        return {
            "start": {
                "speaker": "Old Man Henderson",
                "text": "He came by. Sat on my porch. Said nothing for an hour. Then he cried.\nThat's enough. That's all I wanted.",
                "next": "1",
            },
            "1": {
                "speaker": "Old Man Henderson",
                "text": "You did a kind thing, doctor. Kindness is rare in Beckley.\nGo on, then. Finish what you came for.",
                "next": None,
            },
        }
    if p.flags["talked_henderson"]:
        return {
            "start": {
                "speaker": "Old Man Henderson",
                "text": "Find the boy. Give him the note. That's all I'm asking.",
                "next": None,
            }
        }
    return {
        "start": {
            "speaker": "Old Man Henderson",
            "text": "You're the doctor from up north. Heard you'd come.\nDon't stand in the door. Cold gets in.",
            "next": "1",
        },
        "1": {
            "speaker": "Old Man Henderson",
            "text": "Two of them broke in last March. One held me down. The other took\nthe hand. Like he was breaking kindling.",
            "next": "2",
        },
        "2": {
            "speaker": "Old Man Henderson",
            "text": "I saw his face. Jared Blake. Used to mow my lawn before the pills.\nHe's at the hospital now. They say he overdosed.",
            "choices": [
                ("Why tell me?", "why", None),
                ("Do you want him jailed?", "jail", None),
            ],
        },
        "why": {
            "speaker": "Old Man Henderson",
            "text": "Because you're the only outsider in fifty miles. Town won't touch him.\nTown's already touched him too much.",
            "next": "give",
        },
        "jail": {
            "speaker": "Old Man Henderson",
            "text": "Jail. Forgiveness. I don't know anymore. Take this note.\nIf you find him breathing — give it to him. Then he decides.",
            "next": "give",
        },
        "give": {
            "speaker": "Old Man Henderson",
            "text": "It says I forgive him. I wrote it last night. Hands shook the whole time.\nMaybe it's true. Maybe it isn't. Either way.",
            "effect": lambda g: (
                _give(g, "Old Man's Note", "Received: Old Man's Note"),
                g.player.flags.update({"talked_henderson": True}),
            ),
            "next": None,
        },
    }


# ---------------------------------------------------------------- JARED
def jared(game):
    p = game.player
    if p.flags["delivered_note"]:
        return {
            "start": {
                "speaker": "Jared Blake",
                "text": "I read it. He says he forgives me. I don't believe him.\nBut I'm going to walk to his house. I'm going to sit on his porch.",
                "next": "1",
            },
            "1": {
                "speaker": "Jared Blake",
                "text": "If he tells me to leave I'll leave. If he lets me stay\nI'll stay until the snow melts.\nThank you, doctor.",
                "effect": lambda g: g.player.flags.update({"reconciled": True}),
                "next": None,
            },
        }
    if p.flags["talked_jared"]:
        if "Old Man's Note" in p.key_items:
            return {
                "start": {
                    "speaker": "Jared Blake",
                    "text": "You came back. With paper in your hand.",
                    "choices": [
                        ("Give him the note.", "deliver", None),
                        ("Not yet.", None, None),
                    ],
                },
                "deliver": {
                    "speaker": "Jared Blake",
                    "text": "...He wrote this? He wrote this for me?",
                    "effect": lambda g: (
                        g.player.flags.update({"delivered_note": True, "henderson_forgave": True}),
                        g.player.add_hunger(-8),
                        g.show_message("Hunger -8. The note is gone."),
                        g.player.key_items.discard("Old Man's Note"),
                    ),
                    "next": "deliver2",
                },
                "deliver2": {
                    "speaker": "Jared Blake",
                    "text": "(He folds the paper. He folds it again. Tucks it in his shirt\nover his heart, like a child hiding a stone.)",
                    "next": None,
                },
            }
        return {
            "start": {
                "speaker": "Jared Blake",
                "text": "He hates me. Doesn't he. He should.",
                "next": None,
            }
        }
    return {
        "start": {
            "speaker": "NARRATION",
            "text": "The boy lies in a hospital bed. The IV beeps. His eyes are open\nbut he is looking at something behind your shoulder.",
            "next": "1",
        },
        "1": {
            "speaker": "Jared Blake",
            "text": "...You're not from here.",
            "next": "2",
        },
        "2": {
            "speaker": "Jared Blake",
            "text": "Don't lie to me. Nobody from here sits with me. Not since.\nMy mother won't come. My sister won't come.",
            "choices": [
                ("I heard you hurt someone.", "hurt", None),
                ("I came to listen.", "listen", None),
            ],
        },
        "hurt": {
            "speaker": "Jared Blake",
            "text": "I broke an old man's hand. Cory held him. I broke it. For pills.\nThat's what I am now. Say it.",
            "next": "core",
        },
        "listen": {
            "speaker": "Jared Blake",
            "text": "Nobody listens. They watch. They wait to see which way I tip.",
            "next": "core",
        },
        "core": {
            "speaker": "Jared Blake",
            "text": "Leah used to come. Before. She left me a photograph in my locker\nthe day before. I don't know if she meant it as goodbye.\nIt's in my coat pocket. The nurses won't touch it.",
            "next": "take",
        },
        "take": {
            "speaker": "NARRATION",
            "text": "You take the photograph from his coat. He doesn't stop you.",
            "effect": lambda g: (
                _give(g, "Leah's Photo", "Received: Leah's Photo"),
                g.player.flags.update({"talked_jared": True}),
            ),
            "next": None,
        },
    }


# ---------------------------------------------------------------- LEAH
def leah(game):
    p = game.player
    if p.flags["delivered_photo"]:
        return {
            "start": {
                "speaker": "Leah",
                "text": "He kept it. All this time. I thought he'd burned it.",
                "next": "1",
            },
            "1": {
                "speaker": "Leah",
                "text": "I'll see him. I owe him that much. I'll see him today.",
                "next": None,
            },
        }
    if p.flags["talked_leah"]:
        if "Leah's Photo" in p.key_items:
            return {
                "start": {
                    "speaker": "Leah",
                    "text": "You came back. You're holding something.",
                    "choices": [
                        ("Show her the photograph.", "show", None),
                        ("Not yet.", None, None),
                    ],
                },
                "show": {
                    "speaker": "Leah",
                    "text": "...Where did you get this. Where did — he kept it?",
                    "effect": lambda g: (
                        g.player.flags.update({"delivered_photo": True}),
                        g.player.add_hunger(-6),
                        g.show_message("Hunger -6. The photo is gone."),
                        g.player.key_items.discard("Leah's Photo"),
                    ),
                    "next": None,
                },
            }
        return {
            "start": {
                "speaker": "Leah",
                "text": "Dealer's in the trailer with the blue door. North end.\nGo if you have to. Don't say my name.",
                "next": None,
            }
        }
    return {
        "start": {
            "speaker": "Leah",
            "text": "What. What do you want.",
            "next": "1",
        },
        "1": {
            "speaker": "Leah",
            "text": "I haven't slept. I don't sleep anymore. Something keeps singing\nfrom the woods. You hear it too. I can see it on you.",
            "choices": [
                ("Where is the dealer?", "dealer", None),
                ("Who is singing?", "ash", None),
            ],
        },
        "dealer": {
            "speaker": "Leah",
            "text": "Blue door trailer, north end of the park. He moves around but\nhe's there now. He's always there at dusk.",
            "next": "warn",
        },
        "ash": {
            "speaker": "Leah",
            "text": "Mother Ash. That's what we called her when we were kids.\nThere's a hole in the woods. She lives down there now. Or she\nis the hole. I never could tell.",
            "next": "warn",
        },
        "warn": {
            "speaker": "Leah",
            "text": "Tell Jared — if you see him — tell him I'm sorry. That's all.\nGod, I'm so tired.",
            "effect": lambda g: g.player.flags.update({"talked_leah": True}),
            "next": None,
        },
    }


# ---------------------------------------------------------------- CORY
def cory(game):
    p = game.player
    if p.flags["talked_cory"]:
        return {
            "start": {
                "speaker": "Cory",
                "text": "Get out of the alley, lady. I told you what I know.",
                "next": None,
            }
        }
    return {
        "start": {
            "speaker": "Cory",
            "text": "You looking for me? You ain't looking for me.",
            "next": "1",
        },
        "1": {
            "speaker": "Cory",
            "text": "Whatever the old man told you, Jared swung first. He swung.\nI just held the door. I just held the door.",
            "choices": [
                ("You broke a man's hand.", "accuse", None),
                ("Tell me about the woods.", "woods", None),
            ],
        },
        "accuse": {
            "speaker": "Cory",
            "text": "I held the door. That's all. Write it down in your little notebook.\nWrite it: Cory held the door.",
            "next": "leave",
        },
        "woods": {
            "speaker": "Cory",
            "text": "Don't. Don't go out there. That ain't a place. That's a mouth.",
            "next": "give_symbol",
        },
        "give_symbol": {
            "speaker": "Cory",
            "text": "Here. Take this. Wear it if you go. Won't help. But take it.",
            "effect": lambda g: (
                _give(g, "Cult Symbol", "Received: Cult Symbol"),
                g.player.flags.update({"talked_cory": True}),
            ),
            "next": None,
        },
        "leave": {
            "speaker": "Cory",
            "text": "Go on. Go talk to the old man some more. Go.",
            "effect": lambda g: g.player.flags.update({"talked_cory": True}),
            "next": None,
        },
    }


# ---------------------------------------------------------------- DEALER
def dealer(game):
    p = game.player
    if p.flags["killed_dealer"]:
        return {"start": {"speaker": "NARRATION", "text": "There is nothing here but a stain on the carpet.", "next": None}}
    if p.flags["took_dealer_pills"]:
        return {
            "start": {
                "speaker": "The Dealer",
                "text": "You came back. Hungry?",
                "choices": [
                    ("No.", None, None),
                    ("Yes.", "more", lambda g: (g.player.add_hunger(-5), g.player.add_corruption(15), g.show_message("Hunger -5. Corruption +15."))),
                ],
            },
            "more": {
                "speaker": "The Dealer",
                "text": "Knew you'd be back. They all come back.",
                "next": None,
            },
        }
    return {
        "start": {
            "speaker": "The Dealer",
            "text": "Door's open, doc. I been expecting you.",
            "next": "1",
        },
        "1": {
            "speaker": "The Dealer",
            "text": "You want what I know? About the woods? About Ash?\nFine. But you take something with you when you leave.",
            "choices": [
                ("Take the pills.", "take", lambda g: (
                    g.player.inventory.__setitem__("Pill", g.player.inventory.get("Pill", 0) + 4),
                    g.player.add_corruption(10),
                    g.player.flags.update({"took_dealer_pills": True, "talked_dealer": True}),
                    g.show_message("Received: 4 Pills. Corruption +10."),
                )),
                ("Refuse.", "refuse", lambda g: g.player.flags.update({"talked_dealer": True})),
                ("Attack him.", "fight", lambda g: g.start_combat("dealer")),
            ],
        },
        "take": {
            "speaker": "The Dealer",
            "text": "Smart. Mother Ash don't make a sound until you're standing in her mouth.\nWear iron. Don't speak first. Don't eat what she offers.\nThat's all I got. Now get out.",
            "next": None,
        },
        "refuse": {
            "speaker": "The Dealer",
            "text": "Suit yourself. Then I don't say a word. Door's that way.",
            "next": None,
        },
        "fight": {
            "speaker": "NARRATION",
            "text": "He's already reaching for the knife on the table.",
            "next": None,
        },
    }


# ---------------------------------------------------------------- MOTHER ASH
def mother_ash(game):
    p = game.player
    if p.flags["fed_hunger"] or p.flags["refused_hunger"]:
        return {
            "start": {
                "speaker": "Mother Ash",
                "text": "You have already chosen, child. The sinkhole remembers.",
                "next": None,
            }
        }
    has_symbol = "Cult Symbol" in p.key_items
    intro = {
        "start": {
            "speaker": "NARRATION",
            "text": "The sinkhole opens wider than it should. The snow does not\nfall into it. The snow stops at the edge.",
            "next": "1",
        },
        "1": {
            "speaker": "Mother Ash",
            "text": "Maya. Daughter. You are bright with hunger. I have been\nlistening to your footsteps for three days.",
            "next": "2",
        },
        "2": {
            "speaker": "Mother Ash",
            "text": "I will offer what I always offer. Feed me, and the meter\nin your chest will quiet forever. You will not unravel.\nYou will be the next throat that speaks for me.",
            "next": "3" if has_symbol else "no_symbol",
        },
        "no_symbol": {
            "speaker": "Mother Ash",
            "text": "But you came empty-handed. You do not even carry the iron.\nThat is a sadness. Choose anyway.",
            "next": "3",
        },
        "3": {
            "speaker": "Mother Ash",
            "text": "Step forward and feed me. Or turn your back and unravel slowly.\nThese are the two doors. Choose.",
            "choices": [
                ("Step forward. Feed her.", "feed", lambda g: g.player.flags.update({"fed_hunger": True, "talked_mother_ash": True})),
                ("Turn your back.", "refuse", lambda g: g.player.flags.update({"refused_hunger": True, "talked_mother_ash": True})),
            ],
        },
        "feed": {
            "speaker": "Mother Ash",
            "text": "Good. Good. Open your mouth, daughter. Open your mouth.",
            "next": None,
        },
        "refuse": {
            "speaker": "NARRATION",
            "text": "You turn. The wind does not follow you. Behind you, something\nthat is not a voice begins to laugh, and then to weep, and then\nto stop entirely.",
            "next": None,
        },
    }
    return intro


# ---------------------------------------------------------------- DISPATCH
# ----------------------------------------------------------------- REVEREND
def _accept_prayer(game):
    game.player.flags["spoke_prayer"] = True
    game.trigger_game_over(
        "The chapel goes quiet. Your hands forget how to make a fist.\n"
        "Your voice forgets how to call for help.\n"
        "Peace, the Reverend says — from very far away. Peace."
    )


def _refuse_reverend(game):
    game.player.flags["refused_reverend"] = True
    # Defiance has a cost — but the door is still open.
    game.player.add_hunger(3)


def reverend(game):
    p = game.player

    if p.flags.get("spoke_prayer"):
        # Should never be reached (game ended), but keep a safe fallback.
        return {
            "start": {"speaker": "The Reverend", "text": "...", "next": None}
        }

    if p.flags.get("refused_reverend"):
        return {
            "start": {
                "speaker": "The Reverend",
                "text": "I knew you would not kneel. The Mother is patient.\n"
                        "Leave my chapel, doctor. Do not waste my breath again.",
                "next": None,
            },
        }

    return {
        "start": {
            "speaker": "The Reverend",
            "text": "You walked in unbidden. That alone is a sin she will forgive.\n"
                    "Kneel with me, doctor. The hour is late, and you are tired.",
            "choices": [
                ("Kneel.", "pray", None),
                ("Why are you still here?", "why", None),
                ("Leave.", None, None),
            ],
        },
        "why": {
            "speaker": "The Reverend",
            "text": "The flock went into the woods. I stayed.\n"
                    "Someone must say the words at the end.\n"
                    "The Mother taught me the words before you were born.",
            "next": "ask_pray",
        },
        "ask_pray": {
            "speaker": "The Reverend",
            "text": "Will you pray with me, doctor? It costs you nothing.",
            "choices": [
                ("Yes. Pray.", "pray", None),
                ("No.", None, _refuse_reverend),
            ],
        },
        "pray": {
            "speaker": "The Reverend",
            "text": "Close your eyes.\n\n"
                    "  Silence in Sin.\n"
                    "  Darkness hides the truth.\n"
                    "  Peace in Oblivion.",
            "next": "confirm",
        },
        "confirm": {
            "speaker": "The Reverend",
            "text": "Say it with me, now. Mean it.\nDo you accept?",
            "choices": [
                ("Yes. I accept.", None, _accept_prayer),
                ("No. Get out of my head.", None, _refuse_reverend),
            ],
        },
    }


# ----------------------------------------------------------------- HOLLIS
def _give_master_key(game):
    game.player.key_items.add("Master Key")
    game.show_message("Hollis slides a key under the door.")
    game.player.flags["got_master_key"] = True


def hollis(game):
    p = game.player
    if p.flags.get("got_master_key"):
        return {
            "start": {
                "speaker": "Deputy Hollis",
                "text": "(Through the door.) Keep it. I'm not coming out. The door stays locked.",
                "next": None,
            }
        }
    return {
        "start": {
            "speaker": "Deputy Hollis",
            "text": "(Through the door.) Go away. I'm not opening this.",
            "choices": [
                ("Deputy, it's Dr. Chen. I was sent.", "sent", None),
                ("How long have you been in there?", "duration", None),
                ("Leave him.", None, None),
            ],
        },
        "sent": {
            "speaker": "Deputy Hollis",
            "text": "(Through the door.) Sent by who? The sheriff? Sheriff hasn't been the sheriff for two weeks.",
            "next": "warn",
        },
        "duration": {
            "speaker": "Deputy Hollis",
            "text": "(Through the door.) Twelve days. Maybe thirteen. I lost count when the radio stopped.",
            "next": "warn",
        },
        "warn": {
            "speaker": "Deputy Hollis",
            "text": "(Through the door.) Listen. They walk at night. They don't blink.\n"
                    "If you have to be out there, you need a key. Evidence room. Top drawer.\n"
                    "I never went back for it.",
            "choices": [
                ("Slide it under. Please.", "give", _give_master_key),
                ("Keep it. I'll manage.", None, None),
            ],
        },
        "give": {
            "speaker": "Deputy Hollis",
            "text": "(Something metal scrapes the floor.)\nThat's the last favor I do anyone. Now go.",
            "next": None,
        },
    }


# ----------------------------------------------------------------- JANITOR
def _mark_janitor(game):
    game.player.flags["talked_janitor"] = True


def janitor(game):
    p = game.player
    if p.flags.get("talked_janitor"):
        return {
            "start": {
                "speaker": "The Janitor",
                "text": "(He sweeps the same patch of floor he was sweeping before.)\n"
                        "Should be done by recess. Recess is soon.",
                "next": None,
            }
        }
    return {
        "start": {
            "effect": _mark_janitor,
            "speaker": "The Janitor",
            "text": "Don't track snow in. The little ones are studying.",
            "choices": [
                ("There are no children here.", "denial", None),
                ("What are they studying?", "study", None),
                ("Leave.", None, None),
            ],
        },
        "denial": {
            "speaker": "The Janitor",
            "text": "(He looks at the empty desks. He looks at his broom.)\n"
                    "They'll be back. Recess is soon.",
            "next": "warn",
        },
        "study": {
            "speaker": "The Janitor",
            "text": "Their letters. They're learning their letters.\n"
                    "(On the chalkboard: SHE IS COMING. SHE IS COMING. SHE IS COMING.)",
            "next": "warn",
        },
        "warn": {
            "speaker": "The Janitor",
            "text": "You should go, doctor. Recess is soon.\nThey don't like being interrupted.",
            "next": None,
        },
    }


# ----------------------------------------------------------------- MOTEL GUEST
def _mark_motel_guest(game):
    game.player.flags["talked_motel_guest"] = True


def motel_guest(game):
    p = game.player
    if p.flags.get("talked_motel_guest"):
        return {
            "start": {
                "speaker": "The Guest",
                "text": "(She stands in the doorway. She is not coming out.)\n"
                        "The walls are dripping. I think they want me to stay.",
                "next": None,
            }
        }
    return {
        "start": {
            "effect": _mark_motel_guest,
            "speaker": "The Guest",
            "text": "Don't come in. The walls are not what they look like.",
            "choices": [
                ("How long have you been here?", "duration", None),
                ("What's wrong with the walls?", "walls", None),
                ("You should leave with me.", "leave_with_me", None),
            ],
        },
        "duration": {
            "speaker": "The Guest",
            "text": "I checked in on a Tuesday. I don't know which Tuesday.\nThe clerk took my plates.",
            "next": "henderson",
        },
        "walls": {
            "speaker": "The Guest",
            "text": "They bleed. Just a little, around the edges of the paper.\n"
                    "At night the room is smaller. In the morning it isn't.",
            "next": "henderson",
        },
        "leave_with_me": {
            "speaker": "The Guest",
            "text": "(She does not move.) I tried. I can't make my feet go past the doorway.\n"
                    "Go. You can still go.",
            "next": "henderson",
        },
        "henderson": {
            "speaker": "The Guest",
            "text": "If you see Henderson, tell him Amy says she's sorry.\nHe'll know what for.",
            "next": None,
        },
    }


# ----------------------------------------------------------------- MINER
def _mark_miner(game):
    game.player.flags["talked_miner"] = True


def miner(game):
    p = game.player
    if p.flags.get("talked_miner"):
        return {
            "start": {
                "speaker": "The Miner",
                "text": "(His lips do not move when he speaks. The voice comes from somewhere inside the mine.)\n"
                        "Go home, doctor.",
                "next": None,
            }
        }
    return {
        "start": {
            "effect": _mark_miner,
            "speaker": "The Miner",
            "text": "(His lips move. The voice comes from somewhere else.)\n"
                    "You shouldn't be here, doctor. The shift ended a long time ago.",
            "choices": [
                ("What did you find down there?", "found", None),
                ("Why are you still standing here?", "still", None),
                ("Leave.", None, None),
            ],
        },
        "found": {
            "speaker": "The Miner",
            "text": "(His lips form different words than what you hear.)\n"
                    "We found a room. A round room. She was waiting in it.\n"
                    "We didn't make the room. The room made us.",
            "next": "warn",
        },
        "still": {
            "speaker": "The Miner",
            "text": "(The voice answers from below. His mouth shapes 'help'.)\n"
                    "I'm not standing. I'm being held. There's a difference, doctor.",
            "next": "warn",
        },
        "warn": {
            "speaker": "The Miner",
            "text": "(His lips: please go.)\n"
                    "The sinkhole in the woods is the same room. She built it twice.\n"
                    "Go that way if you must — but not down here.",
            "next": None,
        },
    }


DIALOGUES = {
    "henderson": henderson,
    "jared": jared,
    "leah": leah,
    "cory": cory,
    "dealer": dealer,
    "mother_ash": mother_ash,
    "reverend": reverend,
    "hollis": hollis,
    "janitor": janitor,
    "motel_guest": motel_guest,
    "miner": miner,
}


def get(key, game):
    if key not in DIALOGUES:
        return {"start": {"speaker": "", "text": "...", "next": None}}
    return DIALOGUES[key](game)
