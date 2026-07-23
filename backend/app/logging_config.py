import logging


def setup_logging() -> None:
    """Single place logging is configured -- imported once from main.py.
    Every module just does `logger = logging.getLogger(__name__)` and
    inherits this. See README "Logs" section for where output goes.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # Quiet the noisy ones -- uvicorn's access log already covers request lines.
    logging.getLogger("httpx").setLevel(logging.WARNING)
