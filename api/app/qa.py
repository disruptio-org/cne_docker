# -*- coding: utf-8 -*-
"""Quality-assurance helpers for the extraction pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import csv

from app.utils_text import looks_mojibake

CRITICAL_FIELDS: Tuple[str, ...] = (
    "DTMNFR",
    "ORGAO",
    "TIPO",
    "SIGLA",
    "NOME_LISTA",
    "NUM_ORDEM",
    "NOME_CANDIDATO",
    "PARTIDO_PROPONENTE",
)


def _normalise_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def collect_suspect_rows(
    rows: Sequence[Dict[str, Any]],
    *,
    metadata: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """Return a list of rows that should be highlighted for manual QA."""

    suspects: List[Dict[str, Any]] = []
    needs_review = bool(metadata.get("needs_review")) if metadata else False
    context_flag_used = False

    for idx, row in enumerate(rows, start=1):
        reasons = []
        for field in CRITICAL_FIELDS:
            if not _normalise_string(row.get(field, "")):
                reasons.append(f"missing:{field}")
        for field, value in row.items():
            if isinstance(value, str) and looks_mojibake(value):
                reasons.append(f"mojibake:{field}")
        if needs_review and not context_flag_used:
            reasons.append("context:needs_review")
            context_flag_used = True
        if reasons:
            suspect_row = dict(row)
            suspect_row["_qa_index"] = idx
            suspect_row["_qa_reason"] = ";".join(sorted(set(reasons)))
            suspects.append(suspect_row)

    if needs_review and not context_flag_used and not rows:
        suspects.append({"_qa_index": 0, "_qa_reason": "context:needs_review"})

    return suspects


def _gather_fieldnames(rows: Iterable[Dict[str, Any]]) -> List[str]:
    ordered: List[str] = list(CRITICAL_FIELDS)
    seen = set(ordered)
    for row in rows:
        for key in row.keys():
            if key.startswith("_qa_"):
                continue
            if key not in seen:
                ordered.append(key)
                seen.add(key)
    for extra in ("_qa_index", "_qa_reason"):
        if extra not in seen:
            ordered.append(extra)
            seen.add(extra)
    return ordered

QA_OUTPUT_DIR = Path("/app/out")


def write_qa_csv(
    rows: Sequence[Dict[str, Any]],
    output_csv_path: str,
    *,
    metadata: Optional[Dict[str, Any]] = None,
    suspects: Optional[Sequence[Dict[str, Any]]] = None,
    encoding: str = "utf-8-sig",
) -> Tuple[str, List[Dict[str, Any]]]:
    """Persist a QA CSV in ``/app/out`` and return its location."""

    qa_name = f"{Path(output_csv_path).stem}_qa.csv"
    qa_path = QA_OUTPUT_DIR / qa_name
    qa_path.parent.mkdir(parents=True, exist_ok=True)

    suspect_rows = list(suspects) if suspects is not None else collect_suspect_rows(
        rows, metadata=metadata
    )

    fieldnames = _gather_fieldnames(list(rows) + suspect_rows)

    with qa_path.open("w", newline="", encoding=encoding) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=";", extrasaction="ignore")
        writer.writeheader()
        for suspect in suspect_rows:
            row = {key: suspect.get(key, "") for key in fieldnames}
            writer.writerow(row)

    return str(qa_path), suspect_rows
