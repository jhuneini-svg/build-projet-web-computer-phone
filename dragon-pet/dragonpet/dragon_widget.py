"""Procedurally-drawn baby dragon.

The whole dragon is painted with QPainter (no external sprite assets needed),
so it is fully self-contained and every state can be animated: breathing,
wing-flap, blinking, yawning, fire breath, rainbow/green glows and the little
emoji screen on its chest.
"""

from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)

from .states import CHEST_EMOJI, EYE_COLORS, Mood

# Logical drawing canvas; the widget scales this to its real size.
CANVAS = 200.0


def _rainbow(t: float) -> QColor:
    """Return a rainbow color cycling with phase t (0..1)."""
    h = (t % 1.0)
    c = QColor()
    c.setHsvF(h, 0.85, 1.0)
    return c


class DragonPainter:
    """Stateless-ish helper that paints the dragon for a given frame/mood."""

    def __init__(self) -> None:
        self.base_body = QColor(90, 170, 235)
        self.base_belly = QColor(225, 245, 255)
        self.base_wing = QColor(140, 120, 225)

    # -- public -----------------------------------------------------------
    def paint(
        self,
        painter: QPainter,
        size: float,
        frame: int,
        mood: Mood,
        blink: bool,
        mouth_open: float,
    ) -> None:
        painter.setRenderHint(QPainter.Antialiasing, True)
        scale = size / CANVAS
        painter.save()
        painter.scale(scale, scale)

        t = frame / 60.0
        breathe = math.sin(t * 2.0) * 3.0
        # exaggerated bounce when happy/excited
        if mood in (Mood.HAPPY, Mood.EXCITED, Mood.FEEDING):
            bounce = abs(math.sin(t * 6.0)) * 14.0
        else:
            bounce = 0.0
        cx = CANVAS / 2

        body_color = self._body_color(mood, t)

        painter.save()
        painter.translate(0, -bounce + breathe * 0.3)

        self._draw_glow(painter, mood, t)
        self._draw_tail(painter, cx, frame, body_color)
        wing_flap = self._wing_phase(mood, t)
        self._draw_wing(painter, cx, body_color, wing_flap, left=True)
        self._draw_body(painter, cx, body_color, breathe)
        self._draw_legs(painter, cx, body_color)
        self._draw_chest_screen(painter, cx, mood, frame)
        self._draw_wing(painter, cx, body_color, wing_flap, left=False)
        self._draw_head(painter, cx, body_color, mood, blink, mouth_open, t)

        painter.restore()

        if mood == Mood.SLEEPING:
            self._draw_zzz(painter, cx, frame)
        if mood == Mood.ON_FIRE:
            self._draw_fire(painter, cx, frame)

        painter.restore()

    # -- colors -----------------------------------------------------------
    def _body_color(self, mood: Mood, t: float) -> QColor:
        if mood == Mood.POWERSHELL:
            return _rainbow(t * 0.5)
        if mood == Mood.ON_FIRE:
            f = (math.sin(t * 12) + 1) / 2
            return QColor(
                int(220 + 35 * f),
                int(90 + 40 * f),
                40,
            )
        if mood == Mood.INSTALLING:
            return QColor(90, 210, 120)
        return QColor(self.base_body)

    # -- glows ------------------------------------------------------------
    def _draw_glow(self, painter: QPainter, mood: Mood, t: float) -> None:
        color = None
        if mood == Mood.ON_FIRE:
            color = QColor(255, 120, 30, 120)
        elif mood == Mood.INSTALLING:
            color = QColor(70, 255, 120, 110)
        elif mood == Mood.POWERSHELL:
            color = _rainbow(t * 0.5)
            color.setAlpha(110)
        elif mood == Mood.HAPPY:
            color = QColor(255, 230, 120, 90)
        if color is None:
            return
        grad = QRadialGradient(CANVAS / 2, CANVAS / 2, CANVAS / 2)
        grad.setColorAt(0.0, color)
        transparent = QColor(color)
        transparent.setAlpha(0)
        grad.setColorAt(1.0, transparent)
        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QRectF(0, 0, CANVAS, CANVAS))

    # -- body parts -------------------------------------------------------
    def _draw_body(self, painter: QPainter, cx: float, color: QColor, breathe: float) -> None:
        w = 92 + breathe
        h = 84 + breathe
        rect = QRectF(cx - w / 2, 96 - breathe / 2, w, h)
        grad = QLinearGradient(rect.topLeft(), rect.bottomRight())
        grad.setColorAt(0.0, color.lighter(115))
        grad.setColorAt(1.0, color.darker(115))
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(color.darker(150), 2))
        painter.drawEllipse(rect)

        # belly
        belly = QRectF(cx - 26, 118, 52, 56)
        painter.setBrush(QBrush(self.base_belly))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(belly)

    def _draw_legs(self, painter: QPainter, cx: float, color: QColor) -> None:
        painter.setBrush(QBrush(color.darker(110)))
        painter.setPen(QPen(color.darker(150), 2))
        for dx in (-24, 24):
            painter.drawEllipse(QRectF(cx + dx - 13, 168, 26, 22))

    def _draw_chest_screen(self, painter: QPainter, cx: float, mood: Mood, frame: int) -> None:
        rect = QRectF(cx - 20, 126, 40, 34)
        painter.setBrush(QBrush(QColor(20, 24, 34)))
        painter.setPen(QPen(QColor(180, 200, 230), 2))
        painter.drawRoundedRect(rect, 8, 8)
        # subtle scanline glow
        glow = QColor(120, 200, 255, 40)
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect.adjusted(2, 2, -2, -2), 6, 6)

        emoji = CHEST_EMOJI.get(mood, "\U0001F642")
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = QFont("Segoe UI Emoji")
        font.setPixelSize(22)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignCenter, emoji)

    def _wing_phase(self, mood: Mood, t: float) -> float:
        if mood in (Mood.FLYING, Mood.EXCITED):
            return math.sin(t * 14.0) * 34.0
        if mood == Mood.POWERSHELL:
            return math.sin(t * 8.0) * 26.0
        return math.sin(t * 2.0) * 6.0

    def _draw_wing(
        self, painter: QPainter, cx: float, color: QColor, flap: float, left: bool
    ) -> None:
        painter.save()
        anchor_x = cx + (-38 if left else 38)
        painter.translate(anchor_x, 108)
        sign = -1 if left else 1
        painter.rotate(sign * (20 + flap))
        path = QPainterPath()
        path.moveTo(0, 0)
        path.quadTo(sign * 60, -30, sign * 78, 26)
        path.quadTo(sign * 50, 20, sign * 44, 54)
        path.quadTo(sign * 30, 22, 0, 30)
        path.closeSubpath()
        wc = QColor(self.base_wing)
        grad = QLinearGradient(0, 0, sign * 78, 40)
        grad.setColorAt(0.0, wc.lighter(120))
        grad.setColorAt(1.0, wc.darker(120))
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(wc.darker(150), 2))
        painter.drawPath(path)
        painter.restore()

    def _draw_tail(self, painter: QPainter, cx: float, frame: int, color: QColor) -> None:
        t = frame / 60.0
        sway = math.sin(t * 3.0) * 14.0
        painter.save()
        path = QPainterPath()
        path.moveTo(cx + 30, 160)
        path.quadTo(cx + 78 + sway, 150, cx + 96 + sway, 116)
        path.quadTo(cx + 70, 140, cx + 34, 150)
        path.closeSubpath()
        painter.setBrush(QBrush(color.darker(108)))
        painter.setPen(QPen(color.darker(150), 2))
        painter.drawPath(path)
        # tail spade
        painter.setBrush(QBrush(QColor(255, 150, 120)))
        painter.drawEllipse(QPointF(cx + 96 + sway, 116), 8, 10)
        painter.restore()

    def _draw_head(
        self,
        painter: QPainter,
        cx: float,
        color: QColor,
        mood: Mood,
        blink: bool,
        mouth_open: float,
        t: float,
    ) -> None:
        head = QRectF(cx - 40, 34, 80, 74)
        grad = QLinearGradient(head.topLeft(), head.bottomRight())
        grad.setColorAt(0.0, color.lighter(115))
        grad.setColorAt(1.0, color.darker(112))
        painter.setBrush(QBrush(grad))
        painter.setPen(QPen(color.darker(150), 2))
        painter.drawEllipse(head)

        # snout
        snout = QRectF(cx - 22, 74, 44, 34 + mouth_open * 16)
        painter.setBrush(QBrush(color.lighter(108)))
        painter.drawRoundedRect(snout, 14, 14)
        # nostrils
        painter.setBrush(QBrush(color.darker(170)))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx - 9, 84), 2.4, 2.4)
        painter.drawEllipse(QPointF(cx + 9, 84), 2.4, 2.4)

        # horns
        painter.setBrush(QBrush(QColor(255, 235, 200)))
        painter.setPen(QPen(QColor(200, 180, 150), 1.5))
        for dx in (-20, 20):
            horn = QPainterPath()
            horn.moveTo(cx + dx - 5, 40)
            horn.lineTo(cx + dx + (4 if dx > 0 else -4), 14)
            horn.lineTo(cx + dx + 5, 40)
            horn.closeSubpath()
            painter.drawPath(horn)

        # eyes
        self._draw_eyes(painter, cx, mood, blink, t)

    def _draw_eyes(
        self, painter: QPainter, cx: float, mood: Mood, blink: bool, t: float
    ) -> None:
        eye_rgb = EYE_COLORS.get(mood, (120, 200, 255))
        if mood == Mood.POWERSHELL:
            eye_col = _rainbow(t)
        else:
            eye_col = QColor(*eye_rgb)
        for dx in (-16, 16):
            center = QPointF(cx + dx, 62)
            # white
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            if blink or mood == Mood.SLEEPING:
                painter.setPen(QPen(QColor(40, 50, 70), 2.5))
                painter.drawLine(
                    QPointF(cx + dx - 8, 62), QPointF(cx + dx + 8, 62)
                )
                painter.setPen(Qt.NoPen)
                continue
            painter.drawEllipse(center, 11, 12)
            # iris
            painter.setBrush(QBrush(eye_col))
            painter.drawEllipse(center, 7, 8)
            # pupil
            painter.setBrush(QBrush(QColor(20, 20, 30)))
            painter.drawEllipse(center, 3.2, 3.6)
            # sparkle
            painter.setBrush(QBrush(QColor(255, 255, 255)))
            painter.drawEllipse(QPointF(cx + dx - 2.5, 59), 2.0, 2.0)

    # -- effects ----------------------------------------------------------
    def _draw_zzz(self, painter: QPainter, cx: float, frame: int) -> None:
        painter.setPen(QPen(QColor(150, 180, 230)))
        t = frame / 60.0
        for i in range(3):
            font = QFont()
            font.setPixelSize(14 + i * 6)
            painter.setFont(font)
            rise = (t * 20 + i * 14) % 42
            painter.drawText(
                QPointF(cx + 30 + i * 12, 40 - rise + i * 6), "z"
            )

    def _draw_fire(self, painter: QPainter, cx: float, frame: int) -> None:
        t = frame / 60.0
        painter.save()
        painter.translate(cx, 96)
        for i in range(9):
            flick = math.sin(t * 18 + i) * 6
            r = 10 + (i % 3) * 5
            y = -i * 9 - 4
            col = QColor(
                255,
                int(120 + (i * 12) % 120),
                40,
                200 - i * 15,
            )
            painter.setBrush(QBrush(col))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(QPointF(flick, y), r, r + 4)
        painter.restore()
