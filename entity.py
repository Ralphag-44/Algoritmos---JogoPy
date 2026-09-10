from math import sin, cos, pi
import numpy as np
import pyxel
from config import PIXEL_SIZE


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


    def draw(self):
        cx, cy = self.points[-1]

        if self.type == 'img':
            w = h = self.size * 2
            pyxel.blt(cx - self.size, cy - self.size, self.img, 0, 0, w, h, 0)
            return

        outline = self.points[:-1]
        n = len(outline)

        for i in range(n):
            x1, y1 = outline[i]
            x2, y2 = outline[(i + 1) % n]
            pyxel.tri(cx, cy, x1, y1, x2, y2, self.color)
