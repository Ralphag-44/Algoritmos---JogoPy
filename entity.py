from math import sin, cos, pi, floor, hypot
import numpy as np
import pyxel
from config import DEBUG
from sprites import CLEAR


def side(start, end, p):
    # diz de que lado da reta o ponto esta
    return ((end[..., 0] - start[..., 0]) * (p[..., 1] - start[..., 1])
            - (end[..., 1] - start[..., 1]) * (p[..., 0] - start[..., 0]))


class Entity:
    __slots__ = ('points', 'size', 'type', 'img')

    def __init__(self, cvx, cx, cy, num_p, size, list_points, type, img=None, angle_offset=0):
        if cvx:
            list_points = Entity.__generate_points(cx, cy, num_p, size, angle_offset)
        elif not size:
            size = Entity.__calc_size(cx, cy, list_points)

        # o centro fica sempre no ultimo ponto
        list_points.append((cx, cy))
        self.points = np.array([[x, y] for x, y in list_points], dtype=np.float32)
        self.size = size

        self.type = type
        self.img = img


    @staticmethod
    def __generate_points(cx, cy, num_points, size, angle_offset=0):
        points = []
        for i in range(num_points):
            angle = 2 * pi * i / num_points + angle_offset
            x = cx + size * cos(angle)
            y = cy + size * sin(angle)
            points.append((x, y))
        return points


    @staticmethod
    def __calc_size(cx, cy, list_points):
        return max(hypot(x - cx, y - cy) for x, y in list_points)


    def translate(self, vx, vy):
        self.points += np.array([vx, vy])


    def rotate(self, angle):
        sin_a = sin(angle)
        cos_a = cos(angle)

        center = self.points[-1]
        diff = self.points[:-1] - center

        x = diff[:, 0] * cos_a - diff[:, 1] * sin_a
        y = diff[:, 0] * sin_a + diff[:, 1] * cos_a

        self.points[:-1, 0] = x + center[0]
        self.points[:-1, 1] = y + center[1]


    def collide(self, other):
        # se estao longe nem precisa testar
        ax, ay = self.points[-1]
        bx, by = other.points[-1]
        if hypot(ax - bx, ay - by) > self.size + other.size:
            return False

        # cada aresta vai de um vertice ate o proximo
        a_start = self.points[:-1]
        a_end = np.roll(a_start, -1, axis=0)
        b_start = other.points[:-1]
        b_end = np.roll(b_start, -1, axis=0)

        # monta uma tabela com todas as arestas de A contra todas de B
        a_start = a_start[:, np.newaxis]
        a_end = a_end[:, np.newaxis]
        b_start = b_start[np.newaxis, :]
        b_end = b_end[np.newaxis, :]

        # as pontas de B ficam em lados opostos da reta de A
        b_split = (side(a_start, a_end, b_start) > 0) != (side(a_start, a_end, b_end) > 0)
        # as pontas de A ficam em lados opostos da reta de B
        a_split = (side(b_start, b_end, a_start) > 0) != (side(b_start, b_end, a_end) > 0)

        # se as duas coisas valem as arestas se cruzam
        return bool((a_split & b_split).any())


    def aabb(self):
        outline = self.points[:-1]
        return outline[:, 0].min(), outline[:, 0].max(), outline[:, 1].min(), outline[:, 1].max()


    def resolve(self, other, axis, vel):
        if not self.collide(other):
            return 0.0

        sxmin, sxmax, symin, symax = self.aabb()
        oxmin, oxmax, oymin, oymax = other.aabb()

        if axis == 'x':
            if vel > 0:
                return oxmin - sxmax
            if vel < 0:
                return oxmax - sxmin
        else:
            if vel > 0:
                return oymin - symax
            if vel < 0:
                return oymax - symin
        return 0.0


    def draw(self, flip=False, angle=0.0, pal=None):
        if self.type == 'tiles':
            self.__paint_tiles(pal)
        else:
            cx, cy = self.points[-1]
            Entity.paint(self.img, cx, cy, flip, angle, pal)

        if DEBUG:
            self.__draw_hitbox()


    @staticmethod
    def paint(sprite, x, y, flip=False, angle=0.0, pal=None):
        if angle:
            Entity.__paint_rotated(sprite, x, y, flip, angle, pal)
            return

        # canto de cima a esquerda do desenho
        pivot_x = sprite.w - sprite.px if flip else sprite.px
        left = floor(x - pivot_x)
        top = floor(y - sprite.py)
        # atalho para desenhar mais rapido
        pset = pyxel.pset

        for row, line in enumerate(sprite.grid):
            for col, color in enumerate(line):
                if color == CLEAR:
                    continue
                # espelhado le a linha de tras pra frente
                if flip:
                    col = sprite.w - 1 - col
                pset(left + col, top + row, pal[color] if pal else color)


    @staticmethod
    def __paint_rotated(sprite, x, y, flip, angle, pal):
        cos_a, sin_a = cos(angle), sin(angle)
        mirror = -1 if flip else 1

        # tamanho da area que cabe o desenho girado
        reach = int(hypot(max(sprite.px, sprite.w - sprite.px),
                          max(sprite.py, sprite.h - sprite.py))) + 1
        base_x, base_y = floor(x), floor(y)
        pset = pyxel.pset

        # passa por cada pixel da tela e procura a cor no desenho
        for dy in range(-reach, reach + 1):
            ry = base_y + dy + 0.5 - y
            for dx in range(-reach, reach + 1):
                rx = base_x + dx + 0.5 - x

                # desgira o pixel para achar o lugar dele no desenho
                u = mirror * (rx * cos_a + ry * sin_a) + sprite.px
                v = -rx * sin_a + ry * cos_a + sprite.py

                # caiu fora do desenho
                if not (0 <= u < sprite.w and 0 <= v < sprite.h):
                    continue

                color = sprite.grid[int(v)][int(u)]
                if color != CLEAR:
                    pset(base_x + dx, base_y + dy, pal[color] if pal else color)


    def __paint_tiles(self, pal):
        top_tile, body_tile = self.img
        xmin, xmax, ymin, ymax = self.aabb()
        left, top = floor(xmin), floor(ymin)
        pset = pyxel.pset

        for y in range(top, floor(ymax)):
            row = y - top
            # o topo vem primeiro e depois o corpo se repete
            if row < top_tile.h:
                line = top_tile.grid[row]
            else:
                line = body_tile.grid[(row - top_tile.h) % body_tile.h]

            for x in range(left, floor(xmax)):
                # o azulejo se repete para o lado
                color = line[(x - left) % len(line)]
                if color != CLEAR:
                    pset(x, y, pal[color] if pal else color)


    def __draw_hitbox(self):
        outline = self.points[:-1]
        n = len(outline)

        for i in range(n):
            x1, y1 = outline[i]
            x2, y2 = outline[(i + 1) % n]
            pyxel.line(x1, y1, x2, y2, 8)
