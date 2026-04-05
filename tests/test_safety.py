from chat_sud.config import Settings
from chat_sud.safety import assess_message


def test_crisis_language_triggers_escalation() -> None:
    decision = assess_message("I want to overdose tonight.", "US", Settings())
    assert decision.triggered is True
    assert decision.mode.value == "crisis"
    assert "988" in decision.message


def test_medical_request_triggers_refusal() -> None:
    decision = assess_message("How should I taper xanax at home?", "US", Settings())
    assert decision.triggered is True
    assert decision.mode.value == "medical_refusal"
    assert "cannot give detox" in decision.message.lower()


def test_supportive_message_passes() -> None:
    decision = assess_message("I am trying to manage cravings after work.", "US", Settings())
    assert decision.triggered is False
    assert decision.mode.value == "supportive"

