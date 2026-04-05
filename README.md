# ChatSUD

ChatSUD is an early-stage, privacy-first therapeutic support system for substance use recovery. It is designed for supportive coaching, research, and local prototyping. It is not a clinician, medical device, or emergency service.

## Safety note

ChatSUD preserves the project's non-clinical disclaimer and safety-first intent:

- Crisis language triggers escalation to region-aware live resources.
- Requests for medical dosing, detox, tapering, or emergency instructions are refused.
- Normal conversations stay supportive, grounded, and non-judgmental.

## Repository structure

```text
ChatSUD/
├─ chat_sud/
│  ├─ api.py
│  ├─ app_state.py
│  ├─ chunking.py
│  ├─ config.py
│  ├─ generation.py
│  ├─ ingestion.py
│  ├─ retrieval.py
│  ├─ safety.py
│  ├─ schemas.py
│  ├─ training.py
│  ├─ cli.py
│  └─ resources/
├─ frontend/
├─ tests/
├─ docs/
├─ pyproject.toml
└─ SUD_Therapist_Pipeline_colab.ipynb
```

## Backend setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e .[dev]
```

Optional extras:

```bash
pip install -e .[pdf,retrieval,training]
```

Run the API:

```bash
uvicorn chat_sud.api:app --reload
```

## Frontend setup

```bash
cd frontend
npm install
npm run dev
```

The frontend expects the API at `http://localhost:8000` by default. Override with `NEXT_PUBLIC_API_BASE_URL`.

## One-shot WSL startup

For Ubuntu on WSL, you can start the backend and frontend together:

```bash
cd /mnt/c/Users/Kwaz9/Documents/coding/ChatSUD
chmod +x scripts/start-dev-wsl.sh
./scripts/start-dev-wsl.sh
```

Optional custom ports:

```bash
BACKEND_PORT=8001 FRONTEND_PORT=3001 ./scripts/start-dev-wsl.sh
```

Stop both services with `Ctrl+C`.

## Environment variables

- `CHAT_SUD_API_HOST`
- `CHAT_SUD_API_PORT`
- `CHAT_SUD_DOCS_DIR`
- `CHAT_SUD_INDEX_DIR`
- `CHAT_SUD_ARTIFACTS_DIR`
- `CHAT_SUD_EMBEDDING_MODEL_NAME`
- `CHAT_SUD_GENERATION_BACKEND`
- `CHAT_SUD_GENERATION_MODEL_NAME`

## API endpoints

- `GET /health`
- `POST /ingest`
- `POST /rebuild-index`
- `POST /chat`
- `POST /chat/stream`

`POST /chat` returns:

- assistant message
- whether safety escalation triggered
- retrieved sources
- session id

## Tests

```bash
python -m pytest -q
```

## Notebook status

`SUD_Therapist_Pipeline_colab.ipynb` remains in the repo as an optional demo and migration reference. The maintainable source of truth now lives in `chat_sud/`.

## Migration

See `docs/migration-notes.md` for the notebook-to-application mapping and design rationale.
