"""Layout, timing, palette, block font and sprite art for Park Hopper."""

FPS = 30
TICK = 1.0 / FPS

# ---------------------------------------------------------------- screen layout
VIEW_COLS = 80
HUD_ROWS = 2
PLAY_ROWS = 19
MSG_ROWS = 3
VIEW_ROWS = HUD_ROWS + PLAY_ROWS + MSG_ROWS        # 24 terminal rows
PLAY_TOP = HUD_ROWS                                # first play row (2)
MSG_TOP = PLAY_TOP + PLAY_ROWS                     # first message row (21)
GROUND_Y = 15          # play row where feet stand; rows 16..18 are pavement
WATER_Y = GROUND_Y + 2 # where you splash down when you fall into a pit

# ---------------------------------------------------------------- physics
WALK_SPEED = 0.45      # cells per tick
MOVE_HOLD = 9          # ticks a key event keeps you walking (bridges key-repeat delay)
JUMP_V = -0.74         # initial jump velocity (rows per tick, negative = up)
GRAVITY = 0.066
STUN_TICKS = 18

# ---------------------------------------------------------------- the day
DAY_START = 9 * 60            # 9:00 AM
DAY_END = 21 * 60             # 9:00 PM, fireworks and closing
TICKS_PER_MINUTE = 40         # walking: one park minute every 1.33 seconds
BUS_MINUTES_PER_FORK = 6      # a clean three-fork bus trip is 18 minutes
WRONG_EXIT_MINUTES = 8
WATER_PARK_MINUTES = 15
RIDE_MINUTES = 12
FALL_MINUTES = 3
HIT_MINUTES = 2

SCORE = {
    "ride": 1000, "puzzle": 500, "mickey": 2500, "stamp": 100,
    "fork": 50, "hit": -50, "fall": -75, "wrong_exit": -100, "minute_left": 5,
}

# ---------------------------------------------------------------- destinations
# code -> (name, bus sign text)
DEST = {
    "MK": "MAGIC KINGDOM",
    "EP": "EPCOT",
    "HS": "HOLLYWOOD STUDIOS",
    "AK": "ANIMAL KINGDOM",
    "DS": "DISNEY SPRINGS",
    "RS": "STARLIGHT RESORT",
    "TL": "TYPHOON LAGOON",
    "BB": "BLIZZARD BEACH",
}
PARKS = ("MK", "EP", "HS", "AK")
ICON = {"MK": "▲", "EP": "●", "HS": "★", "AK": "♣"}
ICON_NAME = {"MK": "castle", "EP": "sphere", "HS": "star", "AK": "tree"}

# park code -> (ride name, short name shown on the HUD)
RIDES = {
    "MK": ("SPACE MOUNTAIN", "Space Mountain"),
    "EP": ("COSMIC REWIND", "Guardians of the Galaxy: Cosmic Rewind"),
    "HS": ("RUNAWAY RAILWAY", "Mickey & Minnie's Runaway Railway"),
    "AK": ("EXPEDITION EVEREST", "Expedition Everest"),
}

# ---------------------------------------------------------------- palette
# name -> (256-colour index, basic 8-colour index)
# basic: 0 black 1 red 2 green 3 yellow 4 blue 5 magenta 6 cyan 7 white
PALETTE = {
    "black":    (16, 0),
    "white":    (231, 7),
    "gray":     (245, 7),
    "dgray":    (238, 0),
    "silver":   (252, 7),
    "blue":     (27, 4),
    "lblue":    (75, 6),
    "navy":     (18, 4),
    "yellow":   (226, 3),
    "gold":     (220, 3),
    "orange":   (208, 1),
    "red":      (196, 1),
    "dred":     (124, 1),
    "purple":   (93, 5),
    "dpurple":  (54, 5),
    "pink":     (213, 5),
    "magenta":  (201, 5),
    "green":    (40, 2),
    "dgreen":   (28, 2),
    "brown":    (94, 1),
    "tan":      (180, 3),
    "cyan":     (51, 6),
    "teal":     (37, 6),
    "skin":     (216, 3),
    "water":    (39, 6),
    "dwater":   (25, 4),

    # backgrounds
    "sky":      (39, 4),
    "sky_hi":   (33, 4),
    "sky_dusk": (99, 5),
    "sky_night": (17, 0),
    "space":    (16, 0),
    "cosmic":   (54, 5),
    "toon":     (117, 6),
    "asphalt":  (240, 0),
    "asphalt2": (236, 0),
    "pave_rs":  (246, 7),
    "pave_mk":  (131, 1),
    "pave_ep":  (250, 7),
    "pave_hs":  (181, 5),
    "pave_ak":  (137, 3),
    "pave_ds":  (180, 3),
    "grass":    (34, 2),
    "road":     (240, 0),
    "roadline": (226, 3),
    "sign_bg":  (55, 5),
    "sign_top": (160, 1),
    "led":      (208, 1),
    "led_bg":   (16, 0),

    # chrome
    "hud_bg":   (16, 0),
    "hud":      (231, 7),
    "hud_dim":  (245, 7),
    "hud_gold": (220, 3),
    "hud_red":  (196, 1),
    "hud_green": (46, 2),
    "msg":      (159, 6),
    "msg_alert": (203, 1),
    "msg_good": (120, 2),
    "panel":    (16, 0),
    "panel_fg": (231, 7),
    "title":    (51, 6),
    "title2":   (201, 5),
    "title3":   (220, 3),
}

# ---------------------------------------------------------------- sprite legend
# Sprites are tuples of strings.  Each character is looked up in the sprite's
# own legend first, then in GLYPHS: letter -> (character to draw, colour name).
# A space is transparent.
GLYPHS = {
    "K": ("█", "black"), "W": ("█", "white"), "G": ("█", "gray"), "g": ("█", "dgray"),
    "S": ("█", "silver"), "s": ("▓", "gray"), "B": ("█", "blue"), "b": ("█", "lblue"),
    "V": ("█", "navy"), "Y": ("█", "yellow"), "A": ("█", "gold"), "O": ("█", "orange"),
    "R": ("█", "red"), "r": ("█", "dred"), "P": ("█", "purple"), "p": ("█", "pink"),
    "M": ("█", "magenta"), "E": ("█", "green"), "e": ("█", "dgreen"), "N": ("█", "brown"),
    "n": ("█", "tan"), "C": ("█", "cyan"), "T": ("█", "teal"), "H": ("█", "skin"),
    "k": ("▪", "black"), "y": ("▪", "yellow"), "*": ("✦", "gold"), "+": ("✦", "white"),
    "|": ("│", "gray"), "~": ("≈", "water"), "=": ("━", "gray"), ":": ("░", "silver"),
    "^": ("▲", "blue"), "'": ("▲", "gold"), "/": ("◢", "white"), "\\": ("◣", "white"),
    "<": ("◢", "red"), ">": ("◣", "red"), "u": ("▄", "gray"), "o": ("●", "cyan"),
    "x": ("▒", "dgray"), "v": ("▼", "red"),
}


def spr(rows, **legend):
    """Build a sprite: (rows, legend).  Legend keys are single characters."""
    return (tuple(rows), legend)


PLAIN = {}

# ---------------------------------------------------------------- people
def person(shirt, pants="blue", skin="skin", hat=None):
    """A 3-row guest.  Two leg frames for walking."""
    leg = {"(": ("▗", hat or "black"), ")": ("▖", hat or "black"), "H": ("█", skin),
           "[": ("▐", skin), "]": ("▌", skin), "S": ("█", shirt),
           "L": ("▌", pants), "R": ("▐", pants), "F": ("█", pants)}
    return [
        spr(("(H)", "[S]", "L R"), **leg),
        spr(("(H)", "[S]", " F "), **leg),
    ]


PLAYER = person("red", "blue")
CAST_MEMBER = person("blue", "navy", hat="navy")
GUEST_A = person("green", "dgray")
GUEST_B = person("yellow", "purple", hat="pink")

MICKEY = spr(("K K", "KHK", " R ", "Y Y"), H=("█", "skin"))
MINNIE = spr(("K K", "KHK", " p ", "Y Y"), H=("█", "skin"), p=("█", "pink"))
STORMTROOPER = spr((" W ", "kWk", "W W"), k=("▪", "black"))
YETI = spr(("gWg", "WvW", "W W"), v=("▼", "red"))

# ---------------------------------------------------------------- landmarks
CASTLE = spr((
    "             *             ",
    "             ^             ",
    "             B             ",
    "      *     BBB     *      ",
    "      ^    BBBBB    ^      ",
    "      B    WkWkW    B      ",
    "     BBB   WWWWW   BBB     ",
    "  * WkWkW  WWkWW  WkWkW *  ",
    "  ^ WWWWW  WWWWW  WWWWW ^  ",
    "  B WWWWWWWWWWWWWWWWWWW B  ",
    " BBBWkWWkWWWkWWWkWWWkWWkBBB",
    " WkWWWWWWWWWWWWWWWWWWWWWWkW",
    " WWWWWWWWWWWGGGGGWWWWWWWWWW",
    " WWWWWWWWWWWGkkkGWWWWWWWWWW",
    " WWWWWWWWWWWGkkkGWWWWWWWWWW",
))

SPACESHIP_EARTH = spr((
    "      sSSSSSSs      ",
    "    sSsSSsSSsSSs    ",
    "   SsSSsSSsSSsSSs   ",
    "  sSSsSSsSSsSSsSSs  ",
    "  SsSSsSSsSSsSSsSS  ",
    "  sSSsSSsSSsSSsSSs  ",
    "  SsSSsSSsSSsSSsSS  ",
    "   SsSSsSSsSSsSSs   ",
    "    sSsSSsSSsSSs    ",
    "      sSSSSSSs      ",
    "      ||    ||      ",
    "      ||    ||      ",
))

SPACE_MOUNTAIN = spr((
    "          W           ",
    "          W           ",
    "         WSW          ",
    "        WSWSW         ",
    "   |   WSWSWSW   |    ",
    "   |  WSWSWSWSW  |    ",
    "  WW WSWSWSWSWSW WW   ",
    " WSWSWSWSWSWSWSWSWSW  ",
    " WSWSWSWSWSWSWSWSWSW  ",
    "WSWSWSWSWSWSWSWSWSWSW ",
    "WSWSWSWSWkkkWSWSWSWSW ",
), S=("█", "silver"))

GUARDIANS = spr((
    "      bbbbbbbbbbbbbbbb      ",
    "   BBBBBBBBBBBBBBBBBBBBBB   ",
    " BBBBBBBBBBBBBBBBBBBBBBBBBB ",
    " BBBBBBBBB   *    BBBBBBBBB ",
    " BBBBBBBBBBBBBBBBBBBBBBBBBB ",
    " BVBVBVBVBVBVBVBVBVBVBVBVBV ",
    " BBBBBBBBBBBBBBBBBBBBBBBBBB ",
    " BBBBBBBBBBBBkkkBBBBBBBBBBB ",
))

CHINESE_THEATRE = spr((
    "          rRRRRr          ",
    "        rRRRRRRRRr        ",
    "       nnnnnnnnnnnn       ",
    "    rRRRRRRRRRRRRRRRRr    ",
    "  rRRRRRRRRRRRRRRRRRRRRr  ",
    "   nnnnnnnnnnnnnnnnnnnn   ",
    "   nkknnkknnnnnnkknnkkn   ",
    "   nnnnnnnnnRRRRnnnnnnn   ",
    "   nnnnnnnnnRkkRnnnnnnn   ",
    "   nnnnnnnnnRkkRnnnnnnn   ",
))

TOWER_OF_TERROR = spr((
    "    gggggg    ",
    "   nnnnnnnn   ",
    "   nknnnnkn   ",
    "   nnnnnnnn   ",
    "   nkknnkkn   ",
    "  nnnnnnnnnn  ",
    "  nkknnnnkkn  ",
    "  nnnnnnnnnn  ",
    "  nkknnnnkkn  ",
    "  nnnnnnnnnn  ",
    " nnnnnnnnnnnn ",
    " nkknnkknnkkn ",
    " nnnnnnnnnnnn ",
    " nnnnnkkknnnn ",
))

TREE_OF_LIFE = spr((
    "        EEEEEEEE        ",
    "     EEEEeEEEEEeEEE     ",
    "   EEEeEEEEEEEEEEeEEE   ",
    "  EEEEEEEeEEEEeEEEEEEE  ",
    " EEEeEEEEEEEEEEEEEEeEEE ",
    " EEEEEEEEeEEEEEEEEEEEEE ",
    "  EEEEEEEEEENNEEEEEEEE  ",
    "    EEEEEENNNNNNEEEE    ",
    "        NNnNNNnN        ",
    "         NNNnNN         ",
    "         NnNNNN         ",
    "        NNNNnNNN        ",
    "       NNnNNNNNnN       ",
))

EVEREST = spr((
    "              W                 ",
    "             WWW                ",
    "            WWWWW               ",
    "           WWGWWWW              ",
    "          WGGGGGGWW             ",
    "         GGGGGGGGGGG            ",
    "        GGGGGgggGGGGG           ",
    "       GGGGGG===GGGGGG          ",
    "      GGGGggGGGGGGgGGGG         ",
    "     GGGG===GGGGGGGG===G        ",
    "    GGGGGGGGGGGGGGGGGGGGG       ",
    "   gggGGGGGGGGGGGGGGGGGGGg      ",
    "  gggggggggggggggggggggggggg    ",
    "  ggggggRRRRgggggggggggggggg    ",
    "  ggggggRkkRgggggggggggggggg    ",
))

FALCON = spr((
    "       GGGGGG        ",
    "    GGGGGGGGGGGGGG   ",
    "  GGGGGGGGCCGGGGGGGGG",
    " GGGGGGGGGGGGGGGGGGGG",
    "  GGGGGGGGGGGGGGGGGG ",
    "     gg        gg    ",
))

TRAIN_STATION = spr((
    "         RRRR         ",
    "       RRRRRRRR       ",
    "     RRRRRRRRRRRR     ",
    "   RRRRRRRRRRRRRRRR   ",
    "   WWWWWWWWkkWWWWWW   ",
    "   WkkWWWWWWWWWWkkW   ",
    "   WWWWWWWWWWWWWWWW   ",
    "   WWWWWWWkkkkWWWWW   ",
    "   WWWWWWWkkkkWWWWW   ",
))

RESORT = spr((
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT",
    "pWWkWWkWWkWWkWWkWWkWWkWWkWWkWWWp",
    "pWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWp",
    "pWWkWWkWWkWWkWWkWWkWWkWWkWWkWWWp",
    "pWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWp",
    "pWWkWWkWWkWWkWWkWWkWWkWWkWWkWWWp",
    "pWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWp",
    "pWWkWWkWWkWWkWWkWWkWWkWWkWWkWWWp",
    "pWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWp",
    "pWWWWWWWWWTkkTWWWWWWWWWWWWWWWWWp",
    "pWWWWWWWWWTkkTWWWWWWWWWWWWWWWWWp",
), T=("█", "teal"), p=("█", "pink"))

CROSSROADS = spr((
    "  o  ",
    "  |  ",
    "  |  ",
    " BBB ",
    " BkB ",
    " BBB ",
    "bbbbb",
    "bbbbb",
))

BALLOON = spr((
    "  PPPP  ",
    " PPPPPP ",
    " PMPPMP ",
    "  PPPP  ",
    "   ||   ",
    "   nn   ",
))

SPRINGS_SHOP = spr((
    " nnnnnnnnnnnn ",
    " NkkNNkkNNkkN ",
    " NNNNNNNNNNNN ",
    " NkkNNkkNNkkN ",
    " NNNNNkkNNNNN ",
    " NNNNNkkNNNNN ",
))


def shop(roof, wall="W", w=10, h=7):
    rows = [" " + roof * (w - 2) + " "]
    for i in range(1, h):
        if i in (2, 5, 6):
            body = (wall + "kk" + wall) * ((w - 2) // 4)
            body = body + wall * ((w - 2) - len(body))
        else:
            body = wall * (w - 2)
        rows.append(" " + body + " ")
    return spr(rows)


def pavilion(wall, roof):
    return spr((
        " " + roof * 12 + " ",
        wall * 14,
        wall + "kk" + wall * 3 + "kk" + wall * 3 + "kk" + wall,
        wall * 14,
        wall * 5 + "kkkk" + wall * 5,
        wall * 5 + "kkkk" + wall * 5,
    ))


# World Showcase: code -> (name, flag colours left to right, wall, roof)
PAVILIONS = {
    "MX": ("MEXICO", ("green", "white", "red"), "n", "N"),
    "NO": ("NORWAY", ("red", "white", "blue"), "N", "r"),
    "CN": ("CHINA", ("red", "yellow", "red"), "R", "A"),
    "DE": ("GERMANY", ("black", "red", "yellow"), "n", "N"),
    "JP": ("JAPAN", ("white", "red", "white"), "W", "R"),
    "MA": ("MOROCCO", ("red", "green", "red"), "n", "T"),
    "FR": ("FRANCE", ("blue", "white", "red"), "S", "g"),
    "CA": ("CANADA", ("red", "white", "red"), "N", "e"),
}
PAVILION_ORDER = ("MX", "NO", "CN", "DE", "JP", "MA", "FR", "CA")

# ---------------------------------------------------------------- street furniture
PALM = spr(("  E E  ", " EEEEE ", "E EEE E", "   N   ", "   N   ", "   N   "))
TREE = spr(("  EEE  ", " EEEEE ", "EEEEEEE", "   N   ", "   N   "))
BUSH = spr(("eEEe", "EEEE"))
LAMP = spr(("y", "|", "|", "|"))
BENCH = spr(("NNNN", "N  N"))
BALLOON_CART = spr(("R B Y M", " | | | ", "  |||  ", " nnnnn ", "  K K  "))
POPCORN = spr(("YyYy", "RRRR", "RWWR", " KK "))
FOUNTAIN = spr(("  ~  ", " ~~~ ", "GGGGG"))
POOL = spr(("~~~~~~~~~~~~",), **{"~": ("≈", "cyan")})
KIOSK = spr((" BBB ", " BkB ", "  |  "))
SIGN_ARCH = spr(("PPPPPPPPPPPPPPPP", "P              P", "P              P", "P              P", "P              P"))
TAPSTILE = spr((" o ", "GGG", "GGG"))
TAPSTILE_OK = spr((" o ", "GGG", "GGG"), o=("●", "green"))
LEVER_L = spr(("Y  ", " N ", "GGG"), Y=("█", "yellow"))
LEVER_R = spr(("  Y", " N ", "GGG"), Y=("█", "yellow"))
MAGICBAND = spr(("▐▌",), **{"▐": ("▐", "magenta"), "▌": ("▌", "magenta")})
BED = spr(("BBBBBB", "NkkkkN"))
DOOR = spr(("NNN", "NyN", "NNN"))
STAIR_LO = spr(("GGGG", "GGGG"))
PLATFORM = spr(("GGGGGG", "G    G", "G    G", "G    G", "G    G"))
PILLAR = spr(("|", "|", "|"))
POLE = spr(("|",))

BUS = spr((
    " gGGGGGGGGGGGGGg ",
    " GCCGCCGCCGCCGkk ",
    " GCCGCCGCCGCCGkk ",
    " MMMMMMMMMMMMMMM ",
    " SSSSSSSSSSSSSSS ",
    "   KK       KK   ",
))
BUS_DOOR_X = 14          # column of the bus door within the sprite
BUS_STOP = spr(("BBBB", "BWWB", " || ", " || "), W=("█", "white"))
DEPARTURE_BOARD = spr((
    "KKKKKKKKKKKKKKKKKKKKKK",
    "KKKKKKKKKKKKKKKKKKKKKK",
    "KKKKKKKKKKKKKKKKKKKKKK",
    "KKKKKKKKKKKKKKKKKKKKKK",
    "KKKKKKKKKKKKKKKKKKKKKK",
    "KKKKKKKKKKKKKKKKKKKKKK",
    "KKKKKKKKKKKKKKKKKKKKKK",
    "          ||          ",
    "          ||          ",
))

MONORAIL = spr((" RRRRRRRRRRRRRRRRRRRR ", "WCWCWCWCWCWCWCWCWCWCWW"))
TROLLEY = spr(("NkNkNkN", " K   K "))
RACE_CAR_L = spr(("◄RRk",), **{"◄": ("◄", "red")})
RACE_CAR_R = spr(("kRR►",), **{"►": ("►", "red")})
LOG = spr(("NnN",), n=("●", "tan"))
CROC_CLOSED = spr(("EyEEE",))
CROC_OPEN = spr(("R    ", "EyEEE"))
PEOPLEMOVER_CAR = spr(("bbbbbb",))
CLOUD = spr(("  WWW   ", " WWWWWWW"), W=("█", "white"))

# ---------------------------------------------------------------- ride vehicles
ROCKET = spr((" W    ", "WWWWW▶", " W    "), **{"▶": ("▶", "white")})
POD_FRAMES = [
    spr(("Y   Y", " CCC ", "Y   Y")),
    spr(("  Y  ", "YCCCY", "  Y  ")),
    spr(("Y   Y", " CCC ", "Y   Y")),
    spr(("  Y  ", "YCCCY", "  Y  ")),
]
TRAIN = spr((
    "  RR      pppp  ",
    " RRRRRk  pkkkkp ",
    " K  K    K   K  ",
), p=("█", "pink"))
COASTER = spr(("RRRRRR", "K K K "))
FIREWORK_CHARS = ("✦", "✧", "•", "·")

# ---------------------------------------------------------------- 3x5 block font
FONT = {
    "A": (" █ ", "█ █", "███", "█ █", "█ █"),
    "B": ("██ ", "█ █", "██ ", "█ █", "██ "),
    "C": (" ██", "█  ", "█  ", "█  ", " ██"),
    "D": ("██ ", "█ █", "█ █", "█ █", "██ "),
    "E": ("███", "█  ", "██ ", "█  ", "███"),
    "F": ("███", "█  ", "██ ", "█  ", "█  "),
    "G": (" ██", "█  ", "█ █", "█ █", " ██"),
    "H": ("█ █", "█ █", "███", "█ █", "█ █"),
    "I": ("███", " █ ", " █ ", " █ ", "███"),
    "J": ("  █", "  █", "  █", "█ █", " █ "),
    "K": ("█ █", "█ █", "██ ", "█ █", "█ █"),
    "L": ("█  ", "█  ", "█  ", "█  ", "███"),
    "M": ("█ █", "███", "███", "█ █", "█ █"),
    "N": ("██ ", "█ █", "█ █", "█ █", "█ █"),
    "O": ("███", "█ █", "█ █", "█ █", "███"),
    "P": ("██ ", "█ █", "██ ", "█  ", "█  "),
    "Q": ("███", "█ █", "█ █", "███", "  █"),
    "R": ("██ ", "█ █", "██ ", "█ █", "█ █"),
    "S": (" ██", "█  ", " █ ", "  █", "██ "),
    "T": ("███", " █ ", " █ ", " █ ", " █ "),
    "U": ("█ █", "█ █", "█ █", "█ █", "███"),
    "V": ("█ █", "█ █", "█ █", "█ █", " █ "),
    "W": ("█ █", "█ █", "███", "███", "█ █"),
    "X": ("█ █", "█ █", " █ ", "█ █", "█ █"),
    "Y": ("█ █", "█ █", " █ ", " █ ", " █ "),
    "Z": ("███", "  █", " █ ", "█  ", "███"),
    "0": ("███", "█ █", "█ █", "█ █", "███"),
    "1": (" █ ", "██ ", " █ ", " █ ", "███"),
    "2": ("███", "  █", "███", "█  ", "███"),
    "3": ("███", "  █", "███", "  █", "███"),
    "4": ("█ █", "█ █", "███", "  █", "  █"),
    "5": ("███", "█  ", "███", "  █", "███"),
    "6": ("█  ", "█  ", "███", "█ █", "███"),
    "7": ("███", "  █", "  █", "  █", "  █"),
    "8": ("███", "█ █", "███", "█ █", "███"),
    "9": ("███", "█ █", "███", "  █", "███"),
    "!": (" █ ", " █ ", " █ ", "   ", " █ "),
    "-": ("   ", "   ", "███", "   ", "   "),
    "&": (" █ ", "█ █", " █ ", "█ █", " ██"),
    "'": (" █ ", " █ ", "   ", "   ", "   "),
    " ": ("   ", "   ", "   ", "   ", "   "),
}
