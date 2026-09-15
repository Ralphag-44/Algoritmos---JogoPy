import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
MAIN = os.path.join(ROOT, "main.py")
REQUISITOS = os.path.join(ROOT, "requirements.txt")

NO_WINDOWS = os.name == "nt"
CASA = os.path.join(os.path.expanduser("~"), ".venvs", "jogo-algoritmo")

CANDIDATOS = [os.path.join(ROOT, ".venv"), os.path.join(ROOT, "venv"), CASA]


def python_do_venv(venv):
    if NO_WINDOWS:
        return os.path.join(venv, "Scripts", "python.exe")
    return os.path.join(venv, "bin", "python")


def tem_pyxel(python):
    if not python or not os.path.isfile(python):
        return False
    try:
        return subprocess.call(
            [python, "-c", "import pyxel"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        ) == 0
    except OSError:
        return False


def procurar():
    if tem_pyxel(sys.executable):
        return sys.executable

    for venv in CANDIDATOS:
        python = python_do_venv(venv)
        if tem_pyxel(python):
            return python

    return None


def criar(venv):
    print("Criando o venv em %s" % venv)

    if os.path.exists(venv):
        shutil.rmtree(venv, ignore_errors=True)

    if subprocess.call([sys.executable, "-m", "venv", venv]) != 0:
        return None

    python = python_do_venv(venv)
    if not os.path.isfile(python):
        # exFAT e NTFS nao aceitam symlink e deixam o venv sem bin/
        print("  o venv saiu quebrado (o sistema de arquivos nao aceita symlink)")
        shutil.rmtree(venv, ignore_errors=True)
        return None

    print("Instalando as dependencias...")
    if subprocess.call([python, "-m", "pip", "install", "-q", "-r", REQUISITOS]) != 0:
        return None

    return python


def preparar():
    python = procurar()
    if python:
        return python

    print("Nenhum interpretador com pyxel encontrado.")

    for venv in (os.path.join(ROOT, ".venv"), CASA):
        python = criar(venv)
        if python:
            return python
        if venv != CASA:
            print("  tentando fora da pasta do projeto...")

    print("\nNao consegui preparar o ambiente. Faca na mao:")
    print("    python -m venv %s" % CASA)
    print("    %s -m pip install -r %s" % (python_do_venv(CASA), REQUISITOS))
    sys.exit(1)


def main():
    opcoes = sys.argv[1:]
    argumentos = [a for a in opcoes if a not in ("--info", "--recriar")]

    if "--recriar" in opcoes:
        for venv in CANDIDATOS:
            if os.path.isdir(venv):
                print("Apagando %s" % venv)
                shutil.rmtree(venv, ignore_errors=True)

    python = preparar()

    if "--info" in opcoes:
        print("Interpretador: %s" % python)
        print("Projeto:       %s" % ROOT)
        return 0

    return subprocess.call([python, MAIN] + argumentos, cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
