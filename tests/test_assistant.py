import pytest

from ignition.poker_assistant import PokerAssistant


def test_assistant_preflop_facade():
    assistant = PokerAssistant()
    result = assistant.recommend_preflop(position="CO", hero_hand="AsKd", stack_bb=100)
    assert result.stage == "preflop"
    assert result.action == "raise"
    assert result.metadata["position"] == "CO"


def test_assistant_postflop_invalid_board_raises():
    assistant = PokerAssistant()
    with pytest.raises(ValueError):
        assistant.recommend_postflop(
            stage="flop",
            hero_hand="AsKd",
            board_cards="AdKh",
            pot_size=6,
            stack_bb=100,
        )
