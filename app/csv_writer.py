# -*- coding: utf-8 -*-
"""Helper utilities to export the final CNE-compliant CSV file."""

from pathlib import Path
from typing import List, Dict
import pandas as pd

from app.utils_text import clean_text, sanitize_rows, looks_mojibake

CNE_COLS = [
    "DTMNFR",
    "ORGAO",
    "TIPO",
    "SIGLA",
    "SIMBOLO",
    "NOME_LISTA",
    "NUM_ORDEM",
    "NOME_CANDIDATO",
    "PARTIDO_PROPONENTE",
    "INDEPENDENTE",
]


def _row_contains_mojibake(row: pd.Series) -> bool:
    """Return ``True`` when any field in ``row`` still looks mojibake-heavy."""

    for value in row:
        if isinstance(value, str) and looks_mojibake(value):
            return True
    return False


def _export_qa_csv(df: pd.DataFrame, out_path: str) -> str:
    """Persist a QA CSV listing rows that still contain mojibake tokens."""

    qa_rows = df[df.apply(_row_contains_mojibake, axis=1)]
    qa_path = Path(out_path).with_name(f"{Path(out_path).stem}_qa.csv")
    qa_rows.to_csv(qa_path, sep=";", index=False, encoding="utf-8")
    return str(qa_path)


def write_cne_csv(
    rows: List[Dict[str, str]],
    out_path: str,
    encoding: str = "utf-8-sig",
    *,
    excel_compat: bool = False,
) -> str:
    """Sanitise the provided ``rows`` and export them to ``out_path``.

    The resulting CSV uses ``;`` as separator (CNE requirement) and writes
    UTF-8 with BOM by default so Excel autodetects it correctly. Passing
    ``excel_compat=True`` switches the encoding to Windows-1252 for legacy
    compatibility.
    """
    safe_rows = sanitize_rows(rows)

    if excel_compat:
        encoding = "cp1252"

    df = pd.DataFrame(safe_rows, columns=CNE_COLS)
    df = df.fillna("")

    for col in ("NOME_CANDIDATO", "NOME_LISTA", "PARTIDO_PROPONENTE", "SIGLA"):
        if col in df.columns:
            df[col] = df[col].map(clean_text)

    df.to_csv(out_path, sep=";", index=False, encoding=encoding)
    _export_qa_csv(df, out_path)
    return out_path
