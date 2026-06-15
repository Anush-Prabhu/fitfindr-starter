"""
Unit tests for FitFindr tools (LLM calls mocked).
"""

import tools
from tools import (
    create_fit_card,
    estimate_price_fairness,
    search_listings,
    suggest_outfit,
)
from utils.data_loader import load_listings


class _Msg:
    def __init__(self, text):
        self.content = text


class _Choice:
    def __init__(self, text):
        self.message = _Msg(text)


class _Resp:
    def __init__(self, text):
        self.choices = [_Choice(text)]


class _Completions:
    def __init__(self, recorder):
        self._recorder = recorder

    def create(self, **kwargs):
        self._recorder["kwargs"] = kwargs
        return _Resp("mock stylist reply")


class _Chat:
    def __init__(self, recorder):
        self.completions = _Completions(recorder)


class _FakeGroq:
    def __init__(self, recorder):
        self.chat = _Chat(recorder)


def _mock_llm(monkeypatch):
    recorder = {}
    monkeypatch.setattr(tools, "_groq_client", lambda: _FakeGroq(recorder))
    return recorder


SAMPLE_ITEM = {
    "id": "lst_006",
    "title": "Graphic Tee — 2003 Tour Bootleg Style",
    "category": "tops",
    "colors": ["black"],
    "style_tags": ["graphic tee", "vintage", "streetwear"],
    "size": "L",
    "price": 24.0,
    "platform": "depop",
    "condition": "good",
    "brand": None,
}


# search_listings

def test_search_finds_graphic_tees():
    hits = search_listings("vintage graphic tee", size=None, max_price=50)
    assert hits
    assert all(isinstance(row, dict) for row in hits)


def test_search_no_matches_returns_empty_list():
    assert search_listings("designer ballgown", size="XXS", max_price=5) == []


def test_search_respects_max_price():
    hits = search_listings("jacket", size=None, max_price=10)
    assert all(row["price"] <= 10 for row in hits)


def test_search_size_filter():
    hits = search_listings("tee", size="M", max_price=50)
    for row in hits:
        assert "m" in row["size"].lower()


# suggest_outfit

def test_suggest_with_wardrobe(monkeypatch):
    _mock_llm(monkeypatch)
    wardrobe = {
        "items": [
            {
                "name": "Baggy jeans",
                "category": "bottoms",
                "colors": ["blue"],
                "style_tags": ["denim"],
            }
        ]
    }
    text = suggest_outfit(SAMPLE_ITEM, wardrobe)
    assert text.strip()


def test_suggest_empty_wardrobe(monkeypatch):
    recorder = _mock_llm(monkeypatch)
    text = suggest_outfit(SAMPLE_ITEM, {"items": []})
    assert text.strip()
    prompt = recorder["kwargs"]["messages"][-1]["content"].lower()
    assert "no saved" in prompt or "generic" in prompt


# create_fit_card

def test_fit_card_happy_path(monkeypatch):
    _mock_llm(monkeypatch)
    card = create_fit_card("Jeans and sneakers.", SAMPLE_ITEM)
    assert card.strip()


def test_fit_card_empty_outfit():
    msg = create_fit_card("", SAMPLE_ITEM)
    assert "outfit" in msg.lower()
    assert "caption" in msg.lower() or "fit card" in msg.lower()


def test_fit_card_whitespace_only():
    msg = create_fit_card("   ", SAMPLE_ITEM)
    assert isinstance(msg, str) and msg


# estimate_price_fairness

def _top_at(price: float) -> dict:
    return next(l for l in load_listings() if l["category"] == "tops" and l["price"] == price)


def test_price_verdicts():
    assert estimate_price_fairness(_top_at(15.0))["verdict"] == "great_deal"
    assert estimate_price_fairness(_top_at(35.0))["verdict"] == "overpriced"
    assert estimate_price_fairness(_top_at(21.0))["verdict"] == "fair"


def test_price_unknown_category():
    fake = {"id": "x", "category": "__none__", "style_tags": [], "price": 99.0}
    out = estimate_price_fairness(fake)
    assert out["verdict"] == "unknown"
    assert out["median_comparable"] is None
