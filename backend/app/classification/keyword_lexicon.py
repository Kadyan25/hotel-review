"""Phrase lexicon for keyword-based topic classification.

Each topic maps to phrases/words that, if found in a review snippet,
indicate that topic is being discussed. Sentiment isn't encoded here --
it comes from which field (positive_text vs negative_text) the match was
found in, per architecture.md "Insight Classification Methodology".

Deliberately plain Python data, not a database table -- it's small, static,
and versioned with the code that uses it.
"""

LEXICON: dict[str, list[str]] = {
    "cleanliness": [
        "clean", "dirty", "dust", "dusty", "grime", "grimy", "stain", "stained",
        "hygiene", "hygienic", "unhygienic", "smell", "smelly", "odor", "odour",
        "mold", "mould", "sanit", "spotless", "filthy", "messy", "tidy",
    ],
    "checkin_experience": [
        "check-in", "check in", "checkin", "check-out", "check out", "checkout",
        "reception desk", "front desk", "arrival", "early check", "late check",
        "waited to check", "queue", "lobby wait",
    ],
    "staff_behaviour": [
        "staff", "receptionist", "reception staff", "manager", "employee",
        "customer service", "helpful", "unhelpful", "rude", "friendly",
        "welcoming", "attentive", "unprofessional", "professional", "service was",
    ],
    "noise": [
        "noise", "noisy", "loud", "quiet", "silence", "soundproof", "traffic noise",
        "street noise", "party noise", "could hear", "thin walls", "banging",
    ],
    "facilities": [
        "wifi", "wi-fi", "internet", "pool", "gym", "elevator", "lift", "parking",
        "breakfast", "kitchen", "amenities", "facilities", "air conditioning",
        "aircon", "a/c", "heating", "laundry", "tv", "hot water",
    ],
    "location": [
        "location", "located", "walk to", "walking distance", "close to",
        "near the", "nearby", "central", "convenient", "far from", "transport",
        "train station", "airport", "neighbourhood", "neighborhood",
    ],
    "room_condition": [
        "room was", "bed was", "mattress", "furniture", "outdated", "run down",
        "run-down", "renovat", "worn out", "broken", "damaged", "old fashioned",
        "old-fashioned", "shabby", "small room", "tiny room", "spacious",
    ],
    "value_for_money": [
        "value for money", "worth the price", "overpriced", "expensive",
        "cheap", "good price", "price for", "worth it", "not worth", "budget",
        "affordable", "rip off", "rip-off",
    ],
}

TOPICS_WITH_OTHER = [*LEXICON.keys(), "other"]
