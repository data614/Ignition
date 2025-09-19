"""Command line entry-point for the Ignition poker assistant prototype."""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image

from ignition.config import AssistantConfig, load_config
from ignition.decision import RuleBasedDecisionEngine
from ignition.detection import CardTemplateLibrary
from ignition.ocr import OcrEngine
from ignition.pipeline import FrameInterpreter
from ignition.state import TableSnapshot


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ignition poker assistant prototype")
    parser.add_argument("--config", required=True, help="Path to the table configuration (YAML or JSON)")
    parser.add_argument("--templates", help="Directory containing 52 card template PNGs")
    parser.add_argument("--hero-position", default="MP", help="Hero position (e.g. UTG, HJ, CO)")
    parser.add_argument(
        "--screenshots",
        nargs="*",
        help="Offline mode: list of PNG screenshots that will be processed sequentially",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Enable live capture via mss. Without this flag the assistant runs in offline mode.",
    )
    return parser.parse_args(list(argv))


def load_templates(path: str | None) -> CardTemplateLibrary | None:
    if not path:
        return None
    directory = Path(path)
    if not directory.exists():
        raise FileNotFoundError(directory)
    return CardTemplateLibrary(directory)


def load_screenshot(path: str) -> np.ndarray:
    image = Image.open(path).convert("RGB")
    return np.array(image)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    config = load_config(args.config)

    card_library = load_templates(args.templates)
    interpreter = FrameInterpreter(
        config,
        card_library=card_library,
        ocr_engine=OcrEngine(),
        decision_engine=RuleBasedDecisionEngine(),
    )

    if args.live:
        return run_live_loop(interpreter, config, hero_position=args.hero_position)

    if not args.screenshots:
        print("No screenshots provided. Specify --live for real-time capture or provide PNG files.")
        return 1

    for path in args.screenshots:
        frame = load_screenshot(path)
        result = interpreter.process_frame(frame, hero_position=args.hero_position)
        print_json(result.snapshot)
        print(f"Decision: {result.decision.action} (confidence={result.decision.confidence:.2f})")
        print(f"Explanation: {result.decision.explanation}\n")
    return 0


def run_live_loop(interpreter: FrameInterpreter, config: AssistantConfig, hero_position: str) -> int:
    try:
        from ignition.capture import ScreenCapture
    except RuntimeError as exc:
        print(f"Screen capture unavailable: {exc}")
        return 1

    capture = ScreenCapture(config.capture)
    print("Starting live capture loop. Press Ctrl+C to stop.")
    try:
        for frame in capture.loop():
            result = interpreter.process_frame(frame, hero_position=hero_position)
            print_json(result.snapshot)
            print(f"Decision: {result.decision.action} (confidence={result.decision.confidence:.2f})")
            print(f"Explanation: {result.decision.explanation}\n")
    except KeyboardInterrupt:
        print("Stopping live capture loop.")
    return 0


def print_json(snapshot: TableSnapshot) -> None:
    print(json.dumps(snapshot.as_dict(), indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
