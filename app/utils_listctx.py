# -*- coding: utf-8 -*-
# utils_listctx.py — Contexto de lista + detecção de ORGAO + início de lista
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Iterable
import re

ORG_PATTERNS = [
    (re.compile(r"\bAssembleia Municipal\b", re.I), "AM"),
    (re.compile(r"\bC[âa]mara Municipal\b", re.I), "CM"),
    (re.compile(r"\bAssembleia de Freguesia\b", re.I), "AF"),
]

NEW_LIST_PATTERNS = [
    re.compile(r"^\s*(Lista|Candidatura)\b", re.I),
    re.compile(r"^\s*Denomina[cç][aã]o\b", re.I),
    re.compile(r"^\s*Nome da lista\b", re.I),
    re.compile(r"^\s*Designa[cç][aã]o\b", re.I),
]

@dataclass
class ListContext:
    orgao: Optional[str] = None
    sigla: Optional[str] = None
    nome_lista: Optional[str] = None
    simbolo: Optional[str] = None
    needs_review: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)

def detect_orgao(line: str, current: Optional[str]) -> Optional[str]:
    for pat, tag in ORG_PATTERNS:
        if pat.search(line):
            return tag
    return current

def is_new_list_heading(line: str) -> bool:
    return any(p.search(line) for p in NEW_LIST_PATTERNS)

def split_into_sections_by_orgao(lines: Iterable[str]):
    current = None
    bucket = []
    for ln in lines:
        new = detect_orgao(ln, current)
        if new != current:
            if bucket and current:
                yield {"orgao": current, "lines": bucket}
            bucket = [ln]
            current = new
        else:
            bucket.append(ln)
    if bucket:
        yield {"orgao": current, "lines": bucket}
