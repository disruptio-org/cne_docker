# -*- coding: utf-8 -*-
"""
extract_pipeline.py
Corrige:
  - Mojibake/acentos (NOME_LISTA, NOME_CANDIDATO) com clean_text()
  - ORGAO por state machine (AM/CM/AF)
  - SIGLA/NOME_LISTA reavaliadas por lista
  - PARTIDO_PROPONENTE (procura "proposto por ..."; fallback em coligações)
"""

from typing import List, Dict
from app.utils_text import clean_text
from api.extractor.pipeline import parse_docx
from api.extractor.rules import clean_lines, normalize_whitespace
from app.utils_listctx import ListContext, detect_orgao, is_new_list_heading
from app.utils_party import (
    find_sigla, find_nome_lista, is_coalition,
    extract_proponente_from_line, normalize_proponente
)

# Usa as tuas versões reais se já existirem
try:
    from app.parsers import is_candidate_line, parse_candidate_fields  # type: ignore
except Exception:
    def is_candidate_line(line: str) -> bool:
        return bool(line and line.strip() and line.strip()[0].isdigit() and " " in line.strip())
    def parse_candidate_fields(line: str) -> Dict[str, str]:
        import re
        d = {"NUM_ORDEM": "", "NOME_CANDIDATO": "", "TIPO": "2", "INDEPENDENTE": "0"}
        m = re.match(r"^\s*(\d{1,3})[\)\.\-]?\s+(.*)$", line)
        if m:
            d["NUM_ORDEM"] = m.group(1)
            d["NOME_CANDIDATO"] = m.group(2).strip()
        if "suplente" in line.lower():
            d["TIPO"] = "3"
        return d

REQUIRED_FIELDS = (
    "DTMNFR","ORGAO","TIPO","SIGLA","SIMBOLO",
    "NOME_LISTA","NUM_ORDEM","NOME_CANDIDATO",
    "PARTIDO_PROPONENTE","INDEPENDENTE"
)

def linearize_document_to_lines(doc_path: str, enable_ia: bool = True) -> List[str]:
    """Return a list of cleaned text lines extracted from *doc_path*.

    The function normalises whitespace, removes bullet markers and applies
    ``clean_text`` when ``enable_ia`` is ``True`` (mirroring the previous
    behaviour of the legacy extractor).
    """

    raw_text = parse_docx(doc_path)
    normalised = normalize_whitespace(raw_text)
    candidate_lines = clean_lines(normalised)

    lines: List[str] = []
    for raw in candidate_lines:
        line = clean_text(raw) if enable_ia else raw.strip()
        if line:
            lines.append(line)
    return lines

def _sanitize_row(row: Dict[str, str]) -> Dict[str, str]:
    row["NOME_CANDIDATO"] = clean_text(row.get("NOME_CANDIDATO", ""))
    row["NOME_LISTA"] = clean_text(row.get("NOME_LISTA", ""))
    row["PARTIDO_PROPONENTE"] = clean_text(row.get("PARTIDO_PROPONENTE", ""))
    row["SIGLA"] = clean_text(row.get("SIGLA", ""))
    return row

def process_document_lines(lines: List[str]) -> List[Dict[str, str]]:
    ctx = ListContext(orgao=None, sigla=None, nome_lista=None, simbolo=None, needs_review=0)
    out_rows: List[Dict[str, str]] = []

    for raw in lines:
        # Limpeza logo à cabeça — isto já resolve "PESSOAS â€“ ..." -> "PESSOAS – ..."
        line = clean_text(raw)

        # 1) alternância de órgão
        ctx.orgao = detect_orgao(line, ctx.orgao)

        # 2) início de nova lista — reestimar SIGLA/NOME_LISTA e LIMPAR nome_lista
        if is_new_list_heading(line):
            sig = find_sigla(line) or ctx.sigla
            nome = find_nome_lista(line) or ctx.nome_lista
            ctx.sigla = sig
            ctx.nome_lista = clean_text(nome) if nome else None  # <— limpar aqui
            continue

        # 3) partido proponente inline (em coligações)
        proponente_inline = normalize_proponente(extract_proponente_from_line(line))

        # 4) candidatos
        if is_candidate_line(line):
            item = parse_candidate_fields(line)

            # Limpeza de campos textuais por linha
            item["NOME_CANDIDATO"] = clean_text(item.get("NOME_CANDIDATO", ""))
            item["NOME_LISTA"] = clean_text(ctx.nome_lista) if ctx.nome_lista else clean_text(item.get("NOME_LISTA", ""))

            # Contexto
            item["ORGAO"] = ctx.orgao or item.get("ORGAO") or "CM"
            if ctx.sigla:
                item["SIGLA"] = ctx.sigla

            # PARTIDO_PROPONENTE
            sigla = item.get("SIGLA") or ctx.sigla or ""
            if is_coalition(sigla):
                item["PARTIDO_PROPONENTE"] = proponente_inline or sigla
                if not proponente_inline:
                    ctx.needs_review = 1
            else:
                item["PARTIDO_PROPONENTE"] = item.get("PARTIDO_PROPONENTE") or sigla

            if sigla == "ICA":
                item["INDEPENDENTE"] = "1"

            for k in REQUIRED_FIELDS:
                item.setdefault(k, "")

            # Limpeza final de segurança
            item = _sanitize_row(item)

            out_rows.append(item)

    # Passagem final (belt-and-braces)
    out_rows = [_sanitize_row(r) for r in out_rows]
    return out_rows
