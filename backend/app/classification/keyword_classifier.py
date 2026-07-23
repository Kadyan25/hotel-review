"""Keyword-based topic classification -- the default, always-on path.

Deterministic and free: a phrase match is a match, there's no graded
certainty to compute, so every keyword match gets the same flat confidence
rather than inventing a fake precision score.
"""

from app.classification.keyword_lexicon import LEXICON

KEYWORD_CONFIDENCE = 0.75


def _matched_topics(text: str) -> list[str]:
    lowered = text.lower()
    return [topic for topic, phrases in LEXICON.items() if any(phrase in lowered for phrase in phrases)]


def classify_review_keyword(positive_text: str | None, negative_text: str | None) -> list[dict]:
    """Matches positive_text / negative_text independently -- sentiment
    comes from which field matched, not from the phrase itself (see
    architecture.md "Insight Classification Methodology").
    """
    results: list[dict] = []

    if positive_text:
        for topic in _matched_topics(positive_text):
            results.append({"topic": topic, "sentiment": "positive", "confidence": KEYWORD_CONFIDENCE, "source": "keyword"})

    if negative_text:
        for topic in _matched_topics(negative_text):
            results.append({"topic": topic, "sentiment": "negative", "confidence": KEYWORD_CONFIDENCE, "source": "keyword"})

    return results


def has_any_match(positive_text: str | None, negative_text: str | None) -> bool:
    """Used to decide whether a review is a candidate for the LLM fallback --
    "ambiguous" means the keyword pass found nothing on non-trivial text."""
    return bool(classify_review_keyword(positive_text, negative_text))
