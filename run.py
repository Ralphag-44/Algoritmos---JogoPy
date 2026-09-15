import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
VENV = os.path.join(os.path.expanduser('~'), '.venvs', 'jogo-algoritmo')

if os.name == 'nt':
    python = os.path.join(VENV, 'Scripts', 'python.exe')
else:
    python = os.path.join(VENV, 'bin', 'python')

if not os.path.exists(python):
    print(f"Venv nao encontrado em {VENV}.")
    print("Crie com: python -m venv " + VENV)
    print("E instale as dependencias com: " + python + " -m pip install -r requirements.txt")
    sys.exit(1)

sys.exit(subprocess.call([python, os.path.join(ROOT, 'main.py')]))
