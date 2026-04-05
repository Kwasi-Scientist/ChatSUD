from __future__ import annotations

import re
from uuid import uuid4

from chat_sud.config import Settings, get_settings
from chat_sud.schemas import ChunkRecord, DocumentRecord

SUBSTANCE_TAGS = {
    "alcohol": ["alcohol", "drinking", "beer", "wine", "liquor", "aud"],
    "opioids": ["opioid", "heroin", "fentanyl", "oxycodone", "oud"],
    "stimulants": ["cocaine", "meth", "amphetamine", "stimulant"],
    "cannabis": ["cannabis", "marijuana", "thc"],
    "benzos": ["benzodiazepine", "xanax", "lorazepam", "diazepam"],
    "nicotine": ["nicotine", "cigarette", "smoking", "vaping", "tobacco"],
}


def detect_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags = [tag for tag, keywords in SUBSTANCE_TAGS.items() if any(word in lowered for word in keywords)]
    return tags or ["general"]


def detect_primary_category(explicit: str | None, tags: list[str]) -> str:
    if explicit and explicit != "general":
        return explicit
    return tags[0] if tags else "general"


def split_text_into_chunks(
    text: str,
    chunk_size: int,
    overlap: int,
    min_chunk_size: int,
) -> list[str]:
    normalized = text.strip()
    if len(normalized) <= chunk_size:
        return [normalized] if normalized else []

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        window = normalized[start:end]
        boundary = max(window.rfind(". "), window.rfind("\n"))
        if boundary > min_chunk_size:
            end = start + boundary + 1
            window = normalized[start:end]
        cleaned = window.strip()
        if len(cleaned) >= min_chunk_size:
            chunks.append(cleaned)
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks


def build_chunks(
    documents: list[DocumentRecord],
    settings: Settings | None = None,
) -> list[ChunkRecord]:
    settings = settings or get_settings()
    chunks: list[ChunkRecord] = []
    for document in documents:
        inherited_tags = document.tags or detect_tags(document.text)
        primary = detect_primary_category(document.substance_category, inherited_tags)
        for text in split_text_into_chunks(
            document.text,
            chunk_size=settings.chunk_size,
            overlap=settings.chunk_overlap,
            min_chunk_size=settings.min_chunk_size,
        ):
            tags = sorted(set(inherited_tags + detect_tags(text)))
            snippet = re.sub(r"\s+", " ", text)[:220].strip()
            chunks.append(
                ChunkRecord(
                    chunk_id=str(uuid4()),
                    source=document.source,
                    title=document.title,
                    text=text,
                    snippet=snippet,
                    tags=tags,
                    substance_category=detect_primary_category(primary, tags),
                )
            )
    return chunks

