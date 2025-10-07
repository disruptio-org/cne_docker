import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from extractor.rules import clean_lines, split_candidates_by_type


def test_clean_lines_removes_ordinals():
    text = "1.º João Silva\n2° Maria Sousa\n3º- José Lima"
    assert clean_lines(text) == [
        "João Silva",
        "Maria Sousa",
        "José Lima",
    ]


def test_clean_lines_preserves_leading_digits_without_delimiters():
    text = "123ABC\n45º DEF"
    assert clean_lines(text) == [
        "123ABC",
        "DEF",
    ]


def test_split_candidates_handles_ordinals():
    content = """Candidatos efetivos:\n1.º João Silva\n2° Maria Sousa\nCandidatos suplentes:\n1.º Ana Dias"""
    efetivos, suplentes = split_candidates_by_type(content)
    assert efetivos == ["João Silva", "Maria Sousa"]
    assert suplentes == ["Ana Dias"]
