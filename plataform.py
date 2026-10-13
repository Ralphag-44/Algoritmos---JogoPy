from math import hypot

import pyxel

from entity import Entity
from sprites import STONE_TOP, STONE, RAFT, GLOW


class Platform(Entity):
    __slots__ = ('dx', 'dy')

    def __init__(self, cx, cy, list_points, tiles=(STONE_TOP, STONE)):
        super().__init__(False, cx, cy, 0, 0, list_points, 'tiles', img=tiles)

        self.dx = 0.0
        self.dy = 0.0

    def update(self, pace=1.0):
        pass


class MovingPlatform(Platform):
    __slots__ = ('ax', 'ay', 'rx', 'ry', 'step', 't', 'way')

    def __init__(self, cx, cy, list_points, to_x, to_y, speed=0.6):
        super().__init__(cx, cy, list_points, tiles=(RAFT, RAFT))

        self.ax, self.ay = cx, cy
        self.rx, self.ry = to_x - cx, to_y - cy

        span = hypot(self.rx, self.ry) or 1.0
        self.step = speed / span

        self.t = 0.0
        self.way = 1

    def update(self, pace=1.0):
        # t vai de 0 (inicio) a 1 (fim) e volta; pace acelera com a dificuldade
        self.t += self.step * self.way * pace
        if self.t >= 1.0:
            self.t, self.way = 1.0, -1
        elif self.t <= 0.0:
            self.t, self.way = 0.0, 1

        cx, cy = self.points[-1]
        dx = self.ax + self.rx * self.t - cx
        dy = self.ay + self.ry * self.t - cy

        self.translate(dx, dy)
        # guarda o quanto andou para levar junto quem esta em cima ou preso nela
        self.dx, self.dy = dx, dy

    def draw(self):
        super().draw(pal=GLOW[pyxel.frame_count // 6 % len(GLOW)])
