from math import atan2, cos, sin, pi

import pyxel

from entity import Entity
from config import GRAVITY, wrap

LENGTH = 6.0
HALF_W = 1.4
HEAD = 3.0
FLETCH = 2.6

DRAG = 0.998
ALIGN = 0.0055
SPIN_DRAG = 0.14
MAX_SPIN = 0.35

EMBED = 0.9
MIN_EMBED = 1.0
MAX_EMBED = LENGTH * 1.6

STEP = 1.0
STUCK_LIFE = 600
COLOR = 4
COLOR_HEAD = 0
COLOR_FLETCH = 1


class Arrow(Entity):
    __slots__ = ('vx', 'vy', 'angle', 'spin', 'stuck', 'host', 'age', 'damage')

    def __init__(self, x, y, vx, vy, damage=6):
        angle = atan2(vy, vx)
        ca, sa = cos(angle), sin(angle)

        shape = []
        for ox, oy in ((LENGTH, 0.0), (-LENGTH * 0.5, -HALF_W),
                       (-LENGTH, 0.0), (-LENGTH * 0.5, HALF_W)):
            shape.append((x + ox * ca - oy * sa, y + ox * sa + oy * ca))

        super().__init__(False, x, y, 0, LENGTH, shape, 'color', color=COLOR)

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
        speed = (self.vx ** 2 + self.vy ** 2) ** 0.5
        attack = wrap(self.angle - atan2(self.vy, self.vx))

        self.spin += -ALIGN * speed * sin(attack) - SPIN_DRAG * self.spin
        self.spin = max(-MAX_SPIN, min(MAX_SPIN, self.spin))

        if self.spin:
            self.rotate(self.spin)
            self.angle = wrap(self.angle + self.spin)

    def __advance(self, platforms):
        speed = (self.vx ** 2 + self.vy ** 2) ** 0.5
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
        cx, cy = self.points[-1]
        ca, sa = cos(self.angle), sin(self.angle)

        def local(ox, oy):
            return cx + ox * ca - oy * sa, cy + ox * sa + oy * ca

        tail_x, tail_y = local(-LENGTH, 0.0)
        neck_x, neck_y = local(LENGTH - HEAD, 0.0)

        pyxel.line(tail_x, tail_y, neck_x, neck_y, COLOR)

        tip_x, tip_y = local(LENGTH, 0.0)
        bx1, by1 = local(LENGTH - HEAD, -HEAD * 0.55)
        bx2, by2 = local(LENGTH - HEAD, HEAD * 0.55)
        pyxel.tri(tip_x, tip_y, bx1, by1, bx2, by2, COLOR_HEAD)

        for side in (-1.0, 1.0):
            fx, fy = local(-LENGTH + FLETCH, side * FLETCH * 0.75)
            pyxel.line(tail_x, tail_y, fx, fy, COLOR_FLETCH)


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
