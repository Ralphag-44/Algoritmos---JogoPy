from math import pi

GRAVITY = 0.25
PIXEL_SIZE = 2


def wrap(angle):
    return (angle + pi) % (2 * pi) - pi
