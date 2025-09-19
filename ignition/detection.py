"""Object detection helpers (card recognition and template matching)."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None  # type: ignore

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    cv2 = None  # type: ignore


@dataclass
class TemplateMatchResult:
    label: str
    score: float


class CardTemplateLibrary:
    """Load and query template images for rank/suit recognition."""

    def __init__(self, template_dir: Path, threshold: float = 0.75):
        _require_numpy()
        if cv2 is None:
            raise RuntimeError(
                "opencv-python is not installed. Install it with `pip install opencv-python` to enable template matching."
            )
        self._threshold = threshold
        self._templates: Dict[str, "np.ndarray"] = {}
        self._load_templates(template_dir)

    def _load_templates(self, template_dir: Path) -> None:
        if not template_dir.exists():
            raise FileNotFoundError(f"Template directory not found: {template_dir}")
        for path in template_dir.glob("*.png"):
            label = path.stem.upper()
            image = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
            if image is None:
                continue
            self._templates[label] = image
        if not self._templates:
            raise RuntimeError(f"No PNG templates found in {template_dir}")

    def match_card(self, image: np.ndarray) -> Optional[TemplateMatchResult]:
        """Return the best matching template for ``image``."""

        if cv2 is None:  # pragma: no cover - handled in __init__, safeguard for linting
            return None
        if not self._templates:
            return None

        query = self._prepare(image)
        best_label: Optional[str] = None
        best_score = float("-inf")
        for label, template in self._templates.items():
            if query.shape[0] < template.shape[0] or query.shape[1] < template.shape[1]:
                continue
            result = cv2.matchTemplate(query, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(result)
            if max_val > best_score:
                best_label = label
                best_score = float(max_val)
        if best_label and best_score >= self._threshold:
            return TemplateMatchResult(label=best_label, score=best_score)
        return None

    @staticmethod
    def _prepare(image: np.ndarray) -> np.ndarray:
        if image.ndim == 3:
            return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        return image


from .config import BoundingBox


def crop_region(frame: "np.ndarray", box: BoundingBox) -> "np.ndarray":
    """Return a NumPy array representing ``box`` cropped from ``frame``."""

    return frame[box.top : box.bottom, box.left : box.right]


def _require_numpy() -> None:
    if np is None:
        raise RuntimeError("NumPy is required for card template matching")
