"""The scenes: your resort, the four parks, Disney Springs, and their bus loops."""
from .constants import (
    GROUND_Y, DEST, PARKS, PAVILIONS, PAVILION_ORDER,
    CASTLE, SPACESHIP_EARTH, SPACE_MOUNTAIN, GUARDIANS, CHINESE_THEATRE, TOWER_OF_TERROR,
    TREE_OF_LIFE, EVEREST, FALCON, TRAIN_STATION, RESORT, CROSSROADS, BALLOON, SPRINGS_SHOP,
    shop, pavilion, PALM, TREE, BUSH, LAMP, BENCH, BALLOON_CART, POPCORN, FOUNTAIN, POOL,
    KIOSK, TAPSTILE, LEVER_L, MAGICBAND, BED, STAIR_LO, PLATFORM, PILLAR, POLE, BUS, BUS_STOP,
    DEPARTURE_BOARD, CAST_MEMBER, GUEST_A, GUEST_B, MICKEY,
)
from .entities import (
    Trolley, Speedway, LogRoll, Trooper, Croc, PeopleMover, Monorail, Clouds,
)

BAY_X0 = 26          # first bus bay
BAY_DX = 21          # spacing between bays
BOARD_X = 2          # departure board
GATE_X = 132         # park tapstiles
PARK_X0 = 140        # first column of park content
LOOP_END = 128       # asphalt ends here in parks


def height(sprite):
    return len(sprite[0])


class Scene:
    def __init__(self, code, name, width, pave, sky="sky"):
        self.code = code
        self.name = name
        self.width = width
        self.pave = pave
        self.sky = sky
        self.asphalt = None        # (x0, x1) drawn as asphalt instead of pavement
        self.props = []            # (x, top_row, sprite)
        self.labels = []           # (x, row, text, fg, bg or None)
        self.flags = []            # (x, row, (colour, colour, colour))
        self.interacts = []        # dicts with "x" (centre column) and "kind"
        self.platforms = []        # (x0, x1, feet_row)
        self.pits = []             # (x0, x1) inclusive: no ground
        self.hazards = []          # Hazard instances
        self.crocs = []
        self.movers = []           # PeopleMover instances
        self.decor = []            # Monorail / Clouds
        self.bays = []             # (bus_x, dest_code, bay_number)
        self.spawn_x = 10
        self.gate_x = None
        self.mickey_x = None
        self.yeti_x = None

    # ------------------------------------------------------------ building helpers
    def ground(self, x, sprite):
        self.props.append((x, GROUND_Y - height(sprite) + 1, sprite))

    def at(self, x, row, sprite):
        self.props.append((x, row, sprite))

    def label(self, x, row, text, fg="white", bg=None):
        self.labels.append((x, row, text, fg, bg))

    def interact(self, x, kind, **data):
        d = {"x": x, "kind": kind}
        d.update(data)
        self.interacts.append(d)

    def update(self, rng):
        for h in self.hazards:
            h.update(rng)
        for c in self.crocs:
            c.update(rng)
        for m in self.movers:
            m.update(rng)
        for d in self.decor:
            d.update(rng)

    def in_pit(self, x):
        return any(x0 <= x <= x1 for x0, x1 in self.pits)

    def all_platforms(self):
        """Yield (x0, x1, feet_row, carrier) where carrier is a PeopleMover car index or None."""
        for p in self.platforms:
            yield p[0], p[1], p[2], None
        for c in self.crocs:
            p = c.platform()
            if p:
                yield p[0], p[1], p[2], None
        for m in self.movers:
            for x0, x1, feet, i in m.platforms():
                yield x0, x1, feet, (m, i)


def bus_loop(scene, dests, x0=BAY_X0, board_x=BOARD_X):
    """Lay out a departure board and one bay per destination."""
    scene.at(board_x, GROUND_Y - height(DEPARTURE_BOARD) + 1, DEPARTURE_BOARD)
    scene.label(board_x + 1, GROUND_Y - 8, "  DEPARTURES  ", "gold", "black")
    for i, d in enumerate(dests):
        bx = x0 + i * BAY_DX
        scene.ground(bx, BUS)
        scene.ground(bx - 4, BUS_STOP)
        scene.label(bx - 3, GROUND_Y - 3, str(i + 1), "black", "white")
        scene.label(board_x + 1, GROUND_Y - 7 + i, ("%d %s" % (i + 1, DEST[d]))[:20].ljust(20), "yellow", "black")
        scene.bays.append((bx, d, i + 1))
        scene.interact(bx + 13, "bus", dest=d, bay=i + 1, bus_x=bx)


def park_common(scene, dests, welcome):
    scene.asphalt = (0, LOOP_END)
    bus_loop(scene, dests)
    scene.ground(GATE_X, TAPSTILE)
    scene.ground(GATE_X + 4, TAPSTILE)
    scene.label(GATE_X - 4, GROUND_Y - 4, welcome, "white", "purple")
    scene.gate_x = GATE_X
    scene.spawn_x = GATE_X - 10


# ---------------------------------------------------------------- Starlight Resort
def build_resort(rng, dests):
    s = Scene("RS", "Starlight Resort", 212, "pave_rs")
    s.ground(4, RESORT)
    s.label(11, 3, " STARLIGHT RESORT ", "white", "teal")
    s.ground(18, MAGICBAND)
    s.interact(18, "band")
    s.label(15, GROUND_Y - 4, "MagicBand", "magenta", None)
    s.ground(40, PALM)
    s.at(44, GROUND_Y + 1, POOL)
    s.label(46, GROUND_Y - 1, "HIPPY DIPPY POOL", "white", None)
    s.ground(58, PALM)
    s.ground(63, BENCH)
    s.ground(70, shop("O"))
    s.label(70, GROUND_Y - 8, "FOOD COURT", "white", "orange")
    s.ground(84, POPCORN)
    s.ground(90, GUEST_A[0])
    s.interact(91, "talk", lines=["Guest: Buses leave from the loop on the right.",
                                  "Check the departure board for the right bay!"])
    s.asphalt = (96, 212)
    bus_loop(s, dests, x0=124, board_x=100)
    s.label(100, 2, "BUS LOOP", "white", "dgray")
    s.spawn_x = 112
    s.decor.append(Clouds(rng, s.width))
    s.decor.append(Monorail(s.width))
    s.start_x = 8
    return s


# ---------------------------------------------------------------- Magic Kingdom
def build_mk(rng, dests):
    s = Scene("MK", "Magic Kingdom", 362, "pave_mk")
    park_common(s, dests, " MAGIC KINGDOM ")
    s.ground(142, TRAIN_STATION)
    s.label(144, 4, "MAIN STREET U.S.A.", "white", "dred")
    for i, roof in enumerate("RBEP"):
        s.ground(168 + i * 12, shop(roof))
        if i < 3:
            s.ground(179 + i * 12, LAMP)
    s.ground(215, POPCORN)
    s.ground(222, BALLOON_CART)
    s.hazards.append(Trolley(166, 230))
    s.ground(232, GUEST_B[0])
    s.interact(233, "talk", lines=["Guest: Watch out for the trolley!", "Jump when it rolls at you."])
    s.ground(236, CASTLE)
    s.label(240, 0, " CINDERELLA CASTLE ", "white", "blue")
    s.mickey_x = 268
    s.interact(269, "mickey")
    s.ground(266, GUEST_A[0])
    s.interact(267, "talk", lines=["Guest: Tomorrowland is to the right.",
                                   "The PeopleMover glides right over the Speedway."])
    s.label(274, GROUND_Y - 9, "TOMORROWLAND", "white", "purple")
    s.label(274, GROUND_Y - 8, "  ------->  ", "white", "purple")
    # PeopleMover: stairs, station A, track, station B
    s.ground(278, STAIR_LO)
    s.ground(282, STAIR_LO)
    s.platforms.append((278, 285, GROUND_Y - 2))
    s.ground(285, PLATFORM)
    s.platforms.append((285, 290, GROUND_Y - 5))
    track_row = GROUND_Y - 3
    for x in range(291, 331):
        s.at(x, track_row, (("=",), {}))
    for x in range(296, 331, 9):
        s.at(x, track_row + 1, PILLAR)
    s.movers.append(PeopleMover(291, 330, track_row))
    s.ground(331, PLATFORM)
    s.platforms.append((331, 336, GROUND_Y - 5))
    s.label(300, GROUND_Y - 7, "PEOPLEMOVER", "lblue", None)
    s.hazards.append(Speedway(292, 330))
    s.label(298, GROUND_Y - 1, "TOMORROWLAND SPEEDWAY", "white", None)
    s.ground(338, SPACE_MOUNTAIN)
    s.label(340, 3, " SPACE MOUNTAIN ", "white", "navy")
    s.interact(348, "ride", park="MK")
    s.decor.append(Clouds(rng, s.width))
    s.decor.append(Monorail(s.width))
    return s


# ---------------------------------------------------------------- Epcot
def build_epcot(rng, dests, stamps_needed):
    s = Scene("EP", "Epcot", 402, "pave_ep")
    park_common(s, dests, "     EPCOT     ")
    s.ground(142, SPACESHIP_EARTH)
    s.label(145, 2, " SPACESHIP EARTH ", "white", "dgray")
    s.ground(166, FOUNTAIN)
    s.ground(176, GUARDIANS)
    s.label(183, GROUND_Y - 9, "GUARDIANS OF THE GALAXY", "white", "navy")
    s.label(186, GROUND_Y - 8, " COSMIC REWIND ", "yellow", "navy")
    s.ground(207, CAST_MEMBER[0])
    s.interact(189, "ride", park="EP")
    s.interact(208, "ep_cm")
    s.label(214, GROUND_Y - 9, "WORLD SHOWCASE", "white", "purple")
    s.label(214, GROUND_Y - 8, "  ------->    ", "white", "purple")
    s.ground(214, PALM)
    for i, code in enumerate(PAVILION_ORDER):
        name, colours, wall, roof = PAVILIONS[code]
        x = 226 + i * 22
        s.ground(x, pavilion(wall, roof))
        s.label(x + (14 - len(name)) // 2, GROUND_Y - 7, name, "white", "black")
        s.flags.append((x - 3, GROUND_Y - 7, colours))
        for r in range(GROUND_Y - 6, GROUND_Y + 1):
            s.at(x - 4, r, POLE)
        s.interact(x + 7, "pavilion", code=code)
    s.ground(400, BUSH)
    s.decor.append(Clouds(rng, s.width))
    s.decor.append(Monorail(s.width))
    s.stamps_needed = stamps_needed
    return s


# ---------------------------------------------------------------- Hollywood Studios
def build_hs(rng, dests):
    s = Scene("HS", "Hollywood Studios", 348, "pave_hs")
    park_common(s, dests, "HOLLYWOOD STUDIOS")
    s.ground(142, CROSSROADS)
    s.label(150, GROUND_Y - 9, "HOLLYWOOD BLVD", "white", "dred")
    for i, roof in enumerate("pTY"):
        s.ground(150 + i * 12, shop(roof))
        if i < 2:
            s.ground(161 + i * 12, LAMP)
    lever_xs = (188, 230, 264, 280, 326)
    for i, x in enumerate(lever_xs):
        s.interact(x + 1, "lever", idx=i)
    s.lever_xs = lever_xs
    s.ground(194, CHINESE_THEATRE)
    s.label(197, 4, " MICKEY & MINNIE'S ", "white", "dred")
    s.label(198, 5, "  RUNAWAY RAILWAY  ", "yellow", "dred")
    s.ground(222, CAST_MEMBER[0])
    s.interact(207, "ride", park="HS")
    s.interact(223, "hs_cm")
    s.label(236, GROUND_Y - 9, "SUNSET BLVD", "white", "purple")
    s.label(236, GROUND_Y - 8, " -------->  ", "white", "purple")
    s.ground(244, TOWER_OF_TERROR)
    s.label(243, 0, " TOWER OF TERROR ", "white", "dgray")
    s.ground(270, PALM)
    s.label(288, GROUND_Y - 9, "GALAXY'S EDGE", "white", "purple")
    s.label(288, GROUND_Y - 8, "  ------->   ", "white", "purple")
    s.ground(296, FALCON)
    s.label(299, GROUND_Y - 7, "MILLENNIUM FALCON", "cyan", None)
    s.hazards.append(Trooper(290, 342, 300, 1))
    s.hazards.append(Trooper(290, 342, 328, -1))
    s.ground(336, TREE)
    s.decor.append(Clouds(rng, s.width))
    return s


# ---------------------------------------------------------------- Animal Kingdom
def build_ak(rng, dests):
    s = Scene("AK", "Animal Kingdom", 332, "pave_ak")
    park_common(s, dests, " ANIMAL KINGDOM ")
    s.ground(142, PALM)
    s.ground(150, TREE)
    s.label(162, 1, " DISCOVERY ISLAND ", "white", "dgreen")
    s.ground(160, TREE_OF_LIFE)
    s.ground(188, TREE)
    s.ground(196, BUSH)
    s.label(200, GROUND_Y - 9, "ASIA", "white", "purple")
    s.label(200, GROUND_Y - 8, "--->", "white", "purple")
    s.ground(199, GUEST_B[0])
    s.interact(200, "talk", lines=["Guest: The trail to Everest is rough.",
                                   "Jump the rivers and hop the logs. Crocs bite when their mouths open!"])
    s.pits.append((206, 212))
    s.label(205, GROUND_Y - 4, "KALI RIVER", "white", None)
    s.hazards.append(LogRoll(216, 252))
    s.ground(253, TREE)
    s.pits.append((258, 273))
    s.crocs.append(Croc(260, 0))
    s.crocs.append(Croc(267, 0))
    s.ground(276, PALM)
    s.pits.append((282, 287))
    s.ground(290, EVEREST)
    s.label(292, 0, " EXPEDITION EVEREST ", "white", "dgray")
    s.yeti_x = 303
    s.interact(300, "ride", park="AK")
    s.decor.append(Clouds(rng, s.width))
    return s


# ---------------------------------------------------------------- Disney Springs
def build_springs(rng, dests):
    s = Scene("DS", "Disney Springs", 240, "pave_ds")
    s.asphalt = (0, LOOP_END)
    bus_loop(s, dests)
    s.spawn_x = 136
    s.label(134, GROUND_Y - 9, " DISNEY SPRINGS ", "white", "teal")
    for x in (150, 166, 182, 198):
        s.ground(x, SPRINGS_SHOP)
    s.ground(214, PALM)
    s.at(222, 1, BALLOON)
    s.ground(224, CAST_MEMBER[0])
    s.interact(225, "talk", lines=["Cast Member: Lovely shops, but no rides here!",
                                   "The buses back to the parks are to the left."])
    s.decor.append(Clouds(rng, s.width))
    return s


def build_world(rng, stamps_needed):
    """Build every scene with a fresh random bay layout."""
    def park_bays(code):
        others = [p for p in PARKS if p != code]
        extra = rng.choice(["DS", "TL", "BB"])
        bays = others + ["RS", extra]
        rng.shuffle(bays)
        return bays

    resort_bays = list(PARKS) + ["DS"]
    rng.shuffle(resort_bays)
    springs_bays = list(PARKS) + ["RS"]
    rng.shuffle(springs_bays)
    return {
        "RS": build_resort(rng, resort_bays),
        "MK": build_mk(rng, park_bays("MK")),
        "EP": build_epcot(rng, park_bays("EP"), stamps_needed),
        "HS": build_hs(rng, park_bays("HS")),
        "AK": build_ak(rng, park_bays("AK")),
        "DS": build_springs(rng, springs_bays),
    }
