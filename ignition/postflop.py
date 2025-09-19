"""Simple post-flop heuristics for a study-mode poker assistant."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Sequence

from .cards import Card
from .hand_evaluator import evaluate_best_hand


@dataclass
class PostflopAnalysis:
    classification: str
    best_category: str
    draws: Dict[str, bool]


@dataclass
class Recommendation:
    stage: str
    action: str
    sizing: str | None
    rationale: str
    equity_estimate: float
    details: Dict[str, str]


CLASSIFICATION_EQUITY = {
    "premium_made": 0.85,
    "strong_made": 0.72,
    "combo_draw": 0.62,
    "medium_made": 0.55,
    "draw": 0.45,
    "weak_pair": 0.35,
    "air": 0.2,
}


def _board_ranks(board: Sequence[Card]) -> List[int]:
    return sorted((card.value for card in board), reverse=True)


def _has_flush_draw(hero: Sequence[Card], board: Sequence[Card]) -> bool:
    counts: Dict[str, int] = {}
    for card in hero:
        counts[card.suit] = counts.get(card.suit, 0) + 1
    for card in board:
        counts[card.suit] = counts.get(card.suit, 0) + 1
    for suit, count in counts.items():
        if count == 4:
            hero_count = sum(1 for card in hero if card.suit == suit)
            board_count = sum(1 for card in board if card.suit == suit)
            if hero_count >= 1 and board_count >= 2:
                return True
    return False


def _has_open_ended_draw(hero: Sequence[Card], board: Sequence[Card]) -> bool:
    all_cards = hero + list(board)
    ranks = {card.value for card in all_cards}
    hero_ranks = {card.value for card in hero}
    if 14 in ranks:
        ranks.add(1)
    if 14 in hero_ranks:
        hero_ranks.add(1)
    for start in range(1, 11):
        window = {start, start + 1, start + 2, start + 3}
        if window.issubset(ranks) and window & hero_ranks:
            return True
    return False


def _is_overpair(hero: Sequence[Card], board: Sequence[Card]) -> bool:
    if len(hero) != 2 or hero[0].value != hero[1].value:
        return False
    if not board:
        return False
    return hero[0].value > max(card.value for card in board)


def _has_top_pair(hero: Sequence[Card], board: Sequence[Card]) -> bool:
    if not board:
        return False
    top_board = max(card.value for card in board)
    return any(card.value == top_board for card in hero)


def _top_pair_kicker(hero: Sequence[Card], board: Sequence[Card]) -> int:
    top_board = max(card.value for card in board)
    kicker_values = [card.value for card in hero if card.value != top_board]
    return max(kicker_values) if kicker_values else 0


def _top_two(hero: Sequence[Card], board: Sequence[Card]) -> bool:
    board_ranks = _board_ranks(board)
    if len(board_ranks) < 2:
        return False
    highest = board_ranks[0]
    second = board_ranks[1]
    hero_values = sorted((card.value for card in hero), reverse=True)
    return hero_values[0] >= highest and hero_values[1] >= second


def analyze_postflop(hero: Sequence[Card], board: Sequence[Card]) -> PostflopAnalysis:
    best_category, _ = evaluate_best_hand(list(hero) + list(board))
    flush_draw = _has_flush_draw(hero, board)
    straight_draw = _has_open_ended_draw(hero, board)
    classification = "air"

    if best_category in {"straight_flush", "four_of_a_kind", "full_house"}:
        classification = "premium_made"
    elif best_category in {"flush", "straight", "three_of_a_kind"}:
        classification = "strong_made"
    elif best_category == "two_pair":
        if _top_two(hero, board):
            classification = "strong_made"
        else:
            classification = "medium_made"
    elif best_category == "one_pair":
        if _is_overpair(hero, board):
            classification = "medium_made"
        elif _has_top_pair(hero, board) and _top_pair_kicker(hero, board) >= 11:
            classification = "medium_made"
        else:
            classification = "weak_pair"

    if classification in {"medium_made", "weak_pair", "air"} and (flush_draw or straight_draw):
        classification = "combo_draw" if classification == "medium_made" else "draw"

    draws = {"flush_draw": flush_draw, "straight_draw": straight_draw}
    return PostflopAnalysis(classification, best_category, draws)


def recommend_postflop(
    stage: str,
    hero: Sequence[Card],
    board: Sequence[Card],
    pot_size: float,
    stack_size: float,
) -> Recommendation:
    analysis = analyze_postflop(hero, board)
    spr = stack_size / pot_size if pot_size else float("inf")

    sizing = None
    rationale = ""
    action = "check"
    classification = analysis.classification

    if classification == "premium_made":
        action = "bet"
        sizing = "100%"
        rationale = "With a premium made hand you should build the pot aggressively."
    elif classification == "strong_made":
        action = "bet"
        sizing = "66%"
        rationale = "Strong made hands can value bet for two streets against most ranges."
    elif classification == "combo_draw":
        action = "bet"
        sizing = "66%"
        rationale = "Combination draws benefit from semi-bluffing with fold equity."
    elif classification == "medium_made":
        if stage == "river" or spr < 3:
            action = "check"
            rationale = "Control the pot with medium-strength holdings at low SPR."
        else:
            action = "bet"
            sizing = "33%"
            rationale = "Small bets with medium hands deny equity and get thin value."
    elif classification == "draw":
        if spr > 2:
            action = "bet"
            sizing = "66%"
            rationale = "Leverage fold equity with your draw while building a pot for when you hit."
        else:
            action = "check"
            rationale = "With shallow stacks take the free card rather than risking a shove."
    elif classification == "weak_pair":
        action = "check"
        rationale = "Weak pairs perform best by controlling pot size and bluff-catching carefully."
    else:
        action = "check"
        rationale = "Air hands should usually check-fold against aggression on this texture."

    equity = CLASSIFICATION_EQUITY.get(classification, 0.25)
    details = {
        "hand_classification": classification,
        "best_category": analysis.best_category,
        "spr": f"{spr:.2f}",
        "draws": ", ".join(
            name for name, present in analysis.draws.items() if present
        )
        or "none",
    }

    return Recommendation(
        stage=stage,
        action=action,
        sizing=sizing,
        rationale=rationale,
        equity_estimate=equity,
        details=details,
    )
