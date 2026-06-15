import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

USER_NAME         = os.getenv("USER_NAME", "Falah")
USER_EMAIL        = os.getenv("USER_EMAIL", "falahalzeyoudi55@gmail.com")

GROQ_API_KEY      = os.getenv("GROQ_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")

VOICE_RECORD_SECONDS = int(os.getenv("VOICE_RECORD_SECONDS", "30"))
BRIEFING_TIME  = os.getenv("BRIEFING_TIME", "08:00")
WRAPUP_TIME    = os.getenv("WRAPUP_TIME", "18:00")
TIMEZONE       = os.getenv("TIMEZONE", "Asia/Dubai")

GOOGLE_CREDENTIALS_FILE = BASE_DIR / "credentials.json"
GOOGLE_TOKEN_FILE       = BASE_DIR / "token.json"
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
]

MEMORY_FILE = BASE_DIR / "mada_memory.json"
HISTORY_FILE = BASE_DIR / "mada_history.json"

GROQ_MODEL   = "mixtral-8x7b-32768"
