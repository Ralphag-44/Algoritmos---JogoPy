from math import sin, cos, pi, floor
import numpy as np
import pyxel
from config import DEBUG
from sprites import CLEAR


class Entity:
    __slots__ = ('points', 'size', 'type', 'img', 'color')

    def __init__(self, cvx, cx, cy, num_p, size, list_points, type, img=None, color=None, angle_offset=0):
        if cvx:
            list_points = Entity.__generate_points(cx, cy, num_p, size, angle_offset)
        elif not size:
            size = Entity.__calc_size(cx, cy, list_points)

        list_points.append((cx, cy))
        self.points = np.array([[x, y] for x, y in list_points], dtype=np.float32)
        self.size = size

        self.type = type
        self.img = img
        self.color = color


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
        return max(((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 for x, y in list_points)

    
    def translate(self, vx, vy):
        self.points += np.array([vx, vy])

    
    def rotate(self, angle, sin=sin, cos=cos):
        sin_a = sin(angle)
        cos_a = cos(angle)

        center = self.points[-1]
        diff = self.points[:-1] - center

        x = diff[:, 0] * cos_a - diff[:, 1] * sin_a
        y = diff[:, 0] * sin_a + diff[:, 1] * cos_a

        self.points[:-1, 0] = x + center[0]
        self.points[:-1, 1] = y + center[1]


    def collide(self, other):
        center_a = self.points[-1]
        center_b = other.points[-1]

        dist = ((center_a[0] - center_b[0]) ** 2 + (center_a[1] - center_b[1]) ** 2) ** 0.5
        if dist > self.size + other.size:
            return False

        poly_a = self.points[:-1]
        poly_b = other.points[:-1]

        p1a = poly_a
        p2a = np.roll(poly_a, -1, axis=0)

        p1b = poly_b
        p2b = np.roll(poly_b, -1, axis=0)

        p1 = p1a[:, np.newaxis, :]   
        p2 = p2a[:, np.newaxis, :]
        p3 = p1b[np.newaxis, :, :]   
        p4 = p2b[np.newaxis, :, :]

        d1 = (p2[...,0]-p1[...,0])*(p3[...,1]-p1[...,1]) - (p2[...,1]-p1[...,1])*(p3[...,0]-p1[...,0])
        d2 = (p2[...,0]-p1[...,0])*(p4[...,1]-p1[...,1]) - (p2[...,1]-p1[...,1])*(p4[...,0]-p1[...,0])
        d3 = (p4[...,0]-p3[...,0])*(p1[...,1]-p3[...,1]) - (p4[...,1]-p3[...,1])*(p1[...,0]-p3[...,0])
        d4 = (p4[...,0]-p3[...,0])*(p2[...,1]-p3[...,1]) - (p4[...,1]-p3[...,1])*(p2[...,0]-p3[...,0])

        intersecta = ((d1 > 0) != (d2 > 0)) & ((d3 > 0) != (d4 > 0))
        return intersecta.any()


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


    def center(self):
        return self.points[-1]


    def draw(self, flip=False, angle=0.0, pal=None):
        cx, cy = self.points[-1]

        if self.type == 'sprite':
            Entity.paint(self.img, cx, cy, flip, angle, pal)
        elif self.type == 'tiles':
            self.__paint_tiles(pal)
        elif self.type == 'img':
            w = h = self.size * 2
            pyxel.blt(cx - self.size, cy - self.size, self.img, 0, 0, w, h, 0)
        else:
            outline = self.points[:-1]
            n = len(outline)

            for i in range(n):
                x1, y1 = outline[i]
                x2, y2 = outline[(i + 1) % n]
                pyxel.tri(cx, cy, x1, y1, x2, y2, self.color)

        if DEBUG:
            self.__draw_hitbox()


    @staticmethod
    def paint(sprite, x, y, flip=False, angle=0.0, pal=None):
        if angle:
            Entity.__paint_rotated(sprite, x, y, flip, angle, pal)
            return

        w = sprite.w
        ox = floor(x - (w - sprite.px if flip else sprite.px))
        oy = floor(y - sprite.py)
        pset = pyxel.pset

        for j, row in enumerate(sprite.grid):
            for i, c in enumerate(row):
                if c == CLEAR:
                    continue
                pset(ox + (w - 1 - i if flip else i), oy + j, pal[c] if pal else c)


    @staticmethod
    def __paint_rotated(sprite, x, y, flip, angle, pal):
        grid, w, h, px, py = sprite.grid, sprite.w, sprite.h, sprite.px, sprite.py
        cos_a, sin_a = cos(angle), sin(angle)
        side = -1 if flip else 1

        reach = int((max(px, w - px) ** 2 + max(py, h - py) ** 2) ** 0.5) + 1
        bx, by = floor(x), floor(y)
        pset = pyxel.pset

        for dy in range(-reach, reach + 1):
            ry = by + dy + 0.5 - y
            for dx in range(-reach, reach + 1):
                rx = bx + dx + 0.5 - x

                u = side * (rx * cos_a + ry * sin_a) + px
                v = -rx * sin_a + ry * cos_a + py
                if not (0 <= u < w and 0 <= v < h):
                    continue

                c = grid[int(v)][int(u)]
                if c != CLEAR:
                    pset(bx + dx, by + dy, pal[c] if pal else c)


    def __paint_tiles(self, pal):
        top, body = self.img
        xmin, xmax, ymin, ymax = self.aabb()
        x0, y0 = floor(xmin), floor(ymin)
        x1, y1 = floor(xmax), floor(ymax)
        pset = pyxel.pset

        for y in range(y0, y1):
            j = y - y0
            row = top.grid[j] if j < top.h else body.grid[(j - top.h) % body.h]
            w = len(row)

            for x in range(x0, x1):
                c = row[(x - x0) % w]
                if c != CLEAR:
                    pset(x, y, pal[c] if pal else c)


    def __draw_hitbox(self):
        outline = self.points[:-1]
        n = len(outline)

        for i in range(n):
            x1, y1 = outline[i]
            x2, y2 = outline[(i + 1) % n]
            pyxel.line(x1, y1, x2, y2, 8)
