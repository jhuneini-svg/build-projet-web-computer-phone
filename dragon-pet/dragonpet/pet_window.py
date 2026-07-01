"""The transparent, always-on-top desktop window that hosts the dragon."""

from __future__ import annotations

import random

from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRect,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import QAction, QCursor, QGuiApplication, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QInputDialog,
    QMenu,
    QWidget,
)

from .dragon_widget import DragonPainter
from .speech_bubble import SpeechBubble
from .states import MOOD_SPEECH, Mood, PetStats

WIDGET_SIZE = 200
FPS = 30


class PetWindow(QWidget):
    """Frameless window that draws the dragon and reacts to its mood."""

    command_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.resize(WIDGET_SIZE, WIDGET_SIZE)

        self.painter_helper = DragonPainter()
        self.stats = PetStats()

        self._frame = 0
        self._mood = Mood.IDLE
        self._mood_hold = 0          # frames to hold a transient mood
        self._blink = False
        self._blink_timer = random.randint(60, 160)
        self._mouth_open = 0.0
        self._idle_frames = 0
        self._interacting = False
        self._drag_offset: QPoint | None = None

        self.bubble = SpeechBubble()

        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._tick)
        self._anim_timer.start(int(1000 / FPS))

        self._wander_timer = QTimer(self)
        self._wander_timer.timeout.connect(self._maybe_wander)
        self._wander_timer.start(6000)

        self._move_anim: QPropertyAnimation | None = None

        self._place_bottom_right()
        self.say(MOOD_SPEECH[Mood.IDLE], 3500)

    # -- placement --------------------------------------------------------
    def _place_bottom_right(self) -> None:
        screen = QGuiApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - WIDGET_SIZE - 40, screen.bottom() - WIDGET_SIZE - 40)

    # -- mood API ---------------------------------------------------------
    @property
    def mood(self) -> Mood:
        return self._mood

    def set_mood(self, mood: Mood, hold_seconds: float = 0.0, speak: bool = True) -> None:
        self._mood = mood
        self._mood_hold = int(hold_seconds * FPS)
        self._idle_frames = 0
        if speak and mood in MOOD_SPEECH:
            self.say(MOOD_SPEECH[mood], max(2000, int(hold_seconds * 1000)))
        self.update()

    def celebrate(self) -> None:
        self.stats.tasks_done += 1
        self.stats.happiness = min(100.0, self.stats.happiness + 8)
        self.set_mood(Mood.HAPPY, 5.0)

    def on_error(self, message: str = "") -> None:
        self.set_mood(Mood.ON_FIRE, 5.0, speak=False)
        self.say(message or MOOD_SPEECH[Mood.ON_FIRE], 5000, error=True)

    def feed(self) -> None:
        self.stats.hunger = min(100.0, self.stats.hunger + 30)
        self.stats.happiness = min(100.0, self.stats.happiness + 6)
        self.set_mood(Mood.FEEDING, 4.5)

    # -- speech -----------------------------------------------------------
    def say(self, text: str, duration_ms: int = 3500, error: bool = False) -> None:
        self.bubble.show_message(self, text, duration_ms, error=error)

    # -- animation loop ---------------------------------------------------
    def _tick(self) -> None:
        self._frame += 1

        # blink handling
        self._blink_timer -= 1
        if self._blink_timer <= 0:
            self._blink = not self._blink
            self._blink_timer = 4 if self._blink else random.randint(60, 160)

        # transient mood countdown
        if self._mood_hold > 0:
            self._mood_hold -= 1
            if self._mood_hold == 0:
                self._mood = Mood.IDLE

        # idle -> sleep after inactivity (never doze off mid-conversation)
        if self._mood == Mood.IDLE and not self._interacting:
            self._idle_frames += 1
            if self._idle_frames == FPS * 8:
                self._mouth_open = 1.0  # yawn
            elif self._idle_frames == FPS * 9:
                self._mouth_open = 0.0
            elif self._idle_frames >= FPS * 18:
                self.set_mood(Mood.SLEEPING, speak=True)
        else:
            self._idle_frames = 0

        # stats decay
        if self._frame % (FPS * 5) == 0:
            self.stats.hunger -= 0.6
            self.stats.energy -= 0.3
            self.stats.clamp()
            if self.stats.hunger < 20 and self._mood == Mood.IDLE:
                self.say(
                    "\u062c\u0627\u0626\u0639... \u0623\u0637\u0639\u0645\u0646\u064a \U0001F356",
                    3000,
                )

        self.update()

    # -- wandering --------------------------------------------------------
    def _maybe_wander(self) -> None:
        if self._interacting or self._mood not in (Mood.IDLE,):
            return
        if random.random() < 0.5:
            return
        screen = QGuiApplication.primaryScreen().availableGeometry()
        nx = random.randint(screen.left() + 20, screen.right() - WIDGET_SIZE - 20)
        ny = random.randint(
            screen.top() + int(screen.height() * 0.4),
            screen.bottom() - WIDGET_SIZE - 20,
        )
        self.walk_to(QPoint(nx, ny))

    def walk_to(self, target: QPoint, duration: int = 1400) -> None:
        anim = QPropertyAnimation(self, b"pos", self)
        anim.setDuration(duration)
        anim.setStartValue(self.pos())
        anim.setEndValue(target)
        anim.setEasingCurve(QEasingCurve.InOutSine)
        anim.start()
        self._move_anim = anim

    def fly_off_and_return(self) -> None:
        """Fly toward the top of the screen (searching) then come back."""
        self.set_mood(Mood.FLYING, speak=True)
        screen = QGuiApplication.primaryScreen().availableGeometry()
        origin = self.pos()
        top = QPoint(random.randint(screen.left() + 40, screen.right() - WIDGET_SIZE - 40), screen.top() + 10)
        self.walk_to(top, 900)
        QTimer.singleShot(1400, lambda: self.walk_to(origin, 1000))
        QTimer.singleShot(2500, lambda: self.set_mood(Mood.IDLE, speak=False))

    # -- painting ---------------------------------------------------------
    def paintEvent(self, event) -> None:  # noqa: N802
        painter = QPainter(self)
        self.painter_helper.paint(
            painter,
            float(WIDGET_SIZE),
            self._frame,
            self._mood,
            self._blink,
            self._mouth_open,
        )

    # -- interaction ------------------------------------------------------
    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self.pos()
            if self._mood == Mood.SLEEPING:
                self.set_mood(Mood.IDLE, speak=True)
        elif event.button() == Qt.RightButton:
            self._show_menu(event.globalPosition().toPoint())

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self._drag_offset is not None:
            self.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._drag_offset = None

    def mouseDoubleClickEvent(self, event) -> None:  # noqa: N802
        self.prompt_command()

    def prompt_command(self) -> None:
        self._interacting = True
        self._idle_frames = 0
        try:
            text, ok = QInputDialog.getText(
                self,
                "\U0001F409 \u0627\u0644\u062a\u0646\u064a\u0646",
                "\u0645\u0627\u0630\u0627 \u062a\u0631\u064a\u062f\u0646\u064a \u0623\u0646 \u0623\u0641\u0639\u0644\u061f",
            )
        finally:
            self._interacting = False
        if ok and text.strip():
            self.set_mood(Mood.EXCITED, 1.0)
            self.command_requested.emit(text.strip())

    def _show_menu(self, pos) -> None:
        menu = QMenu()
        act_talk = QAction("\U0001F4AC \u0623\u0639\u0637\u0650 \u0623\u0645\u0631\u0627\u064b", menu)
        act_talk.triggered.connect(self.prompt_command)
        act_feed = QAction("\U0001F356 \u0623\u0637\u0639\u0645\u0647", menu)
        act_feed.triggered.connect(self.feed)
        act_stats = QAction("\U0001F4CA \u0627\u0644\u062d\u0627\u0644\u0629", menu)
        act_stats.triggered.connect(self._show_stats)
        act_quit = QAction("\u274C \u0625\u063A\u0644\u0627\u0642", menu)
        act_quit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_talk)
        menu.addAction(act_feed)
        menu.addAction(act_stats)
        menu.addSeparator()
        menu.addAction(act_quit)
        self._interacting = True
        self._idle_frames = 0
        try:
            menu.exec(pos)
        finally:
            self._interacting = False

    def _show_stats(self) -> None:
        s = self.stats
        self.say(
            f"\U0001F356 {int(s.hunger)}%  \U0001F60A {int(s.happiness)}%  "
            f"\u26A1 {int(s.energy)}%  \u2705 {s.tasks_done}",
            4000,
        )
