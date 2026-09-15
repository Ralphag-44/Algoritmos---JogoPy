from math import pi

GRAVITY = 0.25
PIXEL_SIZE = 2
DEBUG = True


def wrap(angle):
    return (angle + pi) % (2 * pi) - pi
