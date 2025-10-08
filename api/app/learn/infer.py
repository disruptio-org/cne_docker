"""Inference utilities for NER-driven candidate extraction."""
from __future__ import annotations

import re
from functools import lru_cache
from typing import Dict, List

import spacy
from spacy.language import Language
from spacy.tokens import Doc

from app.utils_text import clean_text
from app.utils_listctx import ListContext, detect_orgao, is_new_list_heading
from app.utils_party import (
    extract_proponente_from_line,
    find_nome_lista,
    find_sigla,
    is_coalition,
    normalize_proponente,
)


_ORDER_RE = re.compile(r"^\s*(\d{1,3})[\)\.-]?\s+(.*)$")


@lru_cache(maxsize=1)
def _load_model(model_dir: str) -> Language:
    """Load and cache the spaCy model used for NER."""
    return spacy.load(model_dir)


def _extract_candidate_name(doc: Doc, text: str) -> str:
    """Use the PERSON entities detected by *doc* to select the candidate name."""
    persons = [clean_text(ent.text) for ent in doc.ents if ent.label_ == "PERSON"]
    if persons:
        return persons[0]

    # Fallback: take the portion before separators like " - " or ",".
    fallback = re.split(r"\s+[–-]\s+|,", text, maxsplit=1)[0]
    return clean_text(fallback)


def _base_row() -> Dict[str, str]:
    return {
        "DTMNFR": "",
        "ORGAO": "",
        "TIPO": "2",
        "SIGLA": "",
        "SIMBOLO": "",
        "NOME_LISTA": "",
        "NUM_ORDEM": "",
        "NOME_CANDIDATO": "",
        "PARTIDO_PROPONENTE": "",
        "INDEPENDENTE": "0",
    }


def predict_rows(lines: List[str], model_dir: str = "/app/models/ner_pt") -> List[Dict[str, str]]:
    """Predict CNE-style rows from raw document lines using an NER model."""
    nlp = _load_model(model_dir)
    ctx = ListContext(orgao=None, sigla=None, nome_lista=None, simbolo=None, needs_review=0)
    ctx.extra["proponente"] = None

    rows: List[Dict[str, str]] = []

    for raw_line in lines:
        line = clean_text(raw_line)
        if not line:
            continue

        ctx.orgao = detect_orgao(line, ctx.orgao)

        if is_new_list_heading(line):
            new_sigla = find_sigla(line)
            if new_sigla:
                ctx.sigla = new_sigla
            new_nome = find_nome_lista(line)
            if new_nome:
                ctx.nome_lista = clean_text(new_nome)
            ctx.extra["proponente"] = None
            continue

        nome_lista = find_nome_lista(line)
        if nome_lista:
            ctx.nome_lista = clean_text(nome_lista)
            continue

        sigla_inline = find_sigla(line)
        if sigla_inline and sigla_inline != ctx.sigla:
            ctx.sigla = sigla_inline

        proponente_inline = normalize_proponente(extract_proponente_from_line(line))
        if proponente_inline:
            ctx.extra["proponente"] = proponente_inline

        match = _ORDER_RE.match(line)
        if not match:
            continue

        num_ordem, remainder = match.groups()
        candidate_text = remainder.strip()
        if not candidate_text:
            continue

        doc = nlp(candidate_text)
        candidate_name = _extract_candidate_name(doc, candidate_text)

        row = _base_row()
        row["NUM_ORDEM"] = num_ordem
        row["NOME_CANDIDATO"] = candidate_name
        row["ORGAO"] = ctx.orgao or "CM"
        row["NOME_LISTA"] = clean_text(ctx.nome_lista) if ctx.nome_lista else ""

        sigla = ctx.sigla or sigla_inline or ""
        row["SIGLA"] = clean_text(sigla)

        sigla_upper = row["SIGLA"]
        proponente = ctx.extra.get("proponente") if isinstance(ctx.extra, dict) else None
        if is_coalition(sigla_upper):
            row["PARTIDO_PROPONENTE"] = clean_text(proponente or sigla_upper)
        else:
            row["PARTIDO_PROPONENTE"] = clean_text(sigla_upper)

        if "suplente" in candidate_text.lower():
            row["TIPO"] = "3"
        if sigla_upper == "ICA":
            row["INDEPENDENTE"] = "1"

        if row["SIGLA"]:
            ctx.sigla = row["SIGLA"]
        if row["NOME_LISTA"]:
            ctx.nome_lista = row["NOME_LISTA"]

        rows.append(row)

    return rows
