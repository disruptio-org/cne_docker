"""Train a spaCy NER model on local corpora."""
from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import Iterable, List

import spacy
from spacy.language import Language
from spacy.tokens import Doc, DocBin
from spacy.training import Example
from spacy.util import minibatch

LABELS = ["PERSON", "LISTA", "ORGAO"]


def build_nlp() -> Language:
    """Create a blank Portuguese pipeline with an NER component."""

    nlp = spacy.blank("pt")
    ner = nlp.add_pipe("ner")
    for label in LABELS:
        ner.add_label(label)
    return nlp


def load_docs(path: Path, vocab) -> List[Doc]:
    """Load documents from a DocBin file using the provided vocab."""

    docbin = DocBin().from_disk(path)
    return list(docbin.get_docs(vocab))


def docs_to_examples(nlp: Language, docs: Iterable[Doc]) -> List[Example]:
    """Convert annotated docs to spaCy training examples."""

    examples: List[Example] = []
    for doc in docs:
        entities = [(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]
        example_doc = nlp.make_doc(doc.text)
        examples.append(Example.from_dict(example_doc, {"entities": entities}))
    return examples


def train_model(
    nlp: Language,
    train_examples: List[Example],
    dev_examples: List[Example],
    n_iter: int = 15,
    batch_size: int = 8,
    dropout: float = 0.2,
) -> Language:
    """Train the provided NER pipeline on the provided examples."""

    optimizer = nlp.initialize(lambda: train_examples)

    for epoch in range(1, n_iter + 1):
        random.shuffle(train_examples)
        losses = {}
        batches = minibatch(train_examples, size=batch_size)
        for batch in batches:
            nlp.update(batch, sgd=optimizer, drop=dropout, losses=losses)
        message = f"Epoch {epoch}/{n_iter} - Loss: {losses.get('ner', 0.0):.4f}"
        if dev_examples:
            scores = nlp.evaluate(dev_examples)
            message += f" | Dev F: {scores.get('ents_f', 0.0):.2f}"
        print(message)
    return nlp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train a spaCy NER model locally.")
    parser.add_argument("train_path", type=Path, help="Path to the training DocBin file")
    parser.add_argument("dev_path", type=Path, help="Path to the development DocBin file")
    parser.add_argument("output_dir", type=Path, help="Directory to store the trained model")
    parser.add_argument(
        "--epochs", type=int, default=15, help="Number of training epochs (default: 15)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    nlp = build_nlp()
    train_docs = load_docs(args.train_path, nlp.vocab)
    dev_docs = load_docs(args.dev_path, nlp.vocab)

    train_examples = docs_to_examples(nlp, train_docs)
    dev_examples = docs_to_examples(nlp, dev_docs)

    trained_nlp = train_model(
        nlp,
        train_examples,
        dev_examples,
        n_iter=args.epochs,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    trained_nlp.to_disk(args.output_dir)
    print(f"Model saved to {args.output_dir}")


if __name__ == "__main__":
    main()
