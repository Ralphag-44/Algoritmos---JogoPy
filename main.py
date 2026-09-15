import random

import pyxel

from config import DEBUG
from player import Player, MAX_HP, KEY_LEFT, KEY_RIGHT, KEY_JUMP, KEY_HOOK_HOLD, KEY_ROPE_IN, KEY_ROPE_OUT
from plataform import Platform, MovingPlatform
from projectile import Projectile
from enemy import Archer, Charger, Caster
from lava import Lava

WIDTH = 256
HEIGHT = 192
FPS = 60

LEVEL_WIDTH = 256
LEVEL_HEIGHT = 192 * 12

TIER = 42
NEAR_X = 200.0
NEAR_Y = 160.0
AWAKE = 260.0

SPAWN_X = 30
SEED = 7


class World:
    __slots__ = ('arrows', 'spells', 'blasts')

    def __init__(self):
        self.arrows = []
        self.spells = []
        self.blasts = []


class Game:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="Jogo-Algoritmo", fps=FPS)
        pyxel.mouse(True)

        self.cam_x = 0
        self.cam_y = 0

        self.player = Player(SPAWN_X, LEVEL_HEIGHT - 30, half_size=3)
        self.platforms, self.enemies = self.__build_level()
        self.lava = Lava(LEVEL_HEIGHT, LEVEL_WIDTH)
        self.projectiles = []
        self.world = World()

        pyxel.run(self.update, self.draw)

    @staticmethod
    def __build_level():
        sorteador = random.Random(SEED)

        platforms = [
            Platform(LEVEL_WIDTH / 2, LEVEL_HEIGHT - 5, [
                (0, LEVEL_HEIGHT - 10), (LEVEL_WIDTH, LEVEL_HEIGHT - 10),
                (LEVEL_WIDTH, LEVEL_HEIGHT), (0, LEVEL_HEIGHT),
            ]),
        ]
        enemies = []

        kinds = (Archer, Charger, Caster)
        y = LEVEL_HEIGHT - 60
        tier = 0

        while y > 80:
            w = sorteador.choice((44, 52, 60))
            h = 8
            x = 12 + (LEVEL_WIDTH - 24 - w) * (0.15 if tier % 2 else 0.85)
            x += sorteador.randint(-10, 10)
            x = max(6, min(LEVEL_WIDTH - w - 6, x))

            corners = [(x, y - h), (x + w, y - h), (x + w, y), (x, y)]
            cx, cy = x + w / 2, y - h / 2

            if tier % 5 == 4:
                reach = sorteador.choice((-1, 1)) * sorteador.randint(50, 80)
                to_x = max(w / 2 + 6, min(LEVEL_WIDTH - w / 2 - 6, cx + reach))
                platforms.append(MovingPlatform(cx, cy, corners, to_x, cy,
                                                speed=sorteador.uniform(0.5, 0.85)))
            else:
                platforms.append(Platform(cx, cy, corners))

                if tier % 3 == 2:
                    kind = kinds[(tier // 3) % 3]
                    enemies.append(kind(cx, y - h - 8))

            if tier % 4 == 3:
                wx = 6 if tier % 8 == 3 else LEVEL_WIDTH - 14
                wy = y - TIER
                platforms.append(Platform(wx + 4, wy - 35, [
                    (wx, wy - 70), (wx + 8, wy - 70), (wx + 8, wy), (wx, wy),
                ]))

            y -= TIER
            tier += 1

        return platforms, enemies

    def update(self):
        keys = self.__read_keys()

        self.lava.update()
        self.__update_platforms()

        self.__handle_hook(keys)
        self.player.update(keys, self.__near(self.player))

        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            self.__fire()

        self.__update_enemies()

        self.projectiles = [p for p in self.projectiles
                            if p.update(self.__near(p)) and not self.__hit_enemies(p)]

        self.world.arrows = [a for a in self.world.arrows
                             if a.update(self.__near(a), self.player)]
        self.world.spells = [m for m in self.world.spells
                             if m.update(self.__near(m), self.player, self.world)]
        self.world.blasts = [b for b in self.world.blasts if b.update(self.player)]

        self.__update_camera()

        if not self.player.alive() or self.lava.kills(self.player):
            self.__reset()

    def __update_platforms(self):
        for platform in self.platforms:
            dx, dy = platform.update()

            if (dx or dy) and self.player.ground_platform is platform:
                self.player.translate(dx, dy)

    def __update_enemies(self):
        cy = self.player.points[-1][1]
        alive = []

        for enemy in self.enemies:
            if abs(enemy.points[-1][1] - cy) > AWAKE:
                alive.append(enemy)
                continue

            if enemy.update(self.player, self.__near(enemy), self.world):
                alive.append(enemy)

        self.enemies = alive

    def __hit_enemies(self, projectile):
        if not projectile.active:
            return False

        cy = self.player.points[-1][1]
        for enemy in self.enemies:
            if abs(enemy.points[-1][1] - cy) > AWAKE:
                continue
            if projectile.collide(enemy):
                enemy.hurt(projectile.damage)
                return True

        return False

    def __near(self, entity):
        cx, cy = entity.points[-1]
        return [p for p in self.platforms
                if abs(p.points[-1][0] - cx) < NEAR_X + p.size
                and abs(p.points[-1][1] - cy) < NEAR_Y + p.size]

    def __reset(self):
        self.player.respawn(SPAWN_X, LEVEL_HEIGHT - 30)
        self.platforms, self.enemies = self.__build_level()
        self.lava.reset()
        self.projectiles.clear()
        self.world.arrows.clear()
        self.world.spells.clear()
        self.world.blasts.clear()

    def __update_camera(self):
        cx, cy = self.player.points[-1]
        self.cam_x = min(max(cx - WIDTH / 2, 0), max(LEVEL_WIDTH - WIDTH, 0))
        self.cam_y = min(max(cy - HEIGHT / 2, 0), max(LEVEL_HEIGHT - HEIGHT, 0))

    def __mouse_world(self):
        return pyxel.mouse_x + self.cam_x, pyxel.mouse_y + self.cam_y

    @staticmethod
    def __read_keys():
        keys = 0

        if pyxel.btn(pyxel.KEY_A):
            keys |= KEY_LEFT
        if pyxel.btn(pyxel.KEY_D):
            keys |= KEY_RIGHT
        if pyxel.btnp(pyxel.KEY_W):
            keys |= KEY_JUMP
        if pyxel.btn(pyxel.KEY_W):
            keys |= KEY_ROPE_IN
        if pyxel.btn(pyxel.KEY_S):
            keys |= KEY_ROPE_OUT
        if pyxel.btn(pyxel.MOUSE_BUTTON_RIGHT):
            keys |= KEY_HOOK_HOLD

        return keys

    def __handle_hook(self, keys):
        if keys & KEY_HOOK_HOLD:
            if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
                tx, ty = self.__mouse_world()
                self.player.fire_hook(tx, ty)
        else:
            self.player.release_hook()

    def __fire(self):
        tx, ty = self.__mouse_world()
        cx, cy, vx, vy = self.player.fire(tx, ty)
        self.projectiles.append(Projectile(cx, cy, vx, vy))

    def draw(self):
        pyxel.camera(self.cam_x, self.cam_y)
        pyxel.cls(7)

        top = self.cam_y - 40
        bottom = self.cam_y + HEIGHT + 40

        for platform in self.platforms:
            if top < platform.points[-1][1] < bottom:
                platform.draw()

        self.lava.draw()
        if DEBUG:
            self.lava.draw_debug()

        for arrow in self.world.arrows:
            arrow.draw()

        for projectile in self.projectiles:
            projectile.draw()

        for enemy in self.enemies:
            if top < enemy.points[-1][1] < bottom:
                enemy.draw()

        for spell in self.world.spells:
            spell.draw()

        for blast in self.world.blasts:
            blast.draw()

        self.player.draw()
        self.__draw_hud()

    def __draw_hud(self):
        pyxel.camera()

        pyxel.rect(4, 4, 52, 6, 0)
        pyxel.rect(5, 5, 50 * self.player.hp / MAX_HP, 4, 8)
        pyxel.text(60, 5, f"{self.player.hp}/{MAX_HP}", 0)

        height = int(LEVEL_HEIGHT - self.player.points[-1][1])
        pyxel.text(WIDTH - 40, 5, f"{height}m", 0)


Game()
