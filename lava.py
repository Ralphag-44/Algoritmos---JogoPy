from math import sin

import pyxel

RISE_SPEED = 0.25
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
    __slots__ = ('level', 'width', 'timer')

    def __init__(self, bottom, width):
        # indica a altura da lava
        self.level = bottom + START_BELOW
        self.width = width
        self.timer = 0

    def update(self, pace=1.0):
        self.timer += 1
        # a lava sobe
        self.level -= RISE_SPEED * pace

    def kills(self, entity):
        # morre quem esta abaixo da lava
        return entity.points[-1][1] >= self.level

    @staticmethod
    def __bezier(p0, p1, p2, p3, t):
        # quanto cada ponto puxa a curva
        u = 1.0 - t
        w0 = u * u * u
        w1 = 3 * u * u * t
        w2 = 3 * u * t * t
        w3 = t * t * t

        x = w0 * p0[0] + w1 * p1[0] + w2 * p2[0] + w3 * p3[0]
        y = w0 * p0[1] + w1 * p1[1] + w2 * p2[1] + w3 * p3[1]
        return x, y

    def __anchor(self, i):
        # ponto da superficie que sobe e desce
        x = self.width * i / SEGMENTS
        y = self.level + sin(self.timer * WAVE_SPEED + i * WAVE_PHASE) * WAVE_AMP
        return x, y

    def __segment(self, i):
        start = self.__anchor(i)
        end = self.__anchor(i + 1)

        # pontos que entortam a curva
        third = (end[0] - start[0]) / 3.0
        phase = self.timer * CTRL_SPEED + i * CTRL_PHASE

        ctrl1 = (start[0] + third, start[1] + sin(phase) * CTRL_AMP)
        ctrl2 = (end[0] - third, end[1] + sin(phase + 1.6) * CTRL_AMP)

        return start, ctrl1, ctrl2, end

    def __surface(self):
        # quebra a curva em retas curtas
        for i in range(SEGMENTS):
            p0, p1, p2, p3 = self.__segment(i)

            prev = p0
            for s in range(1, SAMPLES + 1):
                cur = Lava.__bezier(p0, p1, p2, p3, s / SAMPLES)
                yield prev, cur
                prev = cur

    def draw(self, bottom):
        # lava fora da tela
        if self.level - WAVE_AMP - CTRL_AMP > bottom:
            return

        for (x0, y0), (x1, y1) in self.__surface():
            # pinta embaixo da superficie
            for x in range(int(x0), int(x1)):
                y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
                pyxel.line(x, y, x, bottom, COLOR)

            pyxel.line(x0, y0, x1, y1, COLOR)

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
