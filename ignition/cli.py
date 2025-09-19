"""Command line interface for the Ignition poker study assistant."""
from __future__ import annotations

import argparse
from typing import Sequence

from .cards import CardParsingError, format_cards, parse_cards
from .postflop import Recommendation as PostflopRecommendation
from .postflop import recommend_postflop
from .range_engine import PreflopRecommendation, RangeEngine


def _parse_arguments(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ignition range coach CLI")
    parser.add_argument("--stage", choices=["preflop", "flop", "turn", "river"], required=True)
    parser.add_argument("--position", default="BTN", help="Hero position (UTG, HJ, CO, BTN, SB, BB)")
    parser.add_argument("--stack", type=float, default=100.0, help="Effective stack in big blinds")
    parser.add_argument("--pot", type=float, default=3.0, help="Current pot size in big blinds")
    parser.add_argument("--hand", required=True, help="Hero hole cards, e.g. 'AsKd'")
    parser.add_argument("--board", default="", help="Board cards, e.g. 'AhKdTs'")
    parser.add_argument(
        "--situation",
        default="open",
        choices=["open", "vs_raise", "vs_3bet"],
        help="Preflop situation: opening, facing a raise or facing a 3-bet",
    )
    return parser.parse_args(argv)


def _handle_preflop(args: argparse.Namespace) -> None:
    engine = RangeEngine()
    rec: PreflopRecommendation = engine.recommend(
        position=args.position,
        hero_hand=args.hand,
        stack_bb=args.stack,
        situation=args.situation,
    )
    print("=== Preflop Recommendation ===")
    print(f"Position: {rec.position} | Stack configuration: {rec.stack_key} | Situation: {rec.situation}")
    print(f"Suggested action: {rec.action.upper()}" + (f" ({rec.sizing})" if rec.sizing else ""))
    print(f"Equity vs charted range: {rec.equity_estimate:.2f}")
    print(rec.rationale)


def _validate_board(stage: str, board: Sequence[object]) -> None:
    expected = {"preflop": 0, "flop": 3, "turn": 4, "river": 5}[stage]
    if len(board) != expected:
        stage_name = stage.capitalize()
        raise ValueError(f"{stage_name} requires exactly {expected} board cards (got {len(board)}).")


def _handle_postflop(args: argparse.Namespace) -> None:
    try:
        hero_cards = parse_cards(args.hand)
        board_cards = parse_cards(args.board)
    except CardParsingError as exc:
        raise SystemExit(f"Failed to parse cards: {exc}") from exc

    _validate_board(args.stage, board_cards)
    rec: PostflopRecommendation = recommend_postflop(
        stage=args.stage,
        hero=hero_cards,
        board=board_cards,
        pot_size=args.pot,
        stack_size=args.stack,
    )
    print("=== Postflop Recommendation ===")
    print(f"Stage: {args.stage.capitalize()} | Hero: {format_cards(hero_cards)} | Board: {format_cards(board_cards)}")
    sizing_text = f" {rec.sizing}" if rec.sizing else ""
    print(f"Suggested action: {rec.action.upper()}{sizing_text}")
    print(f"Equity estimate vs top of range: {rec.equity_estimate:.2f}")
    print(rec.rationale)
    for key, value in rec.details.items():
        print(f"- {key.replace('_', ' ').capitalize()}: {value}")


def main(argv: Sequence[str] | None = None) -> None:
    args = _parse_arguments(argv)
    if args.stage == "preflop":
        _handle_preflop(args)
    else:
        _handle_postflop(args)


if __name__ == "__main__":
    main()
