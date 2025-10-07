import pandas as pd
from typing import Tuple, Dict

REQUIRED_COLS = ["DTMNFR","ORGAO","TIPO","SIGLA","SIMBOLO","NOME_LISTA","NUM_ORDEM","NOME_CANDIDATO","PARTIDO_PROPONENTE","INDEPENDENTE"]
KEY = ["ORGAO","SIGLA","TIPO","NUM_ORDEM","NOME_CANDIDATO"]

def validate_csv_schema(path: str) -> Dict:
    df = pd.read_csv(path, sep=";", dtype=str, encoding="utf-8")
    issues = []
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        issues.append({"type":"missing_columns","detail":missing})
    if "ORGAO" in df.columns:
        bad_orgao = df[~df["ORGAO"].isin(["AM","CM"])]
        if not bad_orgao.empty:
            issues.append({"type":"invalid_orgao","rows":bad_orgao.index[:50].tolist()})
    if "TIPO" in df.columns:
        bad_tipo = df[~df["TIPO"].isin(["2","3",2,3])]
        if not bad_tipo.empty:
            issues.append({"type":"invalid_tipo","rows":bad_tipo.index[:50].tolist()})
    if "INDEPENDENTE" in df.columns:
        bad_ind = df[~df["INDEPENDENTE"].isin(["S","N"])]
        if not bad_ind.empty:
            issues.append({"type":"invalid_indep","rows":bad_ind.index[:50].tolist()})
    return {"ok": len(issues)==0, "issues": issues, "rows": int(df.shape[0])}

def _read_csv(path: str) -> pd.DataFrame:
    return pd.read_csv(path, sep=";", dtype=str, encoding="utf-8").fillna("")

def _prep(df: pd.DataFrame) -> pd.DataFrame:
    for c in REQUIRED_COLS:
        if c not in df.columns:
            df[c] = ""
        else:
            df[c] = df[c].astype(str).str.strip()
    return df

def diff_csvs(csv_a: str, csv_b: str) -> Tuple[Dict, pd.DataFrame]:
    a = _prep(_read_csv(csv_a))
    b = _prep(_read_csv(csv_b))

    akey = a[KEY].drop_duplicates()
    bkey = b[KEY].drop_duplicates()

    a_only = akey.merge(bkey, on=KEY, how="left", indicator=True)
    a_only = a_only[a_only["_merge"]=="left_only"][KEY]

    b_only = bkey.merge(akey, on=KEY, how="left", indicator=True)
    b_only = b_only[b_only["_merge"]=="left_only"][KEY]

    diffs = {
        "only_in_A": a_only.to_dict(orient="records"),
        "only_in_B": b_only.to_dict(orient="records"),
        "equal": len(a_only)==0 and len(b_only)==0,
        "rows_A": int(a.shape[0]),
        "rows_B": int(b.shape[0])
    }

    union = pd.concat([a, b], ignore_index=True)
    union = union.drop_duplicates(subset=KEY, keep="first")
    for c in REQUIRED_COLS:
        if c not in union.columns:
            union[c] = ""
    union = union[REQUIRED_COLS]
    union = union.sort_values(by=["ORGAO","SIGLA","TIPO","NOME_LISTA","NUM_ORDEM","NOME_CANDIDATO"]).reset_index(drop=True)

    return diffs, union
