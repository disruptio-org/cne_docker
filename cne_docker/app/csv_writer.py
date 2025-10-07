# -*- coding: utf-8 -*-
# app/csv_writer.py — Escrita do CSV final no formato CNE

from typing import List, Dict
import pandas as pd
from app.utils_text import clean_text, sanitize_rows

CNE_COLS = [
    "DTMNFR","ORGAO","TIPO","SIGLA","SIMBOLO",
    "NOME_LISTA","NUM_ORDEM","NOME_CANDIDATO",
    "PARTIDO_PROPONENTE","INDEPENDENTE",
]

def write_cne_csv(rows: List[Dict[str, str]], out_path: str, encoding: str = "utf-8-sig") -> str:
    """
    Escreve o CSV final:
      - Sanitiza todas as strings (corrige mojibake)
      - Exporta com encoding configurável (default UTF-8-SIG; Excel-friendly)
        Se o Excel do cliente insistir em falhar a auto-detecção, usar encoding="cp1252".
    """
    # 1) Sanitização global defensiva
    rows = sanitize_rows(rows)

    # 2) DataFrame com colunas na ordem exigida
    df = pd.DataFrame(rows, columns=CNE_COLS)

    # 3) “cinto e suspensórios”: limpeza extra em colunas críticas
    for col in ("NOME_CANDIDATO","NOME_LISTA","PARTIDO_PROPONENTE","SIGLA"):
        if col in df.columns:
            df[col] = df[col].map(clean_text)

    # 4) Export
    df.to_csv(out_path, sep=";", index=False, encoding=encoding)
    return out_path
