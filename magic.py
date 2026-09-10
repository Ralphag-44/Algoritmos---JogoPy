from math import atan2, cos, sin

import pyxel

from entity import Entity
from config import wrap
from explosion import Blast

SPEED = 1.15
TURN = 0.045
HOMING = 75
FUSE = 120

RADIUS = 20.0
DAMAGE = 10

SIZE = 3.0
SPIN = 0.18
STEP = 1.0

COLOR = 2
COLOR_CORE = 14
COLOR_WARN = 8


class Magic(Entity):
    __slots__ = ('vx', 'vy', 'heading', 'timer')

    def __init__(self, x, y, tx, ty):
        self.heading = atan2(ty - y, tx - x)

        super().__init__(True, x, y, 4, SIZE, [], 'color', color=COLOR)

        self.vx = cos(self.heading) * SPEED
        self.vy = sin(self.heading) * SPEED
        self.timer = 0

    def update(self, platforms, player, world):
        self.timer += 1
        self.rotate(SPIN)

        if self.timer <= HOMING:
            self.__steer(player)

        if self.timer >= FUSE:
            self.__blow(world)
            return False

        return not self.__advance(platforms, player, world)

    def __steer(self, player):
        px, py = player.points[-1]
        cx, cy = self.points[-1]

        error = wrap(atan2(py - cy, px - cx) - self.heading)
        self.heading = wrap(self.heading + max(-TURN, min(TURN, error)))

        self.vx = cos(self.heading) * SPEED
        self.vy = sin(self.heading) * SPEED

    def __advance(self, platforms, player, world):
        steps = max(1, int(SPEED / STEP) + 1)
        step_x = self.vx / steps
        step_y = self.vy / steps

        for _ in range(steps):
            self.translate(step_x, step_y)

            if self.collide(player):
                self.__blow(world)
                return True

            for platform in platforms:
                if self.collide(platform):
                    self.translate(-step_x, -step_y)
                    self.__blow(world)
                    return True

        return False

    def __blow(self, world):
        cx, cy = self.points[-1]
        world.blasts.append(Blast(cx, cy, RADIUS, 1, DAMAGE))

    def draw(self):
        cx, cy = self.points[-1]

        grow = self.timer / FUSE
        pyxel.circb(cx, cy, RADIUS, COLOR_WARN)
        pyxel.circ(cx, cy, RADIUS * grow, COLOR_WARN)

        super().draw()
        pyxel.pset(cx, cy, COLOR_CORE)
