import pyxel

COLOR_WARN = 8
COLOR_RING = 14
COLOR_BOOM = 9
COLOR_CORE = 10

FLASH = 8


class Blast:
    __slots__ = ('x', 'y', 'radius', 'delay', 'damage', 'timer', 'blown')

    def __init__(self, x, y, radius, delay, damage):
        self.x = x
        self.y = y
        self.radius = radius
        self.delay = max(1, delay)
        self.damage = damage
        self.timer = 0
        self.blown = False

    def update(self, player):
        self.timer += 1

        if not self.blown:
            if self.timer >= self.delay:
                self.blown = True
                self.__hit(player)

            return True

        return self.timer < self.delay + FLASH

    def __hit(self, player):
        px, py = player.points[-1]
        if (px - self.x) ** 2 + (py - self.y) ** 2 <= self.radius ** 2:
            player.hurt(self.damage)

    def draw(self):
        if self.blown:
            fade = 1.0 - (self.timer - self.delay) / FLASH
            pyxel.circ(self.x, self.y, self.radius * fade, COLOR_BOOM)
            pyxel.circb(self.x, self.y, self.radius, COLOR_CORE)
            return

        grow = self.timer / self.delay
        pyxel.circb(self.x, self.y, self.radius, COLOR_WARN)
        pyxel.circ(self.x, self.y, self.radius * grow, COLOR_WARN)
        pyxel.circb(self.x, self.y, self.radius * grow, COLOR_RING)
