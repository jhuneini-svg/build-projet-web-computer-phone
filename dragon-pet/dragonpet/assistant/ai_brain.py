"""Natural-language understanding via OpenAI or a local Ollama server.

Both integrations are optional. If neither is configured, callers should fall
back to the rule-based intent parser in :mod:`commands`.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

_SYSTEM_PROMPT = (
    "You are the brain of a desktop dragon assistant. "
    "Given a user's request (Arabic or English), respond ONLY with compact JSON "
    '{"intent": <one of: open_app, web_search, find_files, organize_folder, '
    'run_powershell, write_code, chat>, "argument": <string>}. '
    "No prose, no markdown."
)


def _parse_json(text: str) -> dict[str, str] | None:
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        obj = json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None
    if "intent" in obj:
        return {"intent": str(obj["intent"]), "argument": str(obj.get("argument", ""))}
    return None


def openai_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY"))


def _ask_openai(text: str) -> dict[str, str] | None:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return None
    model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "temperature": 0,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        return _parse_json(content)
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError):
        return None


def ollama_available() -> bool:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    try:
        urllib.request.urlopen(host + "/api/tags", timeout=1.5)
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def _ask_ollama(text: str) -> dict[str, str] | None:
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    model = os.environ.get("OLLAMA_MODEL", "llama3")
    payload = json.dumps(
        {
            "model": model,
            "prompt": f"{_SYSTEM_PROMPT}\n\nUser: {text}\nJSON:",
            "stream": False,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        host + "/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return _parse_json(body.get("response", ""))
    except (urllib.error.URLError, KeyError, json.JSONDecodeError, TimeoutError):
        return None


def understand(text: str) -> dict[str, str] | None:
    """Return {intent, argument} using OpenAI then Ollama, else None."""
    if openai_available():
        result = _ask_openai(text)
        if result:
            return result
    if ollama_available():
        return _ask_ollama(text)
    return None
