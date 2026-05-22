"""Twisted America: Hunger — global constants."""

WIDTH = 1280
HEIGHT = 720
FPS = 60
TILE = 32

# --- Muted, desaturated palette ---
BLACK       = (8, 8, 10)
NEAR_BLACK  = (16, 16, 20)
DARK_GRAY   = (32, 32, 38)
GRAY        = (62, 62, 68)
LIGHT_GRAY  = (118, 118, 124)
BONE        = (190, 188, 180)
WHITE       = (210, 210, 215)
TEXT        = (188, 188, 192)
TEXT_DIM    = (128, 128, 134)
TEXT_BLOOD  = (160, 40, 40)
TEXT_WARN   = (170, 130, 60)

BLOOD_RED   = (110, 20, 20)
DULL_RED    = (140, 50, 50)
COAT_BROWN  = (72, 48, 32)
SKIN        = (175, 148, 128)
SNOW        = (175, 180, 188)
SNOW_DEEP   = (140, 148, 158)
ASPHALT     = (38, 36, 40)
ASPHALT_CRK = (28, 26, 30)
TREE_DARK   = (28, 38, 30)
TREE        = (38, 52, 38)
WOOD        = (52, 38, 28)
WOOD_DARK   = (32, 22, 16)
WINDOW      = (22, 28, 38)
ROOF        = (44, 32, 30)
HOSPITAL    = (60, 64, 72)
CHURCH      = (44, 42, 56)
TRAILER     = (72, 64, 56)
DEAD_GRASS  = (68, 60, 44)
SINKHOLE    = (12, 8, 14)

HUNGER_BAR  = (140, 30, 30)
HUNGER_BG   = (40, 14, 14)
HP_BAR      = (80, 120, 90)
HP_BG       = (28, 40, 32)
CORRUPT_BAR = (90, 40, 110)

# --- Game states ---
STATE_MENU       = "menu"
STATE_PLAYING    = "playing"
STATE_DIALOGUE   = "dialogue"
STATE_COMBAT     = "combat"
STATE_INVENTORY  = "inventory"
STATE_ENDING     = "ending"
STATE_GAME_OVER  = "game_over"
STATE_INTRO      = "intro"

# --- Hunger thresholds ---
HUNGER_NORMAL    = 25
HUNGER_UNEASE    = 50
HUNGER_WARPED    = 75
HUNGER_UNRAVEL   = 99

# --- Save path ---
SAVE_PATH = "save.json"
