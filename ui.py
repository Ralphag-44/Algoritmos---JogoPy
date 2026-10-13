import pyxel

CHAR_W = 4
COLOR_EDGE = 7


def label(x, y, text, color, edge=COLOR_EDGE):
    # contorno de 1 pixel em volta para ler em cima de qualquer fundo
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        pyxel.text(x + dx, y + dy, text, edge)
    pyxel.text(x, y, text, color)


def label_right(x, y, text, color, edge=COLOR_EDGE):
    label(x - len(text) * CHAR_W + 1, y, text, color, edge)


def label_center(x, y, text, color, edge=COLOR_EDGE):
    label(x - len(text) * CHAR_W // 2, y, text, color, edge)
