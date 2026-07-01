"""Mood / state definitions for the dragon and the emotions it displays."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class Mood(Enum):
    """High-level mood that drives eye color, chest emoji and animation."""

    IDLE = auto()          # calm, breathing, blinking
    HAPPY = auto()         # exaggerated joy after a successful task
    EXCITED = auto()       # jumping / eager, awaiting a command
    SLEEPING = auto()      # yawning then asleep after inactivity
    THINKING = auto()      # processing an AI / search request
    FLYING = auto()        # flew off-screen to search web / files
    ON_FIRE = auto()       # an error happened somewhere
    POWERSHELL = auto()    # rainbow color while typing in a terminal
    INSTALLING = auto()    # green glow while installing / updating
    FEEDING = auto()       # being fed after lots of work


# Eye color per mood (RGB).
EYE_COLORS: dict[Mood, tuple[int, int, int]] = {
    Mood.IDLE: (120, 200, 255),
    Mood.HAPPY: (120, 255, 160),
    Mood.EXCITED: (255, 220, 90),
    Mood.SLEEPING: (90, 110, 150),
    Mood.THINKING: (180, 160, 255),
    Mood.FLYING: (150, 230, 255),
    Mood.ON_FIRE: (255, 90, 40),
    Mood.POWERSHELL: (255, 255, 255),
    Mood.INSTALLING: (90, 255, 120),
    Mood.FEEDING: (255, 180, 210),
}

# Chest-screen emoji per mood.
CHEST_EMOJI: dict[Mood, str] = {
    Mood.IDLE: "\U0001F642",       # slightly smiling
    Mood.HAPPY: "\U0001F929",      # star-struck
    Mood.EXCITED: "\U0001F60D",    # eager / heart-eyes
    Mood.SLEEPING: "\U0001F634",   # sleeping
    Mood.THINKING: "\U0001F914",   # thinking
    Mood.FLYING: "\U0001F50D",     # searching (magnifier)
    Mood.ON_FIRE: "\U0001F525",    # fire
    Mood.POWERSHELL: "\U0001F308",  # rainbow
    Mood.INSTALLING: "\u2705",     # green check
    Mood.FEEDING: "\U0001F356",    # meat on bone
}

# Short Arabic status line the pet can speak in a bubble.
MOOD_SPEECH: dict[Mood, str] = {
    Mood.IDLE: "\u0623\u0646\u0627 \u0647\u0646\u0627 \u0625\u0646 \u0627\u062d\u062a\u062c\u062a\u0646\u064a \u2728",
    Mood.HAPPY: "\u064a\u0627\u0647\u0648! \u0623\u0646\u062c\u0632\u062a \u0627\u0644\u0645\u0647\u0645\u0629 \U0001F389",
    Mood.EXCITED: "\u0623\u0648\u0627\u0645\u0631\u0643 \u064a\u0627 \u0642\u0627\u0626\u062f! \U0001F680",
    Mood.SLEEPING: "\u0632\u064f\u0632\u064f\u0632... \U0001F4A4",
    Mood.THINKING: "\u062f\u0639\u0646\u064a \u0623\u0641\u0643\u0631... \U0001F914",
    Mood.FLYING: "\u0637\u0627\u0626\u0631 \u0644\u0644\u0628\u062d\u062b! \U0001FAB6",
    Mood.ON_FIRE: "\u062e\u0637\u0623! \u0627\u0634\u062a\u0639\u0644\u062a \U0001F525",
    Mood.POWERSHELL: "\u0648\u0636\u0639 \u0627\u0644\u062a\u064a\u0631\u0645\u0646\u0627\u0644 \U0001F308",
    Mood.INSTALLING: "\u062c\u0627\u0631\u064d \u0627\u0644\u062a\u062b\u0628\u064a\u062a... \U0001F7E2",
    Mood.FEEDING: "\u0634\u0643\u0631\u0627\u064b \u0639\u0644\u0649 \u0627\u0644\u0637\u0639\u0627\u0645! \U0001F356",
}


@dataclass
class PetStats:
    """Persistent-ish pet stats (0-100)."""

    hunger: float = 70.0
    happiness: float = 80.0
    energy: float = 90.0
    tasks_done: int = 0

    def clamp(self) -> None:
        self.hunger = max(0.0, min(100.0, self.hunger))
        self.happiness = max(0.0, min(100.0, self.happiness))
        self.energy = max(0.0, min(100.0, self.energy))
