"""Data models describing the extracted poker table state."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class PlayerSnapshot:
    """Information captured for a single player."""

    name: str
    stack: Optional[float] = None
    position: Optional[str] = None


@dataclass
class TableSnapshot:
    """Aggregated state required for the decision engine."""

    table_name: str
    hero_cards: List[str] = field(default_factory=list)
    community_cards: List[str] = field(default_factory=list)
    pot_size: Optional[float] = None
    hero_stack: Optional[float] = None
    opponents: List[PlayerSnapshot] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "table_name": self.table_name,
            "hero_cards": self.hero_cards,
            "community_cards": self.community_cards,
            "pot_size": self.pot_size,
            "hero_stack": self.hero_stack,
            "opponents": [player.__dict__ for player in self.opponents],
            "notes": self.notes,
        }
