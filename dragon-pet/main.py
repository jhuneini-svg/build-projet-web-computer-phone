"""DragonPet entry point.

Run with:  python main.py
Double-click the dragon (or right-click -> "give a command") to talk to it.
"""

from __future__ import annotations

import os
import sys

# Make the app runnable from any working directory (e.g. via Start-Process,
# a shortcut, or a different cwd) by ensuring this file's folder is importable.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from dragonpet.assistant.commands import CommandController
from dragonpet.assistant.memory import Memory
from dragonpet.pet_window import PetWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    pet = PetWindow()
    memory = Memory()
    controller = CommandController(pet, memory)
    pet.command_requested.connect(controller.handle)

    # If the app itself hits an unhandled error, the dragon bursts into flames.
    def _fire_hook(exc_type, exc_value, tb):
        try:
            pet.on_error(f"{exc_type.__name__}: {exc_value}")
        finally:
            sys.__excepthook__(exc_type, exc_value, tb)

    sys.excepthook = _fire_hook

    pet.show()

    # Periodic smart suggestion based on remembered habits.
    def _suggest() -> None:
        text = memory.suggestion()
        if text and pet.mood.name == "IDLE":
            pet.say(text, 5000)

    suggest_timer = QTimer()
    suggest_timer.timeout.connect(_suggest)
    suggest_timer.start(90_000)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
