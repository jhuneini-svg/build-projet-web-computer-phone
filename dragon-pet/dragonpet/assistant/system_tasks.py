"""System-level actions the dragon can perform on Windows.

Every destructive action is routed through :func:`is_protected` so the dragon
"protects system files completely" and refuses to touch Windows/Program Files
and other critical locations.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# Directories the dragon will never modify or delete.
_PROTECTED_ROOTS = [
    Path(os.environ.get("SystemRoot", r"C:\Windows")),
    Path(os.environ.get("ProgramFiles", r"C:\Program Files")),
    Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")),
    Path(os.environ.get("ProgramData", r"C:\ProgramData")),
]


class ProtectedPathError(Exception):
    """Raised when an operation targets a protected system path."""


def is_protected(path: str | os.PathLike[str]) -> bool:
    """Return True if *path* lives inside a protected system location."""
    try:
        resolved = Path(path).resolve()
    except (OSError, ValueError):
        return True  # if we cannot resolve it, treat as unsafe
    # A bare drive root (C:\) is also protected.
    if resolved.parent == resolved:
        return True
    for root in _PROTECTED_ROOTS:
        try:
            resolved.relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def guard(path: str | os.PathLike[str]) -> Path:
    """Return a resolved Path, raising if it is protected."""
    if is_protected(path):
        raise ProtectedPathError(str(path))
    return Path(path).resolve()


# -- app / process launching ---------------------------------------------
# Friendly aliases -> executable names.
APP_ALIASES = {
    "chrome": "chrome",
    "\u0643\u0631\u0648\u0645": "chrome",  # كروم
    "edge": "msedge",
    "notepad": "notepad",
    "\u0645\u0641\u0643\u0631\u0629": "notepad",  # مفكرة
    "calc": "calc",
    "\u0622\u0644\u0629 \u062d\u0627\u0633\u0628\u0629": "calc",
    "explorer": "explorer",
    "code": "code",
    "vscode": "code",
    "terminal": "wt",
    "powershell": "powershell",
}


def open_app(name: str) -> str:
    """Launch an application by friendly name or executable."""
    exe = APP_ALIASES.get(name.strip().lower(), name.strip())
    subprocess.Popen(exe, shell=True)
    return exe


def run_powershell(script: str) -> subprocess.CompletedProcess[str]:
    """Run a PowerShell script and capture its output."""
    return subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        timeout=60,
    )


# -- folder organisation --------------------------------------------------
# Map file extensions to category folder names.
_CATEGORIES = {
    "Images": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"},
    "Documents": {".pdf", ".doc", ".docx", ".txt", ".md", ".xlsx", ".pptx"},
    "Archives": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Audio": {".mp3", ".wav", ".flac", ".m4a"},
    "Video": {".mp4", ".mkv", ".mov", ".avi"},
    "Code": {".py", ".js", ".ts", ".c", ".cpp", ".java", ".cs", ".go", ".rs"},
}


def organize_folder(folder: str | os.PathLike[str]) -> dict[str, int]:
    """Sort loose files in *folder* into category sub-folders.

    Returns a mapping of category -> number of files moved.
    """
    base = guard(folder)
    if not base.is_dir():
        raise NotADirectoryError(str(base))
    moved: dict[str, int] = {}
    for entry in list(base.iterdir()):
        if entry.is_dir():
            continue
        category = _category_for(entry.suffix.lower())
        target_dir = base / category
        target_dir.mkdir(exist_ok=True)
        entry.rename(target_dir / entry.name)
        moved[category] = moved.get(category, 0) + 1
    return moved


def _category_for(suffix: str) -> str:
    for category, exts in _CATEGORIES.items():
        if suffix in exts:
            return category
    return "Other"
