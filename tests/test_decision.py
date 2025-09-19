"""Unit tests for the rule-based decision engine."""
from ignition.decision import RuleBasedDecisionEngine, canonical_hand
from ignition.state import TableSnapshot


def test_canonical_hand_suited_and_offsuit():
    assert canonical_hand("K♠", "8♦") == "K8O"
    assert canonical_hand("A♠", "K♠") == "AKS"
    assert canonical_hand("Ad", "Ac") == "AA"
    assert canonical_hand("10h", "Js") == "JTO"


def test_rule_engine_open_raise():
    engine = RuleBasedDecisionEngine()
    snapshot = TableSnapshot(table_name="Test", hero_cards=["A♠", "K♠"], hero_stack=40)
    decision = engine.recommend(snapshot, hero_position="MP")
    assert decision.action == "Raise"
    assert decision.confidence > 0.5


def test_rule_engine_short_stack_shove():
    engine = RuleBasedDecisionEngine()
    snapshot = TableSnapshot(table_name="Test", hero_cards=["A♠", "K♠"], hero_stack=10)
    decision = engine.recommend(snapshot, hero_position="BTN")
    assert decision.action == "Shove"


def test_rule_engine_fold_unknown_hand():
    engine = RuleBasedDecisionEngine()
    snapshot = TableSnapshot(table_name="Test", hero_cards=["2♣", "7♦"], hero_stack=40)
    decision = engine.recommend(snapshot, hero_position="EP")
    assert decision.action == "Fold"
