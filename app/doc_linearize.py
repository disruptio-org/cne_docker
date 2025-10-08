"""Utilities to linearize DOCX/PDF documents into plain-text training data."""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
from typing import Iterable, List, Sequence

from app.utils_text import clean_text
from api.extractor.rules import clean_lines, normalize_whitespace
from api.extractor.pipeline import parse_docx


def _ensure_directory(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _iter_clean_lines(raw_lines: Iterable[str]) -> List[str]:
    cleaned: List[str] = []
    for raw in raw_lines:
        txt = clean_text(raw)
        if txt:
            cleaned.append(txt)
    return cleaned


def _lines_from_docx(src_path: Path) -> List[str]:
    text = parse_docx(str(src_path))
    normalized = normalize_whitespace(text)
    return _iter_clean_lines(clean_lines(normalized))


def _lines_from_pdf(src_path: Path) -> List[str]:
    if importlib.util.find_spec("pdfminer.high_level") is None:
        raise RuntimeError("PDF support requires the 'pdfminer.six' package to be installed.")

    from pdfminer.high_level import extract_text  # type: ignore

    text = extract_text(str(src_path))
    normalized = normalize_whitespace(text or "")
    return _iter_clean_lines(clean_lines(normalized))


def _linearize(src_path: Path) -> List[str]:
    suffix = src_path.suffix.lower()
    if suffix == ".docx":
        return _lines_from_docx(src_path)
    if suffix == ".pdf":
        return _lines_from_pdf(src_path)
    raise ValueError(f"Unsupported document type: {suffix or 'unknown'}")


def linearize_to_txt(src_path: str, dst_path: str, enable_ia: bool = True) -> str:
    """Linearize *src_path* into UTF-8 text lines stored at *dst_path*.

    Parameters
    ----------
    src_path:
        Input document path (DOCX or PDF).
    dst_path:
        Destination plain-text file path.
    enable_ia:
        Currently unused placeholder to keep signature compatible with
        other tooling. Reserved for future intelligent adjustments.
    """

    del enable_ia  # placeholder until intelligent adjustments are required

    src = Path(src_path)
    dst = Path(dst_path)

    lines = _linearize(src)

    _ensure_directory(dst)
    dst.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(dst)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Linearize DOCX/PDF documents to training text.")
    parser.add_argument("src_path", help="Path to the input document (DOCX/PDF).")
    parser.add_argument("dst_path", help="Path to the output UTF-8 text file.")
    parser.add_argument(
        "--disable-ia",
        action="store_true",
        help="Reserved flag to disable IA-assisted adjustments (currently unused).",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> str:
    args = _parse_args(argv)
    enable_ia = not args.disable_ia
    output_path = linearize_to_txt(args.src_path, args.dst_path, enable_ia=enable_ia)
    print(output_path)
    return output_path


if __name__ == "__main__":  # pragma: no cover
    main()
