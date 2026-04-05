from chat_sud.chunking import build_chunks, detect_tags
from chat_sud.config import Settings
from chat_sud.schemas import DocumentRecord


def test_detect_tags_finds_substance_keywords() -> None:
    assert "alcohol" in detect_tags("Alcohol cravings are strong after work.")


def test_build_chunks_creates_metadata() -> None:
    settings = Settings(chunk_size=120, chunk_overlap=20, min_chunk_size=40)
    document = DocumentRecord(
        source="guide.txt",
        title="Guide",
        text=("Cravings rise fast after alcohol cues. " * 10).strip(),
        tags=[],
        substance_category="general",
    )
    chunks = build_chunks([document], settings)
    assert chunks
    assert all(chunk.source == "guide.txt" for chunk in chunks)

