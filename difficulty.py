LEVEL_TIME = 20 * 60
MAX_LEVEL = 10

LAVA_GAIN = 0.08
PLATFORM_GAIN = 0.12
ENEMY_GAIN = 0.10


class Difficulty:
    __slots__ = ('timer',)

    def __init__(self):
        self.timer = 0

    def update(self):
        self.timer += 1

    def level(self):
        # sobe um nivel a cada LEVEL_TIME frames, ate MAX_LEVEL
        return min(self.timer // LEVEL_TIME, MAX_LEVEL)

    def leveled_up(self):
        # verdadeiro so no frame exato em que o nivel muda
        return self.timer % LEVEL_TIME == 0 and 0 < self.timer <= LEVEL_TIME * MAX_LEVEL

    def __scale(self, gain):
        # nivel 0 = velocidade normal, cada nivel soma gain
        return 1.0 + gain * self.level()

    def lava(self):
        return self.__scale(LAVA_GAIN)

    def platforms(self):
        return self.__scale(PLATFORM_GAIN)

    def enemies(self):
        return self.__scale(ENEMY_GAIN)
