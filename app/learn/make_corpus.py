"""Utilities to build spaCy NER corpora from gold annotations."""
from __future__ import annotations

import argparse
import csv
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

import spacy
from spacy.tokens import Doc, DocBin, Span
from spacy.util import filter_spans

ORGAO_LABELS = {
    "AM": "Assembleia Municipal",
    "CM": "Câmara Municipal",
    "AF": "Assembleia de Freguesia",
}


@dataclass
class GoldEntry:
    """Representation of a row in the gold annotations."""

    nome_candidato: str
    nome_lista: str
    orgao: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "GoldEntry":
        nome_candidato = (row.get("NOME_CANDIDATO") or "").strip()
        nome_lista = (row.get("NOME_LISTA") or "").strip()
        orgao_key = (row.get("ORGAO") or "").strip()
        orgao_value = ORGAO_LABELS.get(orgao_key)
        return cls(nome_candidato=nome_candidato, nome_lista=nome_lista, orgao=orgao_value)


def load_text(path: Path) -> str:
    """Load the raw text input as UTF-8."""

    return path.read_text(encoding="utf-8")


def load_gold(path: Path) -> List[GoldEntry]:
    """Load gold annotations from a CSV file encoded with UTF-8-SIG."""

    entries: List[GoldEntry] = []
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream, delimiter=";")
        for row in reader:
            entry = GoldEntry.from_row(row)
            if entry.nome_candidato or entry.nome_lista:
                entries.append(entry)
    return entries


def find_all_occurrences(text: str, phrase: str) -> List[Tuple[int, int]]:
    """Find all (start, end) pairs of *phrase* in *text*.

    The search is case-sensitive and returns non-overlapping occurrences.
    """

    positions: List[Tuple[int, int]] = []
    if not phrase:
        return positions
    start = 0
    while True:
        index = text.find(phrase, start)
        if index == -1:
            break
        end = index + len(phrase)
        positions.append((index, end))
        start = end
    return positions


def collect_spans(doc: Doc, entries: Sequence[GoldEntry]) -> List[Span]:
    """Collect spaCy spans from the gold entries."""

    text = doc.text
    span_candidates: List[Span] = []
    seen_keys: set[Tuple[int, int, str]] = set()

    def add_spans(label: str, phrase: str) -> None:
        for start, end in find_all_occurrences(text, phrase):
            key = (start, end, label)
            if key in seen_keys:
                continue
            span = doc.char_span(start, end, label=label, alignment_mode="contract")
            if span is None:
                continue
            seen_keys.add(key)
            span_candidates.append(span)

    unique_persons = {entry.nome_candidato for entry in entries if entry.nome_candidato}
    unique_lists = {entry.nome_lista for entry in entries if entry.nome_lista}
    unique_orgao = {entry.orgao for entry in entries if entry.orgao}

    for person in unique_persons:
        add_spans("PERSON", person)
    for lista in unique_lists:
        add_spans("LISTA", lista)
    for orgao in unique_orgao:
        add_spans("ORGAO", orgao)  # type: ignore[arg-type]

    return list(filter_spans(span_candidates))


def create_doc(entries: Sequence[GoldEntry], text: str) -> Doc:
    """Create a spaCy Doc with NER spans from the provided entries."""

    nlp = spacy.blank("pt")
    doc = nlp.make_doc(text)
    spans = collect_spans(doc, entries)
    doc.set_ents(spans)
    return doc


def split_docs(docs: Sequence[Doc], dev_ratio: float, seed: int) -> Tuple[List[Doc], List[Doc]]:
    """Split documents into train/dev partitions according to *dev_ratio*."""

    docs_list = list(docs)
    if not docs_list:
        return [], []

    if dev_ratio <= 0 or len(docs_list) < 2:
        return docs_list, []

    rng = random.Random(seed)
    rng.shuffle(docs_list)

    dev_count = max(1, round(len(docs_list) * dev_ratio))
    dev_count = min(dev_count, len(docs_list) - 1)
    dev_docs = docs_list[:dev_count]
    train_docs = docs_list[dev_count:]
    return train_docs, dev_docs


def save_docbin(docs: Iterable[Doc], output_path: Path) -> None:
    """Save documents to disk in spaCy's DocBin format."""

    docbin = DocBin(store_user_data=True)
    for doc in docs:
        docbin.add(doc)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    docbin.to_disk(output_path)


def infer_dev_path(train_output: Path) -> Path:
    """Infer the dev output path from the train output path."""

    if train_output.suffix == ".spacy":
        name = train_output.stem
        if "train" in name:
            dev_name = name.replace("train", "dev")
        else:
            dev_name = f"{name}_dev"
        return train_output.with_name(f"{dev_name}{train_output.suffix}")
    return train_output / "ner_dev.spacy"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_text", type=Path, help="Path to the UTF-8 input text file")
    parser.add_argument("gold_csv", type=Path, help="Path to the UTF-8-SIG gold CSV file")
    parser.add_argument("train_output", type=Path, help="File path for the training DocBin")
    parser.add_argument(
        "--dev-output",
        type=Path,
        default=None,
        help="Optional file path for the development DocBin (defaults beside train)",
    )
    parser.add_argument(
        "--dev-ratio",
        type=float,
        default=0.2,
        help="Fraction of documents reserved for the development set (default: 0.2)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=13,
        help="Random seed for splitting the documents into train/dev",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    text = load_text(args.input_text)
    gold_entries = load_gold(args.gold_csv)
    doc = create_doc(gold_entries, text)

    train_docs, dev_docs = split_docs([doc], args.dev_ratio, args.seed)

    train_output = args.train_output
    dev_output = args.dev_output if args.dev_output is not None else infer_dev_path(train_output)

    save_docbin(train_docs, train_output)

    if args.dev_ratio > 0 and (len(train_docs) + len(dev_docs)) > 1:
        save_docbin(dev_docs, dev_output)
    elif args.dev_output is not None or args.dev_ratio > 0:
        # Always create an (possibly empty) dev DocBin when requested.
        save_docbin(dev_docs, dev_output)


if __name__ == "__main__":
    main()
