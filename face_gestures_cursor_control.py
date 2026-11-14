"""Compatibility launcher for face control. Prefer `python main.py --mode face`."""

from main import run


if __name__ == "__main__":
    run("face", 0)
