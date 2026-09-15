from math import pi

GRAVITY = 0.25
PIXEL_SIZE = 2

# Desenha na tela as tripas de quem tem tripas pra mostrar:
# por enquanto, o poligono de controle das beziers da lava e o nivel que mata.
DEBUG = True


def wrap(angle):
    return (angle + pi) % (2 * pi) - pi
