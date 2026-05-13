from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Iterable, Protocol

from chat_sud.config import Settings, get_settings
from chat_sud.schemas import MessageTurn, RetrievedSource
from chat_sud.safety import SafetyDecision

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z'-]{2,}")
STOPWORDS = {
    "about",
    "after",
    "again",
    "because",
    "been",
    "before",
    "being",
    "could",
    "feel",
    "feeling",
    "from",
    "have",
    "help",
    "into",
    "just",
    "like",
    "make",
    "need",
    "really",
    "some",
    "that",
    "this",
    "trying",
    "want",
    "when",
    "with",
    "would",
}


def build_system_prompt(substance_hint: str | None, privacy_mode: bool) -> str:
    scope = substance_hint or "general recovery support"
    privacy_text = (
        "Minimize stored history and avoid unnecessary personal details."
        if privacy_mode
        else "Use recent session context when it improves continuity, but stay concise."
    )
    return (
        "You are ChatSUD, a privacy-first recovery support assistant. "
        "You are not a clinician, therapist, emergency service, or medical provider. "
        "Offer supportive, practical, non-clinical guidance; encourage licensed or real-time "
        "support when appropriate; avoid detox, tapering, dosing, or emergency instructions; "
        f"focus on {scope}; and {privacy_text}"
    )


@dataclass(frozen=True)
class GenerationPrompt:
    system: str
    user_message: str
    source_notes: list[str]
    recent_history: list[MessageTurn]
    substance_hint: str | None
    privacy_mode: bool

    def as_text(self) -> str:
        history = "\n".join(
            f"{turn.role}: {turn.content}" for turn in self.recent_history
        ) or "No recent history supplied."
        sources = "\n".join(f"- {note}" for note in self.source_notes) or "No retrieved source notes."
        return (
            f"System instructions:\n{self.system}\n\n"
            f"Recent conversation:\n{history}\n\n"
            f"Retrieved recovery material:\n{sources}\n\n"
            f"Current user message:\n{self.user_message}\n\n"
            "Write a concise, supportive response that is specific to the current user message."
        )


class PromptBuilder:
    def build(
        self,
        user_message: str,
        retrieved_sources: list[RetrievedSource],
        history: list[MessageTurn] | None,
        substance_hint: str | None,
        privacy_mode: bool,
    ) -> GenerationPrompt:
        recent_history = [] if privacy_mode else list((history or [])[-4:])
        source_notes = [
            f"{source.title}: {source.snippet}"
            for source in retrieved_sources[:3]
            if source.snippet.strip()
        ]
        return GenerationPrompt(
            system=build_system_prompt(substance_hint, privacy_mode),
            user_message=user_message.strip(),
            source_notes=source_notes,
            recent_history=recent_history,
            substance_hint=substance_hint,
            privacy_mode=privacy_mode,
        )


class GenerationBackend(Protocol):
    def generate(self, prompt: GenerationPrompt) -> str | None:
        ...


def _contains_any(text: str, words: set[str]) -> bool:
    return any(word in text for word in words)


def _classify_concern(user_message: str) -> str:
    text = user_message.lower()
    if _contains_any(text, {"craving", "cravings", "urge", "using", "drink", "drinking"}):
        return "craving"
    if _contains_any(text, {"relapse", "slip", "lapse", "restart", "prevention"}):
        return "relapse_prevention"
    if _contains_any(text, {"lonely", "loneliness", "alone", "isolated", "isolation", "weekend"}):
        return "loneliness"
    if _contains_any(text, {"anxiety", "anxious", "panic", "stress", "stressed", "overwhelmed"}):
        return "anxiety_stress"
    if _contains_any(text, {"plan", "planning", "check-in", "checkin", "check", "schedule", "today"}):
        return "planning"
    return "general"


def _key_terms(text: str, limit: int = 5) -> list[str]:
    seen: set[str] = set()
    terms: list[str] = []
    for raw in TOKEN_RE.findall(text.lower()):
        term = raw.strip("-'")
        if term in STOPWORDS or term in seen:
            continue
        seen.add(term)
        terms.append(term)
        if len(terms) >= limit:
            break
    return terms


def _last_user_context(history: list[MessageTurn]) -> str:
    for turn in reversed(history):
        if turn.role == "user" and turn.content.strip():
            return turn.content.strip()
    return ""


class TemplateBackend:
    def generate(self, prompt: GenerationPrompt) -> str:
        concern = _classify_concern(prompt.user_message)
        terms = _key_terms(prompt.user_message)
        prior_user = _last_user_context(prompt.recent_history)
        prior_terms = _key_terms(prior_user, limit=3)

        openers = {
            "craving": "It makes sense to treat this as an urge that can be slowed down before it runs the whole evening.",
            "relapse_prevention": "You are catching relapse risk early, which gives you room to make the next choice easier.",
            "loneliness": "Loneliness can raise recovery risk because it makes the hard moment feel private and endless.",
            "anxiety_stress": "Stress and anxiety can make recovery feel urgent, so the goal is to lower the intensity first.",
            "planning": "A short plan can help turn the next few hours into something more predictable.",
            "general": "Thank you for saying what is happening. We can keep this practical and focused on the next safe step.",
        }
        actions = {
            "craving": [
                "Delay acting on the craving for 10 to 20 minutes and change rooms, routes, or routines if the after-work cue is strong.",
                "Name the trigger in plain words, then do one grounding action that keeps distance between you and access.",
                "Message or call one recovery-supportive person before deciding what to do next.",
            ],
            "relapse_prevention": [
                "Map the highest-risk trigger, the first warning sign, and the safer action you want ready in advance.",
                "Remove or avoid one easy access point that could turn a difficult moment into a slip.",
                "Set one check-in for today so the plan is not only living in your head.",
            ],
            "loneliness": [
                "Choose one low-friction connection: text someone, attend a meeting, sit in a public sober space, or schedule a call.",
                "Give the weekend some shape with one anchored activity in the morning or early evening.",
                "If isolation is feeding urges, move toward people before the urge gets louder.",
            ],
            "anxiety_stress": [
                "Lower the body alarm first: slow breathing, cold water, a short walk, or naming five things you can see.",
                "Separate the stressor from the recovery choice by writing one sentence about what is actually needed next.",
                "Use support early if stress is making substance use feel like the only relief.",
            ],
            "planning": [
                "Pick a time window, a likely trigger, and a specific coping response for that window.",
                "Make the safer choice easier to reach than the risky one by changing the environment now.",
                "Add one check-in point with a person, meeting, or written note.",
            ],
            "general": [
                "Name the situation and the feeling in one sentence so the risk is easier to work with.",
                "Choose one small action that supports recovery in the next 10 minutes.",
                "Reach for professional, peer, or trusted support if the risk starts rising.",
            ],
        }

        lines = [openers[concern]]
        if terms:
            lines.append(f"I am hearing the key pieces as: {', '.join(terms)}.")
        if prior_terms:
            lines.append(
                "Since this session also included "
                f"{', '.join(prior_terms)}, keep that context in the plan without letting it take over."
            )

        lines.append("")
        lines.append("For the next stretch:")
        lines.extend(f"{index}. {action}" for index, action in enumerate(actions[concern], start=1))

        if prompt.source_notes:
            lines.append("")
            lines.append("From the indexed recovery materials:")
            lines.extend(f"- {note}" for note in prompt.source_notes)

        lines.append("")
        lines.append(
            "This is supportive guidance only, not clinical or medical care. "
            "I can help turn this into a brief check-in, coping card, or prevention plan."
        )
        return "\n".join(lines)


class OpenAIBackend:
    def __init__(self, settings: Settings) -> None:
        self.model = settings.generation_model_name or "gpt-4o-mini"
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("CHAT_SUD_OPENAI_API_KEY")

    def generate(self, prompt: GenerationPrompt) -> str | None:
        if not self.api_key:
            return None
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt.system},
                {"role": "user", "content": prompt.as_text()},
            ],
            "temperature": 0.4,
        }
        request = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (OSError, urllib.error.HTTPError, urllib.error.URLError, KeyError, json.JSONDecodeError):
            return None
        return body["choices"][0]["message"]["content"].strip() or None


class GenerationOrchestrator:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.prompt_builder = PromptBuilder()
        self.template_backend = TemplateBackend()

    def _backend(self) -> GenerationBackend:
        if self.settings.generation_backend.lower() == "openai":
            return OpenAIBackend(self.settings)
        return self.template_backend

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

        prompt = self.prompt_builder.build(
            user_message=user_message,
            retrieved_sources=retrieved_sources,
            history=history,
            substance_hint=substance_hint,
            privacy_mode=privacy_mode,
        )
        generated = self._backend().generate(prompt)
        if generated:
            return generated
        return self.template_backend.generate(prompt)


def iter_text_chunks(text: str, chunk_size: int = 40) -> Iterable[str]:
    for start in range(0, len(text), chunk_size):
        yield text[start : start + chunk_size]
