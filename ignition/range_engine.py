"""Preflop range lookup for the Ignition study assistant."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence

from .cards import canonicalize_hand, parse_cards


@dataclass
class PreflopRecommendation:
    stack_key: str
    position: str
    situation: str
    action: str
    sizing: Optional[str]
    rationale: str
    equity_estimate: float


class RangeEngine:
    """Load curated ranges and provide simple recommendations."""

    def __init__(self, data_path: Optional[Path] = None) -> None:
        if data_path is None:
            data_path = Path(__file__).resolve().parent / "data" / "preflop_ranges.json"
        self._data = json.loads(data_path.read_text(encoding="utf8"))
        self._ranges: Dict[str, Dict[str, Dict[str, Dict[str, Iterable[str]]]]] = self._data["ranges"]

    def available_stacks(self) -> Sequence[str]:
        return list(self._ranges.keys())

    def _stack_key(self, stack_bb: float) -> str:
        available = []
        for key in self.available_stacks():
            if key.endswith("bb"):
                try:
                    available.append((abs(float(key[:-2]) - stack_bb), key))
                except ValueError:
                    continue
        if not available:
            raise ValueError("No stack configurations available in range data.")
        _, nearest = min(available, key=lambda item: item[0])
        return nearest

    def recommend(
        self,
        position: str,
        hero_hand: str,
        stack_bb: float,
        situation: str = "open",
    ) -> PreflopRecommendation:
        stack_key = self._stack_key(stack_bb)
        position_key = position.upper()
        try:
            position_data = self._ranges[stack_key][position_key]
        except KeyError as exc:
            raise ValueError(f"No range data for position {position_key!r} at {stack_key}.") from exc

        try:
            situation_data = position_data[situation]
        except KeyError as exc:
            available = ", ".join(position_data.keys())
            raise ValueError(
                f"Unsupported situation {situation!r}; available: {available}."
            ) from exc

        cards = parse_cards(hero_hand)
        if len(cards) != 2:
            raise ValueError("Preflop recommendations require exactly two hole cards.")
        canonical = canonicalize_hand(cards)

        action = self._lookup_action(canonical, situation_data)
        rationale = self._build_rationale(action, canonical, position_key, situation)
        sizing = self._recommended_sizing(action, situation)
        equity = self._equity_estimate(action)

        return PreflopRecommendation(
            stack_key=stack_key,
            position=position_key,
            situation=situation,
            action=action,
            sizing=sizing,
            rationale=rationale,
            equity_estimate=equity,
        )

    @staticmethod
    def _lookup_action(hand: str, data: Dict[str, Iterable[str]]) -> str:
        for action, combos in data.items():
            if hand in combos:
                return action
        return "fold"

    @staticmethod
    def _build_rationale(action: str, hand: str, position: str, situation: str) -> str:
        if action == "fold":
            return f"{hand} falls outside the recommended {situation} range for {position}."
        if situation == "open":
            if action == "raise":
                return f"{hand} is profitable to open-raise from {position} at this stack depth."
            if action == "call":
                return f"{hand} performs better as a call from {position}; avoid bloating the pot."
            if action == "shove":
                return f"Low SPR situations favor open-shoving premium hands like {hand}."
        elif situation == "vs_raise":
            if action == "three_bet":
                return f"{hand} is strong enough to 3-bet for value or as a bluff from {position}."
            if action == "call":
                return f"{hand} defends the position well as a flat call versus an open raise."
        elif situation == "vs_3bet":
            if action == "four_bet":
                return f"{hand} is a reliable four-bet candidate from {position} at this depth."
            if action == "call":
                return f"{hand} can profitably continue by calling the three-bet."  
        return f"Follow the chart recommendation to {action} with {hand} from {position}."

    @staticmethod
    def _recommended_sizing(action: str, situation: str) -> Optional[str]:
        if action == "fold":
            return None
        if situation == "open":
            if action == "raise":
                return "2.5bb"
            if action == "shove":
                return "shove"
        if situation == "vs_raise":
            if action == "three_bet":
                return "3x"
            if action == "call":
                return "call"
        if situation == "vs_3bet":
            if action == "four_bet":
                return "2.2x"
            if action == "call":
                return "call"
        return None

    @staticmethod
    def _equity_estimate(action: str) -> float:
        mapping = {
            "fold": 0.0,
            "raise": 0.6,
            "call": 0.48,
            "three_bet": 0.58,
            "four_bet": 0.64,
            "shove": 0.7,
        }
        return mapping.get(action, 0.5)
