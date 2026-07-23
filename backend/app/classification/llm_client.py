import json

from anthropic import AsyncAnthropic

from app.classification.topics import TOPICS
from app.config import Settings

MODEL = "claude-haiku-4-5-20251001"

_SYSTEM_PROMPT = (
    "You classify a hotel guest review snippet into operational topics for a hotel "
    f"operations dashboard. Valid topics: {', '.join(TOPICS)}. "
    "Reply with ONLY a JSON array of objects: "
    '[{"topic": "...", "sentiment": "positive"|"negative", "confidence": 0.0-1.0}]. '
    "Return an empty array [] if no topic clearly applies. No prose, no markdown fences."
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

    raw = "".join(block.text for block in response.content if block.type == "text")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return []

    return [item for item in parsed if isinstance(item, dict) and item.get("topic") in TOPICS]
