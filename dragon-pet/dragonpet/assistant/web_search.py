"""Web search and local file search helpers."""

from __future__ import annotations

import os
import webbrowser
from pathlib import Path
from urllib.parse import quote_plus


def web_search(query: str) -> str:
    """Open the default browser on a search results page. Returns the URL."""
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    webbrowser.open(url)
    return url


def open_url(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return url


def find_files(
    pattern: str,
    roots: list[str] | None = None,
    limit: int = 25,
) -> list[str]:
    """Search common user folders for files whose name contains *pattern*."""
    if roots is None:
        home = Path.home()
        roots = [
            str(home / "Desktop"),
            str(home / "Documents"),
            str(home / "Downloads"),
        ]
    needle = pattern.lower()
    results: list[str] = []
    for root in roots:
        root_path = Path(root)
        if not root_path.is_dir():
            continue
        for dirpath, _dirs, files in os.walk(root_path):
            for name in files:
                if needle in name.lower():
                    results.append(str(Path(dirpath) / name))
                    if len(results) >= limit:
                        return results
    return results
