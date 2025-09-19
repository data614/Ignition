import pytest

from ignition.cards import CardParsingError, canonicalize_hand, parse_cards


def test_parse_cards_valid():
    cards = parse_cards("AsKd")
    assert len(cards) == 2
    assert str(cards[0]) == "AS"
    assert str(cards[1]) == "KD"


def test_parse_cards_raises_on_duplicates():
    with pytest.raises(CardParsingError):
        parse_cards("AsAs")


def test_canonicalize_hand_pairs_and_suited():
    pocket = parse_cards("AhAd")
    suited = parse_cards("AsKs")
    offsuit = parse_cards("AdKc")

    assert canonicalize_hand(pocket) == "AA"
    assert canonicalize_hand(suited) == "AKs"
    assert canonicalize_hand(offsuit) == "AKo"
