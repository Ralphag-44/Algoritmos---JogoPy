from entity import Entity
from config import GRAVITY

DRAG = 0.985
RESTITUTION = 0.8
MIN_SPEED = 0.05
LIFETIME = 240
STEP = 1.0
DAMAGE = 8


class Projectile(Entity):
    __slots__ = ('vx', 'vy', 'age', 'active', 'damage')

    def __init__(self, x, y, vx, vy, size=1.5):
        super().__init__(True, x, y, 6, size, [], 'color', color=9)

        self.vx = vx
        self.vy = vy
        self.age = 0
        self.active = True
        self.damage = DAMAGE

    def update(self, platforms):
        self.age += 1

        if self.active:
            self.vx *= DRAG
            self.vy *= DRAG
            self.vy += GRAVITY

            self.__move_and_collide(platforms)

            speed = (self.vx ** 2 + self.vy ** 2) ** 0.5
            if speed <= MIN_SPEED:
                self.active = False

        return self.age < LIFETIME

    def __move_and_collide(self, platforms):
        dist = (self.vx ** 2 + self.vy ** 2) ** 0.5
        if dist == 0:
            return

        steps = max(1, int(dist / STEP) + 1)
        step_x = self.vx / steps
        step_y = self.vy / steps

        for _ in range(steps):
            self.translate(step_x, step_y)

            hit = None
            for platform in platforms:
                if self.collide(platform):
                    hit = platform
                    break

            if hit is not None:
                self.translate(-step_x, -step_y)
                self.__reflect(hit)
                break

    def __reflect(self, platform):
        outline_a = self.points[:-1]
        outline_b = platform.points[:-1]
        nb = len(outline_b)

        dist = None
        nx = ny = 0

        for vax, vay in outline_a:
            for i in range(nb):
                x1, y1 = outline_b[i]
                x2, y2 = outline_b[(i + 1) % nb]

                ex, ey = x2 - x1, y2 - y1
                elen2 = ex * ex + ey * ey

                t = 0 if elen2 == 0 else max(0, min(1, ((vax - x1) * ex + (vay - y1) * ey) / elen2))
                px, py = x1 + ex * t, y1 + ey * t

                dx, dy = vax - px, vay - py
                d = (dx ** 2 + dy ** 2) ** 0.5

                if dist is None or d < dist:
                    dist = d
                    nx, ny = dx, dy

        if dist is None or dist == 0:
            return

        nx, ny = nx / dist, ny / dist

        dot = self.vx * nx + self.vy * ny
        self.vx = (self.vx - 2 * dot * nx) * RESTITUTION
        self.vy = (self.vy - 2 * dot * ny) * RESTITUTION
