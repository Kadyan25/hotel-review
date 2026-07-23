import hashlib


def compute_external_review_id(
    reviewer_name: str | None,
    review_date_iso: str | None,
    positive_text: str | None,
    negative_text: str | None,
) -> str:
    """Booking.com exposes no review ID anywhere in the DOM (confirmed by
    live inspection, see architecture.md) -- this hash is the only option
    for a dedup key, not a fallback for an edge case.
    """
    parts = [reviewer_name or "", review_date_iso or "", positive_text or "", negative_text or ""]
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return digest[:32]
