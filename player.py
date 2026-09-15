from math import pi, sqrt

import pyxel

from entity import Entity
from hook import Hook, MAX_RANGE
from config import GRAVITY

MOVE_SPEED = 1.4
JUMP_SPEED = 3.6
MAX_FALL = 6.0
HOOK_PULL = 0.15
ROPE_SPEED = 1.5
MIN_ROPE = 10.0

WALL_JUMP_X = 2.6
WALL_JUMP_Y = 3.8
WALL_COYOTE = 6
WALL_LOCK = 9
WALL_SLIDE = 1.4

MAX_HP = 50
IFRAMES = 45

ON_GROUND    = 1 << 0
JUMPING      = 1 << 1
DOUBLE_JUMP  = 1 << 2
HOOKED       = 1 << 3
FACING_RIGHT = 1 << 4

KEY_LEFT      = 1 << 0
KEY_RIGHT     = 1 << 1
KEY_JUMP      = 1 << 2
KEY_HOOK_HOLD = 1 << 3
KEY_ROPE_IN   = 1 << 4
KEY_ROPE_OUT  = 1 << 5


class Player(Entity):
    __slots__ = ('half', 'vx', 'vy', 'state', 'hook', 'hp', 'iframes',
                 'wall_dir', 'wall_timer', 'lock', 'ground_platform')

    def __init__(self, cx, cy, half_size=4):
        super().__init__(True, cx, cy, 4, half_size * sqrt(2), [], 'color', color=8, angle_offset=pi / 4)

        self.half = half_size
        self.vx = 0.0
        self.vy = 0.0
        self.state = DOUBLE_JUMP | FACING_RIGHT
        self.hook = None

        self.hp = MAX_HP
        self.iframes = 0

        self.wall_dir = 0
        self.wall_timer = 0
        self.lock = 0
        self.ground_platform = None

    def update(self, keys, platforms):
        if self.iframes:
            self.iframes -= 1
        if self.wall_timer:
            self.wall_timer -= 1
        if self.lock:
            self.lock -= 1

        swinging = self.__update_hook(platforms)

        if swinging:
            self.state |= HOOKED
            self.__swing(keys)
        else:
            self.state &= ~HOOKED
            self.__walk(keys)
            self.vy = min(self.vy + GRAVITY, MAX_FALL)

            if self.__on_wall() and self.vy > WALL_SLIDE:
                self.vy = WALL_SLIDE

            if keys & KEY_JUMP:
                self.__jump()

        self.__move_and_collide(platforms)

    def __update_hook(self, platforms):
        if not self.hook:
            return False

        was_attached = bool(self.state & HOOKED)
        cx, cy = self.points[-1]
        self.hook.update(cx, cy, platforms)

        if self.hook.done():
            self.hook = None
            return False

        if not self.hook.attached():
            return False

        if not was_attached:
            self.__set_rope(cx, cy)

        return True

    def __set_rope(self, cx, cy):
        dx, dy = cx - self.hook.anchor_x, cy - self.hook.anchor_y
        dist = (dx * dx + dy * dy) ** 0.5
        self.hook.length = min(max(dist, MIN_ROPE), MAX_RANGE)

    def __walk(self, keys):
        if self.lock:
            return

        self.vx = 0.0
        if keys & KEY_LEFT:
            self.vx -= MOVE_SPEED
            self.state &= ~FACING_RIGHT
        if keys & KEY_RIGHT:
            self.vx += MOVE_SPEED
            self.state |= FACING_RIGHT

    def __on_wall(self):
        return self.wall_timer and not (self.state & ON_GROUND)

    def __jump(self):
        if self.state & ON_GROUND:
            self.vy = -JUMP_SPEED
            self.state = (self.state & ~ON_GROUND) | JUMPING
        elif self.__on_wall():
            self.vy = -WALL_JUMP_Y
            self.vx = -self.wall_dir * WALL_JUMP_X
            self.lock = WALL_LOCK
            self.wall_timer = 0
            self.state |= JUMPING
            if self.wall_dir > 0:
                self.state &= ~FACING_RIGHT
            else:
                self.state |= FACING_RIGHT
        elif self.state & DOUBLE_JUMP:
            self.vy = -JUMP_SPEED
            self.state &= ~DOUBLE_JUMP

    def fire_hook(self, tx, ty):
        if self.hook is None:
            cx, cy = self.points[-1]
            self.hook = Hook(cx, cy, tx, ty)

    def release_hook(self):
        if self.hook:
            self.hook.release()

    def __swing(self, keys):
        cx, cy = self.points[-1]

        if keys & KEY_ROPE_IN:
            self.hook.length = max(self.hook.length - ROPE_SPEED, MIN_ROPE)
        if keys & KEY_ROPE_OUT:
            self.hook.length = min(self.hook.length + ROPE_SPEED, MAX_RANGE)

        hx, hy = self.hook.anchor_x, self.hook.anchor_y

        self.vy += GRAVITY
        if keys & KEY_LEFT:
            self.vx -= HOOK_PULL
        if keys & KEY_RIGHT:
            self.vx += HOOK_PULL

        nx = cx + self.vx
        ny = cy + self.vy

        dx = nx - hx
        dy = ny - hy
        dist = (dx ** 2 + dy ** 2) ** 0.5

        if dist > self.hook.length and dist > 0:
            scale = self.hook.length / dist
            nx = hx + dx * scale
            ny = hy + dy * scale

        self.vx = nx - cx
        self.vy = ny - cy

    def hurt(self, damage):
        if self.iframes or self.hp <= 0:
            return False

        self.hp -= damage
        self.iframes = IFRAMES
        return True

    def alive(self):
        return self.hp > 0

    def __move_and_collide(self, platforms):
        self.translate(self.vx, 0)
        for platform in platforms:
            self.__resolve(platform, axis='x')

        self.translate(0, self.vy)
        self.state &= ~ON_GROUND
        self.ground_platform = None
        for platform in platforms:
            self.__resolve(platform, axis='y')

    def __resolve(self, platform, axis):
        if axis == 'x':
            push = self.resolve(platform, 'x', self.vx)
            if not push:
                return

            self.wall_dir = 1 if self.vx > 0 else -1
            self.wall_timer = WALL_COYOTE

            self.translate(push, 0)
            self.vx = 0
            return

        push = self.resolve(platform, 'y', self.vy)
        if not push:
            return

        if self.vy > 0:
            self.state |= (ON_GROUND | DOUBLE_JUMP)
            self.state &= ~JUMPING
            self.ground_platform = platform

        self.translate(0, push)
        self.vy = 0

    def fire(self, target_x, target_y, speed=3.0):
        cx, cy = self.points[-1]
        dx = target_x - cx
        dy = target_y - cy
        dist = (dx ** 2 + dy ** 2) ** 0.5 or 1
        return cx, cy, dx / dist * speed, dy / dist * speed

    def respawn(self, cx, cy):
        px, py = self.points[-1]
        self.translate(cx - px, cy - py)

        self.vx = self.vy = 0.0
        self.hp = MAX_HP
        self.iframes = IFRAMES
        self.state = DOUBLE_JUMP | FACING_RIGHT
        self.hook = None
        self.wall_timer = self.lock = 0
        self.ground_platform = None

    def draw(self):
        if not (self.iframes and pyxel.frame_count % 6 < 3):
            super().draw()

        if self.hook:
            cx, cy = self.points[-1]
            self.hook.draw(cx, cy)
