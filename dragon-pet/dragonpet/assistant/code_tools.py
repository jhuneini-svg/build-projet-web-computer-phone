"""Lightweight code helpers: syntax-check / auto-fix and scaffolding.

Full AI code generation is delegated to :mod:`ai_brain` when configured; these
helpers provide deterministic, offline-safe utilities the dragon can always do.
"""

from __future__ import annotations

import ast
import io
import tokenize
from pathlib import Path

_TEMPLATES: dict[str, str] = {
    "python": (
        '"""{name}."""\n\n\n'
        "def main() -> None:\n"
        '    print("Hello from {name}!")\n\n\n'
        'if __name__ == "__main__":\n'
        "    main()\n"
    ),
    "html": (
        "<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n"
        "  <meta charset=\"utf-8\" />\n  <title>{name}</title>\n</head>\n"
        "<body>\n  <h1>{name}</h1>\n</body>\n</html>\n"
    ),
}


def check_python(source: str) -> tuple[bool, str]:
    """Return (ok, message) after attempting to parse *source* as Python."""
    try:
        ast.parse(source)
        return True, "\u0644\u0627 \u062a\u0648\u062c\u062f \u0623\u062e\u0637\u0627\u0621 \u0646\u062d\u0648\u064a\u0629 \u2705"
    except SyntaxError as exc:
        return False, f"SyntaxError: {exc.msg} (line {exc.lineno})"


def fix_python_whitespace(source: str) -> str:
    """Normalise trailing whitespace and ensure a single trailing newline."""
    lines = [line.rstrip() for line in source.splitlines()]
    return "\n".join(lines).rstrip("\n") + "\n"


def tokenize_ok(source: str) -> bool:
    try:
        list(tokenize.generate_tokens(io.StringIO(source).readline))
        return True
    except (tokenize.TokenError, IndentationError):
        return False


def scaffold(path: str, language: str = "python") -> str:
    """Create a starter file at *path* for the given language."""
    p = Path(path)
    name = p.stem or "project"
    template = _TEMPLATES.get(language, _TEMPLATES["python"]).format(name=name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(template, encoding="utf-8")
    return str(p)
