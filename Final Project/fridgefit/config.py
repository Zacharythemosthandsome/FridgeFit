"""Shared configuration for the FridgeFit application."""

from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
USERS_DB_FILE = APP_DIR / "users.json"
DEFAULT_USERS = {"admin": "123"}

HEALTH_EXPORT_TAGS = ("Record", "Workout", "ActivitySummary")

DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_MODEL = "deepseek-chat"
DEEPSEEK_SYSTEM_PROMPT = "You are a helpful and professional health assistant."
