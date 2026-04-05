from __future__ import annotations


def test_ingest_and_rebuild_index(client, sample_documents) -> None:
    ingest_response = client.post(
        "/ingest",
        json={"documents": sample_documents, "replace_existing": True, "rebuild_index": True},
    )
    assert ingest_response.status_code == 200
    payload = ingest_response.json()
    assert payload["ingested_documents"] == len(sample_documents)
    assert payload["chunks_created"] >= 1

    rebuild_response = client.post("/rebuild-index", json={})
    assert rebuild_response.status_code == 200
    assert rebuild_response.json()["indexed_documents"] == len(sample_documents)


def test_chat_endpoint_returns_sources(client, sample_documents) -> None:
    client.post(
        "/ingest",
        json={"documents": sample_documents, "replace_existing": True, "rebuild_index": True},
    )
    response = client.post(
        "/chat",
        json={
            "user_message": "I need help with alcohol cravings after work.",
            "region": "US",
            "substance_hint": "alcohol",
            "privacy_mode": False
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["assistant_message"]
    assert payload["session_id"]
    assert payload["retrieved_sources"]


def test_chat_endpoint_handles_crisis(client) -> None:
    response = client.post(
        "/chat",
        json={"user_message": "I want to overdose tonight", "region": "US"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["safety_escalation_triggered"] is True
    assert payload["safety_mode"] == "crisis"
