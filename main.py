import pyxel

from player import (KEY_LEFT, KEY_RIGHT, KEY_JUMP, KEY_HOOK_HOLD, KEY_ROPE_IN, KEY_ROPE_OUT,
                    KEY_FIRE, KEY_HOOK_FIRE)
from session import Session, WIDTH, HEIGHT
from replay import Replay, DEMO_FILE, BEST_FILE
from ui import label_center

FPS = 60

MENU = 0
PLAYING = 1

CURTAIN_TIME = 60
DEMO_TAIL = 90

TITLE = "OVERFLOW"
TITLE_SCALE = 4
TITLE_Y = 46

BUTTON_TEXT = "APERTE PARA JOGAR"
BUTTON_W = 84
BUTTON_H = 15
BUTTON_Y = 92

CONTROLS = "A/D andar  W pular  S/W corda  mouse: esq atira, dir gancho"

# cores claras da gameplay de fundo
FADED = (5, 5, 13, 6, 13, 13, 6, 7, 14, 15, 15, 6, 6, 13, 14, 15)

COLOR_SHADE = 1
COLOR_CURTAIN = 1
COLOR_CURTAIN_EDGE = 8
COLOR_TITLE = 8
COLOR_BUTTON = 8
COLOR_BUTTON_HOVER = 9
COLOR_LIGHT = 7
COLOR_TEXT = 5


class Game:
    def __init__(self):
        pyxel.init(WIDTH, HEIGHT, title="Overflow", fps=FPS)
        pyxel.mouse(True)
        Game.__bake_title()

        self.mode = MENU
        self.curtain = 0
        self.best = Replay.load(BEST_FILE)
        self.demo = self.best if len(self.best) else Replay.load(DEMO_FILE)
        self.record = None
        self.last = None

        self.__start_demo()
        pyxel.run(self.update, self.draw)

    @staticmethod
    def __bake_title():
        # escreve o titulo pequeno para desenhar grande depois
        bank = pyxel.images[0]
        bank.cls(0)
        bank.text(0, 0, TITLE, COLOR_TITLE)
        bank.text(0, 8, TITLE, COLOR_SHADE)

    def __start_demo(self):
        self.session = Session()
        self.tick = 0

    def update(self):
        if self.mode == MENU:
            self.__step_demo()
            if not self.curtain and self.__pressed_play():
                self.curtain = 1
        elif not self.curtain:
            self.__step_game()

        if self.curtain:
            self.__update_curtain()

    def __step_demo(self):
        # a run acabou entao recomeca
        ended = len(self.demo) and self.tick > len(self.demo) + DEMO_TAIL
        if ended or self.session.over():
            self.__start_demo()

        if self.tick < len(self.demo):
            keys, tx, ty = self.demo.frame(self.tick)
        else:
            keys, tx, ty = 0, 0, 0

        self.session.step(keys, tx, ty)
        self.tick += 1

    def __step_game(self):
        keys, tx, ty = self.__read_input()
        self.record.record(keys, tx, ty)
        self.session.step(keys, tx, ty)

        if self.session.over():
            self.__finish()

    def __finish(self):
        self.last = self.session.best
        self.record.height = self.session.best

        # a melhor run vira o fundo do menu
        if self.record.height > self.best.height:
            self.record.save(BEST_FILE)
            self.best = self.demo = self.record

        self.curtain = 1

    def __update_curtain(self):
        self.curtain += 1

        # troca a cena com a tela coberta
        if self.curtain == CURTAIN_TIME // 2:
            self.__swap()

        if self.curtain >= CURTAIN_TIME:
            self.curtain = 0

    def __swap(self):
        if self.mode == MENU:
            self.mode = PLAYING
            self.session = Session()
            self.record = Replay()
        else:
            self.mode = MENU
            self.__start_demo()

    def __curtain_bottom(self):
        # altura da cortina
        t = self.curtain / CURTAIN_TIME
        return 2 * HEIGHT * t * t * (3 - 2 * t)

    def __button(self):
        return (WIDTH - BUTTON_W) // 2, BUTTON_Y

    def __pressed_play(self):
        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_SPACE):
            return True
        if not pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            return False
        return self.__hover()

    def __hover(self):
        bx, by = self.__button()
        return bx <= pyxel.mouse_x < bx + BUTTON_W and by <= pyxel.mouse_y < by + BUTTON_H

    def __read_input(self):
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
        if pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            keys |= KEY_HOOK_FIRE
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT):
            keys |= KEY_FIRE

        # alvo do mouse so no clique
        tx = ty = 0
        if keys & (KEY_FIRE | KEY_HOOK_FIRE):
            tx = int(pyxel.mouse_x + self.session.cam_x)
            ty = int(pyxel.mouse_y + self.session.cam_y)

        return keys, tx, ty

    def draw(self):
        if self.mode == PLAYING:
            self.session.draw()
            self.session.draw_hud()
        else:
            for color, faded in enumerate(FADED):
                pyxel.pal(color, faded)
            self.session.draw()
            pyxel.pal()
            self.__draw_menu()

        if self.curtain:
            self.__draw_curtain()

    def __draw_menu(self):
        # o painel desce junto com a cortina
        drop = 0
        if self.curtain and self.curtain < CURTAIN_TIME // 2:
            drop = self.__curtain_bottom()

        self.__draw_title(TITLE_Y + drop)

        bx, by = self.__button()
        by += drop
        color = COLOR_BUTTON_HOVER if self.__hover() and not self.curtain else COLOR_BUTTON
        pyxel.rect(bx, by, BUTTON_W, BUTTON_H, color)
        pyxel.rectb(bx, by, BUTTON_W, BUTTON_H, COLOR_LIGHT)
        label_center(WIDTH // 2, by + 5, BUTTON_TEXT, COLOR_LIGHT, color)

        if self.best.height:
            label_center(WIDTH // 2, by + 26, f"recorde: {self.best.height}m", COLOR_SHADE)
        if self.last is not None:
            label_center(WIDTH // 2, by + 36, f"ultima: {self.last}m", COLOR_TEXT)

        label_center(WIDTH // 2, HEIGHT - 10 + drop, CONTROLS, COLOR_TEXT)

    @staticmethod
    def __draw_title(y):
        w = len(TITLE) * 4
        x = (WIDTH - w) // 2
        # desenha o titulo grande com sombra
        pyxel.blt(x + 2, y + 2, 0, 0, 8, w, 6, 0, scale=TITLE_SCALE)
        pyxel.blt(x, y, 0, 0, 0, w, 6, 0, scale=TITLE_SCALE)

    def __draw_curtain(self):
        bottom = self.__curtain_bottom()
        top = bottom - HEIGHT

        pyxel.rect(0, top, WIDTH, HEIGHT, COLOR_CURTAIN)
        pyxel.rect(0, bottom - 2, WIDTH, 2, COLOR_CURTAIN_EDGE)
        pyxel.rect(0, top, WIDTH, 2, COLOR_CURTAIN_EDGE)


if __name__ == "__main__":
    Game()
