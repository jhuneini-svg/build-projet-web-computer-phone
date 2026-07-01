"""Context memory: remembers preferences and frequent commands.

Persisted as JSON under the user's home directory so it survives restarts,
and used to produce smart suggestions such as
"\u062a\u0631\u064a\u062f \u0641\u062a\u062d Chrome\u061f \u0623\u0646\u062a \u062a\u0633\u062a\u062e\u062f\u0645\u0647 \u0643\u062b\u064a\u0631\u0627\u064b".
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

_STORE = Path.home() / ".dragonpet" / "memory.json"


class Memory:
    def __init__(self, path: Path = _STORE) -> None:
        self.path = path
        self.data: dict[str, Any] = {
            "command_counts": {},
            "app_counts": {},
            "preferences": {},
        }
        self.load()

    # -- persistence ------------------------------------------------------
    def load(self) -> None:
        if self.path.exists():
            try:
                self.data.update(json.loads(self.path.read_text(encoding="utf-8")))
            except (json.JSONDecodeError, OSError):
                pass

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # -- recording --------------------------------------------------------
    def record_command(self, intent: str) -> None:
        counts = self.data.setdefault("command_counts", {})
        counts[intent] = counts.get(intent, 0) + 1
        self.save()

    def record_app(self, app: str) -> None:
        counts = self.data.setdefault("app_counts", {})
        counts[app] = counts.get(app, 0) + 1
        self.save()

    def set_preference(self, key: str, value: Any) -> None:
        self.data.setdefault("preferences", {})[key] = value
        self.save()

    # -- suggestions ------------------------------------------------------
    def top_app(self) -> str | None:
        counts = Counter(self.data.get("app_counts", {}))
        if not counts:
            return None
        app, hits = counts.most_common(1)[0]
        return app if hits >= 3 else None

    def suggestion(self) -> str | None:
        app = self.top_app()
        if app:
            return (
                f"\u062a\u0631\u064a\u062f \u0641\u062a\u062d {app}\u061f "
                f"\u0623\u0646\u062a \u062a\u0633\u062a\u062e\u062f\u0645\u0647 \u0643\u062b\u064a\u0631\u0627\u064b \U0001F609"
            )
        return None
