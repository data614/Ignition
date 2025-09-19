"""Simple rule-based decision engine used by the prototype."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, Mapping, Optional, Set

from .state import TableSnapshot


RANK_ORDER = "AKQJT98765432"
SUIT_ALIASES = {
    "♠": "s",
    "♣": "c",
    "♥": "h",
    "♦": "d",
    "S": "s",
    "C": "c",
    "H": "h",
    "D": "d",
}
POSITION_ALIASES = {
    "UTG": "EP",
    "UTG+1": "EP",
    "LJ": "MP",
    "HJ": "MP",
    "CO": "CO",
    "BTN": "BTN",
    "SB": "SB",
    "BB": "BB",
    "MP": "MP",
    "EP": "EP",
}


def _build_range(entries: Iterable[str]) -> Set[str]:
    return {entry.upper() for entry in entries}


DEFAULT_OPEN_RANGES: Mapping[str, Set[str]] = {
    "EP": _build_range(["AA", "KK", "QQ", "JJ", "TT", "AKS", "AQs", "AKO"]),
    "MP": _build_range(["AA", "KK", "QQ", "JJ", "TT", "99", "88", "AKS", "AQs", "AJs", "KQs", "AKO", "AQO"]),
    "CO": _build_range(
        [
            "AA",
            "KK",
            "QQ",
            "JJ",
            "TT",
            "99",
            "88",
            "77",
            "A2S",
            "A3S",
            "A4S",
            "A5S",
            "A6S",
            "A7S",
            "A8S",
            "A9S",
            "ATS",
            "AKO",
            "AQO",
            "AJO",
            "KQO",
            "KJS",
            "QJS",
            "JTS",
        ]
    ),
    "BTN": _build_range(
        [
            "AA",
            "KK",
            "QQ",
            "JJ",
            "TT",
            "99",
            "88",
            "77",
            "66",
            "55",
            "44",
            "33",
            "22",
            "A2S",
            "A3S",
            "A4S",
            "A5S",
            "A6S",
            "A7S",
            "A8S",
            "A9S",
            "ATS",
            "AKO",
            "AQO",
            "AJO",
            "ATO",
            "KTO",
            "QTO",
            "JTO",
            "T9S",
            "98S",
            "87S",
        ]
    ),
    "SB": _build_range(["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "A2S", "A3S", "A4S", "A5S", "AKO", "AQO"]),
    "BB": _build_range(["AA", "KK", "QQ", "JJ", "TT", "99", "88", "AKS", "AQS", "AKO", "AQO"]),
}

SHORT_STACK_SHOVES: Mapping[str, Set[str]] = {
    "EP": _build_range(["AA", "KK", "QQ", "JJ", "TT", "AKS", "AKO", "AQs"]),
    "MP": _build_range(["AA", "KK", "QQ", "JJ", "TT", "99", "88", "AKS", "AQs", "AKO", "AQo"]),
    "CO": _build_range(["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "AJs", "ATs", "KQs", "AKO", "AQO"]),
    "BTN": _build_range(["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "A9S", "A8S", "A5S", "AKS", "AKO", "AQO", "AJO", "KQO"]),
    "SB": _build_range(["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "66", "55", "A9S", "A8S", "AKO", "AQO"]),
    "BB": _build_range(["AA", "KK", "QQ", "JJ", "TT", "99", "88", "77", "AJs", "AQO", "AKO"]),
}


@dataclass
class Decision:
    action: str
    confidence: float
    explanation: str


class RuleBasedDecisionEngine:
    """Very small rule engine built around canned preflop ranges."""

    def recommend(self, table: TableSnapshot, hero_position: Optional[str]) -> Decision:
        if len(table.hero_cards) < 2:
            return Decision(action="No Action", confidence=0.0, explanation="Hero cards not detected yet.")

        combo = canonical_hand(table.hero_cards[0], table.hero_cards[1])
        if combo is None:
            return Decision(action="Review", confidence=0.1, explanation="Unable to parse hero cards.")

        position_key = POSITION_ALIASES.get((hero_position or "MP").upper(), "MP")
        stack = table.hero_stack
        if stack is not None and stack <= 12:
            range_map = SHORT_STACK_SHOVES
            positive_action = "Shove"
            baseline = "Fold"
        else:
            range_map = DEFAULT_OPEN_RANGES
            positive_action = "Raise"
            baseline = "Fold"

        allowed = range_map.get(position_key, set())
        if combo in allowed:
            explanation = (
                f"{combo} is within the {position_key} range. Suggesting {positive_action.lower()} with stack {stack}bb"
                if stack is not None
                else f"{combo} in {position_key} opening range."
            )
            return Decision(action=positive_action, confidence=0.8, explanation=explanation)
        explanation = (
            f"{combo} not present in {position_key} range. Defaulting to fold." if position_key else "Hand not in range."
        )
        return Decision(action=baseline, confidence=0.6, explanation=explanation)


def canonical_hand(card_a: str, card_b: str) -> Optional[str]:
    """Return a canonical representation of a two-card poker hand."""

    parsed_a = _parse_card(card_a)
    parsed_b = _parse_card(card_b)
    if not parsed_a or not parsed_b:
        return None

    rank_a, suit_a = parsed_a
    rank_b, suit_b = parsed_b

    idx_a = RANK_ORDER.index(rank_a)
    idx_b = RANK_ORDER.index(rank_b)

    # Ensure first rank is the higher one.
    if idx_a > idx_b:
        rank_a, rank_b = rank_b, rank_a
        suit_a, suit_b = suit_b, suit_a
        idx_a, idx_b = idx_b, idx_a

    if rank_a == rank_b:
        return f"{rank_a}{rank_b}"
    suited = suit_a == suit_b
    suffix = "S" if suited else "O"
    return f"{rank_a}{rank_b}{suffix}"


def _parse_card(card: str) -> Optional[tuple[str, str]]:
    text = card.strip().upper()
    if not text:
        return None

    rank = text[0]
    rest = text[1:]

    if rank == "1" and rest.startswith("0"):
        rank = "T"
        rest = rest[1:]

    if rank not in RANK_ORDER:
        return None

    suit_char = rest[:1] if rest else ""
    if not suit_char and len(text) >= 2:
        suit_char = text[-1]

    suit = SUIT_ALIASES.get(suit_char, suit_char.lower())
    if suit not in {"s", "h", "d", "c"}:
        return None
    return rank, suit
