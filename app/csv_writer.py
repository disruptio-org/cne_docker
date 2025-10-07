# -*- coding: utf-8 -*-
"""Helper utilities to export the final CNE-compliant CSV file."""

from typing import List, Dict
import pandas as pd

from app.utils_text import clean_text, sanitize_rows

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


def write_cne_csv(rows: List[Dict[str, str]], out_path: str, encoding: str = "utf-8-sig") -> str:
    """Sanitise the provided ``rows`` and export them to ``out_path``.

    The resulting CSV uses ``;`` as separator (CNE requirement) and writes
    UTF-8 with BOM by default so Excel autodetects it correctly.
    """
    safe_rows = sanitize_rows(rows)

    df = pd.DataFrame(safe_rows, columns=CNE_COLS)
    df = df.fillna("")

    for col in ("NOME_CANDIDATO", "NOME_LISTA", "PARTIDO_PROPONENTE", "SIGLA"):
        if col in df.columns:
            df[col] = df[col].map(clean_text)

    df.to_csv(out_path, sep=";", index=False, encoding=encoding)
    return out_path
