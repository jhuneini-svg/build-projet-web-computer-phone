"""Render the dragon in every mood to PNGs (offscreen) for quick visual QA."""

from __future__ import annotations

import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtGui import QImage, QPainter  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from dragonpet.dragon_widget import DragonPainter  # noqa: E402
from dragonpet.states import Mood  # noqa: E402


def main() -> None:
    app = QApplication(sys.argv)  # noqa: F841
    helper = DragonPainter()
    out_dir = os.path.join(os.path.dirname(__file__), "..", "preview")
    out_dir = os.path.abspath(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    size = 300
    for mood in Mood:
        img = QImage(size, size, QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        p = QPainter(img)
        helper.paint(p, float(size), frame=20, mood=mood, blink=False, mouth_open=0.0)
        p.end()
        path = os.path.join(out_dir, f"dragon_{mood.name.lower()}.png")
        img.save(path)
        print("wrote", path)


if __name__ == "__main__":
    main()
