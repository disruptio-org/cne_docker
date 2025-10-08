# -*- coding: utf-8 -*-
# utils_party.py — SIGLA, NOME_LISTA, detecção de coligação e "proposto por"
from typing import Optional
import re

SIGLAS_PARTIDOS = {
    "PS","PPD/PSD","CDS-PP","PAN","BE","PCP-PEV","CDU","IL","LIVRE","CHEGA","NC","MPT","PTP","RIR","JPP"
}

COALITION_RE = re.compile(r"\b([A-Z]{2,}(?:/[A-Z]{2,})?(?:\.[A-Z]{2,}(?:/[A-Z]{2,})?)*)\b")

NOME_LISTA_LABELS = [r"Denomina[cç][aã]o", r"Nome da lista", r"Designa[cç][aã]o"]

PROPONENTE_PATTERNS = [
    re.compile(r"\bproposto por\s+([A-Z/-]{2,})\b", re.I),
    re.compile(r"\bproponente:\s*([A-Z/-]{2,})\b", re.I),
    re.compile(r"[–-]\s*([A-Z/-]{2,})\s*$", re.I),
]

def find_sigla(text: str) -> Optional[str]:
    if not text:
        return None
    for sig in sorted(SIGLAS_PARTIDOS, key=len, reverse=True):
        if re.search(rf"\b{re.escape(sig)}\b", text):
            return sig
    m = COALITION_RE.search(text or "")
    if m:
        cand = m.group(1)
        if "." in cand:
            return cand
    return None

def find_nome_lista(text: str) -> Optional[str]:
    if not text:
        return None
    for lbl in NOME_LISTA_LABELS:
        m = re.search(rf"{lbl}\s*:\s*(.+?)\s*$", text, re.I)
        if m:
            return m.group(1).strip()
    return None

def is_coalition(sigla: Optional[str]) -> bool:
    if not sigla:
        return False
    return "." in sigla

def extract_proponente_from_line(line: str) -> Optional[str]:
    if not line:
        return None
    for pat in PROPONENTE_PATTERNS:
        m = pat.search(line)
        if m:
            return m.group(1).upper().strip()
    return None

def normalize_proponente(proponente: Optional[str]) -> Optional[str]:
    if not proponente:
        return None
    p = proponente.replace("CDSPP", "CDS-PP").replace("PPDPSD","PPD/PSD")
    return p
