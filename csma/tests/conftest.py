"""Pytest configuration — load .env before tests run."""

from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (csma/)
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_env_path, override=True)
