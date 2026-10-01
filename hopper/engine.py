"""Game loop, input, platform physics, bus trips, park puzzles, rides and the ending."""
import curses
import json
import os
import random
import time
from collections import deque

from .constants import (
    FPS, TICK, VIEW_COLS, GROUND_Y, WATER_Y, WALK_SPEED, MOVE_HOLD, JUMP_V, GRAVITY,
    STUN_TICKS, DAY_START, DAY_END, TICKS_PER_MINUTE, BUS_MINUTES_PER_FORK,
    WRONG_EXIT_MINUTES, WATER_PARK_MINUTES, RIDE_MINUTES, FALL_MINUTES, HIT_MINUTES,
    SCORE, DEST, PARKS, ICON, RIDES, PAVILIONS, PAVILION_ORDER,
)
from .world import build_world
from .entities import Trolley, Speedway, LogRoll, Trooper, overlap

HIGH_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "highscore.json")

KEYS_LEFT = (curses.KEY_LEFT, ord("a"), ord("A"), ord("h"), ord("H"))
KEYS_RIGHT = (curses.KEY_RIGHT, ord("d"), ord("D"), ord("l"), ord("L"))
KEYS_JUMP = (ord(" "), ord("z"), ord("Z"), ord("j"), ord("J"))
KEYS_USE = (curses.KEY_UP, ord("w"), ord("W"), ord("e"), ord("E"), ord("k"), ord("K"),
            curses.KEY_ENTER, 10, 13)
KEYS_ENTER = (curses.KEY_ENTER, 10, 13, ord(" "))
ESC = 27
N_SIGNALS = 5
FORKS = 3
FORK_X = 8              # the sign passes the bus here
SIGN_START = VIEW_COLS + 4
SIGN_SPEED = 0.55


def clamp(v, lo, hi):
    return lo if v < lo else hi if v > hi else v


class Player:
    WIDTH = 3

    def __init__(self, x):
        self.x = float(x)
        self.y = float(GROUND_Y)
        self.vy = 0.0
        self.facing = 1
        self.airborne = False
        self.move_t = 0
        self.walk_t = 0
        self.stun = 0
        self.carrier = None       # (PeopleMover, car index) when riding a car

    @property
    def cx(self):
        return int(self.x) + 1

    @property
    def x0(self):
        return int(self.x)

    @property
    def x1(self):
        return int(self.x) + self.WIDTH - 1

    @property
    def feet(self):
        return int(round(self.y))


class BusTrip:
    """A bus ride between two places: three forks, each with a purple road sign."""

    def __init__(self, game, dest, origin):
        self.g = game
        self.dest = dest
        self.origin = origin
        self.fork_i = 0
        self.lane = 0
        self.phase = "drive"          # drive / result / arrive / closed
        self.t = 0
        self.phase_t = 0
        self.sign = None
        self.sign_x = 0.0
        self.wrong = 0
        self.banner = ""
        self.banner_t = 0
        self.scroll = 0.0
        rng = game.rng
        self.scenery = [[rng.uniform(0, VIEW_COLS + 40), rng.choice("PPPLT")] for _ in range(9)]
        self.water_park = dest in ("TL", "BB")
        if not self.water_park:
            self.new_sign()

    # ------------------------------------------------------------ signs
    def new_sign(self):
        rng = self.g.rng
        dest = self.dest
        level = self.fork_i + 1
        side = rng.choice((-1, 1))
        if level >= 3 and dest in PARKS:
            others = [p for p in PARKS if p != dest]
            rng.shuffle(others)
            mine = [ICON[dest], ICON[others[0]]]
            rng.shuffle(mine)
            theirs = [ICON[others[1]], ICON[others[2]]]
            kind = "icons"
        elif level == 2:
            if dest in PARKS:
                mine = ["ALL THEME PARKS"]
                theirs = rng.sample(["WATER PARKS", "DISNEY SPRINGS", "RESORT AREA"], 2)
            else:
                mine = [DEST[dest]]
                theirs = ["ALL THEME PARKS"]
            kind = "groups"
        else:
            pool = [d for d in DEST if d != dest]
            rng.shuffle(pool)
            mine = [DEST[dest], DEST[pool[0]]]
            rng.shuffle(mine)
            theirs = [DEST[pool[1]], DEST[pool[2]]]
            kind = "names"
        left, right = (mine, theirs) if side < 0 else (theirs, mine)
        self.sign = {"left": left, "right": right, "answer": side, "kind": kind}
        self.sign_x = float(SIGN_START)
        self.lane = 0

    def say_banner(self, text, ticks=60):
        self.banner = text
        self.banner_t = ticks

    # ------------------------------------------------------------ input / update
    def key(self, k):
        if self.phase != "drive" or self.water_park:
            return
        if k in KEYS_LEFT:
            self.lane = -1
        elif k in KEYS_RIGHT:
            self.lane = 1

    def update(self):
        g = self.g
        self.t += 1
        self.phase_t += 1
        self.scroll += SIGN_SPEED
        for s in self.scenery:
            s[0] -= SIGN_SPEED
            if s[0] < -8:
                s[0] += VIEW_COLS + 40
        if self.banner_t > 0:
            self.banner_t -= 1

        if self.water_park:
            if self.phase == "drive" and self.phase_t > 110:
                self.phase = "closed"
                self.phase_t = 0
                self.say_banner("%s IS CLOSED TODAY. THE BUS LOOPS BACK." % DEST[self.dest], 120)
                g.add_minutes(WATER_PARK_MINUTES)
            elif self.phase == "closed" and self.phase_t > 120:
                g.finish_bus(self.origin, wrong_bus=True)
            return

        if self.phase == "drive":
            self.sign_x -= SIGN_SPEED
            if self.sign_x <= FORK_X:
                self.resolve_fork()
        elif self.phase == "result":
            if self.phase_t > 45:
                if self.fork_i >= FORKS:
                    self.phase = "arrive"
                    self.phase_t = 0
                    self.say_banner("NOW ARRIVING: %s" % DEST[self.dest], 90)
                else:
                    self.phase = "drive"
                    self.phase_t = 0
                    self.new_sign()
        elif self.phase == "arrive":
            if self.phase_t > 80:
                g.finish_bus(self.dest)

    def resolve_fork(self):
        g = self.g
        g.add_minutes(BUS_MINUTES_PER_FORK)
        if self.lane == self.sign["answer"]:
            self.fork_i += 1
            g.score += SCORE["fork"]
            self.say_banner("RIGHT EXIT!  %d OF %d" % (self.fork_i, FORKS), 45)
            g.r.flash()
        else:
            self.wrong += 1
            g.add_minutes(WRONG_EXIT_MINUTES)
            g.score += SCORE["wrong_exit"]
            if self.lane == 0:
                self.say_banner("YOU MISSED THE EXIT! THE DRIVER LOOPS BACK. +%d MIN" % WRONG_EXIT_MINUTES, 45)
            else:
                self.say_banner("WRONG EXIT! THE DRIVER LOOPS BACK. +%d MIN" % WRONG_EXIT_MINUTES, 45)
        self.phase = "result"
        self.phase_t = 0


class Ride:
    def __init__(self, game, park):
        self.g = game
        self.park = park
        self.t = 0
        self.dur = 190
        rng = game.rng
        self.stars = [[rng.uniform(0, VIEW_COLS), rng.randint(0, 18), rng.uniform(0.6, 2.2)] for _ in range(45)]

    def update(self):
        self.t += 1
        for s in self.stars:
            s[0] -= s[2]
            if s[0] < 0:
                s[0] += VIEW_COLS
        if self.t >= self.dur:
            self.g.finish_ride(self.park)


class Game:
    def __init__(self, stdscr, renderer=None):
        self.stdscr = stdscr
        if renderer is None:
            from .render import Renderer
            renderer = Renderer(stdscr)
        self.r = renderer
        self.rng = random.Random()
        self.high = self.load_high()
        self.running = True
        self.mode = "title"
        self.prev_mode = "title"
        self.tick = 0
        self.title_t = 0
        self.messages = deque(maxlen=3)
        self.msg_expire = 0
        self.reset_state()

    # ------------------------------------------------------------ setup
    def reset_state(self):
        self.score = 0
        self.clock = DAY_START
        self.minute_t = 0
        self.band = False
        self.rides_done = set()
        self.stamps_needed = self.rng.sample(PAVILION_ORDER, 3)
        self.stamps_have = []
        self.ep_brief = False
        self.hs_brief = False
        self.hs_solved = False
        self.hs_levers = [False] * N_SIGNALS
        self.signals = [True] * N_SIGNALS
        pulls = self.rng.sample(range(N_SIGNALS), self.rng.randint(2, 4))
        for i in pulls:
            self.pull_signal(i)
            self.hs_levers[i] = not self.hs_levers[i]
        if all(self.signals):
            self.pull_signal(0)
            self.hs_levers[0] = not self.hs_levers[0]
        self.gate_open = set()
        self.scenes = build_world(self.rng, self.stamps_needed)
        self.scene_code = "RS"
        self.player = Player(self.scenes["RS"].start_x)
        self.cam_x = 0.0
        self.bus = None
        self.ride = None
        self.end_t = 0
        self.fireworks = []
        self.messages.clear()
        self.stats = {"buses": 0, "wrong_exits": 0, "hits": 0, "falls": 0}

    def pull_signal(self, i):
        for j in (i - 1, i, i + 1):
            if 0 <= j < N_SIGNALS:
                self.signals[j] = not self.signals[j]

    @property
    def scene(self):
        return self.scenes[self.scene_code]

    @property
    def mickey_ready(self):
        return len(self.rides_done) == len(PARKS)

    def load_high(self):
        try:
            with open(HIGH_PATH) as f:
                return int(json.load(f).get("high", 0))
        except (OSError, ValueError):
            return 0

    def save_high(self):
        if self.score > self.high:
            self.high = self.score
        try:
            with open(HIGH_PATH, "w") as f:
                json.dump({"high": self.high}, f)
        except OSError:
            pass

    # ------------------------------------------------------------ messages & time
    def say(self, text, kind="msg", secs=6):
        self.messages.append((text, kind))
        self.msg_expire = self.tick + int(secs * FPS)

    def add_minutes(self, m):
        self.clock += m
        if self.clock >= DAY_END and self.mode not in ("ending", "gameover"):
            self.park_closed()

    def clock_text(self):
        h, m = divmod(self.clock, 60)
        ampm = "AM" if h < 12 else "PM"
        h12 = h % 12 or 12
        return "%2d:%02d %s" % (h12, m, ampm)

    def minutes_left(self):
        return max(0, DAY_END - self.clock)

    def park_closed(self):
        self.mode = "gameover"
        self.end_t = 0
        self.save_high()

    def objective(self):
        """One line for the HUD describing what to do next."""
        if not self.band:
            return "Grab your MagicBand by the room door, then catch a bus from the loop."
        if self.mickey_ready:
            if self.scene_code == "MK":
                return "Mickey is waiting in front of Cinderella Castle!"
            return "All four rides done! Bus to MAGIC KINGDOM and meet Mickey at the castle."
        code = self.scene_code
        if code in PARKS and code not in self.rides_done:
            if code == "EP" and self.ep_brief and len(self.stamps_have) < 3:
                return "Passport stamps needed (in order):"
            if code == "HS" and self.hs_brief and not self.hs_solved:
                return "Railway signals (all must be green):"
            return "Find %s. It's off to the right." % RIDES[code][1]
        left = [ICON[p] + " " + DEST[p] for p in PARKS if p not in self.rides_done]
        return "Rides left: " + ",  ".join(left)

    # ------------------------------------------------------------ main loop
    def run(self):
        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        try:
            curses.curs_set(0)
        except curses.error:
            pass
        next_t = time.monotonic()
        while self.running:
            self.handle_input()
            self.update()
            self.r.draw(self)
            next_t += TICK
            delay = next_t - time.monotonic()
            if delay > 0:
                time.sleep(delay)
            else:
                next_t = time.monotonic()

    def handle_input(self):
        while True:
            try:
                k = self.stdscr.getch()
            except curses.error:
                break
            if k == -1:
                break
            self.key(k)

    def key(self, k):
        m = self.mode
        if m == "title":
            if k in KEYS_ENTER:
                self.start_game()
            elif k == ord("?"):
                self.prev_mode, self.mode = m, "help"
            elif k in (ord("q"), ord("Q"), ESC):
                self.running = False
        elif m == "help":
            self.mode = self.prev_mode
        elif m == "pause":
            if k in (ord("p"), ord("P"), ESC) or k in KEYS_ENTER:
                self.mode = self.prev_mode
        elif m == "confirm_quit":
            if k in (ord("y"), ord("Y")):
                self.save_high()
                self.running = False
            else:
                self.mode = self.prev_mode
        elif m in ("ending", "gameover"):
            if self.end_t > 40 and (k in KEYS_ENTER or k in (ord("q"), ord("Q"), ESC)):
                self.mode = "title"
        elif m in ("play", "bus", "ride"):
            if k in (ord("q"), ord("Q"), ESC):
                self.prev_mode, self.mode = m, "confirm_quit"
            elif k in (ord("p"), ord("P")):
                self.prev_mode, self.mode = m, "pause"
            elif k == ord("?"):
                self.prev_mode, self.mode = m, "help"
            elif m == "play":
                self.play_key(k)
            elif m == "bus":
                self.bus.key(k)

    def start_game(self):
        self.reset_state()
        self.mode = "play"
        self.say("Good morning! It's 9:00 AM at Walt Disney World. Park closes at 9:00 PM.", "good", 8)
        self.say("Grab your MagicBand (the glowing band by the door) and head right.", "msg", 8)

    # ------------------------------------------------------------ play: input
    def play_key(self, k):
        p = self.player
        if p.stun > 0:
            return
        if k in KEYS_LEFT:
            p.facing = -1
            p.move_t = MOVE_HOLD
        elif k in KEYS_RIGHT:
            p.facing = 1
            p.move_t = MOVE_HOLD
        elif k in KEYS_JUMP:
            if not p.airborne:
                p.vy = JUMP_V
                p.airborne = True
                p.carrier = None
        elif k in KEYS_USE:
            self.interact()

    # ------------------------------------------------------------ play: update
    def update(self):
        self.tick += 1
        if self.mode == "title":
            self.title_t += 1
            return
        if self.mode == "play":
            self.update_play()
        elif self.mode == "bus":
            self.bus.update()
        elif self.mode == "ride":
            self.ride.update()
        elif self.mode in ("ending", "gameover"):
            self.end_t += 1
            self.update_fireworks()
        if self.tick > self.msg_expire and self.messages:
            self.messages.popleft()
            self.msg_expire = self.tick + 3 * FPS

    def update_play(self):
        s = self.scene
        p = self.player
        s.update(self.rng)
        self.physics()
        if p.stun > 0:
            p.stun -= 1
        else:
            self.check_hazards()
        self.check_triggers()
        # camera
        target = p.x - VIEW_COLS / 2 + 4 * p.facing
        self.cam_x += (target - self.cam_x) * 0.15
        self.cam_x = clamp(self.cam_x, 0, max(0, s.width - VIEW_COLS))
        # the clock
        self.minute_t += 1
        if self.minute_t >= TICKS_PER_MINUTE:
            self.minute_t = 0
            self.add_minutes(1)
            if self.clock == DAY_END - 60:
                self.say("One hour to closing! Fireworks at 9:00 PM.", "alert", 6)

    def support_at(self, p):
        """What is under the player's feet right now: ('ground'|'plat', carrier) or None."""
        s = self.scene
        feet = p.feet
        for x0, x1, frow, carrier in s.all_platforms():
            if frow == feet and overlap(p.x0, p.x1, x0, x1):
                return ("plat", carrier)
        if feet == GROUND_Y and not s.in_pit(p.cx):
            return ("ground", None)
        return None

    def physics(self):
        s = self.scene
        p = self.player
        # horizontal
        if p.move_t > 0 and p.stun == 0:
            p.move_t -= 1
            p.x += p.facing * WALK_SPEED
            p.walk_t += 1
        p.x = clamp(p.x, 0, s.width - p.WIDTH)
        if not p.airborne:
            sup = self.support_at(p)
            if sup is None:
                p.airborne = True
                p.vy = 0.0
                p.carrier = None
            else:
                p.carrier = sup[1]
                if p.carrier:
                    mover, i = p.carrier
                    p.x += mover.speed
        if p.airborne:
            prev = p.y
            p.vy += GRAVITY
            p.y += p.vy
            if p.vy > 0:
                best = None
                for x0, x1, frow, carrier in s.all_platforms():
                    if prev <= frow <= p.y and overlap(p.x0, p.x1, x0, x1):
                        if best is None or frow < best[0]:
                            best = (frow, carrier)
                if best is None and not s.in_pit(p.cx) and prev <= GROUND_Y <= p.y:
                    best = (GROUND_Y, None)
                if best is not None:
                    p.y = float(best[0])
                    p.vy = 0.0
                    p.airborne = False
                    p.carrier = best[1]
                elif p.y >= WATER_Y:
                    self.splash()

    def splash(self):
        s = self.scene
        p = self.player
        pit = next(((x0, x1) for x0, x1 in s.pits if x0 <= p.cx <= x1), None)
        if pit:
            x0, x1 = pit
            p.x = float(x1 + 2) if p.cx > (x0 + x1) / 2 and p.facing < 0 else float(x0 - 5)
        else:
            p.x -= 5
        p.x = clamp(p.x, 0, s.width - p.WIDTH)
        p.y = float(GROUND_Y)
        p.vy = 0.0
        p.airborne = False
        p.carrier = None
        p.stun = STUN_TICKS
        p.move_t = 0
        self.add_minutes(FALL_MINUTES)
        self.score += SCORE["fall"]
        self.stats["falls"] += 1
        self.say("SPLASH! You fell in the river. A Cast Member fishes you out. +%d min" % FALL_MINUTES, "alert")

    def check_hazards(self):
        s = self.scene
        p = self.player
        for h in s.hazards:
            if p.feet < h.top:
                continue
            for x0, x1 in h.rects():
                if overlap(p.x0, p.x1, x0, x1):
                    self.hit(h, x0, x1)
                    return

    def hit(self, h, x0, x1):
        s = self.scene
        p = self.player
        if p.cx <= (x0 + x1) / 2:
            p.x = float(x0 - 9)
        else:
            p.x = float(x1 + 7)
        p.x = clamp(p.x, 0, s.width - p.WIDTH)
        p.y = float(GROUND_Y)
        p.vy = 0.0
        p.airborne = False
        p.carrier = None
        p.stun = STUN_TICKS
        p.move_t = 0
        self.add_minutes(HIT_MINUTES)
        self.score += SCORE["hit"]
        self.stats["hits"] += 1
        if isinstance(h, Trolley):
            self.say("DING DING! The trolley bumps you back. Jump over it! +%d min" % HIT_MINUTES, "alert")
        elif isinstance(h, Speedway):
            self.say("HONK! A race car clips you. Ride the PeopleMover over the Speedway. +%d min" % HIT_MINUTES, "alert")
        elif isinstance(h, LogRoll):
            self.say("OOF! A rolling log knocks you down. Hop over them! +%d min" % HIT_MINUTES, "alert")
        elif isinstance(h, Trooper):
            self.say("\"Move along!\" A stormtrooper shoves you back. Jump over him. +%d min" % HIT_MINUTES, "alert")
        else:
            self.say("Ouch! +%d min" % HIT_MINUTES, "alert")

    def check_triggers(self):
        s = self.scene
        p = self.player
        if s.code == "RS" and not self.band and abs(p.cx - 18) <= 1 and not p.airborne:
            self.pick_band()
        if s.gate_x is not None and p.cx >= s.gate_x and s.code not in self.gate_open:
            if self.band:
                self.gate_open.add(s.code)
                self.say("DING! MagicBand accepted. Welcome to %s!" % s.name, "good")
                if s.code == "MK" and self.mickey_ready:
                    self.say("Mickey is waiting for you in front of Cinderella Castle!", "good", 8)
                elif s.code in self.rides_done:
                    self.say("You already rode %s here." % RIDES[s.code][1], "msg")
                else:
                    self.say("Today's goal here: %s." % RIDES[s.code][1], "msg")
            else:
                p.x = float(s.gate_x - 6)
                p.move_t = 0
                self.say("BZZT. Blue light: no MagicBand! It's back at your resort room door.", "alert", 7)

    def pick_band(self):
        self.band = True
        self.score += SCORE["stamp"]
        self.r.flash()
        self.say("You strap on your MagicBand. Tap it at the park gates!", "good")
        self.say("Now head right to the bus loop and pick a park.", "msg")

    # ------------------------------------------------------------ interaction
    def interact(self):
        s = self.scene
        p = self.player
        if p.airborne:
            return
        near = [i for i in s.interacts if abs(i["x"] - p.cx) <= 3]
        if not near:
            if s.code == "RS" and not self.band:
                self.say("Nothing here. The MagicBand is the glowing band by the room door.", "msg")
            return
        i = min(near, key=lambda d: abs(d["x"] - p.cx))
        kind = i["kind"]
        if kind == "bus":
            self.board_bus(i["dest"], i["bay"])
        elif kind == "band":
            if not self.band:
                self.pick_band()
        elif kind == "talk":
            for line in i["lines"]:
                self.say(line, "msg", 7)
        elif kind == "ride":
            self.try_ride(i["park"])
        elif kind == "ep_cm":
            self.epcot_briefing()
        elif kind == "hs_cm":
            self.hs_briefing()
        elif kind == "pavilion":
            self.stamp(i["code"])
        elif kind == "lever":
            self.pull_lever(i["idx"])
        elif kind == "mickey":
            if self.mickey_ready:
                self.meet_mickey()
            else:
                self.say("A sign: MICKEY'S MEET & GREET RETURNS AFTER YOU'VE RIDDEN ALL FOUR PARKS.", "msg")

    def board_bus(self, dest, bay):
        self.say("You board the bus at Bay %d, bound for %s." % (bay, DEST[dest]), "good")
        self.stats["buses"] += 1
        self.bus = BusTrip(self, dest, self.scene_code)
        self.mode = "bus"

    def finish_bus(self, code, wrong_bus=False):
        self.stats["wrong_exits"] += self.bus.wrong
        self.bus = None
        self.mode = "play"
        self.scene_code = code
        s = self.scene
        p = self.player
        p.x = float(s.spawn_x)
        p.y = float(GROUND_Y)
        p.vy = 0.0
        p.airborne = False
        p.carrier = None
        p.facing = 1
        p.move_t = 0
        self.cam_x = clamp(p.x - VIEW_COLS / 2, 0, max(0, s.width - VIEW_COLS))
        if wrong_bus:
            self.say("Back where you started. Read the departure board more carefully!", "alert")
        elif code == "RS":
            self.say("Back at Starlight Resort. The bus loop is to the right.", "msg")
        elif code == "DS":
            self.say("Disney Springs: shops and snacks, but no rides. Oops.", "alert")
        else:
            self.say("Arrived at %s. The park gates are to the right; buses to the left." % s.name, "msg")

    def try_ride(self, park):
        if park in self.rides_done:
            self.say("You already rode %s today. Try one you haven't!" % RIDES[park][1], "msg")
            return
        if park == "EP" and len(self.stamps_have) < 3:
            self.epcot_briefing()
            return
        if park == "HS" and not all(self.signals):
            self.hs_briefing()
            return
        self.say("Cast Member: Enjoy your ride!", "good")
        self.ride = Ride(self, park)
        self.mode = "ride"

    def finish_ride(self, park):
        self.rides_done.add(park)
        self.ride = None
        self.mode = "play"
        self.score += SCORE["ride"]
        self.add_minutes(RIDE_MINUTES)
        self.r.flash()
        self.say("WOW! You rode %s! +%d" % (RIDES[park][1], SCORE["ride"]), "good", 7)
        if self.mickey_ready:
            self.say("That's all four parks! Catch a bus to MAGIC KINGDOM and meet Mickey at the castle.", "good", 9)
        else:
            left = [DEST[p] for p in PARKS if p not in self.rides_done]
            self.say("Still to ride: %s. Back to the bus loop (left)." % ", ".join(left), "msg", 8)

    # ------------------------------------------------------------ Epcot passport puzzle
    def epcot_briefing(self):
        if len(self.stamps_have) >= 3:
            self.say("Cast Member: Boarding group confirmed! Step right up to Cosmic Rewind.", "good")
            return
        self.ep_brief = True
        self.say("Cast Member: Cosmic Rewind is virtual queue only. Boarding groups go to guests", "msg", 9)
        self.say("with a stamped World Showcase passport. Stamp the pavilions flying the flags", "msg", 9)
        self.say("shown above, IN ORDER. World Showcase is to the right. Good luck!", "msg", 9)

    def stamp(self, code):
        name = PAVILIONS[code][0]
        if not self.ep_brief:
            self.say("The %s kiosk stamps passports. You don't have one yet." % name.title(), "msg")
            self.say("Ask the Cast Member outside Cosmic Rewind (back to the left).", "msg")
            return
        if len(self.stamps_have) >= 3:
            self.say("Your passport is full. Head back to Cosmic Rewind!", "msg")
            return
        expected = self.stamps_needed[len(self.stamps_have)]
        if code == expected:
            self.stamps_have.append(code)
            self.score += SCORE["stamp"]
            self.r.flash()
            if len(self.stamps_have) == 3:
                self.score += SCORE["puzzle"]
                self.say("STAMP! %s. Passport complete: boarding group confirmed! +%d" % (name, SCORE["puzzle"]), "good", 8)
                self.say("Head back left to Cosmic Rewind.", "msg", 8)
            else:
                self.say("STAMP! %s (%d of 3). Next flag is shown above." % (name, len(self.stamps_have)), "good")
        elif code in self.stamps_have:
            self.say("Already stamped %s. Find the next flag." % name, "msg")
        else:
            self.stamps_have = []
            self.add_minutes(HIT_MINUTES)
            self.say("Wrong pavilion! %s smudges your passport. Start the sequence over. +%d min" % (name, HIT_MINUTES), "alert")

    # ------------------------------------------------------------ Hollywood Studios signal puzzle
    def hs_briefing(self):
        if all(self.signals):
            self.say("Cast Member: Signals are green! All aboard the Runaway Railway.", "good")
            return
        self.hs_brief = True
        self.say("Cast Member: Goofy's train jumped the track! Every signal must be GREEN before", "msg", 9)
        self.say("we can load. Pull the yellow switch levers along the boulevards. Each lever", "msg", 9)
        self.say("flips its own signal AND its neighbours. Watch the board above.", "msg", 9)

    def pull_lever(self, idx):
        self.pull_signal(idx)
        self.hs_levers[idx] = not self.hs_levers[idx]
        self.hs_brief = True
        self.r.flash()
        if all(self.signals):
            if not self.hs_solved:
                self.hs_solved = True
                self.score += SCORE["puzzle"]
                self.say("CLANK! All signals GREEN. Goofy's train is back on track! +%d" % SCORE["puzzle"], "good", 8)
                self.say("Head back to the Chinese Theatre for Runaway Railway.", "msg", 8)
            else:
                self.say("CLANK! Signals all green.", "good")
        else:
            self.hs_solved = False
            self.say("CLANK! Lever %d flips signals %s." % (
                idx + 1, ", ".join(str(j + 1) for j in (idx - 1, idx, idx + 1) if 0 <= j < N_SIGNALS)), "msg")

    # ------------------------------------------------------------ the finale
    def meet_mickey(self):
        bonus = self.minutes_left() * SCORE["minute_left"]
        self.score += SCORE["mickey"] + bonus
        self.end_bonus = bonus
        self.mode = "ending"
        self.end_t = 0
        self.fireworks = []
        self.save_high()

    def update_fireworks(self):
        rng = self.rng
        if self.mode == "ending" and self.end_t % 9 == 0:
            self.fireworks.append([rng.randint(6, VIEW_COLS - 7), rng.randint(1, 7), 0,
                                   rng.choice(("red", "gold", "cyan", "magenta", "green", "white"))])
        for f in self.fireworks:
            f[2] += 1
        self.fireworks = [f for f in self.fireworks if f[2] < 22]
