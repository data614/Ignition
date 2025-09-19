from ignition.cards import parse_cards
from ignition.postflop import recommend_postflop


def test_postflop_identifies_strong_made_hand():
    hero = parse_cards("AsKd")
    board = parse_cards("AdKhTc")
    rec = recommend_postflop(stage="flop", hero=hero, board=board, pot_size=9, stack_size=91)
    assert rec.action == "bet"
    assert rec.sizing == "66%"
    assert rec.details["hand_classification"] == "strong_made"


def test_postflop_detects_draw_and_prefers_betting():
    hero = parse_cards("9s8s")
    board = parse_cards("6s7s2d")
    rec = recommend_postflop(stage="flop", hero=hero, board=board, pot_size=6, stack_size=94)
    assert rec.details["hand_classification"] in {"combo_draw", "draw"}
    assert rec.action == "bet"
