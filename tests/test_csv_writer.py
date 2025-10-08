from pathlib import Path
import sys

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.csv_writer import write_cne_csv
from app.qa import collect_suspect_rows, write_qa_csv


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


def test_write_qa_csv_creates_empty_file_when_clean(tmp_path: Path) -> None:
    rows = [_base_row()]
    out_path = tmp_path / "clean.csv"
    write_cne_csv(rows, str(out_path))

    qa_path, suspects = write_qa_csv(rows, str(out_path))
    assert Path(qa_path).exists()
    assert not suspects

    qa_df = pd.read_csv(qa_path, sep=";")
    assert qa_df.empty


def test_collect_suspect_rows_flags_mojibake(tmp_path: Path) -> None:
    bad_row = _base_row()
    bad_row["NOME_LISTA"] = "Ã"

    out_path = tmp_path / "bad.csv"
    write_cne_csv([bad_row], str(out_path))

    suspects = collect_suspect_rows([bad_row])
    assert len(suspects) == 1
    assert "mojibake:NOME_LISTA" in suspects[0]["_qa_reason"]

    qa_path, _ = write_qa_csv([bad_row], str(out_path), suspects=suspects)
    qa_df = pd.read_csv(qa_path, sep=";")

    assert len(qa_df) == 1
    assert qa_df.iloc[0]["NOME_LISTA"] == "Ã"
