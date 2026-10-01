"""Moving things: trolleys, race cars, logs, crocodiles, PeopleMover cars, stormtroopers."""
from .constants import (
    GROUND_Y, TROLLEY, RACE_CAR_L, RACE_CAR_R, LOG, CROC_CLOSED, CROC_OPEN,
    PEOPLEMOVER_CAR, STORMTROOPER, MONORAIL, CLOUD,
)


def overlap(a0, a1, b0, b1):
    """Inclusive integer range overlap."""
    return a0 <= b1 and b0 <= a1


class Hazard:
    """Something that knocks you back if you touch it.  `top` is the highest row it
    occupies; you clear it when your feet are above that row."""
    top = GROUND_Y
    width = 1
    penalty = "hit"

    def rects(self):
        """Yield (x0, x1) inclusive column ranges currently occupied."""
        return ()

    def draw_list(self):
        """Yield (x, top_row, sprite)."""
        return ()

    def update(self, rng):
        pass


class Trolley(Hazard):
    """The Main Street trolley, rolling back and forth.  Two rows tall: jump it."""
    top = GROUND_Y - 1
    width = 7

    def __init__(self, x0, x1):
        self.x0, self.x1 = x0, x1 - self.width
        self.x = float(x0)
        self.dir = 1
        self.speed = 0.22

    def update(self, rng):
        self.x += self.dir * self.speed
        if self.x <= self.x0:
            self.x, self.dir = float(self.x0), 1
        elif self.x >= self.x1:
            self.x, self.dir = float(self.x1), -1

    def rects(self):
        xi = int(self.x)
        yield xi, xi + self.width - 1

    def draw_list(self):
        yield int(self.x), GROUND_Y - 1, TROLLEY


class Speedway(Hazard):
    """Tomorrowland Speedway: race cars zip through the zone.  One row tall."""
    top = GROUND_Y
    width = 4

    def __init__(self, x0, x1):
        self.x0, self.x1 = x0, x1
        self.cars = []          # [x, dir]
        self.timer = 20

    def update(self, rng):
        self.timer -= 1
        if self.timer <= 0:
            self.timer = rng.randint(28, 55)
            if rng.random() < 0.5:
                self.cars.append([float(self.x1), -1])
            else:
                self.cars.append([float(self.x0 - self.width), 1])
        for c in self.cars:
            c[0] += c[1] * 0.95
        self.cars = [c for c in self.cars if self.x0 - self.width <= c[0] <= self.x1 + 1]

    def rects(self):
        for c in self.cars:
            xi = int(c[0])
            x0, x1 = max(xi, self.x0), min(xi + self.width - 1, self.x1)
            if x0 <= x1:
                yield x0, x1

    def draw_list(self):
        for c in self.cars:
            yield int(c[0]), GROUND_Y, RACE_CAR_L if c[1] < 0 else RACE_CAR_R


class LogRoll(Hazard):
    """Logs rolling down from Everest's slopes.  One row: hop them."""
    top = GROUND_Y
    width = 3

    def __init__(self, x0, x1):
        self.x0, self.x1 = x0, x1
        self.logs = []
        self.timer = 30

    def update(self, rng):
        self.timer -= 1
        if self.timer <= 0:
            self.timer = rng.randint(55, 85)
            self.logs.append(float(self.x1))
        self.logs = [x - 0.5 for x in self.logs if x - 0.5 >= self.x0]

    def rects(self):
        for x in self.logs:
            xi = int(x)
            yield xi, xi + self.width - 1

    def draw_list(self):
        for x in self.logs:
            yield int(x), GROUND_Y, LOG


class Trooper(Hazard):
    """A stormtrooper on patrol.  Three rows tall: a well-timed jump clears him."""
    top = GROUND_Y - 2
    width = 3

    def __init__(self, x0, x1, start, direction=1):
        self.x0, self.x1 = x0, x1 - self.width
        self.x = float(start)
        self.dir = direction
        self.speed = 0.2

    def update(self, rng):
        self.x += self.dir * self.speed
        if self.x <= self.x0:
            self.x, self.dir = float(self.x0), 1
        elif self.x >= self.x1:
            self.x, self.dir = float(self.x1), -1

    def rects(self):
        xi = int(self.x)
        yield xi, xi + self.width - 1

    def draw_list(self):
        yield int(self.x), GROUND_Y - 2, STORMTROOPER


class Croc:
    """A crocodile in a Kali River pit.  Its back is a platform while its mouth is shut."""
    width = 5

    def __init__(self, x, phase=0):
        self.x = x
        self.t = phase
        self.cycle = 150
        self.open_for = 50

    @property
    def open(self):
        return self.t >= self.cycle - self.open_for

    def update(self, rng):
        self.t = (self.t + 1) % self.cycle

    def platform(self):
        """(x0, x1, feet_row) or None."""
        if self.open:
            return None
        return (self.x, self.x + self.width - 1, GROUND_Y)

    def draw_list(self):
        if self.open:
            yield self.x, GROUND_Y, CROC_OPEN
        else:
            yield self.x, GROUND_Y + 1, CROC_CLOSED


class PeopleMover:
    """The Tomorrowland Transit Authority: cars glide along an elevated track."""
    width = 6

    def __init__(self, x0, x1, track_row):
        self.x0, self.x1 = x0, x1
        self.track_row = track_row
        self.car_row = track_row - 1
        self.feet = track_row - 2
        self.speed = 0.28
        n = max(1, (x1 - x0) // 16)
        self.cars = [float(x0 + i * 16) for i in range(n)]

    def update(self, rng):
        for i, x in enumerate(self.cars):
            x += self.speed
            if x > self.x1:
                x = float(self.x0) - self.width
            self.cars[i] = x

    def platforms(self):
        for i, x in enumerate(self.cars):
            xi = int(x)
            yield (xi, xi + self.width - 1, self.feet, i)

    def draw_list(self):
        for x in self.cars:
            yield int(x), self.car_row, PEOPLEMOVER_CAR


class Monorail:
    """Purely decorative: glides across the sky now and then."""
    def __init__(self, width, row=2):
        self.width = width
        self.row = row
        self.x = -30.0
        self.wait = 60

    def update(self, rng):
        if self.wait > 0:
            self.wait -= 1
            return
        self.x += 0.7
        if self.x > self.width + 5:
            self.x = -30.0
            self.wait = rng.randint(200, 500)

    def draw_list(self):
        if self.wait == 0:
            yield int(self.x), self.row, MONORAIL


class Clouds:
    def __init__(self, rng, width, n=4):
        self.width = width
        self.items = [[rng.uniform(0, width), rng.randint(0, 4)] for _ in range(n)]

    def update(self, rng):
        for c in self.items:
            c[0] += 0.03
            if c[0] > self.width + 10:
                c[0] = -10

    def draw_list(self):
        for x, row in self.items:
            yield int(x), row, CLOUD
