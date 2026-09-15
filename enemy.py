from math import sin

import pyxel

from entity import Entity
from config import GRAVITY
from arrow import Arrow, aim_ballistic
from explosion import Blast
from magic import Magic

MAX_FALL = 6.0
HURT_FLASH = 6
CONTACT_DAMAGE = 4

ARCHER_HP = 16
ARCHER_RANGE = 110.0
ARCHER_COOLDOWN = 100
ARCHER_AIM = 28
ARCHER_SPEED = 5.5
ARROW_DAMAGE = 6

CHARGER_HP = 12
CHARGER_SPEED = 0.9
CHARGER_SIGHT = 150.0
CHARGER_TRIGGER = 26.0
CHARGER_FUSE = 34
CHARGER_RADIUS = 26.0
CHARGER_DAMAGE = 14

CASTER_HP = 20
CASTER_SPEED = 0.55
CASTER_KEEP = 70.0
CASTER_SIGHT = 135.0
CASTER_COOLDOWN = 150
CASTER_CAST = 26


class Enemy(Entity):
    __slots__ = ('vx', 'vy', 'hp', 'ground', 'flash', 'timer', 'walker')

    def __init__(self, cx, cy, num_p, size, color, hp, walker=True, angle_offset=0.0):
        super().__init__(True, cx, cy, num_p, size, [], 'color',
                         color=color, angle_offset=angle_offset)

        self.vx = 0.0
        self.vy = 0.0
        self.hp = hp
        self.ground = False
        self.flash = 0
        self.timer = 0
        self.walker = walker

    def update(self, player, platforms, world):
        self.timer += 1
        if self.flash:
            self.flash -= 1

        self.think(player, platforms, world)

        if self.walker:
            self.vy = min(self.vy + GRAVITY, MAX_FALL)

        self.__move(platforms)

        if self.collide(player):
            player.hurt(CONTACT_DAMAGE)

        return self.hp > 0

    def think(self, player, platforms, world):
        pass

    def hurt(self, damage):
        self.hp -= damage
        self.flash = HURT_FLASH

    def dist_to(self, player):
        cx, cy = self.points[-1]
        px, py = player.points[-1]
        return px - cx, py - cy

    def __move(self, platforms):
        self.translate(self.vx, 0)
        for platform in platforms:
            empurrao = self.resolve(platform, 'x', self.vx)
            if empurrao:
                self.translate(empurrao, 0)
                self.vx = 0.0

        self.translate(0, self.vy)
        self.ground = False
        for platform in platforms:
            empurrao = self.resolve(platform, 'y', self.vy)
            if empurrao:
                self.translate(0, empurrao)
                if self.vy > 0:
                    self.ground = True
                self.vy = 0.0

    def draw(self):
        if self.flash:
            color = self.color
            self.color = 7
            super().draw()
            self.color = color
            return
        super().draw()


class Archer(Enemy):
    __slots__ = ('cooldown', 'aiming', 'shot')

    def __init__(self, cx, cy):
        super().__init__(cx, cy, 3, 5.0, 1, ARCHER_HP)
        self.cooldown = 0
        self.aiming = 0
        self.shot = None

    def think(self, player, platforms, world):
        self.vx = 0.0

        dx, dy = self.dist_to(player)
        far = (dx * dx + dy * dy) ** 0.5 > ARCHER_RANGE

        if self.aiming:
            self.aiming -= 1
            if self.aiming == 0 and not far:
                self.__shoot(world)
            elif self.aiming == 0:
                self.shot = None
            return

        if self.cooldown:
            self.cooldown -= 1
            return

        if far:
            return

        cx, cy = self.points[-1]
        px, py = player.points[-1]
        self.shot = aim_ballistic(cx, cy, px, py, ARCHER_SPEED)

        if self.shot is not None:
            self.aiming = ARCHER_AIM

    def __shoot(self, world):
        cx, cy = self.points[-1]
        vx, vy = self.shot

        speed = (vx * vx + vy * vy) ** 0.5 or 1.0
        world.arrows.append(Arrow(cx + vx / speed * 7, cy + vy / speed * 7,
                                  vx, vy, ARROW_DAMAGE))

        self.shot = None
        self.cooldown = ARCHER_COOLDOWN

    def draw(self):
        super().draw()

        if self.aiming and self.shot is not None:
            cx, cy = self.points[-1]
            vx, vy = self.shot
            speed = (vx * vx + vy * vy) ** 0.5 or 1.0
            pyxel.line(cx, cy, cx + vx / speed * 14, cy + vy / speed * 14, 8)


class Charger(Enemy):
    __slots__ = ('fuse',)

    def __init__(self, cx, cy):
        super().__init__(cx, cy, 4, 4.5, 8, CHARGER_HP)
        self.fuse = 0

    def think(self, player, platforms, world):
        dx, dy = self.dist_to(player)
        dist = (dx * dx + dy * dy) ** 0.5

        if self.fuse:
            self.fuse -= 1
            self.vx = 0.0
            if self.fuse == 0:
                self.__blow(world, player)
            return

        if dist > CHARGER_SIGHT:
            self.vx = 0.0
            return

        if dist <= CHARGER_TRIGGER:
            self.fuse = CHARGER_FUSE
            self.vx = 0.0
            return

        way = 1.0 if dx > 0 else -1.0
        blocked = self.vx and abs(self.vx) < CHARGER_SPEED * 0.5

        self.vx = way * CHARGER_SPEED
        if self.ground and (blocked or dy < -12):
            self.vy = -3.2

    def __blow(self, world, player):
        cx, cy = self.points[-1]
        world.blasts.append(Blast(cx, cy, CHARGER_RADIUS, 1, CHARGER_DAMAGE))
        self.hp = 0

    def draw(self):
        super().draw()

        if self.fuse:
            cx, cy = self.points[-1]
            grow = 1.0 - self.fuse / CHARGER_FUSE
            pyxel.circb(cx, cy, CHARGER_RADIUS, 8)
            pyxel.circ(cx, cy, CHARGER_RADIUS * grow, 8)


class Caster(Enemy):
    __slots__ = ('cooldown', 'casting')

    def __init__(self, cx, cy):
        super().__init__(cx, cy, 5, 5.0, 2, CASTER_HP, walker=False)
        self.cooldown = CASTER_COOLDOWN // 2
        self.casting = 0

    def think(self, player, platforms, world):
        dx, dy = self.dist_to(player)
        dist = (dx * dx + dy * dy) ** 0.5 or 1.0

        if dist > CASTER_SIGHT:
            self.vx = self.vy = 0.0
            self.casting = 0
            return

        if self.casting:
            self.vx = self.vy = 0.0
            self.casting -= 1
            if self.casting == 0:
                self.__cast(player, world)
            return

        way = 1.0 if dist > CASTER_KEEP else -1.0
        self.vx = dx / dist * CASTER_SPEED * way
        self.vy = dy / dist * CASTER_SPEED * way + sin(self.timer * 0.05) * 0.3

        if self.cooldown:
            self.cooldown -= 1
            return

        self.casting = CASTER_CAST

    def __cast(self, player, world):
        cx, cy = self.points[-1]
        px, py = player.points[-1]
        world.spells.append(Magic(cx, cy, px, py))
        self.cooldown = CASTER_COOLDOWN

    def draw(self):
        super().draw()

        if self.casting:
            cx, cy = self.points[-1]
            grow = 1.0 - self.casting / CASTER_CAST
            pyxel.circb(cx, cy, 3 + 5 * grow, 2)
