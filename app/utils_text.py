# -*- coding: utf-8 -*-
"""Utilities for cleaning mojibake-heavy text extracted from DOCX files."""

from typing import Optional, Any, Dict, List
import unicodedata as ud
import re

try:
    from ftfy import fix_text as _fix_text
except Exception:  # pragma: no cover - ftfy is optional at runtime
    _fix_text = None

MOJIBAKE_TOKENS = ("Ã", "Â", "â", "�")
EXPLICIT_FIXES = [
    (re.compile(r"â€“"), "–"),
    (re.compile(r"â€”"), "—"),
    (re.compile(r"â€œ"), "“"),
    (re.compile(r"â€\u009d?"), "”"),
    (re.compile(r"â€˜"), "‘"),
    (re.compile(r"â€™"), "’"),
    (re.compile(r"â€"), "€"),
]
_ACCENT_RE = re.compile(r"[áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ]")


def looks_mojibake(value: str) -> bool:
    """Returns True when typical mojibake glyphs are found in *value*."""
    return bool(value) and any(tok in value for tok in MOJIBAKE_TOKENS)


def _apply_explicit_fixes(value: str) -> str:
    fixed = value
    for pattern, replacement in EXPLICIT_FIXES:
        fixed = pattern.sub(replacement, fixed)
    return fixed


def _latin1_to_utf8(value: str) -> str:
    try:
        return value.encode("latin-1", "ignore").decode("utf-8", "ignore")
    except Exception:
        return value


def _prefer_candidate(current: str, candidate: str) -> str:
    """Pick whichever text looks cleaner (fewer mojibake markers, more accents)."""
    if not candidate:
        return current
    candidate = candidate.strip()
    current = current.strip()
    if not candidate:
        return current

    current_bad = looks_mojibake(current)
    candidate_bad = looks_mojibake(candidate)
    if current_bad and not candidate_bad:
        return candidate
    if candidate_bad and not current_bad:
        return current

    current_repl = sum(current.count(tok) for tok in MOJIBAKE_TOKENS)
    candidate_repl = sum(candidate.count(tok) for tok in MOJIBAKE_TOKENS)
    if candidate_repl < current_repl:
        return candidate

    current_accents = len(_ACCENT_RE.findall(current))
    candidate_accents = len(_ACCENT_RE.findall(candidate))
    if candidate_accents > current_accents:
        return candidate

    return candidate if candidate != current else current


def clean_text(value: Optional[str]) -> str:
    """Fixes mojibake artefacts and normalises the output to NFC."""
    if value is None:
        return ""

    text = str(value)

    if _fix_text:
        try:
            fixed = _fix_text(text)
            text = _prefer_candidate(text, fixed)
        except Exception:
            pass

    if looks_mojibake(text):
        decoded = _latin1_to_utf8(text)
        text = _prefer_candidate(text, decoded)

    text = _apply_explicit_fixes(text)
    text = ud.normalize("NFC", text)
    return text.strip()


def sanitize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Returns a deep copy of ``rows`` with ``clean_text`` applied to all strings."""
    sanitized: List[Dict[str, Any]] = []
    for row in rows:
        cleaned: Dict[str, Any] = {}
        for key, value in row.items():
            cleaned[key] = clean_text(value) if isinstance(value, str) else value
        sanitized.append(cleaned)
    return sanitized
