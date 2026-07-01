"""Offline smoke tests for the assistant backend (no GUI required)."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dragonpet.assistant import code_tools, system_tasks  # noqa: E402
from dragonpet.assistant.commands import parse_intent  # noqa: E402


def test_protection() -> None:
    assert system_tasks.is_protected(r"C:\Windows\System32")
    assert system_tasks.is_protected(r"C:\Program Files\x")
    assert system_tasks.is_protected("C:\\")
    tmp = tempfile.gettempdir()
    assert not system_tasks.is_protected(os.path.join(tmp, "dragon_playground"))
    print("protection OK")


def test_organize() -> None:
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        (base / "a.png").write_text("x")
        (base / "b.pdf").write_text("x")
        (base / "c.py").write_text("x")
        moved = system_tasks.organize_folder(base)
        assert moved.get("Images") == 1
        assert moved.get("Documents") == 1
        assert moved.get("Code") == 1
        assert (base / "Images" / "a.png").exists()
    print("organize OK")


def test_code_tools() -> None:
    ok, _ = code_tools.check_python("def f():\n    return 1\n")
    assert ok
    bad, msg = code_tools.check_python("def f(:\n")
    assert not bad and "SyntaxError" in msg
    with tempfile.TemporaryDirectory() as d:
        p = code_tools.scaffold(os.path.join(d, "proj", "main.py"))
        assert Path(p).exists()
    print("code_tools OK")


def test_intents() -> None:
    assert parse_intent("افتح كروم")[0] == "open_app"
    assert parse_intent("ابحث في الويب عن قطط")[0] == "web_search"
    assert parse_intent("نظم مجلد التنزيلات")[0] == "organize_folder"
    assert parse_intent("powershell get-date")[0] == "run_powershell"
    assert parse_intent("اكتب كود لعبة")[0] == "write_code"
    print("intents OK")


if __name__ == "__main__":
    test_protection()
    test_organize()
    test_code_tools()
    test_intents()
    print("ALL SMOKE TESTS PASSED")
