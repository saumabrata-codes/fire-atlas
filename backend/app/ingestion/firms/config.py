
import os

from pathlib import Path
from dotenv import load_dotenv


# Load backend/.env
load_dotenv(Path(__file__).resolve().parents[3] / ".env")


def get_firms_api_key() -> str:
    api_key = os.getenv("NASA_FIRMS_API_KEY", "").strip()

    if not api_key:
        raise ValueError(
            "NASA_FIRMS_API_KEY is missing from environment."
        )

    return api_key
