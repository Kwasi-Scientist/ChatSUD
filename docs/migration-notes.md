# Migration Notes

## What changed

- The Colab notebook is now a demo artifact instead of the source of truth.
- Backend logic is split into focused modules under `chat_sud/`.
- Crisis resources and regex rules moved into JSON resources for easier review.
- Retrieval now supports metadata-aware search and source snippets.
- Training data generation is organized into reusable functions with train and validation splits.
- A Next.js frontend provides a chat-first UI for local development.

## Notebook to module mapping

- Safety and crisis escalation -> `chat_sud/safety.py`
- PDF parsing and normalization -> `chat_sud/ingestion.py`
- Chunk creation and substance tags -> `chat_sud/chunking.py`
- Embeddings, filtering, retrieval, and persistence -> `chat_sud/retrieval.py`
- SFT dataset generation and QLoRA scaffolding -> `chat_sud/training.py`
- Prompt and response orchestration -> `chat_sud/generation.py`
- FastAPI endpoints and app wiring -> `chat_sud/api.py`

## Why this structure

- The notebook prototype mixed pipeline logic, runtime commands, and saved outputs in one place.
- The new layout keeps safety behavior explicit and testable.
- Local development works with lightweight defaults, while optional dependencies keep the door open for FAISS, sentence-transformers, and QLoRA training.

