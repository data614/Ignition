"""OCR utilities used to read numeric values from the poker table."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None  # type: ignore

try:
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    Image = None  # type: ignore

try:
    import pytesseract
except Exception:  # pragma: no cover - optional dependency
    pytesseract = None  # type: ignore


@dataclass
class OcrOptions:
    """Configuration for the OCR engine."""

    language: str = "eng"
    psm: int = 7  # Treat the image as a single text line.
    oem: int = 3  # Default OCR Engine Mode.
    threshold: Optional[int] = 180


class OcrEngine:
    """Thin wrapper around :mod:`pytesseract` with basic preprocessing."""

    def __init__(self, options: Optional[OcrOptions] = None):
        _require_numpy()
        _require_pillow()
        if pytesseract is None:
            raise RuntimeError(
                "pytesseract is not installed. Install it with `pip install pytesseract` to enable OCR."
            )
        self._options = options or OcrOptions()

    def read_text(self, image: np.ndarray) -> str:
        """Return the text detected in ``image``."""

        pil_image = Image.fromarray(image)
        if self._options.threshold is not None:
            pil_image = self._apply_threshold(pil_image, self._options.threshold)
        config = f"--psm {self._options.psm} --oem {self._options.oem}"
        return pytesseract.image_to_string(pil_image, lang=self._options.language, config=config).strip()

    @staticmethod
    def _apply_threshold(image: Image.Image, threshold: int) -> Image.Image:
        grayscale = image.convert("L")
        return grayscale.point(lambda p: 255 if p > threshold else 0, "1").convert("L")


def _require_numpy() -> None:
    if np is None:
        raise RuntimeError("NumPy is required to run the OCR module")


def _require_pillow() -> None:
    if Image is None:
        raise RuntimeError("Pillow is required to run the OCR module")
