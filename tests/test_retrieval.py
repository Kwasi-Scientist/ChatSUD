from chat_sud.config import Settings
from chat_sud.retrieval import RetrievalEngine
from chat_sud.schemas import ChunkRecord


def test_retrieval_filters_by_substance_category() -> None:
    chunks = [
        ChunkRecord(
            chunk_id="1",
            source="a",
            title="Alcohol Guide",
            text="Alcohol cravings can be delayed with urge surfing and calling a support person.",
            snippet="Alcohol cravings can be delayed.",
            tags=["alcohol"],
            substance_category="alcohol",
        ),
        ChunkRecord(
            chunk_id="2",
            source="b",
            title="Opioid Guide",
            text="Opioid recovery planning can include trigger mapping and naloxone access.",
            snippet="Opioid recovery planning can include trigger mapping.",
            tags=["opioids"],
            substance_category="opioids",
        ),
    ]
    engine = RetrievalEngine.build(chunks, Settings())
    results = engine.search("I need help with alcohol cravings", filters={"substance_category": "alcohol"})
    assert results
    assert all(result.substance_category == "alcohol" for result in results)

