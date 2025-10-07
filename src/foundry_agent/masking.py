"""Simple masking utility for prompt / completion logging.

Modes:
- off: no masking
- standard: basic email + long text truncation
- strict: standard + numbers (>=5 digits) + potential IDs

Usage:
    from .masking import mask_text, get_mode
    masked = mask_text(raw_text)

Environment Variable:
    AGENT_MASKING_MODE = off|standard|strict (default: standard)
"""
from __future__ import annotations
import os, re
from typing import Callable

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+")
LONG_NUMBER_RE = re.compile(r"\b\d{5,}\b")
UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
MAX_LEN = 2000

_DEF_MODE = "standard"

def get_mode() -> str:
    return os.getenv("AGENT_MASKING_MODE", _DEF_MODE).lower()

def _apply_standard(text: str) -> str:
    text = EMAIL_RE.sub("[EMAIL]", text)
    if len(text) > MAX_LEN:
        text = text[:MAX_LEN] + "...[TRUNC]"
    return text

def _apply_strict(text: str) -> str:
    text = _apply_standard(text)
    text = LONG_NUMBER_RE.sub("[NUMBER]", text)
    text = UUID_RE.sub("[UUID]", text)
    return text

_MODE_FUNCS: dict[str, Callable[[str], str]] = {
    "off": lambda t: t,
    "standard": _apply_standard,
    "strict": _apply_strict,
}

def mask_text(text: str | None) -> str:
    if text is None:
        return ""
    mode = get_mode()
    func = _MODE_FUNCS.get(mode, _apply_standard)
    try:
        return func(text)
    except Exception:
        return text  # fail open

if __name__ == "__main__":  # quick manual test
    sample = "Contact me at test@example.com and 123456789 with id 550e8400-e29b-41d4-a716-446655440000"
    for m in ("off", "standard", "strict"):
        os.environ["AGENT_MASKING_MODE"] = m
        print(m, "=>", mask_text(sample))
