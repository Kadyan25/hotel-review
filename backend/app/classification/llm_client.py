import json

from anthropic import AsyncAnthropic

from app.classification.topics import TOPICS
from app.config import Settings

MODEL = "claude-haiku-4-5-20251001"

# Topic definitions given to the model, not just bare slugs -- an LLM asked
# to pick from a list of unexplained enum values (e.g. "checkin_experience")
# tends to guess at scope and over- or under-tag. Definitions come straight
# from the trial brief's own topic list so classification stays aligned
# with what operations staff actually asked to track.
_TOPIC_DEFINITIONS = {
    "cleanliness": "room, bathroom, or common-area cleanliness, dust, stains, smells, hygiene",
    "checkin_experience": "check-in/check-out process itself: waiting, queueing, arrival/departure logistics",
    "staff_behaviour": "how staff or reception treated the guest: helpfulness, rudeness, friendliness, professionalism",
    "noise": "sound disturbance from any source: street, neighbours, thin walls, building noise",
    "facilities": "wifi, breakfast, pool, gym, parking, elevator, aircon, amenities -- not the room itself",
    "location": "the property's position: proximity to transport, attractions, neighbourhood character",
    "room_condition": "physical state of the room/furniture/bed: outdated, broken, worn, damaged, size",
    "value_for_money": "whether the price paid matched what was received",
}

_SYSTEM_PROMPT = (
    "You are analysing a guest review snippet from a hotel operations dashboard used by "
    "non-technical hotel staff to spot recurring operational issues.\n\n"
    "Topics you may tag, each with its scope:\n"
    + "\n".join(f"- {topic}: {desc}" for topic, desc in _TOPIC_DEFINITIONS.items())
    + "\n\nRules:\n"
    "1. Tag a topic only if the text gives clear, specific evidence for it -- generic praise or "
    'complaint ("great stay", "would not recommend") with no specific subject is not evidence.\n'
    "2. A snippet may reasonably match zero, one, or several topics. Do not force a match.\n"
    "3. sentiment reflects the tone of that specific mention, not the review as a whole.\n"
    "4. confidence is 0.0-1.0: use lower values (<0.6) for implied/indirect mentions, higher "
    "(>0.8) only when the topic is explicitly and unambiguously named.\n\n"
    "Reply with ONLY a JSON array, no prose, no markdown fences: "
    '[{"topic": "...", "sentiment": "positive"|"negative", "confidence": 0.0-1.0}]. '
    "Return [] if nothing clearly applies."
)


async def classify_snippet_with_llm(text: str, settings: Settings) -> list[dict] | None:
    """Classify a single review snippet (liked/disliked text) via Claude Haiku.

    Returns None if the LLM path isn't configured/enabled — callers should
    treat that as "fall back to keyword-only", never as an error.
    """
    if not settings.llm_configured or not text.strip():
        return None

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=MODEL,
        max_tokens=300,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text[:2000]}],
    )

    raw = "".join(block.text for block in response.content if block.type == "text").strip()
    # Claude sometimes wraps the response in ```json ... ``` fences despite
    # the system prompt explicitly saying not to -- confirmed by live testing
    # this isn't rare (happened on the very first real test). Defensive
    # stripping here, not just a prompt instruction, since silently treating
    # a fenced response as "no topics found" would be a real accuracy bug.
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []

    return [item for item in parsed if isinstance(item, dict) and item.get("topic") in TOPICS]


_BRIEFING_SYSTEM_PROMPT = (
    "You write a short internal briefing for hotel operations managers, grounded only in the "
    "aggregated topic counts and guest quotes given below -- never invent a detail, number, or "
    "specific that isn't present in the provided data.\n\n"
    "Write 2-4 plain-text sentences: name the most significant recurring issue (or note that "
    "sentiment is broadly positive if nothing stands out), then suggest one concrete, actionable "
    "step operations staff could take in response. No headers, no markdown, no bullet points, no "
    "surrounding quotation marks -- plain prose only."
)


async def generate_manager_briefing(
    topic_counts: list[tuple[str, int]], quotes: list[str], settings: Settings
) -> str | None:
    """Synthesis, not classification -- the one thing an LLM can do here that
    keyword matching structurally can't: read across several reviews and
    suggest a concrete next step, not just count topic mentions again.
    """
    if not settings.llm_configured or (not topic_counts and not quotes):
        return None

    counts_text = "\n".join(f"- {topic}: {count} negative mention(s)" for topic, count in topic_counts) or (
        "(no tagged negative topics)"
    )
    quotes_text = "\n".join(f'- "{q}"' for q in quotes) or "(no sample quotes available)"
    user_content = (
        f"Negative topic counts (current period):\n{counts_text}\n\n"
        f"Sample recent negative review excerpts:\n{quotes_text}"
    )

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model=MODEL,
        max_tokens=200,
        system=_BRIEFING_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )
    text = "".join(block.text for block in response.content if block.type == "text").strip()
    return text or None
