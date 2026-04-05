from __future__ import annotations

from typing import Iterable

from chat_sud.config import Settings, get_settings
from chat_sud.schemas import MessageTurn, RetrievedSource
from chat_sud.safety import SafetyDecision


def build_system_prompt(substance_hint: str | None, privacy_mode: bool) -> str:
    scope = substance_hint or "general recovery support"
    privacy_text = "Minimize stored history and avoid unnecessary personal details." if privacy_mode else (
        "Use prior session context when it improves continuity, but stay concise."
    )
    return (
        "You are ChatSUD, a privacy-first recovery support assistant. "
        "You are not a clinician, therapist, or emergency service. "
        "Offer supportive, grounded guidance, encourage professional help when appropriate, "
        f"focus on {scope}, and {privacy_text}"
    )


def _supportive_opening(user_message: str) -> str:
    if "craving" in user_message.lower() or "urge" in user_message.lower():
        return "It sounds like the urge is active right now, and slowing things down before acting on it is an important step."
    if "relapse" in user_message.lower():
        return "Relapse fear can feel heavy, and talking about it early is a strong move."
    return "Thank you for saying that out loud. We can keep this focused on one practical step at a time."


class GenerationOrchestrator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def generate_response(
        self,
        user_message: str,
        safety_decision: SafetyDecision,
        retrieved_sources: list[RetrievedSource],
        history: list[MessageTurn] | None = None,
        substance_hint: str | None = None,
        privacy_mode: bool = True,
    ) -> str:
        if safety_decision.triggered and safety_decision.message:
            return safety_decision.message

        history = history or []
        source_lines = [
            f"- {source.title}: {source.snippet}"
            for source in retrieved_sources[:3]
        ]
        source_block = "\n".join(source_lines) if source_lines else "- No indexed source matched strongly, so keep the advice general and low-risk."
        continuity = ""
        if history:
            last_user_turn = next((turn.content for turn in reversed(history) if turn.role == "user"), "")
            if last_user_turn:
                continuity = f" You recently mentioned: {last_user_turn[:120]}."

        return (
            f"{_supportive_opening(user_message)}{continuity}\n\n"
            "Here is a grounded plan for the next stretch of time:\n"
            "1. Name the trigger or situation in one sentence so it feels more concrete.\n"
            "2. Pick one action that creates distance from the trigger for the next 10 to 20 minutes.\n"
            "3. Reach out to one person, meeting, or support channel if being alone raises the risk.\n\n"
            "Helpful grounding pulled from the indexed materials:\n"
            f"{source_block}\n\n"
            "I can keep helping you turn this into a short check-in plan, craving card, or relapse-prevention checklist. "
            "This is supportive guidance only, not medical or clinical care."
        )


def iter_text_chunks(text: str, chunk_size: int = 40) -> Iterable[str]:
    for start in range(0, len(text), chunk_size):
        yield text[start : start + chunk_size]

