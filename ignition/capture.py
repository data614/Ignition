"""Screen capture helpers for the Ignition poker assistant prototype."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

import time

try:
    import mss  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    mss = None  # type: ignore

try:
    from PIL import Image
except Exception:  # pragma: no cover - optional dependency
    Image = None  # type: ignore

try:
    import numpy as np
except Exception:  # pragma: no cover - optional dependency
    np = None  # type: ignore

from .config import CaptureConfig


def _require_pillow() -> None:
    if Image is None:
        raise RuntimeError("Pillow is required to run the prototype")


def _require_numpy() -> None:
    if np is None:
        raise RuntimeError("NumPy is required to run the prototype")


class ScreenCapture:
    """Capture frames from a live poker table window using :mod:`mss`."""

    def __init__(self, capture_config: CaptureConfig):
        _require_pillow()
        _require_numpy()
        if mss is None:
            raise RuntimeError(
                "mss is not installed. Install it with `pip install mss` to enable screen capture."
            )
        self._capture_config = capture_config
        self._monitor = capture_config.table_region.to_mss_monitor()
        self._sct = mss.mss()  # type: ignore[call-arg]

    def grab(self) -> np.ndarray:
        """Capture a single frame and return it as a NumPy array."""

        frame = self._sct.grab(self._monitor)
        # mss returns BGRA data; Pillow understands raw bytes and converts to RGB
        image = Image.frombytes("RGB", frame.size, frame.rgb)
        return np.array(image)

    def loop(self) -> Iterator[np.ndarray]:
        """Continuously capture frames at the configured interval."""

        interval_s = self._capture_config.capture_interval_ms / 1000.0
        while True:
            start = time.perf_counter()
            yield self.grab()
            elapsed = time.perf_counter() - start
            delay = max(0.0, interval_s - elapsed)
            if delay:
                time.sleep(delay)


@dataclass
class FileCapture:
    """Utility used for offline development with recorded screenshots."""

    image_paths: Iterable[Path]

    def __post_init__(self) -> None:
        _require_pillow()
        _require_numpy()
        self._paths = [Path(path) for path in self.image_paths]
        if not self._paths:
            raise ValueError("FileCapture requires at least one image path")

    def loop(self) -> Iterator[np.ndarray]:
        for path in self._paths:
            image = Image.open(path).convert("RGB")
            yield np.array(image)

    def grab(self) -> np.ndarray:
        path = self._paths[0]
        return np.array(Image.open(path).convert("RGB"))
