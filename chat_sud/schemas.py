from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class SafetyMode(str, Enum):
    supportive = "supportive"
    crisis = "crisis"
    medical_refusal = "medical_refusal"


class MessageTurn(BaseModel):
    role: str
    content: str


class DocumentInput(BaseModel):
    source: str | None = None
    title: str | None = None
    text: str | None = None
    path: str | None = None
    tags: list[str] = Field(default_factory=list)
    substance_category: str | None = None


class DocumentRecord(BaseModel):
    source: str
    title: str
    text: str
    tags: list[str] = Field(default_factory=list)
    substance_category: str = "general"


class ChunkRecord(BaseModel):
    chunk_id: str
    source: str
    title: str
    text: str
    snippet: str
    tags: list[str] = Field(default_factory=list)
    substance_category: str = "general"


class RetrievedSource(BaseModel):
    source: str
    title: str
    snippet: str
    score: float
    tags: list[str] = Field(default_factory=list)
    substance_category: str = "general"


class ChatRequest(BaseModel):
    session_id: str | None = None
    user_message: str = Field(min_length=1)
    region: str | None = None
    substance_hint: str | None = None
    privacy_mode: bool = True


class ChatResponse(BaseModel):
    assistant_message: str
    safety_escalation_triggered: bool
    safety_mode: SafetyMode
    retrieved_sources: list[RetrievedSource]
    session_id: str


class IngestRequest(BaseModel):
    documents: list[DocumentInput]
    replace_existing: bool = False
    rebuild_index: bool = True


class IngestResponse(BaseModel):
    ingested_documents: int
    chunks_created: int
    index_ready: bool


class RebuildIndexRequest(BaseModel):
    documents: list[DocumentInput] | None = None
    replace_existing: bool = False


class RebuildIndexResponse(BaseModel):
    indexed_documents: int
    indexed_chunks: int
    backend: str


class HealthResponse(BaseModel):
    status: str
    documents_loaded: int
    chunks_loaded: int
    index_backend: str

