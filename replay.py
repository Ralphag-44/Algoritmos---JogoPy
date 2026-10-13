import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
# run que vem com o jogo
DEMO_FILE = os.path.join(ROOT, "demo.json")
# melhor run do jogador
BEST_FILE = os.path.join(ROOT, "best.json")


class Replay:
    __slots__ = ('frames', 'height')

    def __init__(self, frames=None, height=0):
        # cada frame guarda as teclas e o alvo do mouse
        self.frames = [] if frames is None else frames
        self.height = height

    def __len__(self):
        return len(self.frames)

    def record(self, keys, tx, ty):
        self.frames.append((keys, tx, ty))

    def frame(self, i):
        return self.frames[i]

    def save(self, path):
        # junta frames iguais seguidos
        packed = []
        for keys, tx, ty in self.frames:
            if packed and packed[-1][1:] == [keys, tx, ty]:
                packed[-1][0] += 1
            else:
                packed.append([1, keys, tx, ty])

        with open(path, "w") as f:
            json.dump({"height": self.height, "frames": packed}, f, separators=(",", ":"))

    @staticmethod
    def load(path):
        # sem arquivo vira uma run vazia
        try:
            with open(path) as f:
                data = json.load(f)

            frames = []
            for count, keys, tx, ty in data["frames"]:
                frames.extend([(keys, tx, ty)] * count)
            return Replay(frames, data["height"])
        except (OSError, ValueError, KeyError, TypeError):
            return Replay()
