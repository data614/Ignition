"""Hand evaluation helpers for simple Hold'em heuristics."""
from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Sequence, Tuple

from .cards import Card, VALUE_TO_RANK

HAND_CATEGORIES = [
    "high_card",
    "one_pair",
    "two_pair",
    "three_of_a_kind",
    "straight",
    "flush",
    "full_house",
    "four_of_a_kind",
    "straight_flush",
]
HAND_CATEGORY_TO_SCORE = {name: index for index, name in enumerate(HAND_CATEGORIES)}


class HandEvaluationError(RuntimeError):
    """Raised when hand evaluation cannot be completed."""


def _check_straight(ranks: Sequence[int]) -> Tuple[bool, int]:
    """Return whether ranks form a straight and the high card if so."""

    unique = sorted(set(ranks), reverse=True)
    if len(unique) >= 5:
        for index in range(len(unique) - 4):
            window = unique[index : index + 5]
            if window[0] - window[4] == 4:
                return True, window[0]
    # Wheel straight (A-2-3-4-5)
    if {14, 5, 4, 3, 2}.issubset(unique):
        return True, 5
    return False, 0


def _evaluate_five_cards(cards: Sequence[Card]) -> Tuple[int, Tuple[int, ...]]:
    ranks = sorted((card.value for card in cards), reverse=True)
    suits = [card.suit for card in cards]
    counts = Counter(ranks)
    is_flush = len(set(suits)) == 1
    is_straight, straight_high = _check_straight(ranks)
    sorted_counts = sorted(counts.items(), key=lambda item: (-item[1], -item[0]))

    if is_flush and is_straight:
        category = "straight_flush"
        kicker = (straight_high,)
    elif sorted_counts[0][1] == 4:
        category = "four_of_a_kind"
        kicker = (sorted_counts[0][0], sorted_counts[1][0])
    elif sorted_counts[0][1] == 3 and sorted_counts[1][1] == 2:
        category = "full_house"
        kicker = (sorted_counts[0][0], sorted_counts[1][0])
    elif is_flush:
        category = "flush"
        kicker = tuple(ranks)
    elif is_straight:
        category = "straight"
        kicker = (straight_high,)
    elif sorted_counts[0][1] == 3:
        category = "three_of_a_kind"
        kickers = [sorted_counts[0][0]]
        kickers.extend(sorted((rank for rank in ranks if rank != sorted_counts[0][0]), reverse=True))
        kicker = tuple(kickers[:3])
    elif sorted_counts[0][1] == 2 and sorted_counts[1][1] == 2:
        category = "two_pair"
        pair_ranks = sorted([sorted_counts[0][0], sorted_counts[1][0]], reverse=True)
        remaining = max(rank for rank in ranks if rank not in pair_ranks)
        kicker = (*pair_ranks, remaining)
    elif sorted_counts[0][1] == 2:
        category = "one_pair"
        pair_rank = sorted_counts[0][0]
        kickers = [rank for rank in ranks if rank != pair_rank]
        kicker = (pair_rank, *tuple(sorted(kickers, reverse=True)))
    else:
        category = "high_card"
        kicker = tuple(ranks)

    return HAND_CATEGORY_TO_SCORE[category], kicker


def evaluate_best_hand(all_cards: Sequence[Card]) -> Tuple[str, Tuple[int, ...]]:
    """Return the best five-card hand category and kicker tuple."""

    if len(all_cards) < 5:
        raise HandEvaluationError("At least five cards are required to evaluate a hand.")

    best_score: Tuple[int, Tuple[int, ...]] | None = None
    best_category = "high_card"
    for combo in combinations(all_cards, 5):
        score = _evaluate_five_cards(combo)
        if best_score is None or score > best_score:
            best_score = score
            best_category = HAND_CATEGORIES[score[0]]

    if best_score is None:
        raise HandEvaluationError("Unable to evaluate hand.")

    return best_category, best_score[1]


def rank_to_string(rank_value: int) -> str:
    """Convert a numeric rank back to its single-character representation."""

    return VALUE_TO_RANK.get(rank_value, "?")
