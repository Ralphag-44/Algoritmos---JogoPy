import pyxel

COLOR = 10 

SPEED = 5.5
MAX_RANGE = 110.0

FIRING     = 1 << 0
ATTACHED   = 1 << 1
RETRACTING = 1 << 2


class Hook:
    __slots__ = ('x', 'y', 'dx', 'dy', 'traveled', 'anchor_x', 'anchor_y',
                 'length', 'state', 'host')

    def __init__(self, px, py, tx, ty):
        dx, dy = tx - px, ty - py
        dist = (dx ** 2 + dy ** 2) ** 0.5 or 1
        self.dx, self.dy = dx / dist, dy / dist

        self.x, self.y = px, py
        self.traveled = 0.0
        self.anchor_x = self.anchor_y = 0.0
        self.length = 0.0
        self.state = FIRING
        self.host = None

    def update(self, px, py, platforms):
        if self.state & FIRING:
            self.__fly(platforms)
        elif self.state & ATTACHED:
            self.__follow()
        elif self.state & RETRACTING:
            self.__return(px, py)

    def __follow(self):
        if self.host is not None:
            self.anchor_x += self.host.dx
            self.anchor_y += self.host.dy

    def __fly(self, platforms):
        step = min(SPEED, MAX_RANGE - self.traveled)
        self.x += self.dx * step
        self.y += self.dy * step
        self.traveled += step

        for platform in platforms:
            oxmin, oxmax, oymin, oymax = platform.aabb()
            if oxmin <= self.x <= oxmax and oymin <= self.y <= oymax:
                self.anchor_x, self.anchor_y = self.x, self.y
                self.length = self.traveled
                self.state = ATTACHED
                self.host = platform
                return

        if self.traveled >= MAX_RANGE:
            self.state = RETRACTING

    def __return(self, px, py):
        dx, dy = px - self.x, py - self.y
        dist = (dx ** 2 + dy ** 2) ** 0.5

        if dist <= SPEED:
            self.state = 0
            return

        self.x += dx / dist * SPEED
        self.y += dy / dist * SPEED

    def release(self):
        if self.state:
            self.state = RETRACTING

    def attached(self):
        return bool(self.state & ATTACHED)

    def done(self):
        return self.state == 0

    def draw(self, px, py):
        if self.state & ATTACHED:
            pyxel.line(px, py, self.anchor_x, self.anchor_y, COLOR)
            pyxel.circ(self.anchor_x, self.anchor_y, 1, COLOR)
        else:
            pyxel.line(px, py, self.x, self.y, COLOR)
