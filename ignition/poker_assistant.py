"""High level poker assistant interface for study-mode recommendations."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .cards import CardParsingError, parse_cards
from .postflop import Recommendation as PostflopRecommendation
from .postflop import recommend_postflop
from .range_engine import PreflopRecommendation, RangeEngine


@dataclass
class AssistantResult:
    stage: str
    action: str
    sizing: Optional[str]
    equity_estimate: float
    rationale: str
    metadata: Dict[str, str]


class PokerAssistant:
    """Facade that exposes preflop and postflop coaching recommendations."""

    def __init__(self, range_path: Optional[Path] = None) -> None:
        self._range_engine = RangeEngine(range_path)

    def recommend_preflop(
        self,
        position: str,
        hero_hand: str,
        stack_bb: float,
        situation: str = "open",
    ) -> AssistantResult:
        rec: PreflopRecommendation = self._range_engine.recommend(
            position=position,
            hero_hand=hero_hand,
            stack_bb=stack_bb,
            situation=situation,
        )
        metadata = {
            "stack_key": rec.stack_key,
            "position": rec.position,
            "situation": rec.situation,
        }
        return AssistantResult(
            stage="preflop",
            action=rec.action,
            sizing=rec.sizing,
            equity_estimate=rec.equity_estimate,
            rationale=rec.rationale,
            metadata=metadata,
        )

    @staticmethod
    def _parse_board(stage: str, board_text: str) -> list:
        board_cards = parse_cards(board_text)
        expected = {"flop": 3, "turn": 4, "river": 5}[stage]
        if len(board_cards) != expected:
            raise ValueError(
                f"{stage.capitalize()} expects {expected} community cards, got {len(board_cards)}"
            )
        return board_cards

    def recommend_postflop(
        self,
        stage: str,
        hero_hand: str,
        board_cards: str,
        pot_size: float,
        stack_bb: float,
    ) -> AssistantResult:
        if stage not in {"flop", "turn", "river"}:
            raise ValueError("Post-flop stage must be flop, turn or river.")
        try:
            hero_cards = parse_cards(hero_hand)
        except CardParsingError as exc:
            raise ValueError(f"Invalid hero hand: {exc}") from exc
        if len(hero_cards) != 2:
            raise ValueError("Hero hand must contain exactly two cards.")
        try:
            board = self._parse_board(stage, board_cards)
        except CardParsingError as exc:
            raise ValueError(f"Invalid board cards: {exc}") from exc
        rec: PostflopRecommendation = recommend_postflop(
            stage=stage,
            hero=hero_cards,
            board=board,
            pot_size=pot_size,
            stack_size=stack_bb,
        )
        metadata = {
            "classification": rec.details.get("hand_classification", ""),
            "best_category": rec.details.get("best_category", ""),
            "spr": rec.details.get("spr", ""),
            "draws": rec.details.get("draws", ""),
        }
        return AssistantResult(
            stage=stage,
            action=rec.action,
            sizing=rec.sizing,
            equity_estimate=rec.equity_estimate,
            rationale=rec.rationale,
            metadata=metadata,
        )
