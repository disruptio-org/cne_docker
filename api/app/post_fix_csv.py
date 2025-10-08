# -*- coding: utf-8 -*-
# post_fix_csv.py — utilitário para limpar mojibake em CSV já gerado
import sys
import pandas as pd
from app.utils_text import clean_text

def main(inp: str, outp: str):
    df = pd.read_csv(inp, sep=';', dtype=str, keep_default_na=False)
    for col in ("NOME_CANDIDATO","NOME_LISTA","PARTIDO_PROPONENTE","SIGLA"):
        if col in df.columns:
            df[col] = df[col].map(clean_text)
    df.to_csv(outp, sep=';', index=False, encoding='utf-8')
    print(f"Salvo: {outp}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python -m app.post_fix_csv <input.csv> <output.csv>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
