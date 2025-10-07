# -*- coding: utf-8 -*-
# app/utils_text.py — Reparação robusta de mojibake + normalização NFC

from typing import Optional, Any, Dict, List
import unicodedata as ud
import re

try:
    from ftfy import fix_text as _fix_text
except Exception:
    _fix_text = None

# Tokens típicos de mojibake quando UTF-8 é lido como Latin-1/CP1252
MOJIBAKE_TOKENS = ("Ã", "Â", "â", "�")

# Pontuação errada comum
EXPLICIT_FIXES = [
    (re.compile(r"â€“"), "–"),   # en dash
    (re.compile(r"â€”"), "—"),   # em dash
    (re.compile(r"â€œ"), "“"),
    (re.compile(r"â€\u009d?"), "”"),
    (re.compile(r"â€˜"), "‘"),
    (re.compile(r"â€™"), "’"),
    (re.compile(r"â€"), "€"),
]

PT_ACCENTS = "áéíóúâêôãõçÁÉÍÓÚÂÊÔÃÕÇ"

def looks_mojibake(s: str) -> bool:
    return bool(s) and any(tok in s for tok in MOJIBAKE_TOKENS)

def _explicit_fixes(s: str) -> str:
    out = s
    for pat, rep in EXPLICIT_FIXES:
        out = pat.sub(rep, out)
    return out

def _score_quality(s: str) -> int:
    """Maior é melhor: penaliza mojibake, recompensa acentos PT válidos."""
    if not s:
        return -10**6
    score = 0
    # penaliza tokens de mojibake
    for tok in MOJIBAKE_TOKENS:
        score -= s.count(tok) * 5
    # recompensa presença de acentos PT reais
    for ch in PT_ACCENTS:
        score += s.count(ch)
    # pequeno bónus por ausência total de mojibake
    if not looks_mojibake(s):
        score += 3
    return score

def _fix_chain_candidates(s: str) -> List[str]:
    """Gera candidatos de reparação; o melhor (por score) é escolhido."""
    cands = []
    # A) original normalizado
    cands.append(ud.normalize("NFC", s))

    # B) ftfy (se disponível)
    if _fix_text:
        try:
            cands.append(ud.normalize("NFC", _fix_text(s)))
        except Exception:
            pass

    # C) tentativa clássica latin1->utf8
    try:
        cands.append(ud.normalize("NFC", s.encode("latin-1", "ignore").decode("utf-8", "ignore")))
    except Exception:
        pass

    # D) fixes explícitos
    cands.append(ud.normalize("NFC", _explicit_fixes(s)))

    # Remover duplicados mantendo ordem
    seen = set()
    uniq = []
    for c in cands:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq

def clean_text(s: Optional[str]) -> str:
    """Limpa mojibake e normaliza para NFC. Sempre tenta melhorar."""
    if s is None:
        return ""
    raw = str(s)
    # Gera candidatos e escolhe o de melhor qualidade
    cands = _fix_chain_candidates(raw)
    best = max(cands, key=_score_quality)
    return best.strip()

def sanitize_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Aplica clean_text a todas as strings em todas as linhas (dict->str)."""
    out: List[Dict[str, Any]] = []
    for r in rows:
        fixed: Dict[str, Any] = {}
        for k, v in r.items():
            if isinstance(v, str):
                fixed[k] = clean_text(v)
            else:
                fixed[k] = v
        out.append(fixed)
    return out
