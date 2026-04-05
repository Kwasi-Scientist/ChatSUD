from __future__ import annotations

import json
from typing import Iterator

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from chat_sud.app_state import ApplicationState
from chat_sud.config import Settings, get_settings
from chat_sud.generation import iter_text_chunks
from chat_sud.ingestion import ingest_documents
from chat_sud.schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    IngestRequest,
    IngestResponse,
    RebuildIndexRequest,
    RebuildIndexResponse,
)
from chat_sud.safety import assess_message


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    state = ApplicationState(settings=settings)
    app = FastAPI(title=settings.app_name)
    app.state.container = state
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    def get_state() -> ApplicationState:
        return app.state.container

    def _chat_logic(payload: ChatRequest, state: ApplicationState) -> ChatResponse:
        session_id = state.ensure_session(payload.session_id)
        history = [] if payload.privacy_mode else state.sessions.get(session_id, [])
        decision = assess_message(payload.user_message, payload.region or state.settings.default_region, state.settings)
        filters = {
            "substance_category": payload.substance_hint or None,
            "tags": [payload.substance_hint] if payload.substance_hint and payload.substance_hint != "general" else None,
        }
        sources = [] if decision.triggered else state.retriever.search(
            payload.user_message,
            top_k=state.settings.retrieval_top_k,
            filters=filters,
        )
        assistant_message = state.generator.generate_response(
            user_message=payload.user_message,
            safety_decision=decision,
            retrieved_sources=sources,
            history=history,
            substance_hint=payload.substance_hint,
            privacy_mode=payload.privacy_mode,
        )
        if not payload.privacy_mode:
            state.record_turns(session_id, payload.user_message, assistant_message)
        return ChatResponse(
            assistant_message=assistant_message,
            safety_escalation_triggered=decision.mode == "crisis",
            safety_mode=decision.mode,
            retrieved_sources=sources,
            session_id=session_id,
        )

    @app.get("/health", response_model=HealthResponse)
    def health(state: ApplicationState = Depends(get_state)) -> HealthResponse:
        return HealthResponse(
            status="ok",
            documents_loaded=len(state.documents),
            chunks_loaded=len(state.chunks),
            index_backend=state.retriever.backend,
        )

    @app.post("/ingest", response_model=IngestResponse)
    def ingest(payload: IngestRequest, state: ApplicationState = Depends(get_state)) -> IngestResponse:
        documents = ingest_documents(payload.documents)
        if payload.replace_existing:
            state.replace_documents(documents)
        else:
            state.merge_documents(documents)
        if payload.rebuild_index:
            state.rebuild_index()
        return IngestResponse(
            ingested_documents=len(documents),
            chunks_created=len(state.chunks),
            index_ready=bool(state.chunks),
        )

    @app.post("/rebuild-index", response_model=RebuildIndexResponse)
    def rebuild_index(
        payload: RebuildIndexRequest,
        state: ApplicationState = Depends(get_state),
    ) -> RebuildIndexResponse:
        if payload.documents:
            documents = ingest_documents(payload.documents)
            if payload.replace_existing:
                state.replace_documents(documents)
            else:
                state.merge_documents(documents)
        state.rebuild_index()
        return RebuildIndexResponse(
            indexed_documents=len(state.documents),
            indexed_chunks=len(state.chunks),
            backend=state.retriever.backend,
        )

    @app.post("/chat", response_model=ChatResponse)
    def chat(payload: ChatRequest, state: ApplicationState = Depends(get_state)) -> ChatResponse:
        return _chat_logic(payload, state)

    @app.post("/chat/stream")
    def chat_stream(payload: ChatRequest, state: ApplicationState = Depends(get_state)) -> StreamingResponse:
        response = _chat_logic(payload, state)

        def event_stream() -> Iterator[str]:
            yield json.dumps({"type": "session", "session_id": response.session_id}) + "\n"
            for delta in iter_text_chunks(response.assistant_message):
                yield json.dumps({"type": "delta", "delta": delta}) + "\n"
            yield json.dumps({"type": "final", "response": response.model_dump(mode="json")}) + "\n"

        return StreamingResponse(event_stream(), media_type="application/x-ndjson")

    return app


app = create_app()


def run() -> None:
    settings = get_settings()
    uvicorn.run("chat_sud.api:app", host=settings.api_host, port=settings.api_port, reload=settings.debug)

