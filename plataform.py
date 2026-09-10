from entity import Entity

COLOR_STATIC = 0
COLOR_MOVING = 12


class Platform(Entity):
    __slots__ = ('dx', 'dy')

    def __init__(self, cx, cy, list_points, color=COLOR_STATIC):
        super().__init__(False, cx, cy, 0, 0, list_points, 'color', color=color)

        self.dx = 0.0
        self.dy = 0.0

    def update(self):
        return 0.0, 0.0


class MovingPlatform(Platform):
    __slots__ = ('ax', 'ay', 'rx', 'ry', 'step', 't', 'way')

    def __init__(self, cx, cy, list_points, to_x, to_y, speed=0.6):
        super().__init__(cx, cy, list_points, color=COLOR_MOVING)

        self.ax, self.ay = cx, cy
        self.rx, self.ry = to_x - cx, to_y - cy

        span = (self.rx ** 2 + self.ry ** 2) ** 0.5 or 1.0
        self.step = speed / span

        self.t = 0.0
        self.way = 1

    def update(self):
        self.t += self.step * self.way
        if self.t >= 1.0:
            self.t, self.way = 1.0, -1
        elif self.t <= 0.0:
            self.t, self.way = 0.0, 1

        cx, cy = self.points[-1]
        dx = self.ax + self.rx * self.t - cx
        dy = self.ay + self.ry * self.t - cy

        self.translate(dx, dy)

        self.dx, self.dy = dx, dy
        return dx, dy
