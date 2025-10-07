"""Tests for :mod:`app.csv_writer`."""

from pathlib import Path
import sys

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.csv_writer import write_cne_csv


def _base_row() -> dict:
    return {
        "DTMNFR": "2024-01-01",
        "ORGAO": "CM",
        "TIPO": "2",
        "SIGLA": "ABC",
        "SIMBOLO": "",
        "NOME_LISTA": "Lista Boa",
        "NUM_ORDEM": "1",
        "NOME_CANDIDATO": "João",
        "PARTIDO_PROPONENTE": "ABC",
        "INDEPENDENTE": "0",
    }


def test_write_cne_csv_creates_empty_qa_when_clean(tmp_path: Path) -> None:
    out_path = tmp_path / "clean.csv"
    write_cne_csv([_base_row()], str(out_path))

    qa_path = out_path.with_name(f"{out_path.stem}_qa.csv")
    assert qa_path.exists()

    qa_df = pd.read_csv(qa_path, sep=";")
    assert qa_df.empty


def test_write_cne_csv_lists_rows_with_residual_mojibake(tmp_path: Path) -> None:
    bad_row = _base_row()
    bad_row["NOME_LISTA"] = "Ã"

    out_path = tmp_path / "bad.csv"
    write_cne_csv([bad_row], str(out_path))

    qa_path = out_path.with_name(f"{out_path.stem}_qa.csv")
    qa_df = pd.read_csv(qa_path, sep=";")

    assert len(qa_df) == 1
    assert qa_df.iloc[0]["NOME_LISTA"] == "Ã"
