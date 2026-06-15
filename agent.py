"""
FitFindr planning loop — orchestrates tools and session state.
"""

import re

from tools import (
    create_fit_card,
    estimate_price_fairness,
    search_listings,
    suggest_outfit,
)


def _blank_session(query: str, wardrobe: dict) -> dict:
    return {
        "query": query,
        "parsed": {},
        "search_results": [],
        "selected_item": None,
        "price_assessment": None,
        "wardrobe": wardrobe,
        "outfit_suggestion": None,
        "fit_card": None,
        "error": None,
    }


_STANDALONE_SIZES = {"xxs", "xs", "xl", "xxl", "xxxl"}


def parse_user_query(text: str) -> dict:
    """Pull description, optional size, and max price from free text (regex)."""
    raw = text.strip()
    working = raw

    max_price = None
    price_pat = re.compile(
        r"(?:under|below|less than|max(?:imum)?|up to)\s*\$?\s*(\d+(?:\.\d+)?)"
        r"|\$\s*(\d+(?:\.\d+)?)",
        re.I,
    )
    if m := price_pat.search(working):
        max_price = float(m.group(1) or m.group(2))
        working = working[: m.start()] + " " + working[m.end() :]

    size = None
    explicit = re.search(r"\b(?:in\s+)?sizes?\s+([a-z0-9]+)\b", working, re.I)
    if explicit:
        size = explicit.group(1).upper()
        working = working[: explicit.start()] + " " + working[explicit.end() :]
    else:
        for token in _STANDALONE_SIZES:
            if re.search(rf"\b{token}\b", working, re.I):
                size = token.upper()
                working = re.sub(rf"\b{token}\b", " ", working, flags=re.I)
                break

    description = re.sub(
        r"\b(i'?m\s+)?(looking for|searching for|find me|show me|i want|i need)\b",
        " ",
        working,
        flags=re.I,
    )
    description = re.sub(r"\b(a|an|some)\b", " ", description, flags=re.I)
    description = re.sub(r"[.,;:!?]", " ", description)
    description = re.sub(r"\s+", " ", description).strip()

    return {"description": description, "size": size, "max_price": max_price}


def run_agent(query: str, wardrobe: dict) -> dict:
    """Execute the FitFindr pipeline for one user query."""
    session = _blank_session(query, wardrobe)
    session["parsed"] = parse_user_query(query)

    desc = session["parsed"]["description"]
    if not desc:
        session["error"] = (
            "I need a clearer item description — try something like "
            "'vintage graphic tee under $30, size M'."
        )
        return session

    session["search_results"] = search_listings(
        description=desc,
        size=session["parsed"]["size"],
        max_price=session["parsed"]["max_price"],
    )

    if not session["search_results"]:
        parts = [f"No listings matched '{desc}'"]
        if session["parsed"]["size"]:
            parts.append(f"in size {session['parsed']['size']}")
        if session["parsed"]["max_price"] is not None:
            parts.append(f"under ${session['parsed']['max_price']:g}")
        session["error"] = (
            " ".join(parts)
            + ". Try a higher budget, drop the size filter, or broaden the search."
        )
        return session

    session["selected_item"] = session["search_results"][0]
    session["price_assessment"] = estimate_price_fairness(session["selected_item"])

    session["outfit_suggestion"] = suggest_outfit(
        session["selected_item"], session["wardrobe"]
    )
    session["fit_card"] = create_fit_card(
        session["outfit_suggestion"], session["selected_item"]
    )
    return session


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path ===\n")
    ok = run_agent("vintage graphic tee under $30", get_example_wardrobe())
    if ok["error"]:
        print("Error:", ok["error"])
    else:
        print("Item:", ok["selected_item"]["title"])
        print("Outfit:", ok["outfit_suggestion"][:120], "...")
        print("Fit card:", ok["fit_card"][:120], "...")

    print("\n=== No results ===\n")
    miss = run_agent("designer ballgown size XXS under $5", get_example_wardrobe())
    print("Error:", miss["error"])
