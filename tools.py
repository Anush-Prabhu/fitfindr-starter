"""
FitFindr tools — each function is standalone and testable on its own.
"""

import os
import re
import statistics

from dotenv import load_dotenv
from groq import Groq

from utils.data_loader import load_listings

load_dotenv()

LLM_MODEL = "llama-3.3-70b-versatile"


def _groq_client() -> Groq:
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise ValueError("GROQ_API_KEY missing — add it to a .env file in the project root.")
    return Groq(api_key=key)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def _size_ok(requested: str | None, listing_size: str) -> bool:
    if requested is None:
        return True
    want = requested.strip().lower()
    have = {t.lower() for t in re.findall(r"[a-z0-9]+", listing_size)}
    return want in have


def _relevance_score(description: str, listing: dict) -> int:
    """Weighted keyword score — title and tags count more than body text."""
    terms = _tokenize(description)
    if not terms:
        return 0

    title_words = set(_tokenize(listing["title"]))
    tag_words = set(_tokenize(" ".join(listing["style_tags"])))
    body_words = set(_tokenize(listing["description"] + " " + listing["category"]))

    score = 0
    for term in terms:
        if term in title_words:
            score += 3
        if term in tag_words:
            score += 2
        if term in body_words:
            score += 1
    return score


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Filter mock listings by price/size, rank by keyword relevance.
    Returns [] when nothing matches — never raises.
    """
    matches: list[tuple[int, dict]] = []

    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if not _size_ok(size, listing["size"]):
            continue

        score = _relevance_score(description, listing)
        if score > 0:
            matches.append((score, listing))

    matches.sort(key=lambda pair: (-pair[0], pair[1]["price"]))
    return [listing for _, listing in matches]


def _wardrobe_summary(wardrobe: dict) -> str:
    lines = []
    for piece in wardrobe.get("items", []):
        colors = ", ".join(piece.get("colors", []))
        tags = ", ".join(piece.get("style_tags", []))
        note = piece.get("notes") or ""
        extra = f" — {note}" if note else ""
        lines.append(
            f"- {piece['name']} ({piece['category']}, {colors}; {tags}){extra}"
        )
    return "\n".join(lines) if lines else "(no saved pieces)"


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    LLM outfit ideas using wardrobe pieces, or general advice when wardrobe is empty.
    """
    client = _groq_client()
    item_line = (
        f"{new_item['title']} — {new_item['category']}, "
        f"${new_item['price']:g} on {new_item['platform']}, "
        f"colors: {', '.join(new_item['colors'])}, "
        f"tags: {', '.join(new_item['style_tags'])}"
    )

    items = wardrobe.get("items", [])
    if not items:
        user_prompt = (
            f"Thrift find:\n{item_line}\n\n"
            "The shopper has no saved wardrobe yet. Give 1–2 outfit ideas using "
            "generic staples (jeans, skirts, sneakers, boots, etc.) that would pair "
            "well with this item. Be specific about colors and vibe."
        )
    else:
        user_prompt = (
            f"Thrift find:\n{item_line}\n\n"
            f"Wardrobe:\n{_wardrobe_summary(wardrobe)}\n\n"
            "Suggest 1–2 outfits that combine the thrift find with named wardrobe "
            "pieces. Explain briefly why each combo works."
        )

    reply = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a friendly personal stylist who loves secondhand fashion.",
            },
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.75,
    )
    return reply.choices[0].message.content.strip()


def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Turn an outfit suggestion into a casual social caption.
    Returns an error string (not an exception) when outfit is missing.
    """
    if not outfit or not outfit.strip():
        return (
            "No outfit to caption yet — run outfit suggestions first, "
            "then I can draft a fit card."
        )

    client = _groq_client()
    title = new_item.get("title", "this find")
    price = new_item.get("price")
    platform = new_item.get("platform", "secondhand")
    price_text = f"${price:g}" if price is not None else "a steal"

    prompt = (
        "Write a 2–4 sentence OOTD caption for social media. Sound like a real "
        "person, not a product listing. Mention the item name, price, and platform "
        "once each. No hashtags or emoji.\n\n"
        f"Item: {title}\nPrice: {price_text}\nPlatform: {platform}\n"
        f"Outfit notes: {outfit}"
    )

    reply = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=1.1,
    )
    return reply.choices[0].message.content.strip()


def estimate_price_fairness(new_item: dict) -> dict:
    """
    Compare item price to similar listings in the dataset (no LLM).
    """
    category = new_item.get("category")
    item_id = new_item.get("id")
    item_price = float(new_item["price"])
    item_tags = set(new_item.get("style_tags", []))

    pool = [
        row
        for row in load_listings()
        if row.get("category") == category and row.get("id") != item_id
    ]
    tagged = [row for row in pool if item_tags & set(row.get("style_tags", []))]
    comparables = tagged if len(tagged) >= 3 else pool

    if len(comparables) < 3:
        return {
            "verdict": "unknown",
            "item_price": item_price,
            "median_comparable": None,
            "sample_size": len(comparables),
            "message": (
                f"Only {len(comparables)} similar listing(s) in the dataset — "
                f"can't judge whether ${item_price:g} is fair."
            ),
        }

    median = statistics.median(float(row["price"]) for row in comparables)
    ratio = item_price / median if median else 1.0

    if ratio <= 0.85:
        verdict, note = "great_deal", "below typical"
    elif ratio <= 1.15:
        verdict, note = "fair", "around typical"
    else:
        verdict, note = "overpriced", "above typical"

    return {
        "verdict": verdict,
        "item_price": item_price,
        "median_comparable": median,
        "sample_size": len(comparables),
        "message": (
            f"${item_price:g} is {note} for this category "
            f"(median ~${median:g} across {len(comparables)} listings)."
        ),
    }
