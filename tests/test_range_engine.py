import pytest

from ignition.range_engine import RangeEngine


def test_range_engine_recommends_raise_for_button_ak():
    engine = RangeEngine()
    rec = engine.recommend(position="BTN", hero_hand="AsKs", stack_bb=100, situation="open")
    assert rec.action == "raise"
    assert rec.sizing == "2.5bb"


def test_range_engine_defaults_to_fold_for_outside_range():
    engine = RangeEngine()
    rec = engine.recommend(position="UTG", hero_hand="7c2d", stack_bb=100, situation="open")
    assert rec.action == "fold"


def test_unknown_situation_raises():
    engine = RangeEngine()
    with pytest.raises(ValueError):
        engine.recommend(position="BTN", hero_hand="AsKs", stack_bb=100, situation="limp")
