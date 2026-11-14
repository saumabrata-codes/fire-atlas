import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[4]

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(ENV_FILE)


def get_firms_api_key() -> str:
    """
    Retrieve NASA FIRMS API key securely.
    """

    api_key = os.getenv("NASA_FIRMS_API_KEY")

    if not api_key or not api_key.strip():
        raise ValueError(
            "NASA_FIRMS_API_KEY is missing. "
            "Check your project .env file."
        )

    return api_key.strip()