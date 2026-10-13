import random

import pyxel

from config import DEBUG
from player import Player, MAX_HP, KEY_HOOK_HOLD, KEY_HOOK_FIRE, KEY_FIRE
from plataform import Platform, MovingPlatform
from projectile import Projectile
from enemy import Archer, Charger, Caster
from lava import Lava
from difficulty import Difficulty
from ui import label, label_right, label_center

WIDTH = 256
HEIGHT = 192

LEVEL_WIDTH = 256
LEVEL_HEIGHT = 192 * 12

TIER = 42
NEAR_X = 200.0
NEAR_Y = 160.0
AWAKE = 260.0

SPAWN_X = 30
SPAWN_Y = LEVEL_HEIGHT - 30
SEED = 7

HP_BAR = 40
BANNER_TIME = 90

COLOR_SKY = 7
COLOR_TEXT = 5
COLOR_SOFT = 13
COLOR_HP = 8
COLOR_ALERT = 8


class World:
    __slots__ = ('arrows', 'spells', 'blasts', 'pace')

    def __init__(self):
        self.arrows = []
        self.spells = []
        self.blasts = []
        self.pace = 1.0


class Session:
    __slots__ = ('player', 'platforms', 'enemies', 'lava', 'projectiles', 'world',
                 'difficulty', 'cam_x', 'cam_y', 'best', 'banner')

    def __init__(self):
        self.player = Player(SPAWN_X, SPAWN_Y, half_size=3)
        self.platforms, self.enemies = Session.__build_level()
        self.lava = Lava(LEVEL_HEIGHT, LEVEL_WIDTH)
        self.projectiles = []
        self.world = World()
        self.difficulty = Difficulty()

        self.cam_x = self.cam_y = 0
        self.best = 0
        self.banner = 0
        self.__update_camera()

    @staticmethod
    def __build_level():
        rng = random.Random(SEED)

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
            w = rng.choice((44, 52, 60))
            h = 8
            x = 12 + (LEVEL_WIDTH - 24 - w) * (0.15 if tier % 2 else 0.85)
            x += rng.randint(-10, 10)
            x = max(6, min(LEVEL_WIDTH - w - 6, x))

            corners = [(x, y - h), (x + w, y - h), (x + w, y), (x, y)]
            cx, cy = x + w / 2, y - h / 2

            if tier % 5 == 4:
                reach = rng.choice((-1, 1)) * rng.randint(50, 80)
                to_x = max(w / 2 + 6, min(LEVEL_WIDTH - w / 2 - 6, cx + reach))
                platforms.append(MovingPlatform(cx, cy, corners, to_x, cy,
                                                speed=rng.uniform(0.5, 0.85)))
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

    def step(self, keys, tx, ty):
        self.__update_difficulty()

        self.lava.update(self.difficulty.lava())
        self.__update_platforms()

        if keys & KEY_HOOK_FIRE:
            self.player.fire_hook(tx, ty)
        elif not keys & KEY_HOOK_HOLD:
            self.player.release_hook()

        self.player.update(keys, self.__near(self.player))

        if keys & KEY_FIRE:
            cx, cy, vx, vy = self.player.fire(tx, ty)
            self.projectiles.append(Projectile(cx, cy, vx, vy))

        self.__update_enemies()

        self.projectiles = [p for p in self.projectiles
                            if p.update(self.__near(p)) and not self.__hit_enemies(p)]

        self.world.arrows = [a for a in self.world.arrows
                             if a.update(self.__near(a), self.player)]
        self.world.spells = [m for m in self.world.spells
                             if m.update(self.__near(m), self.player, self.world)]
        self.world.blasts = [b for b in self.world.blasts if b.update(self.player)]

        self.__update_camera()
        self.best = max(self.best, self.height())

    def over(self):
        return not self.player.alive() or self.lava.kills(self.player)

    def height(self):
        return max(0, int(LEVEL_HEIGHT - self.player.points[-1][1]))

    def __update_difficulty(self):
        self.difficulty.update()
        self.world.pace = self.difficulty.enemies()

        # mostra o aviso de nivel novo por BANNER_TIME frames
        if self.difficulty.leveled_up():
            self.banner = BANNER_TIME
        elif self.banner:
            self.banner -= 1

    def __update_platforms(self):
        pace = self.difficulty.platforms()

        for platform in self.platforms:
            platform.update(pace)

            # quem esta em cima anda junto com a plataforma
            if self.player.ground_platform is platform:
                self.player.translate(platform.dx, platform.dy)

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

    def __update_camera(self):
        cx, cy = self.player.points[-1]
        self.cam_x = min(max(cx - WIDTH / 2, 0), max(LEVEL_WIDTH - WIDTH, 0))
        self.cam_y = min(max(cy - HEIGHT / 2, 0), max(LEVEL_HEIGHT - HEIGHT, 0))

    def draw(self):
        pyxel.camera(self.cam_x, self.cam_y)
        pyxel.cls(COLOR_SKY)

        top = self.cam_y - 40
        bottom = self.cam_y + HEIGHT + 40

        for platform in self.platforms:
            if top < platform.points[-1][1] < bottom:
                platform.draw()

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

        self.lava.draw(bottom)
        if DEBUG:
            self.lava.draw_debug()

        pyxel.camera()

    def draw_hud(self):
        # vida: barra fina no canto de cima a esquerda
        hp = max(self.player.hp, 0)
        pyxel.rect(5, 5, HP_BAR + 2, 5, COLOR_SKY)
        pyxel.rect(6, 6, HP_BAR, 3, COLOR_SOFT)
        pyxel.rect(6, 6, HP_BAR * hp // MAX_HP, 3, COLOR_HP)
        label(6 + HP_BAR + 4, 5, f"{hp}", COLOR_TEXT)

        # altura e nivel no canto de cima a direita
        label_right(WIDTH - 6, 5, f"{self.height()}m", COLOR_TEXT)
        label_right(WIDTH - 6, 13, f"nivel {self.difficulty.level()}", COLOR_SOFT)

        if self.banner:
            label_center(WIDTH // 2, 24, f"nivel {self.difficulty.level()}: tudo mais rapido", COLOR_ALERT)
