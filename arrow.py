from math import atan2, cos, sin, hypot

from entity import Entity
from config import GRAVITY, wrap
from sprites import ARROW

LENGTH = 6.0
HALF_W = 1.4

DRAG = 0.998
ALIGN = 0.0055
SPIN_DRAG = 0.14
MAX_SPIN = 0.35

EMBED = 0.9
MIN_EMBED = 1.0
MAX_EMBED = LENGTH * 1.6

STEP = 1.0
STUCK_LIFE = 600


class Arrow(Entity):
    __slots__ = ('vx', 'vy', 'angle', 'spin', 'stuck', 'host', 'age', 'damage')

    def __init__(self, x, y, vx, vy, damage=6):
        angle = atan2(vy, vx)
        ca, sa = cos(angle), sin(angle)

        shape = []
        for ox, oy in ((LENGTH, 0.0), (-LENGTH * 0.5, -HALF_W),
                       (-LENGTH, 0.0), (-LENGTH * 0.5, HALF_W)):
            shape.append((x + ox * ca - oy * sa, y + ox * sa + oy * ca))

        super().__init__(False, x, y, 0, LENGTH, shape, 'sprite', img=ARROW)

        self.vx = vx
        self.vy = vy
        self.angle = angle
        self.spin = 0.0
        self.stuck = False
        self.host = None
        self.age = 0
        self.damage = damage

    def update(self, platforms, player=None):
        self.age += 1

        if self.stuck:
            if self.host is not None:
                self.translate(self.host.dx, self.host.dy)
            return self.age < STUCK_LIFE

        self.vx *= DRAG
        self.vy = self.vy * DRAG + GRAVITY

        self.__aim()

        if self.__advance(platforms):
            return True

        if player is not None and self.collide(player):
            player.hurt(self.damage)
            return False

        return self.age < STUCK_LIFE

    def __aim(self):
        speed = hypot(self.vx, self.vy)
        attack = wrap(self.angle - atan2(self.vy, self.vx))

        self.spin += -ALIGN * speed * sin(attack) - SPIN_DRAG * self.spin
        self.spin = max(-MAX_SPIN, min(MAX_SPIN, self.spin))

        if self.spin:
            self.rotate(self.spin)
            self.angle = wrap(self.angle + self.spin)

    def __advance(self, platforms):
        speed = hypot(self.vx, self.vy)
        if speed == 0:
            return False

        steps = max(1, int(speed / STEP) + 1)
        step_x = self.vx / steps
        step_y = self.vy / steps

        for _ in range(steps):
            self.translate(step_x, step_y)

            for platform in platforms:
                if self.collide(platform):
                    self.translate(-step_x, -step_y)
                    self.__embed(platform, speed)
                    return True

        return False

    def __embed(self, platform, speed):
        depth = max(MIN_EMBED, min(speed * EMBED, MAX_EMBED))
        self.translate(cos(self.angle) * depth, sin(self.angle) * depth)

        self.vx = self.vy = self.spin = 0.0
        self.stuck = True
        self.host = platform
        self.age = 0

    def draw(self):
        super().draw(angle=self.angle)


def aim_ballistic(sx, sy, tx, ty, speed):
    dx = tx - sx
    side = 1.0 if dx >= 0 else -1.0
    x = abs(dx)
    y = sy - ty

    if x < 1e-3:
        return None

    v2 = speed * speed
    disc = v2 * v2 - GRAVITY * (GRAVITY * x * x + 2 * y * v2)
    if disc < 0:
        return None

    angle = atan2(v2 - disc ** 0.5, GRAVITY * x)
    return side * speed * cos(angle), -speed * sin(angle)
