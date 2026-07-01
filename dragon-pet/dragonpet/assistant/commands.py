"""Command controller: turns a user request into an action and drives the pet.

Actions run on a background :class:`QThread` so the animation never freezes.
The controller flips the dragon's mood to reflect what is happening:
excited -> (flying/powershell/installing/thinking) -> happy or on-fire.
"""

from __future__ import annotations

import re

from PySide6.QtCore import QObject, QThread, Signal

from . import ai_brain, code_tools, system_tasks, web_search
from .memory import Memory

# Rule-based intent keywords (Arabic + English).
_RULES: list[tuple[str, list[str]]] = [
    ("open_app", ["افتح", "شغل", "open", "launch", "run app"]),
    ("web_search", ["ابحث في الويب", "ابحث في الانترنت", "google", "بحث ويب", "search web"]),
    ("find_files", ["ابحث عن ملف", "جد ملف", "find file", "ابحث في الحاسوب", "locate"]),
    ("organize_folder", ["نظم", "رتب", "organize", "tidy", "sort folder"]),
    ("run_powershell", ["بورشيل", "باور شيل", "powershell", "terminal", "تيرمنال", "امر نظام"]),
    ("write_code", ["اكتب كود", "انشئ ملف", "code", "scaffold", "برمج"]),
    ("web_search", ["ابحث", "search", "جوجل"]),
]


def parse_intent(text: str) -> tuple[str, str]:
    """Rule-based intent detection. Returns (intent, argument)."""
    lowered = text.lower()
    for intent, keywords in _RULES:
        for kw in keywords:
            if kw in lowered:
                argument = re.sub(re.escape(kw), "", lowered, count=1).strip(" :\u060c-")
                return intent, argument or text
    return "chat", text


class Worker(QThread):
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, text: str, intent: str, argument: str) -> None:
        super().__init__()
        self.text = text
        self.intent = intent
        self.argument = argument

    def run(self) -> None:  # noqa: D401
        try:
            # Refine the rule-based guess with AI *in this background thread*
            # so the optional network call never freezes the UI event loop.
            ai = ai_brain.understand(self.text)
            if ai:
                self.intent = ai["intent"]
                self.argument = ai["argument"] or self.text
            self.succeeded.emit(self._execute())
        except Exception as exc:  # noqa: BLE001 - surfaced to the user as fire
            self.failed.emit(f"{type(exc).__name__}: {exc}")

    def _execute(self) -> str:
        intent, arg = self.intent, self.argument
        if intent == "open_app":
            exe = system_tasks.open_app(arg)
            return f"\u0641\u062a\u062d\u062a {exe} \u2705"
        if intent == "web_search":
            url = web_search.web_search(arg)
            return f"\u0628\u062d\u062b\u062a \u0639\u0646: {arg}"
        if intent == "find_files":
            hits = web_search.find_files(arg)
            if not hits:
                return "\u0644\u0645 \u0623\u062c\u062f \u0645\u0644\u0641\u0627\u062a \U0001F50D"
            return f"\u0648\u062c\u062f\u062a {len(hits)} \u0645\u0644\u0641\u0627\u064b"
        if intent == "organize_folder":
            moved = system_tasks.organize_folder(arg)
            total = sum(moved.values())
            return f"\u0631\u062a\u0651\u0628\u062a {total} \u0645\u0644\u0641\u0627\u064b \U0001F4C1"
        if intent == "run_powershell":
            proc = system_tasks.run_powershell(arg)
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip() or "PowerShell error")
            return (proc.stdout.strip() or "\u062a\u0645 \u2705")[:120]
        if intent == "write_code":
            path = code_tools.scaffold(arg or "new_project/main.py")
            return f"\u0623\u0646\u0634\u0623\u062a {path} \u270D\uFE0F"
        return "\u0644\u0633\u062a \u0645\u062a\u0623\u0643\u062f\u0627\u064b \u0645\u0645\u0651\u0627 \u062a\u0631\u064a\u062f \U0001F914"


class CommandController(QObject):
    """Wires user text to a Worker and reflects progress on the PetWindow."""

    def __init__(self, pet, memory: Memory | None = None) -> None:
        super().__init__()
        self.pet = pet
        self.memory = memory or Memory()
        self._worker: Worker | None = None

    def handle(self, text: str) -> None:
        # Rule-based intent gives an instant visual cue; the worker then
        # refines it with AI (if configured) off the UI thread.
        intent, argument = parse_intent(text)

        self.memory.record_command(intent)
        if intent == "open_app":
            self.memory.record_app(argument)

        # Reflect the action visually before running it.
        from ..states import Mood

        if intent in ("web_search", "find_files"):
            self.pet.fly_off_and_return()
        elif intent == "run_powershell":
            self.pet.set_mood(Mood.POWERSHELL, 4.0)
        elif intent == "write_code":
            self.pet.set_mood(Mood.THINKING, 3.0)
        else:
            self.pet.set_mood(Mood.EXCITED, 1.5)

        worker = Worker(text, intent, argument)
        worker.succeeded.connect(self._on_success)
        worker.failed.connect(self._on_failure)
        worker.finished.connect(worker.deleteLater)
        self._worker = worker
        worker.start()

    def _on_success(self, message: str) -> None:
        self.pet.celebrate()
        self.pet.say(message, 4000)

    def _on_failure(self, message: str) -> None:
        self.pet.on_error(message)
