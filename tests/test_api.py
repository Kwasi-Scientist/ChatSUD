from __future__ import annotations

from chat_sud.safety import assess_message


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


def test_template_generation_varies_by_prompt(client) -> None:
    craving_response = client.post(
        "/chat",
        json={
            "user_message": "Alcohol cravings hit me hard after work and I want help getting through tonight.",
            "region": "US",
            "substance_hint": "alcohol",
        },
    )
    loneliness_response = client.post(
        "/chat",
        json={
            "user_message": "I feel lonely and isolated on the weekend and that makes recovery harder.",
            "region": "US",
        },
    )

    assert craving_response.status_code == 200
    assert loneliness_response.status_code == 200
    craving_message = craving_response.json()["assistant_message"]
    loneliness_message = loneliness_response.json()["assistant_message"]

    assert craving_message
    assert loneliness_message
    assert craving_message != loneliness_message
    assert any(term in craving_message.lower() for term in ["craving", "urge", "trigger", "delay"])
    assert any(
        term in loneliness_message.lower()
        for term in ["loneliness", "isolated", "isolation", "connection", "weekend"]
    )


def test_generation_uses_retrieved_sources_when_available(client, sample_documents) -> None:
    client.post(
        "/ingest",
        json={"documents": sample_documents, "replace_existing": True, "rebuild_index": True},
    )

    response = client.post(
        "/chat",
        json={
            "user_message": "What can I do when alcohol cravings show up after work?",
            "region": "US",
            "substance_hint": "alcohol",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["retrieved_sources"]
    assert "Cravings are time-limited" in payload["assistant_message"]


def test_safety_messages_are_not_rewritten(client) -> None:
    user_message = "I want to overdose tonight"
    response = client.post("/chat", json={"user_message": user_message, "region": "US"})

    assert response.status_code == 200
    payload = response.json()
    expected = assess_message(user_message, "US", client.app.state.container.settings).message
    assert payload["safety_escalation_triggered"] is True
    assert payload["assistant_message"] == expected


def test_privacy_mode_false_uses_recent_context_without_repeating(client) -> None:
    first_response = client.post(
        "/chat",
        json={
            "session_id": "context-session",
            "user_message": "My specific trigger is passing the liquor store after work.",
            "region": "US",
            "substance_hint": "alcohol",
            "privacy_mode": False,
        },
    )
    second_response = client.post(
        "/chat",
        json={
            "session_id": "context-session",
            "user_message": "Can you help me make a plan for tonight?",
            "region": "US",
            "substance_hint": "alcohol",
            "privacy_mode": False,
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    first_message = first_response.json()["assistant_message"]
    second_message = second_response.json()["assistant_message"]
    assert second_message != first_message
    assert any(term in second_message.lower() for term in ["liquor", "store", "trigger", "work"])
