"""Configuration models for the Ignition poker assistant prototype."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None  # type: ignore

import json


@dataclass(frozen=True)
class BoundingBox:
    """Simple representation of a rectangular capture region."""

    top: int
    left: int
    width: int
    height: int

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @property
    def right(self) -> int:
        return self.left + self.width

    def to_mss_monitor(self) -> Dict[str, int]:
        """Return the dictionary representation expected by :mod:`mss`."""

        return {
            "top": int(self.top),
            "left": int(self.left),
            "width": int(self.width),
            "height": int(self.height),
        }


@dataclass
class RegionConfig:
    """Collection of regions that should be extracted from the poker table."""

    hero_cards: List[BoundingBox] = field(default_factory=list)
    community_cards: List[BoundingBox] = field(default_factory=list)
    pot: Optional[BoundingBox] = None
    hero_stack: Optional[BoundingBox] = None
    opponent_stacks: List[BoundingBox] = field(default_factory=list)


@dataclass
class CaptureConfig:
    """Options controlling screen capture frequency and bounding boxes."""

    table_region: BoundingBox
    capture_interval_ms: int = 500


@dataclass
class AssistantConfig:
    """Top-level configuration for the prototype assistant."""

    capture: CaptureConfig
    regions: RegionConfig
    table_name: str = "Unknown"

    @staticmethod
    def from_mapping(data: Mapping[str, object]) -> "AssistantConfig":
        """Create an :class:`AssistantConfig` from a nested mapping."""

        def parse_box(raw: Mapping[str, object]) -> BoundingBox:
            return BoundingBox(
                top=int(raw["top"]),
                left=int(raw["left"]),
                width=int(raw["width"]),
                height=int(raw["height"]),
            )

        capture_mapping = data["capture"]  # type: ignore[index]
        capture = CaptureConfig(
            table_region=parse_box(capture_mapping["table_region"])  # type: ignore[index]
        )
        if "capture_interval_ms" in capture_mapping:
            capture.capture_interval_ms = int(capture_mapping["capture_interval_ms"])  # type: ignore[index]

        region_mapping = data["regions"]  # type: ignore[index]
        regions = RegionConfig()

        def parse_boxes(values: Iterable[Mapping[str, object]]) -> List[BoundingBox]:
            return [parse_box(raw) for raw in values]

        if "hero_cards" in region_mapping:
            regions.hero_cards = parse_boxes(region_mapping["hero_cards"])  # type: ignore[index]
        if "community_cards" in region_mapping:
            regions.community_cards = parse_boxes(region_mapping["community_cards"])  # type: ignore[index]
        if "opponent_stacks" in region_mapping:
            regions.opponent_stacks = parse_boxes(region_mapping["opponent_stacks"])  # type: ignore[index]
        if "pot" in region_mapping and region_mapping["pot"]:
            regions.pot = parse_box(region_mapping["pot"])  # type: ignore[index]
        if "hero_stack" in region_mapping and region_mapping["hero_stack"]:
            regions.hero_stack = parse_box(region_mapping["hero_stack"])  # type: ignore[index]

        table_name = str(data.get("table_name", "Unknown"))
        return AssistantConfig(capture=capture, regions=regions, table_name=table_name)


def load_config(path: Path | str) -> AssistantConfig:
    """Load an :class:`AssistantConfig` from ``path``.

    The loader supports both YAML (if :mod:`pyyaml` is installed) and JSON
    configuration files.  YAML support is optional in order to keep the
    prototype easy to run in restricted environments.
    """

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(config_path)

    raw_text = config_path.read_text(encoding="utf8")
    data: MutableMapping[str, object]
    if config_path.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("pyyaml is required to parse YAML configuration files")
        data = yaml.safe_load(raw_text)
    else:
        data = json.loads(raw_text)

    if not isinstance(data, MutableMapping):  # pragma: no cover - sanity check
        raise TypeError("Configuration root must be a mapping")

    return AssistantConfig.from_mapping(data)
