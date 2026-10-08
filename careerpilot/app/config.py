import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "")
REED_API_KEY = os.getenv("REED_API_KEY", "")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///careerpilot.db")
SCAN_MINUTES = int(os.getenv("SCAN_MINUTES", "15"))
LIVE_SOURCES = bool((ADZUNA_APP_ID and ADZUNA_APP_KEY) or REED_API_KEY)
