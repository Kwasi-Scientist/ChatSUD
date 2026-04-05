from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from chat_sud.config import Settings, get_settings
from chat_sud.schemas import SafetyMode


@dataclass(slots=True)
class SafetyDecision:
    mode: SafetyMode
    triggered: bool
    region: str
    message: str | None = None


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_rules(path_str: str) -> dict[str, Any]:
    return _load_json(Path(path_str))


@lru_cache(maxsize=1)
def _load_resources(path_str: str) -> dict[str, Any]:
    return _load_json(Path(path_str))


def _compile_patterns(patterns: list[str]) -> list[re.Pattern[str]]:
    return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]


def _normalize_region(region_hint: str | None, text: str | None) -> str:
    raw = (region_hint or "").upper()
    if raw in {"US", "USA", "UNITED STATES"}:
        return "US"
    if raw in {"UK", "UNITED KINGDOM", "ENGLAND", "SCOTLAND", "WALES"}:
        return "UK"
    if raw in {"EU", "EUROPE"}:
        return "EU"

    hay = (text or "").lower()
    if any(term in hay for term in ["usa", "united states", "911", "988"]):
        return "US"
    if any(term in hay for term in ["united kingdom", "england", "999", "85258"]):
        return "UK"
    if any(term in hay for term in ["europe", "112", "germany", "france", "spain", "italy"]):
        return "EU"
    return "GLOBAL"


def _format_crisis_message(region: str, settings: Settings) -> str:
    resources = _load_resources(str(settings.crisis_resources_path))
    regional = resources.get("regions", {}).get(region, resources["regions"]["GLOBAL"])
    lines = [
        "I am noticing language that may point to an immediate safety risk.",
        "I cannot help with self-harm, overdose, or emergency instructions.",
        "Please reach out to real-time crisis support right now:",
        "",
    ]
    for item in regional["resources"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "If you can, move toward another person, emergency care, or a trusted contact now.",
            "Once you are safe, I can help you make a short grounding plan for the next hour.",
        ]
    )
    return "\n".join(lines)


def _medical_refusal_message() -> str:
    return (
        "I cannot give detox, tapering, dosing, or other medical instructions. "
        "If you may be in withdrawal, at risk of overdose, or mixing substances or medications, "
        "please contact a licensed clinician, urgent care, poison control, or emergency services. "
        "I can still help you write down symptoms, prepare questions for a professional, or make a "
        "short safety-focused coping plan."
    )


def assess_message(
    text: str,
    region_hint: str | None = None,
    settings: Settings | None = None,
) -> SafetyDecision:
    settings = settings or get_settings()
    rules = _load_rules(str(settings.safety_rules_path))
    crisis_patterns = _compile_patterns(rules["crisis_patterns"])
    medical_patterns = _compile_patterns(rules["medical_refusal_patterns"])
    region = _normalize_region(region_hint, text)

    if any(pattern.search(text) for pattern in crisis_patterns):
        return SafetyDecision(
            mode=SafetyMode.crisis,
            triggered=True,
            region=region,
            message=_format_crisis_message(region, settings),
        )

    if any(pattern.search(text) for pattern in medical_patterns):
        return SafetyDecision(
            mode=SafetyMode.medical_refusal,
            triggered=True,
            region=region,
            message=_medical_refusal_message(),
        )

    return SafetyDecision(mode=SafetyMode.supportive, triggered=False, region=region)

