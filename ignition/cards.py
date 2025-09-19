"""Utilities for working with standard playing cards used in poker."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

RANKS = "23456789TJQKA"
SUITS = "CDHS"

RANK_TO_VALUE = {rank: index + 2 for index, rank in enumerate(RANKS)}
VALUE_TO_RANK = {value: rank for rank, value in RANK_TO_VALUE.items()}


@dataclass(frozen=True)
class Card:
    """Representation of a single playing card.

    The rank is stored as an uppercase single character (e.g. ``"A"``),
    and the suit is an uppercase character (``"S"`` for spades, ``"H"`` for hearts,
    ``"D"`` for diamonds and ``"C"`` for clubs).
    """

    rank: str
    suit: str

    def __post_init__(self) -> None:
        if self.rank not in RANKS:
            raise ValueError(f"Invalid rank: {self.rank!r}")
        if self.suit not in SUITS:
            raise ValueError(f"Invalid suit: {self.suit!r}")

    @property
    def value(self) -> int:
        """Return the numeric value of the card rank (2 low, Ace high)."""

        return RANK_TO_VALUE[self.rank]

    def __str__(self) -> str:
        return f"{self.rank}{self.suit}"


class CardParsingError(ValueError):
    """Raised when card parsing fails."""


def parse_card(token: str) -> Card:
    """Parse a single card from a two-character token."""

    token = token.strip().upper()
    if len(token) != 2:
        raise CardParsingError(f"Invalid card token: {token!r}")
    rank, suit = token[0], token[1]
    try:
        return Card(rank=rank, suit=suit)
    except ValueError as exc:
        raise CardParsingError(str(exc)) from exc


def parse_cards(card_string: str) -> List[Card]:
    """Parse a sequence of cards from a string.

    The function accepts either a whitespace separated string (``"As Kd"``)
    or a compact string without separators (``"AsKd"``).
    """

    cleaned = card_string.replace(" ", "").upper()
    if not cleaned:
        return []
    if len(cleaned) % 2 != 0:
        raise CardParsingError(
            "Card strings must contain pairs of rank/suit characters."
        )
    cards = [parse_card(cleaned[i : i + 2]) for i in range(0, len(cleaned), 2)]

    if len(set(cards)) != len(cards):
        raise CardParsingError("Card string contains duplicate cards.")

    return cards


def canonicalize_hand(cards: Sequence[Card]) -> str:
    """Return standard shorthand for a two-card hold'em hand.

    ``AA`` denotes a pair of aces, ``AKs`` suited ace-king and ``AKo`` offsuit.
    """

    if len(cards) != 2:
        raise ValueError("Exactly two cards are required for a hold'em hand.")

    card1, card2 = cards
    if card1.value == card2.value:
        return card1.rank * 2

    ranks = sorted((card1.rank, card2.rank), key=lambda r: RANK_TO_VALUE[r], reverse=True)
    suited = card1.suit == card2.suit
    suffix = "s" if suited else "o"
    return f"{ranks[0]}{ranks[1]}{suffix}"


def format_cards(cards: Iterable[Card]) -> str:
    """Return a human readable string for a card collection."""

    return " ".join(str(card) for card in cards)
