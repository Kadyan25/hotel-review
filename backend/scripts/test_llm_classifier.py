"""Manual verification tool for the Claude Haiku classification path.

Usage: python scripts/test_llm_classifier.py

Not part of the normal pipeline -- run by hand to confirm the Anthropic
key/model/prompt actually work before Phase 6 wires this into the pipeline
for real. Bypasses ENABLE_LLM_CLASSIFICATION on purpose (this IS the
deliberate test call), single snippet, well under the per-run cap.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.classification.llm_client import classify_snippet_with_llm
from app.config import get_settings

# A real non-English negative review from the scraped dataset -- a good test
# case precisely because our English-only keyword lexicon would miss most of
# this, which is the actual reason the LLM fallback exists.
SAMPLE_TEXT = (
    "le foto che si vedono su booking non sono assolutamente vere ma neanche "
    "lontanamente soprattutto quelle delle camere, io e la mia fidanzata abbiamo "
    "preso una camera privata, ed era orribile, vecchia che cascava a pezzi, "
    "sporca e dir poco, con gomme appiccicate al muro del letto dove dormi, "
    "mozziconi di sigarette per la stanza, la pulizia della struttura era "
    "inesistente, la cucina era sporchissima compresa la sala pranzo, piena di "
    "capelli per giorni, macchie sui tavoli e sul muro h24"
)


async def main() -> None:
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise SystemExit("ANTHROPIC_API_KEY not set in backend/.env -- nothing to test")

    test_settings = settings.model_copy(update={"enable_llm_classification": True})

    result = await classify_snippet_with_llm(SAMPLE_TEXT, test_settings)
    print("--- classification result ---")
    print(result)


asyncio.run(main())
