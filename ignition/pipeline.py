"""High level orchestration for the Ignition poker assistant prototype."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None  # type: ignore

from .capture import FileCapture, ScreenCapture
from .config import AssistantConfig, BoundingBox
from .decision import Decision, RuleBasedDecisionEngine
from .detection import CardTemplateLibrary, TemplateMatchResult, crop_region
from .ocr import OcrEngine
from .state import PlayerSnapshot, TableSnapshot


@dataclass
class ExtractionResult:
    snapshot: TableSnapshot
    decision: Decision


class FrameInterpreter:
    """Convert captured frames into poker decisions."""

    def __init__(
        self,
        config: AssistantConfig,
        *,
        card_library: Optional[CardTemplateLibrary] = None,
        ocr_engine: Optional[OcrEngine] = None,
        decision_engine: Optional[RuleBasedDecisionEngine] = None,
    ) -> None:
        _require_numpy()
        self._config = config
        self._card_library = card_library
        self._ocr = ocr_engine or OcrEngine()
        self._decision_engine = decision_engine or RuleBasedDecisionEngine()

    def process_frame(self, frame: np.ndarray, hero_position: Optional[str] = None) -> ExtractionResult:
        snapshot = TableSnapshot(table_name=self._config.table_name)
        snapshot.hero_cards = self._detect_cards(frame, self._config.regions.hero_cards, label_prefix="Hero")
        snapshot.community_cards = self._detect_cards(
            frame, self._config.regions.community_cards, label_prefix="Board"
        )
        if self._config.regions.pot:
            snapshot.pot_size = self._read_amount(frame, self._config.regions.pot)
        if self._config.regions.hero_stack:
            snapshot.hero_stack = self._read_amount(frame, self._config.regions.hero_stack)
        if self._config.regions.opponent_stacks:
            snapshot.opponents = self._read_opponents(frame, self._config.regions.opponent_stacks)

        if self._card_library is None:
            snapshot.notes.append("Card templates not configured; hero cards may be placeholders.")

        decision = self._decision_engine.recommend(snapshot, hero_position)
        return ExtractionResult(snapshot=snapshot, decision=decision)

    def _detect_cards(self, frame: np.ndarray, regions: Sequence[BoundingBox], *, label_prefix: str) -> list[str]:
        cards: list[str] = []
        for index, box in enumerate(regions, start=1):
            crop = crop_region(frame, box)
            label = self._match_card(crop)
            if label is None:
                label = f"{label_prefix}-{index:02d}"
            cards.append(label)
        return cards

    def _match_card(self, image: np.ndarray) -> Optional[str]:
        if self._card_library is None:
            return None
        result = self._card_library.match_card(image)
        return result.label if isinstance(result, TemplateMatchResult) else None

    def _read_amount(self, frame: np.ndarray, box: BoundingBox) -> Optional[float]:
        text = self._ocr.read_text(crop_region(frame, box))
        return _parse_amount(text)

    def _read_opponents(self, frame: np.ndarray, regions: Sequence[BoundingBox]) -> list[PlayerSnapshot]:
        opponents: list[PlayerSnapshot] = []
        for index, box in enumerate(regions, start=1):
            amount = self._read_amount(frame, box)
            opponents.append(PlayerSnapshot(name=f"Villain {index}", stack=amount))
        return opponents


def _parse_amount(text: str) -> Optional[float]:
    clean = text.replace("$", "").replace(",", "").strip()
    if not clean:
        return None
    try:
        return float(clean)
    except ValueError:
        return None


def build_screen_capture(config: AssistantConfig) -> ScreenCapture:
    return ScreenCapture(config.capture)


def build_file_capture(config: AssistantConfig, paths: Iterable[str]) -> FileCapture:
    return FileCapture(Path(path) for path in paths)


def _require_numpy() -> None:
    if np is None:
        raise RuntimeError("NumPy is required to run the frame interpreter")
