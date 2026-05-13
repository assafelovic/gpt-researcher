"""Query safety helpers for blocking dangerous research requests."""

from __future__ import annotations

from dataclasses import dataclass, asdict
import re
from typing import Iterable

from .language import is_german_language


@dataclass(frozen=True)
class QuerySafetyDecision:
    """Structured result for a blocked query."""

    blocked: bool
    category: str
    reason: str
    matched_terms: tuple[str, ...]
    safe_alternatives: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


_HAZARDOUS_CHEMICAL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("schwefelsäure", re.compile(r"\bschwefels(?:ä|ae|a)ure\b", re.IGNORECASE)),
    ("sulfuric acid", re.compile(r"\bsulfuric\s+acid\b", re.IGNORECASE)),
    ("salpetersäure", re.compile(r"\bsalpeters(?:ä|ae|a)ure\b", re.IGNORECASE)),
    ("nitric acid", re.compile(r"\bnitric\s+acid\b", re.IGNORECASE)),
    ("salzsäure", re.compile(r"\bsalzs(?:ä|ae|a)ure\b", re.IGNORECASE)),
    ("hydrochloric acid", re.compile(r"\bhydrochloric\s+acid\b", re.IGNORECASE)),
    ("chlorine gas", re.compile(r"\bchlorine\s+gas\b", re.IGNORECASE)),
    ("toxic gas", re.compile(r"\btoxic\s+gas\b", re.IGNORECASE)),
    ("explosives", re.compile(r"\bexplosives?\b", re.IGNORECASE)),
    ("gunpowder", re.compile(r"\bgunpowder\b", re.IGNORECASE)),
    ("nitroglycerin", re.compile(r"\bnitroglycerin\b", re.IGNORECASE)),
    ("poison", re.compile(r"\bpoisons?\b", re.IGNORECASE)),
    ("nerve agent", re.compile(r"\bnerve\s+agent\b", re.IGNORECASE)),
    ("mustard gas", re.compile(r"\bmustard\s+gas\b", re.IGNORECASE)),
    ("ricin", re.compile(r"\bricin\b", re.IGNORECASE)),
)

_PRODUCTION_INTENT_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("herstellen", re.compile(r"\bherstellen\b", re.IGNORECASE)),
    ("selber machen", re.compile(r"\bselb(er|st)\s+machen\b", re.IGNORECASE)),
    ("machen", re.compile(r"\bmachen\b", re.IGNORECASE)),
    ("produzieren", re.compile(r"\bproduzieren\b", re.IGNORECASE)),
    ("synthetisieren", re.compile(r"\bsynthetisieren\b", re.IGNORECASE)),
    ("anleitung", re.compile(r"\banleitung\b", re.IGNORECASE)),
    ("recipe", re.compile(r"\brecipe\b", re.IGNORECASE)),
    ("how to make", re.compile(r"\bhow\s+to\s+make\b", re.IGNORECASE)),
    ("make", re.compile(r"\bmake\b", re.IGNORECASE)),
    ("prepare", re.compile(r"\bprepare\b", re.IGNORECASE)),
    ("fabricate", re.compile(r"\bfabricate\b", re.IGNORECASE)),
    ("zu hause", re.compile(r"\bzu\s+hause\b", re.IGNORECASE)),
    ("home", re.compile(r"\b(at\s+home|home)\b", re.IGNORECASE)),
    ("privat", re.compile(r"\bprivat(person(en)?)?\b", re.IGNORECASE)),
    ("private use", re.compile(r"\bprivate\s+use\b", re.IGNORECASE)),
)

_SAFE_ALTERNATIVES_GERMAN = (
    "allgemeine Informationen zu Eigenschaften, Gefahren und Schutzmaßnahmen",
    "rechtliche Einordnung und sichere Lagerung",
    "Entsorgung, Arbeitsschutz und Notfallmaßnahmen",
    "ungefährliche Alternativen für denselben Zweck",
)

_SAFE_ALTERNATIVES_ENGLISH = (
    "general information about properties, hazards, and protective measures",
    "legal context and safe storage",
    "disposal, occupational safety, and emergency measures",
    "safe alternatives for the same purpose",
)


def _normalize_query_text(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def _match_terms(text: str, patterns: Iterable[tuple[str, re.Pattern[str]]]) -> list[str]:
    matches: list[str] = []
    for label, pattern in patterns:
        if pattern.search(text):
            matches.append(label)
    return matches


def detect_unsafe_query(query: str | None) -> QuerySafetyDecision | None:
    """Return a refusal decision for dangerous chemistry synthesis requests."""
    text = _normalize_query_text(query)
    if not text:
        return None

    matched_chemicals = _match_terms(text, _HAZARDOUS_CHEMICAL_PATTERNS)
    if not matched_chemicals:
        return None

    matched_intent = _match_terms(text, _PRODUCTION_INTENT_PATTERNS)
    if not matched_intent:
        return None

    matched_terms = tuple(dict.fromkeys([*matched_chemicals, *matched_intent]))
    reason = (
        "Die Anfrage zielt auf die Herstellung oder Beschaffung einer gefährlichen Chemikalie "
        f"ab ({', '.join(matched_terms[:4])})."
    )
    if len(matched_terms) > 4:
        reason = reason.rstrip(".") + " ..."

    return QuerySafetyDecision(
        blocked=True,
        category="hazardous_chemistry",
        reason=reason,
        matched_terms=matched_terms,
        safe_alternatives=_SAFE_ALTERNATIVES_GERMAN,
    )


def render_query_refusal(query: str, decision: QuerySafetyDecision, language: str | None = None) -> str:
    """Render a concise refusal report in the configured language."""
    if is_german_language(language):
        alternatives = decision.safe_alternatives or _SAFE_ALTERNATIVES_GERMAN
        return "\n".join(
            [
                "# Anfrage abgelehnt",
                "",
                "Ich kann keine Anweisungen zur Herstellung gefährlicher Chemikalien geben.",
                "",
                "## Warum",
                f"- {decision.reason}",
                f"- Betroffene Anfrage: {query}",
                "",
                "## Sichere Alternativen",
                *[f"- {item}" for item in alternatives],
            ]
        ).strip()

    alternatives = _SAFE_ALTERNATIVES_ENGLISH
    return "\n".join(
        [
            "# Request declined",
            "",
            "I cannot provide instructions for making dangerous chemicals.",
            "",
            "## Why",
            f"- {decision.reason}",
            f"- Affected request: {query}",
            "",
            "## Safe alternatives",
            *[f"- {item}" for item in alternatives],
        ]
    ).strip()
