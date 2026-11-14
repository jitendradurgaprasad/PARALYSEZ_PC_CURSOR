"""Compatibility launcher for hand control. Prefer `python main.py --mode hand`."""

from main import run


if __name__ == "__main__":
    run("hand", 0)
