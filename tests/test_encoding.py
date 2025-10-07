"""Regression tests for mojibake decoding helper functions."""

from pathlib import Path
import sys

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.utils_text import clean_text


@pytest.mark.parametrize(
    "dirty, expected",
    [
        ("JoÃ£o", "João"),
        ("PESSOAS â€“ ANIMAIS", "PESSOAS – ANIMAIS"),
        ("ClÃ¡udia", "Cláudia"),
    ],
)
def test_clean_text_fixes_common_mojibake(dirty: str, expected: str) -> None:
    """Ensure ``clean_text`` fixes common mojibake patterns."""

    assert clean_text(dirty) == expected
