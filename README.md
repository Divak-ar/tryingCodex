# SAP ABAP Requirement-Doc RAG Design Validator

This repository now includes a validator that checks whether a RAG design for SAP ABAP requirement documents is complete and production-ready.

## What it does

- Evaluates key design sections (data sources, chunking, retrieval, evaluation, feedback loop, security).
- Flags gaps against ABAP requirement-document expectations.
- Applies deterministic fixes.
- Re-runs checks in an **eval → fix → update → repeat** loop.

## Usage

```bash
python rag_abap_validator.py --design examples/design.sample.json
```

Evaluate and persist fixes back to the file:

```bash
python rag_abap_validator.py --design examples/design.sample.json --write-updated-design
```

Evaluation-only mode:

```bash
python rag_abap_validator.py --design examples/design.sample.json --no-auto-fix
```

## Exit codes

- `0` if final design passes.
- `1` if it still fails after max iterations.
