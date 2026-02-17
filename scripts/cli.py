#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from abap_rag.pipeline import RagPipeline
from abap_rag.settings import settings


def main() -> None:
    parser = argparse.ArgumentParser(description="SAP ABAP RAG CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    ingest = sub.add_parser("ingest", help="Ingest ABAP docs")
    ingest.add_argument("path", type=Path, help="Path to ABAP documents")

    ask = sub.add_parser("ask", help="Ask question")
    ask.add_argument("query", type=str, help="Query text")

    args = parser.parse_args()
    pipeline = RagPipeline(settings)

    if args.command == "ingest":
        count = pipeline.ingest(args.path)
        print(f"Indexed chunks: {count}")
    elif args.command == "ask":
        pipeline.load_index()
        result = pipeline.ask(args.query)
        print(result["answer"])


if __name__ == "__main__":
    main()
