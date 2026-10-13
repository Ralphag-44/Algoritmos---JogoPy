import pyxel

COLOR_BOOM = 9
COLOR_CORE = 10

FLASH = 8


class Blast:
    __slots__ = ('x', 'y', 'radius', 'damage', 'timer')

    def __init__(self, x, y, radius, damage):
        self.x = x
        self.y = y
        self.radius = radius
        self.damage = damage
        self.timer = 0

    def update(self, player):
        # o dano acontece so no primeiro frame, o resto e o clarao sumindo
        if self.timer == 0:
            self.__hit(player)

        self.timer += 1
        return self.timer < FLASH

    def __hit(self, player):
        px, py = player.points[-1]
        if (px - self.x) ** 2 + (py - self.y) ** 2 <= self.radius ** 2:
            player.hurt(self.damage)

    def draw(self):
        fade = 1.0 - self.timer / FLASH
        pyxel.circ(self.x, self.y, self.radius * fade, COLOR_BOOM)
        pyxel.circb(self.x, self.y, self.radius, COLOR_CORE)
