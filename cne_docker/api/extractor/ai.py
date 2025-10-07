from rapidfuzz import process, fuzz

CANON_SIGLAS = [
    "PS","PPD/PSD","CDS-PP","CH","IL","BE","BE.L","PCP-PEV","PAN","LIVRE","CHEGA","CDU"
]

def normalize_sigla(sigla_raw: str) -> str:
    s = sigla_raw.strip()
    if s == "CDU":
        return "PCP-PEV"
    best = process.extractOne(s, CANON_SIGLAS, scorer=fuzz.token_set_ratio)
    if best and best[1] >= 90:
        return best[0]
    return s

def guess_is_name(line: str, enable_ia: bool = True) -> bool:
    if not enable_ia:
        return True
    if any(ch.isdigit() for ch in line):
        return False
    tokens = [t for t in line.split() if len(t) > 1]
    ups = sum(1 for t in tokens if t[:1].isupper())
    return len(tokens) >= 2 and ups >= 2
