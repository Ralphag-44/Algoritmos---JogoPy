from math import sin

import pyxel

RISE_SPEED = 0.15
START_BELOW = 48.0

SEGMENTS = 4
SAMPLES = 6

WAVE_AMP = 2.5
WAVE_SPEED = 0.06
WAVE_PHASE = 1.1

CTRL_AMP = 5.0
CTRL_SPEED = 0.09
CTRL_PHASE = 2.3

COLOR = 8
COLOR_CTRL_LINE = 13
COLOR_CTRL_POINT = 12
COLOR_LEVEL = 11


class Lava:
    __slots__ = ('level', 'start', 'speed', 'width', 'timer')

    def __init__(self, bottom, width, speed=RISE_SPEED):
        self.start = bottom + START_BELOW
        self.level = self.start
        self.speed = speed
        self.width = width
        self.timer = 0

    def update(self):
        self.timer += 1
        self.level -= self.speed

    def reset(self):
        self.level = self.start
        self.timer = 0

    def kills(self, entity):
        return entity.points[-1][1] >= self.level

    @staticmethod
    def __point(p0, p1, p2, p3, t):
        u = 1.0 - t
        a = u * u * u
        b = 3 * u * u * t
        c = 3 * u * t * t
        d = t * t * t
        return (a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0],
                a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1])

    def __anchor(self, i):
        x = self.width * i / SEGMENTS
        y = self.level + sin(self.timer * WAVE_SPEED + i * WAVE_PHASE) * WAVE_AMP
        return x, y

    def __segment(self, i):
        p0 = self.__anchor(i)
        p3 = self.__anchor(i + 1)

        third = (p3[0] - p0[0]) / 3.0
        phase = self.timer * CTRL_SPEED + i * CTRL_PHASE

        p1 = (p0[0] + third, p0[1] + sin(phase) * CTRL_AMP)
        p2 = (p3[0] - third, p3[1] + sin(phase + 1.6) * CTRL_AMP)

        return p0, p1, p2, p3

    def draw(self):
        for i in range(SEGMENTS):
            p0, p1, p2, p3 = self.__segment(i)

            prev = p0
            for s in range(1, SAMPLES + 1):
                cur = Lava.__point(p0, p1, p2, p3, s / SAMPLES)
                pyxel.line(prev[0], prev[1], cur[0], cur[1], COLOR)
                prev = cur

    def draw_debug(self):
        pyxel.line(0, self.level, self.width, self.level, COLOR_LEVEL)

        for i in range(SEGMENTS):
            p0, p1, p2, p3 = self.__segment(i)

            pyxel.line(p0[0], p0[1], p1[0], p1[1], COLOR_CTRL_LINE)
            pyxel.line(p1[0], p1[1], p2[0], p2[1], COLOR_CTRL_LINE)
            pyxel.line(p2[0], p2[1], p3[0], p3[1], COLOR_CTRL_LINE)

            pyxel.circb(p1[0], p1[1], 1, COLOR_CTRL_POINT)
            pyxel.circb(p2[0], p2[1], 1, COLOR_CTRL_POINT)
            pyxel.circ(p0[0], p0[1], 1, COLOR_LEVEL)

        last = self.__anchor(SEGMENTS)
        pyxel.circ(last[0], last[1], 1, COLOR_LEVEL)
