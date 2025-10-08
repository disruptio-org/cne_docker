"""Basic regression tests for NER-driven row prediction."""

from pathlib import Path
import sys
from typing import List

import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.learn import infer


class _FakeEnt:
    def __init__(self, text: str, label_: str) -> None:
        self.text = text
        self.label_ = label_


class _FakeDoc:
    def __init__(self, ents: List[_FakeEnt]):
        self.ents = ents


class _FakeNLP:
    def __call__(self, text: str) -> _FakeDoc:
        if "João" in text:
            return _FakeDoc([_FakeEnt("João", "PERSON")])
        return _FakeDoc([])


@pytest.fixture(autouse=True)
def patch_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(infer, "_load_model", lambda model_dir="": _FakeNLP())


def test_predict_rows_extracts_basic_candidate_data() -> None:
    lines = [
        "1 João Silva",
        "2 Maria Santos",
    ]

    rows = infer.predict_rows(lines, model_dir="/does/not/matter")

    assert len(rows) == 2
    assert rows[0]["NUM_ORDEM"] == "1"
    assert rows[0]["NOME_CANDIDATO"] == "João"
    assert rows[1]["NUM_ORDEM"] == "2"
    assert rows[1]["NOME_CANDIDATO"] == "Maria Santos"
