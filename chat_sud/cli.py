from __future__ import annotations

import argparse
import json
from pathlib import Path

from chat_sud.app_state import ApplicationState
from chat_sud.config import get_settings
from chat_sud.ingestion import ingest_documents
from chat_sud.schemas import DocumentInput
from chat_sud.training import build_training_splits, evaluate_dataset, write_training_splits


def _load_document_payload(path: Path) -> list[DocumentInput]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [DocumentInput.model_validate(row) for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="ChatSUD utility commands")
    subcommands = parser.add_subparsers(dest="command", required=True)

    ingest_cmd = subcommands.add_parser("ingest")
    ingest_cmd.add_argument("--json", required=True, help="Path to a JSON file with document inputs.")

    rebuild_cmd = subcommands.add_parser("rebuild-index")
    rebuild_cmd.add_argument("--json", required=False, help="Optional JSON file with document inputs.")

    training_cmd = subcommands.add_parser("generate-sft")
    training_cmd.add_argument("--out", required=True, help="Output directory for train/validation JSONL.")

    args = parser.parse_args()
    state = ApplicationState(settings=get_settings())

    if args.command == "ingest":
        documents = ingest_documents(_load_document_payload(Path(args.json)))
        state.merge_documents(documents)
        state.rebuild_index()
        print(f"Ingested {len(documents)} documents and built {len(state.chunks)} chunks.")
    elif args.command == "rebuild-index":
        if args.json:
            documents = ingest_documents(_load_document_payload(Path(args.json)))
            state.replace_documents(documents)
        state.rebuild_index()
        print(f"Indexed {len(state.documents)} documents into {len(state.chunks)} chunks.")
    elif args.command == "generate-sft":
        dataset = build_training_splits(state.chunks)
        write_training_splits(Path(args.out), dataset)
        print(json.dumps(evaluate_dataset(dataset), indent=2))

