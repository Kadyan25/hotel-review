from app.classification.keyword_classifier import classify_review_keyword, has_any_match


def test_classifies_negative_cleanliness():
    results = classify_review_keyword(None, "The room was dirty and smelly")
    topics = {r["topic"] for r in results}
    assert "cleanliness" in topics
    assert all(r["sentiment"] == "negative" for r in results if r["topic"] == "cleanliness")


def test_classifies_positive_and_negative_independently():
    results = classify_review_keyword("Staff were very friendly", "But the room was noisy")
    by_topic = {(r["topic"], r["sentiment"]) for r in results}
    assert ("staff_behaviour", "positive") in by_topic
    assert ("noise", "negative") in by_topic


def test_multiple_topics_in_one_snippet():
    results = classify_review_keyword(None, "Dirty room, rude staff, overpriced for what it was")
    topics = {r["topic"] for r in results}
    assert {"cleanliness", "staff_behaviour", "value_for_money"}.issubset(topics)


def test_no_match_returns_empty():
    results = classify_review_keyword("xyz abc", "qwerty")
    assert results == []


def test_has_any_match_true_when_keyword_present():
    assert has_any_match(None, "The bed was broken") is True


def test_has_any_match_false_for_ambiguous_text():
    assert has_any_match("Everything was wonderful and memorable", None) is False


def test_has_any_match_false_for_empty():
    assert has_any_match(None, None) is False
