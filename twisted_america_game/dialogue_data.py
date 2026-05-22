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
DIALOGUES = {
    "henderson": henderson,
    "jared": jared,
    "leah": leah,
    "cory": cory,
    "dealer": dealer,
    "mother_ash": mother_ash,
}


def get(key, game):
    if key not in DIALOGUES:
        return {"start": {"speaker": "", "text": "...", "next": None}}
    return DIALOGUES[key](game)
