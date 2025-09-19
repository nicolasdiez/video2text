# src/config.py
import os
from dotenv import load_dotenv

# Cargar .env solo en local (en Azure no será necesario porque las variables ya estarán en el entorno)
load_dotenv()

# --- API Keys ---
YOUTUBE_API_KEY             = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY              = os.getenv("OPENAI_API_KEY")
TWITTER_API_KEY             = os.getenv("X_API_KEY")
TWITTER_API_SECRET          = os.getenv("X_API_SECRET")
TWITTER_ACCESS_TOKEN        = os.getenv("X_API_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("X_API_ACCESS_TOKEN_SECRET")
TWITTER_BEARER_TOKEN        = os.getenv("X_API_BEARER_TOKEN")

# --- Validaciones opcionales ---
required_vars = {
    "YOUTUBE_API_KEY": YOUTUBE_API_KEY,
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "X_API_KEY": TWITTER_API_KEY,
    "X_API_SECRET": TWITTER_API_SECRET,
    "X_API_ACCESS_TOKEN": TWITTER_ACCESS_TOKEN,
    "X_API_ACCESS_TOKEN_SECRET": TWITTER_ACCESS_TOKEN_SECRET,
    "X_API_BEARER_TOKEN": TWITTER_BEARER_TOKEN,
}

missing = [k for k, v in required_vars.items() if not v]
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

