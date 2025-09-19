"""Ignition poker assistant prototype package."""

from .capture import FileCapture, ScreenCapture
from .config import AssistantConfig, BoundingBox, CaptureConfig, RegionConfig, load_config
from .decision import Decision, RuleBasedDecisionEngine
from .detection import CardTemplateLibrary, TemplateMatchResult
from .ocr import OcrEngine, OcrOptions
from .pipeline import ExtractionResult, FrameInterpreter
from .state import PlayerSnapshot, TableSnapshot

__all__ = [
    "AssistantConfig",
    "BoundingBox",
    "CaptureConfig",
    "RegionConfig",
    "load_config",
    "ScreenCapture",
    "FileCapture",
    "CardTemplateLibrary",
    "TemplateMatchResult",
    "OcrEngine",
    "OcrOptions",
    "RuleBasedDecisionEngine",
    "Decision",
    "FrameInterpreter",
    "ExtractionResult",
    "TableSnapshot",
    "PlayerSnapshot",
]
