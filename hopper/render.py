"""Curses renderer: HUD, the scrolling parks, bus trips, ride cutscenes and overlays."""
import curses
import math

from .constants import (
    VIEW_COLS, VIEW_ROWS, PLAY_ROWS, PLAY_TOP, MSG_TOP, MSG_ROWS, GROUND_Y, PALETTE, GLYPHS, FONT,
    DEST, PARKS, ICON, RIDES, PAVILIONS, DAY_END,
    PLAYER, MICKEY, MINNIE, YETI, CAST_MEMBER, CASTLE, EVEREST, TAPSTILE, TAPSTILE_OK,
    LEVER_L, LEVER_R, MAGICBAND, BUS, PALM, LAMP, TREE, ROCKET, POD_FRAMES, TRAIN, COASTER,
    FIREWORK_CHARS,
)

CONTROLS = [
    "LEFT / RIGHT  (or A / D) ..... walk",
    "SPACE  (or Z) ................ jump",
    "UP / ENTER  (or E) ........... use: board a bus, ride, talk, pull, stamp",
    "P ... pause      ? ... this card      Q or ESC ... quit (asks first)",
    "",
    "ON THE BUS: the driver needs a navigator.  Read each purple road sign",
    "and press LEFT or RIGHT for the exit that leads to your destination",
    "before the sign reaches the bus.  Three good exits and you're there.",
    "Park icons:  " + "   ".join("%s %s" % (ICON[p], DEST[p]) for p in PARKS),
    "",
    "IN THE PARKS: the ride is always off to the right of the gates.",
    "Jump trolleys, race cars, logs and stormtroopers.  Jump rivers.",
    "Crocodile backs are safe only while their mouths are shut.",
    "Cosmic Rewind needs a stamped passport; Runaway Railway needs green signals.",
    "",
    "Ride all four, then meet Mickey in front of Cinderella Castle",
    "before the park closes at 9:00 PM.  Time left is bonus points.",
]


class Renderer:
    def __init__(self, stdscr):
        self.scr = stdscr
        self.pairs = {}
        try:
            self.colors_ok = curses.has_colors()
        except curses.error:
            self.colors_ok = False
        if self.colors_ok:
            curses.start_color()
            try:
                curses.use_default_colors()
            except curses.error:
                pass
        self.many = self.colors_ok and curses.COLORS >= 256
        self.max_pairs = curses.COLOR_PAIRS if self.colors_ok else 0
        self.oy = self.ox = 0
        self.flash_t = 0
        self.cam = 0

    # ------------------------------------------------------------ colours
    def cidx(self, name):
        full, basic = PALETTE[name]
        return full if self.many else basic

    def attr(self, fg, bg, bold=False):
        if not self.colors_ok:
            return curses.A_BOLD if bold else 0
        key = (self.cidx(fg), self.cidx(bg))
        if key not in self.pairs:
            n = len(self.pairs) + 1
            if n >= self.max_pairs:
                # Old ncurses builds only have 256 pairs.  Every frame is redrawn
                # from scratch, so we can simply start the table over.
                self.pairs.clear()
                n = 1
            try:
                curses.init_pair(n, key[0], key[1])
            except curses.error:
                return 0
            self.pairs[key] = n
        a = curses.color_pair(self.pairs[key])
        return a | curses.A_BOLD if bold else a

    def flash(self):
        self.flash_t = 2

    # ------------------------------------------------------------ primitives
    def put(self, y, x, s, attr=0):
        try:
            self.scr.addstr(y, x, s, attr)
        except curses.error:
            pass

    def fill(self, y0, x0, rows, cols, attr):
        for y in range(y0, y0 + rows):
            self.put(y, x0, " " * cols, attr)

    def center(self, y, text, attr=0):
        self.put(y, self.ox + (VIEW_COLS - len(text)) // 2, text, attr)

    def big(self, y, x, text, attr):
        for i, ch in enumerate(text.upper()):
            glyph = FONT.get(ch, FONT[" "])
            for r, row in enumerate(glyph):
                for c, px in enumerate(row):
                    if px == "█":
                        self.put(y + r, x + i * 4 + c, "█", attr)

    def big_center(self, y, text, attr):
        w = len(text) * 4 - 1
        self.big(y, self.ox + (VIEW_COLS - w) // 2, text, attr)

    # play-area helpers: (col, row) are relative to the play area
    def pcell(self, row, col, ch, fg, bg, bold=False):
        if 0 <= row < PLAY_ROWS and 0 <= col < VIEW_COLS:
            self.put(self.oy + PLAY_TOP + row, self.ox + col, ch, self.attr(fg, bg, bold))

    def sprite(self, row, col, sprite, bg_fn, bold=False):
        """Draw a sprite with its top-left at play-area (row, col).  bg_fn(row, col) -> bg colour."""
        rows, legend = sprite
        for r, line in enumerate(rows):
            y = row + r
            if y < 0 or y >= PLAY_ROWS:
                continue
            for c, ch in enumerate(line):
                if ch == " ":
                    continue
                x = col + c
                if x < 0 or x >= VIEW_COLS:
                    continue
                g = legend.get(ch) or GLYPHS.get(ch)
                if g is None:
                    glyph, colour = ch, "white"
                else:
                    glyph, colour = g
                self.pcell(y, x, glyph, colour, bg_fn(y, x), bold)

    def ptext(self, row, col, text, fg, bg_fn, bold=False):
        for i, ch in enumerate(text):
            x = col + i
            if 0 <= x < VIEW_COLS and 0 <= row < PLAY_ROWS:
                self.pcell(row, x, ch, fg, bg_fn(row, x), bold)

    # ------------------------------------------------------------ frame
    def draw(self, g):
        self.scr.erase()
        rows, cols = self.scr.getmaxyx()
        if rows < VIEW_ROWS or cols < VIEW_COLS:
            self.put(0, 0, "Park Hopper needs a terminal of at least %dx%d (you have %dx%d)."
                     % (VIEW_COLS, VIEW_ROWS, cols, rows))
            self.put(1, 0, "Enlarge the window.")
            self.scr.refresh()
            return
        self.oy = (rows - VIEW_ROWS) // 2
        self.ox = (cols - VIEW_COLS) // 2
        m = g.mode
        base = g.prev_mode if m in ("help", "pause", "confirm_quit") else m
        if base == "title":
            self.draw_title(g)
        elif base == "play":
            self.draw_play(g)
        elif base == "bus":
            self.draw_bus(g)
        elif base == "ride":
            self.draw_ride(g)
        elif base == "ending":
            self.draw_ending(g)
        elif base == "gameover":
            self.draw_gameover(g)
        if base not in ("title",):
            self.draw_hud(g)
            self.draw_messages(g)
        if m == "help":
            self.draw_help(g)
        elif m == "pause":
            self.panel(["PAUSED", "", "Press P to keep going"])
        elif m == "confirm_quit":
            self.panel(["LEAVE THE PARKS?", "", "Y to quit, any other key to stay"])
        if self.flash_t > 0:
            self.flash_t -= 1
            a = self.attr("black", "white")
            self.put(self.oy + PLAY_TOP, self.ox, " " * VIEW_COLS, a)
            self.put(self.oy + PLAY_TOP + PLAY_ROWS - 1, self.ox, " " * VIEW_COLS, a)
        self.scr.refresh()

    # ------------------------------------------------------------ HUD & messages
    def draw_hud(self, g):
        bg = "hud_bg"
        self.fill(self.oy, self.ox, 2, VIEW_COLS, self.attr("hud", bg))
        y = self.oy
        left = g.minutes_left()
        clock_col = "hud_red" if left <= 60 else "hud"
        self.put(y, self.ox + 1, g.clock_text(), self.attr(clock_col, bg, True))
        self.put(y, self.ox + 12, "MAGIC %06d" % max(0, g.score), self.attr("hud_gold", bg, True))
        x = self.ox + 27
        self.put(y, x, "RIDES", self.attr("hud_dim", bg))
        x += 6
        for p in PARKS:
            done = p in g.rides_done
            self.put(y, x, ICON[p], self.attr("hud_green" if done else "hud_dim", bg, done))
            x += 2
        if g.mode == "bus" and g.bus:
            where = "BUS TO " + DEST[g.bus.dest]
        elif g.mode == "ride" and g.ride:
            where = RIDES[g.ride.park][0]
        else:
            where = g.scene.name.upper()
        self.put(y, self.ox + VIEW_COLS - len(where) - 1, where, self.attr("hud", bg, True))
        # objective row
        y = self.oy + 1
        if g.mode == "bus" and g.bus:
            b = g.bus
            if b.water_park:
                txt = "Hmm, this bus is heading for the water park..."
            elif b.phase == "arrive":
                txt = "Arriving at %s." % DEST[b.dest]
            else:
                lane = {-1: "LEFT", 1: "RIGHT", 0: "---"}[b.lane]
                txt = "Fork %d of 3: press LEFT or RIGHT for the exit to %s.   Chosen: %s" % (
                    min(b.fork_i + 1, 3), DEST[b.dest], lane)
            self.put(y, self.ox + 1, txt, self.attr("hud_gold", bg))
            return
        txt = g.objective()
        self.put(y, self.ox + 1, txt, self.attr("hud_gold", bg))
        x = self.ox + 2 + len(txt)
        if g.scene_code == "EP" and g.ep_brief and len(g.stamps_have) < 3 and g.mode == "play":
            for i, code in enumerate(g.stamps_needed):
                colours = PAVILIONS[code][1]
                got = i < len(g.stamps_have)
                for c in colours:
                    self.put(y, x, "█", self.attr(c, bg))
                    x += 1
                self.put(y, x, "✓" if got else " ", self.attr("hud_green", bg, True))
                x += 2
            self.put(y, x, "(%d/3)" % len(g.stamps_have), self.attr("hud_dim", bg))
        elif g.scene_code == "HS" and g.hs_brief and not g.hs_solved and g.mode == "play":
            for i, on in enumerate(g.signals):
                self.put(y, x, "●", self.attr("hud_green" if on else "hud_red", bg, True))
                self.put(y, x + 1, str(i + 1), self.attr("hud_dim", bg))
                x += 3

    def draw_messages(self, g):
        bg = "hud_bg"
        self.fill(self.oy + MSG_TOP, self.ox, MSG_ROWS, VIEW_COLS, self.attr("hud", bg))
        colours = {"msg": "msg", "alert": "msg_alert", "good": "msg_good"}
        msgs = list(g.messages)[-MSG_ROWS:]
        for i, (text, kind) in enumerate(msgs):
            self.put(self.oy + MSG_TOP + i, self.ox + 1, text[:VIEW_COLS - 2], self.attr(colours.get(kind, "msg"), bg))
        if len(msgs) < MSG_ROWS:
            hint = "ARROWS walk   SPACE jump   UP/ENTER use   ? help   P pause   Q quit"
            self.put(self.oy + MSG_TOP + MSG_ROWS - 1, self.ox + 1, hint, self.attr("hud_dim", bg))

    def panel(self, lines, fg="panel_fg"):
        w = max(len(l) for l in lines) + 6
        h = len(lines) + 2
        x0 = self.ox + (VIEW_COLS - w) // 2
        y0 = self.oy + PLAY_TOP + (PLAY_ROWS - h) // 2
        a = self.attr(fg, "panel")
        self.fill(y0, x0, h, w, a)
        self.put(y0, x0, "▛" + "▀" * (w - 2) + "▜", a)
        self.put(y0 + h - 1, x0, "▙" + "▄" * (w - 2) + "▟", a)
        for i, l in enumerate(lines):
            self.put(y0 + 1 + i, x0 + (w - len(l)) // 2, l, self.attr("title3" if i == 0 else fg, "panel", i == 0))

    def draw_help(self, g):
        a = self.attr("panel_fg", "panel")
        y0 = self.oy + PLAY_TOP
        self.fill(y0, self.ox, PLAY_ROWS, VIEW_COLS, a)
        self.put(y0, self.ox + 2, "HOW TO HAVE A MAGICAL DAY", self.attr("title3", "panel", True))
        for i, line in enumerate(CONTROLS):
            self.put(y0 + 1 + i, self.ox + 2, line, a)
        self.put(y0 + PLAY_ROWS - 1, self.ox + 2, "any key to close", self.attr("hud_dim", "panel"))

    # ------------------------------------------------------------ title
    def draw_title(self, g):
        black = self.attr("white", "black")
        self.fill(self.oy, self.ox, VIEW_ROWS, VIEW_COLS, black)
        t = g.title_t
        cols = ("title", "title2", "title3", "red", "green", "lblue")
        c = cols[(t // 8) % len(cols)]
        self.big_center(self.oy + 1, "PARK HOPPER", self.attr(c, "black", True))
        # Atari colour bars
        bars = ("red", "orange", "gold", "green", "cyan", "blue", "purple")
        for i, b in enumerate(bars):
            self.put(self.oy + 7, self.ox + 6 + i * 10, "█" * 9, self.attr(b, "black"))
        bg = lambda r, cc: "black"
        self.sprite(9, (VIEW_COLS - 27) // 2, CASTLE, bg)
        self.sprite(19, (VIEW_COLS - 27) // 2 + 6, PLAYER[0], bg)
        self.sprite(18, (VIEW_COLS - 27) // 2 + 18, MICKEY, bg)
        left = [
            "A DAY AT",
            "WALT DISNEY WORLD",
            "",
            "Ride one ride in",
            "each of the four",
            "parks, then meet",
            "Mickey in front",
            "of the castle",
            "before 9 PM.",
        ]
        for i, l in enumerate(left):
            self.put(self.oy + 9 + i, self.ox + 3, l, self.attr("white" if i < 2 else "hud_dim", "black", i < 2))
        right = [
            "%s %s" % (ICON["MK"], "SPACE MOUNTAIN"),
            "%s %s" % (ICON["EP"], "COSMIC REWIND"),
            "%s %s" % (ICON["HS"], "RUNAWAY RAILWAY"),
            "%s %s" % (ICON["AK"], "EXPEDITION EVEREST"),
            "",
            "HIGH SCORE %06d" % g.high,
        ]
        for i, l in enumerate(right):
            self.put(self.oy + 9 + i, self.ox + VIEW_COLS - 24, l, self.attr("title3" if i == 5 else "white", "black"))
        if (t // 15) % 2 == 0:
            self.put(self.oy + 17, self.ox + VIEW_COLS - 24, "PRESS ENTER TO START", self.attr("green", "black", True))
        self.put(self.oy + 18, self.ox + VIEW_COLS - 24, "? for how to play", self.attr("hud_dim", "black"))
        self.put(self.oy + VIEW_ROWS - 1, self.ox + 2, "A TERMINAL 2600 GAME", self.attr("hud_dim", "black"))

    # ------------------------------------------------------------ the parks
    def draw_play(self, g):
        s = g.scene
        cam = int(g.cam_x)
        self.cam = cam

        def bg_at(row, col):
            wx = col + cam
            if row <= GROUND_Y:
                return s.sky
            if s.in_pit(wx):
                return "water" if row < GROUND_Y + 3 else "dwater"
            if s.asphalt and s.asphalt[0] <= wx <= s.asphalt[1]:
                return "asphalt" if row != GROUND_Y + 2 else "asphalt2"
            return s.pave

        # sky and ground
        sky = self.attr("white", s.sky)
        for r in range(0, GROUND_Y + 1):
            self.put(self.oy + PLAY_TOP + r, self.ox, " " * VIEW_COLS, sky)
        for r in range(GROUND_Y + 1, PLAY_ROWS):
            for col in range(VIEW_COLS):
                b = bg_at(r, col)
                ch = " "
                wx = col + cam
                if b == "water" and (wx + g.tick // 10) % 3 == 0:
                    ch = "≈"
                elif r == GROUND_Y + 2 and b not in ("water", "dwater") and wx % 4 == 0:
                    ch = "·"
                elif b == "asphalt" and r == GROUND_Y + 1 and wx % 6 < 3:
                    ch = "▬"
                fg = "cyan" if b == "water" else "roadline" if b == "asphalt" else "dgray"
                self.pcell(r, col, ch, fg, b)
        # decor: clouds, monorail
        for d in s.decor:
            for x, row, spr in d.draw_list():
                self.sprite(row, x - cam, spr, bg_at)
        # static props
        for x, row, spr in s.props:
            w = len(spr[0][0])
            if x + w < cam or x > cam + VIEW_COLS:
                continue
            self.sprite(row, x - cam, spr, bg_at)
        # labels and flags
        for x, row, text, fg, bg in s.labels:
            if x + len(text) < cam or x > cam + VIEW_COLS:
                continue
            fn = (lambda r, c, b=bg: b) if bg else bg_at
            self.ptext(row, x - cam, text, fg, fn, bg is not None)
        for x, row, colours in s.flags:
            for i, c in enumerate(colours):
                self.pcell(row, x + i - cam, "█", c, bg_at(row, x + i - cam))
        # dynamic props
        if s.gate_x is not None:
            spr = TAPSTILE_OK if s.code in g.gate_open else TAPSTILE
            self.sprite(GROUND_Y - 2, s.gate_x - cam, spr, bg_at)
            self.sprite(GROUND_Y - 2, s.gate_x + 4 - cam, spr, bg_at)
        if s.code == "HS":
            for i, x in enumerate(s.lever_xs):
                self.sprite(GROUND_Y - 2, x - cam, LEVER_R if g.hs_levers[i] else LEVER_L, bg_at)
        if s.code == "RS" and not g.band and (g.tick // 6) % 2 == 0:
            self.sprite(GROUND_Y, 18 - cam, MAGICBAND, bg_at)
        if s.code == "AK" and s.yeti_x and (g.tick // 100) % 3 == 0:
            self.sprite(7, s.yeti_x - cam, YETI, bg_at)
        if s.code == "MK" and g.mickey_ready and s.mickey_x:
            self.sprite(GROUND_Y - 3, s.mickey_x - cam, MICKEY, bg_at)
            if (g.tick // 10) % 2 == 0:
                self.ptext(GROUND_Y - 5, s.mickey_x - 2 - cam, "MICKEY!", "gold", bg_at, True)
        # bus LED signs
        for bx, dest, n in s.bays:
            if bx + 17 < cam or bx > cam + VIEW_COLS:
                continue
            text = "   %s   BAY %d   " % (DEST[dest], n)
            off = (g.tick // 5) % len(text)
            window = (text + text)[off:off + 15]
            self.ptext(GROUND_Y - 6, bx + 1 - cam, window, "led", lambda r, c: "led_bg", True)
        # movers and hazards
        for m in s.movers:
            for x, row, spr in m.draw_list():
                self.sprite(row, x - cam, spr, bg_at)
        for c in s.crocs:
            for x, row, spr in c.draw_list():
                self.sprite(row, x - cam, spr, bg_at)
        for h in s.hazards:
            for x, row, spr in h.draw_list():
                self.sprite(row, x - cam, spr, bg_at)
        # the guest
        p = g.player
        if p.stun == 0 or (g.tick // 3) % 2 == 0:
            frame = PLAYER[(p.walk_t // 4) % 2] if p.move_t > 0 and not p.airborne else PLAYER[0]
            if p.airborne:
                frame = PLAYER[1]
            self.sprite(p.feet - 2, int(p.x) - cam, frame, bg_at)
        # dusk tint hint on the HUD is handled by the clock; here, lamp glow at night
        if g.clock >= DAY_END - 90:
            for x, row, spr in s.props:
                if spr is LAMP:
                    self.pcell(row, x - cam, "✦", "gold", s.sky, True)

    # ------------------------------------------------------------ the bus
    def draw_bus(self, g):
        b = g.bus
        sky_rows = 10

        def bg_at(row, col):
            if row < sky_rows:
                return "sky"
            if row < 12:
                return "grass"
            if row < 17:
                return "road"
            return "grass"

        for r in range(PLAY_ROWS):
            self.put(self.oy + PLAY_TOP + r, self.ox, " " * VIEW_COLS, self.attr("white", bg_at(r, 0)))
        # centre line
        off = int(b.scroll) % 8
        for col in range(VIEW_COLS):
            if (col + off) % 8 < 4:
                self.pcell(14, col, "▬", "roadline", "road")
        # scenery on the far side
        for x, kind in b.scenery:
            xi = int(x)
            if kind == "P":
                self.sprite(sky_rows - 5, xi, PALM, bg_at)
            elif kind == "T":
                self.sprite(sky_rows - 4, xi, TREE, bg_at)
            else:
                self.sprite(sky_rows - 3, xi, LAMP, bg_at)
        # the bus
        bus_row = 11 - (1 if b.lane < 0 else 0) + (1 if b.lane > 0 else 0)
        self.sprite(bus_row, 4, BUS, bg_at)
        text = "  %s  " % DEST[b.dest]
        o = (g.tick // 5) % len(text)
        self.ptext(bus_row - 1, 5, (text + text)[o:o + 15], "led", lambda r, c: "led_bg", True)
        if (g.tick // 2) % 2 == 0:
            self.pcell(bus_row + 5, 6, "▬", "dgray", bg_at(bus_row + 5, 6))
        # the sign
        if b.sign and b.phase == "drive":
            self.draw_sign(b, int(b.sign_x), bg_at)
        if b.banner_t > 0 and b.banner:
            good = b.banner.startswith("RIGHT") or b.banner.startswith("NOW")
            self.ptext(2, (VIEW_COLS - len(b.banner)) // 2, b.banner,
                       "black", lambda r, c: "green" if good else "red", True)
        if b.water_park and b.phase == "drive":
            self.ptext(2, 10, "The LED sign says %s..." % DEST[b.dest], "white", lambda r, c: "sky")
        if not b.water_park and b.phase == "drive":
            self.ptext(PLAY_ROWS - 1, 2, "◄ LEFT EXIT" if b.lane < 0 else "RIGHT EXIT ►" if b.lane > 0 else "choose an exit...",
                       "white", lambda r, c: "grass", True)

    def draw_sign(self, b, x, bg_at):
        sign = b.sign
        w = 40
        left, right = sign["left"], sign["right"]
        n = max(len(left), len(right))
        top = 1
        purple = lambda r, c: "sign_bg"
        redtop = lambda r, c: "sign_top"
        self.ptext(top, x, " WALT DISNEY WORLD ".center(w), "white", redtop, True)
        for i in range(n):
            l = left[i] if i < len(left) else ""
            r = right[i] if i < len(right) else ""
            line = ("◄ " + l).ljust(w // 2) + (r + " ►").rjust(w // 2)
            self.ptext(top + 1 + i, x, line, "white", purple, True)
        if sign["kind"] == "icons":
            self.ptext(top + 1 + n, x, " NEXT EXITS (symbols) ".center(w), "gold", purple)
        else:
            self.ptext(top + 1 + n, x, " NEXT EXITS ".center(w), "gold", purple)
        h = n + 2
        for r in range(top + h, 10):
            for c in (x + 4, x + w - 5):
                if 0 <= c < VIEW_COLS:
                    self.pcell(r, c, "║", "gray", bg_at(r, c))

    # ------------------------------------------------------------ rides
    def draw_ride(self, g):
        rd = g.ride
        t = rd.t
        park = rd.park
        if park == "MK":
            bgc = "space"
            fillbg = lambda r, c: bgc
            self.fill(self.oy + PLAY_TOP, self.ox, PLAY_ROWS, VIEW_COLS, self.attr("white", bgc))
            for x, y, sp in rd.stars:
                self.pcell(y, int(x), "-" if sp > 1.6 else "·", "white" if sp > 1.4 else "gray", bgc)
            rx = 22 + int(12 * math.sin(t / 17.0))
            ry = 8 + int(4 * math.sin(t / 9.0))
            self.ptext(ry + 1, rx - 4, "≈≈≈", "orange", fillbg, True)
            self.sprite(ry, rx, ROCKET, fillbg)
            if t > 30:
                self.big_center(self.oy + PLAY_TOP + 13, "SPACE MOUNTAIN", self.attr("white" if (t // 6) % 2 else "lblue", bgc, True))
        elif park == "EP":
            bgc = "cosmic"
            fillbg = lambda r, c: bgc
            self.fill(self.oy + PLAY_TOP, self.ox, PLAY_ROWS, VIEW_COLS, self.attr("white", bgc))
            cols = ("cyan", "magenta", "gold", "green", "white")
            for i, (x, y, sp) in enumerate(rd.stars):
                self.pcell(y, int(x), "✦" if sp > 1.6 else "·", cols[(i + t // 4) % len(cols)], bgc)
            cx = 38 + int(16 * math.cos(t / 14.0))
            cy = 7 + int(3 * math.sin(t / 7.0))
            self.sprite(cy, cx, POD_FRAMES[(t // 5) % 4], fillbg)
            if t > 30:
                self.big_center(self.oy + PLAY_TOP + 13, "COSMIC REWIND", self.attr(cols[(t // 5) % len(cols)], bgc, True))
        elif park == "HS":
            bgc = "toon"
            fillbg = lambda r, c: bgc
            self.fill(self.oy + PLAY_TOP, self.ox, PLAY_ROWS, VIEW_COLS, self.attr("white", bgc))
            for col in range(VIEW_COLS):
                self.pcell(12, col, "━", "brown", bgc)
                if (col + t) % 6 == 0:
                    self.pcell(13, col, "▬", "dgray", bgc)
            hills = ("green", "dgreen")
            for i in range(0, VIEW_COLS, 9):
                hx = (i - t) % (VIEW_COLS + 9) - 9
                self.ptext(11, hx, "▄▄▄▄▄▄", hills[(i // 9) % 2], fillbg)
            tx = 8 + int(12 * math.sin(t / 20.0))
            ty = 9 + ((t // 6) % 2)
            self.sprite(ty, tx, TRAIN, fillbg)
            self.sprite(ty - 3, tx + 9, MICKEY, fillbg)
            self.sprite(ty - 3, tx + 12, MINNIE, fillbg)
            if t > 30:
                self.big_center(self.oy + PLAY_TOP + 14, "RUNAWAY RAILWAY", self.attr("red" if (t // 6) % 2 else "yellow", bgc, True))
        else:
            bgc = "sky_hi"
            fillbg = lambda r, c: bgc
            self.fill(self.oy + PLAY_TOP, self.ox, PLAY_ROWS, VIEW_COLS, self.attr("white", bgc))
            mx = (VIEW_COLS - 32) // 2
            top = PLAY_ROWS - 14
            self.sprite(top, mx, EVEREST, fillbg)
            if t < 70:
                cx, cy = mx + 2 + int(t * 0.3), 15 - int(t * 0.12)
            elif t < 120:
                cx, cy = mx + 23 - int((t - 70) * 0.35), 7 + int((t - 70) * 0.1)
            else:
                cx, cy = mx + 5 + int((t - 120) * 0.5), 12 + int((t - 120) * 0.05)
            self.sprite(cy, cx, COASTER, fillbg)
            if 70 <= t < 120 and (t // 5) % 2:
                self.ptext(6, 6, "BACKWARDS!", "red", fillbg, True)
            if t > 90:
                self.sprite(top + 6, mx + 13, YETI, fillbg)
            if t > 30:
                self.big_center(self.oy + PLAY_TOP, "EXPEDITION EVEREST", self.attr("white" if (t // 6) % 2 else "gold", bgc, True))

    # ------------------------------------------------------------ finale & closing
    def night_castle(self):
        bgc = "sky_night"
        self.fill(self.oy + PLAY_TOP, self.ox, PLAY_ROWS, VIEW_COLS, self.attr("white", bgc))
        fillbg = lambda r, c: bgc
        for r in range(GROUND_Y + 1, PLAY_ROWS):
            self.put(self.oy + PLAY_TOP + r, self.ox, " " * VIEW_COLS, self.attr("white", "pave_mk"))
        cx = VIEW_COLS - 30
        self.sprite(GROUND_Y - 14, cx, CASTLE, fillbg)
        return cx, fillbg

    def draw_fireworks(self, g):
        for x, y, age, colour in g.fireworks:
            r = age // 4
            ch = FIREWORK_CHARS[min(3, age // 6)]
            if age < 4:
                self.pcell(y + 3 - age, x, "|", colour, "sky_night")
                continue
            for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r), (r, r // 2), (-r, r // 2), (r, -r // 2), (-r, -r // 2)):
                yy, xx = y + dy // 2, x + dx
                if 0 <= yy < GROUND_Y and 0 <= xx < VIEW_COLS:
                    self.pcell(yy, xx, ch, colour, "sky_night", True)

    def draw_ending(self, g):
        cx, fillbg = self.night_castle()
        self.draw_fireworks(g)
        self.sprite(GROUND_Y - 3, cx + 5, MICKEY, lambda r, c: "sky_night")
        self.sprite(GROUND_Y - 2, cx - 1, PLAYER[0], lambda r, c: "sky_night")
        t = g.end_t
        if t > 20:
            cols = ("gold", "white", "cyan", "magenta")
            a = self.attr(cols[(t // 6) % 4], "sky_night", True)
            self.big(self.oy + PLAY_TOP + 1, self.ox + 4, "YOU MET", a)
            self.big(self.oy + PLAY_TOP + 7, self.ox + 4, "MICKEY!", a)
        if t > 50:
            lines = [
                "\"Ha-ha! You rode every park in one day.",
                " See ya real soon!\"",
                "Time left %d min x%d = %d bonus" % (g.minutes_left(), 5, getattr(g, "end_bonus", 0)),
                "Buses %d  Wrong exits %d  Bumps %d  Splashes %d" % (
                    g.stats["buses"], g.stats["wrong_exits"], g.stats["hits"], g.stats["falls"]),
                "FINAL MAGIC %06d   HIGH SCORE %06d" % (g.score, g.high),
                "press ENTER",
            ]
            for i, l in enumerate(lines):
                self.put(self.oy + PLAY_TOP + 13 + i, self.ox + 2, l, self.attr("gold" if i == 4 else "white", "sky_night", i == 4))

    def draw_gameover(self, g):
        cx, fillbg = self.night_castle()
        self.draw_fireworks(g)
        t = g.end_t
        self.big(self.oy + PLAY_TOP + 1, self.ox + 3, "PARK CLOSED", self.attr("red" if (t // 8) % 2 else "white", "sky_night", True))
        if t > 30:
            lines = [
                "It's 9:00 PM. The fireworks were lovely,",
                "but Mickey went home.",
                "",
                "Rides done: %d of 4" % len(g.rides_done),
                "MAGIC %06d   HIGH SCORE %06d" % (g.score, g.high),
                "press ENTER to try another day",
            ]
            for i, l in enumerate(lines):
                self.put(self.oy + PLAY_TOP + 8 + i, self.ox + 3, l, self.attr("white", "sky_night"))
