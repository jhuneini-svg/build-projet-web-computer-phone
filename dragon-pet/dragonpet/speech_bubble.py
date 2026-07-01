"""A small floating speech bubble the dragon uses to talk."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class SpeechBubble(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self._text = ""
        self._error = False
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)
        self.resize(280, 90)

    def show_message(
        self, anchor: QWidget, text: str, duration_ms: int, error: bool = False
    ) -> None:
        self._text = text
        self._error = error
        # place above the pet, roughly centered
        ax = anchor.x() + anchor.width() // 2 - self.width() // 2
        ay = anchor.y() - self.height() + 10
        self.move(max(0, ax), max(0, ay))
        self.show()
        self.raise_()
        self.update()
        self._timer.start(duration_ms)

    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        rect = QRectF(6, 6, self.width() - 12, self.height() - 24)
        if self._error:
            fill = QColor(60, 20, 20, 235)
            border = QColor(255, 90, 60)
            text_col = QColor(255, 210, 200)
        else:
            fill = QColor(28, 32, 44, 235)
            border = QColor(120, 200, 255)
            text_col = QColor(240, 246, 255)
        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(border, 2))
        painter.drawRoundedRect(rect, 14, 14)
        # tail pointing down toward the pet
        cx = self.width() / 2
        base = rect.bottom()
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(fill))
        painter.drawPolygon(
            [
                QPointF(cx - 12, base - 1),
                QPointF(cx + 12, base - 1),
                QPointF(cx, base + 16),
            ]
        )

        font = QFont("Segoe UI Emoji")
        font.setPixelSize(15)
        painter.setFont(font)
        painter.setPen(QPen(text_col))
        painter.drawText(
            rect.adjusted(12, 8, -12, -8),
            Qt.AlignCenter | Qt.TextWordWrap,
            self._text,
        )
