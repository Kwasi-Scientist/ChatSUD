from __future__ import annotations

from dataclasses import dataclass, field
from uuid import uuid4

from chat_sud.chunking import build_chunks
from chat_sud.config import Settings, get_settings
from chat_sud.generation import GenerationOrchestrator
from chat_sud.retrieval import RetrievalEngine
from chat_sud.schemas import DocumentRecord, MessageTurn


@dataclass
class ApplicationState:
    settings: Settings = field(default_factory=get_settings)
    documents: list[DocumentRecord] = field(default_factory=list)
    chunks: list = field(default_factory=list)
    sessions: dict[str, list[MessageTurn]] = field(default_factory=dict)
    retriever: RetrievalEngine = field(default_factory=RetrievalEngine)

    def __post_init__(self) -> None:
        self.settings.ensure_directories()
        self.generator = GenerationOrchestrator(self.settings)
        self._load_existing_index()

    def _load_existing_index(self) -> None:
        loaded = RetrievalEngine.load(self.settings.index_dir)
        if loaded.chunks:
            self.chunks = loaded.chunks
            self.retriever = loaded

    def replace_documents(self, documents: list[DocumentRecord]) -> None:
        self.documents = documents

    def merge_documents(self, documents: list[DocumentRecord]) -> None:
        self.documents.extend(documents)

    def rebuild_index(self) -> None:
        self.chunks = build_chunks(self.documents, self.settings)
        self.retriever = RetrievalEngine.build(self.chunks, self.settings)
        self.retriever.save(self.settings.index_dir)

    def ensure_session(self, session_id: str | None) -> str:
        session_key = session_id or str(uuid4())
        self.sessions.setdefault(session_key, [])
        return session_key

    def record_turns(self, session_id: str, user_message: str, assistant_message: str) -> None:
        self.sessions.setdefault(session_id, [])
        self.sessions[session_id].append(MessageTurn(role="user", content=user_message))
        self.sessions[session_id].append(MessageTurn(role="assistant", content=assistant_message))

