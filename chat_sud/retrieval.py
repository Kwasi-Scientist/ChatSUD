from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from chat_sud.config import Settings, get_settings
from chat_sud.schemas import ChunkRecord, RetrievedSource

TOKEN_RE = re.compile(r"[a-zA-Z0-9']+")


def _tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def _hash_embed(texts: list[str], dim: int = 256) -> np.ndarray:
    matrix = np.zeros((len(texts), dim), dtype=np.float32)
    for row, text in enumerate(texts):
        for token in _tokenize(text):
            matrix[row, hash(token) % dim] += 1.0
        norm = np.linalg.norm(matrix[row])
        if norm:
            matrix[row] /= norm
    return matrix


def _cosine_scores(query_vector: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    return np.dot(matrix, query_vector)


def _overlap_score(query_tokens: set[str], text: str) -> float:
    doc_tokens = set(_tokenize(text))
    if not query_tokens or not doc_tokens:
        return 0.0
    return len(query_tokens & doc_tokens) / len(query_tokens)


@dataclass
class RetrievalEngine:
    chunks: list[ChunkRecord] = field(default_factory=list)
    embeddings: np.ndarray | None = None
    backend: str = "empty"

    @classmethod
    def build(
        cls,
        chunks: list[ChunkRecord],
        settings: Settings | None = None,
    ) -> "RetrievalEngine":
        settings = settings or get_settings()
        if not chunks:
            return cls()
        texts = [chunk.text for chunk in chunks]
        embeddings = _hash_embed(texts)
        backend = "hash"

        if settings.embedding_model_name != "local-hash":
            try:
                from sentence_transformers import SentenceTransformer

                model = SentenceTransformer(settings.embedding_model_name)
                embeddings = model.encode(
                    texts,
                    normalize_embeddings=True,
                    convert_to_numpy=True,
                ).astype(np.float32)
                backend = "sentence-transformer"
            except Exception:
                backend = "hash"

        if settings.embedding_model_name == "local-hash":
            try:
                import faiss

                index = faiss.IndexFlatIP(int(embeddings.shape[1]))
                index.add(embeddings)
                backend = "faiss-hash"
            except Exception:
                backend = "hash"

        return cls(chunks=chunks, embeddings=embeddings, backend=backend)

    def save(self, index_dir: Path) -> None:
        index_dir.mkdir(parents=True, exist_ok=True)
        (index_dir / "metas.jsonl").write_text(
            "\n".join(json.dumps(chunk.model_dump(), ensure_ascii=False) for chunk in self.chunks) + "\n",
            encoding="utf-8",
        )
        if self.embeddings is not None:
            np.save(index_dir / "embeddings.npy", self.embeddings)
        (index_dir / "index_meta.json").write_text(
            json.dumps({"backend": self.backend}, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, index_dir: Path) -> "RetrievalEngine":
        metas_path = index_dir / "metas.jsonl"
        if not metas_path.exists():
            return cls()
        chunks = [
            ChunkRecord.model_validate(json.loads(line))
            for line in metas_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        embeddings = None
        if (index_dir / "embeddings.npy").exists():
            embeddings = np.load(index_dir / "embeddings.npy")
        backend = "loaded"
        if (index_dir / "index_meta.json").exists():
            backend = json.loads((index_dir / "index_meta.json").read_text(encoding="utf-8")).get(
                "backend",
                backend,
            )
        return cls(chunks=chunks, embeddings=embeddings, backend=backend)

    def _matches_filters(self, chunk: ChunkRecord, filters: dict[str, str | list[str] | None]) -> bool:
        substance = filters.get("substance_category")
        if substance and substance != "general" and chunk.substance_category != substance:
            return False
        tags = filters.get("tags")
        if tags:
            wanted = {tag for tag in tags if tag}
            if wanted and not wanted.intersection(chunk.tags):
                return False
        source = filters.get("source")
        if source and chunk.source != source:
            return False
        return True

    def search(
        self,
        query: str,
        top_k: int = 4,
        filters: dict[str, str | list[str] | None] | None = None,
    ) -> list[RetrievedSource]:
        if not self.chunks:
            return []

        filters = filters or {}
        candidate_indexes = [
            index
            for index, chunk in enumerate(self.chunks)
            if self._matches_filters(chunk, filters)
        ]
        if not candidate_indexes:
            return []

        query_vector = _hash_embed([query])[0]
        dense_scores = (
            _cosine_scores(query_vector, self.embeddings[candidate_indexes])
            if self.embeddings is not None
            else np.zeros(len(candidate_indexes))
        )
        query_tokens = set(_tokenize(query))

        ranked: list[tuple[float, ChunkRecord]] = []
        for offset, index in enumerate(candidate_indexes):
            chunk = self.chunks[index]
            lexical = _overlap_score(query_tokens, chunk.text)
            dense = float(dense_scores[offset])
            score = (0.65 * dense) + (0.35 * lexical)
            ranked.append((score, chunk))

        ranked.sort(key=lambda item: item[0], reverse=True)
        return [
            RetrievedSource(
                source=chunk.source,
                title=chunk.title,
                snippet=chunk.snippet,
                score=round(score, 4),
                tags=chunk.tags,
                substance_category=chunk.substance_category,
            )
            for score, chunk in ranked[:top_k]
        ]

