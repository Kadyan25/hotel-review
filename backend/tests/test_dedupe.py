from app.scraper.dedupe import compute_external_review_id


def test_same_inputs_produce_same_hash():
    a = compute_external_review_id("Georgie", "2026-07-01", "Great location", "Bit noisy")
    b = compute_external_review_id("Georgie", "2026-07-01", "Great location", "Bit noisy")
    assert a == b


def test_different_inputs_produce_different_hash():
    a = compute_external_review_id("Georgie", "2026-07-01", "Great location", "Bit noisy")
    b = compute_external_review_id("Georgie", "2026-07-02", "Great location", "Bit noisy")
    assert a != b


def test_missing_fields_are_stable_not_crashing():
    result = compute_external_review_id(None, None, None, None)
    assert isinstance(result, str)
    assert len(result) == 32


def test_hash_length():
    result = compute_external_review_id("A", "2026-01-01", "x", "y")
    assert len(result) == 32
