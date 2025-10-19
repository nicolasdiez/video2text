# src/config.py

# env vars
import os
from dotenv import load_dotenv

# logging
import logging
import sys
from pythonjsonlogger import jsonlogger
from colorlog import ColoredFormatter


# ===== ENVIRONEMENT VARIABLES =====
# Cargar .env file solo en local (en Azure no será necesario porque las variables ya estarán en el entorno)
load_dotenv()

# --- API Keys ---
YOUTUBE_API_KEY             = os.getenv("YOUTUBE_API_KEY")
OPENAI_API_KEY              = os.getenv("OPENAI_API_KEY")
# credentials related to THE APPLICATION itself:
X_OAUTH1_API_KEY            = os.getenv("X_OAUTH1_API_KEY")             # OAuth 1.0 - Identifica mi aplicación frente a Twitter/X
X_OAUTH1_API_SECRET         = os.getenv("X_OAUTH1_API_SECRET")          # OAuth 1.0 - Identifica mi aplicación frente a Twitter/X
X_OAUTH2_API_BEARER_TOKEN   = os.getenv("X_OAUTH2_API_BEARER_TOKEN")    # OAuth 2.0 - Identifica mi aplicación frente a Twitter/X - se usa en OAuth 2.0 App-only (sin usuario, solo tu app). Sirve para llamadas que no requieren contexto de usuario (ej. buscar tweets públicos).
X_OAUTH2_CLIENT_ID          = os.getenv("X_OAUTH2_CLIENT_ID")           # OAuth 2.0 - Identifica mi aplicación frente a Twitter/X
X_OAUTH2_CLIENT_SECRET      = os.getenv("X_OAUTH2_CLIENT_SECRET")       # OAuth 2.0 - Identifica mi aplicación frente a Twitter/X --> se usa junto con el CLIENT_ID para intercambiar un authorization code por un access token
# credentials related to THE USER of the application:
X_OAUTH1_ACCESS_TOKEN               = os.getenv("X_OAUTH1_ACCESS_TOKEN")                # OAuth 1.0 - Permite actuar en nombre de un usuario frente a Twitter/X
X_OAUTH1_ACCESS_TOKEN_SECRET        = os.getenv("X_OAUTH1_ACCESS_TOKEN_SECRET")         # OAuth 1.0 - Permite actuar en nombre de un usuario frente a Twitter/X
X_OAUTH2_ACCESS_TOKEN               = os.getenv("X_OAUTH2_ACCESS_TOKEN")                # OAuth 2.0 - Permite actuar en nombre de un usuario frente a Twitter/X
X_OAUTH2_ACCESS_TOKEN_EXPIRES_AT    = os.getenv("X_OAUTH2_ACCESS_TOKEN_EXPIRES_AT")     # OAuth 2.0 - Permite actuar en nombre de un usuario frente a Twitter/X
X_OAUTH2_REFRESH_TOKEN              = os.getenv("X_OAUTH2_REFRESH_TOKEN")               # OAuth 2.0 - Permite actuar en nombre de un usuario frente a Twitter/X
X_OAUTH2_REFRESH_TOKEN_EXPIRES_AT   = os.getenv("X_OAUTH2_REFRESH_TOKEN_EXPIRES_AT")    # OAuth 2.0 - Permite actuar en nombre de un usuario frente a Twitter/X
X_SCREEN_NAME                       = os.getenv("X_SCREEN_NAME")                        # permite actuar en nombre de un usuario frente a Twitter/X
# credentials of the application used to retrieve youtube video transcripts
YOUTUBE_OAUTH_CLIENT_ID             = os.getenv("YOUTUBE_OAUTH_CLIENT_ID")              # OAuth 2.0 - Identifica mi aplicación frente a Youtube
YOUTUBE_OAUTH_CLIENT_SECRET         = os.getenv("YOUTUBE_OAUTH_CLIENT_SECRET")          # OAuth 2.0 - Identifica mi aplicación frente a Youtube
YOUTUBE_OAUTH_CLIENT_REFRESH_TOKEN  = os.getenv("YOUTUBE_OAUTH_CLIENT_REFRESH_TOKEN")   # OAuth 2.0 - Identifica mi aplicación frente a Youtube    

# --- MongoDB ---
MONGO_USER     = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_HOST     = os.getenv("MONGO_HOST")
MONGO_DB       = os.getenv("MONGO_DB")

# --- Encryption (used to encrypt user-level X credentials) ---
DB_ENCRIPTION_SECRET_KEY = os.getenv("DB_ENCRIPTION_SECRET_KEY")

# --- Validations  ---
required_vars = {
    # APIs
    "YOUTUBE_API_KEY": YOUTUBE_API_KEY,
    "OPENAI_API_KEY": OPENAI_API_KEY,
    "X_OAUTH1_API_KEY": X_OAUTH1_API_KEY,
    "X_OAUTH1_API_SECRET": X_OAUTH1_API_SECRET,
    "X_OAUTH2_API_BEARER_TOKEN": X_OAUTH2_API_BEARER_TOKEN,
    "X_OAUTH2_CLIENT_ID": X_OAUTH2_CLIENT_ID,
    "X_OAUTH2_CLIENT_SECRET": X_OAUTH2_CLIENT_SECRET,
    "YOUTUBE_OAUTH_CLIENT_ID": YOUTUBE_OAUTH_CLIENT_ID,
    "YOUTUBE_OAUTH_CLIENT_SECRET": YOUTUBE_OAUTH_CLIENT_SECRET,
    "YOUTUBE_OAUTH_CLIENT_REFRESH_TOKEN": YOUTUBE_OAUTH_CLIENT_REFRESH_TOKEN,
    # Mongo
    "MONGO_USER": MONGO_USER,
    "MONGO_PASSWORD": MONGO_PASSWORD,
    "MONGO_HOST": MONGO_HOST,
    "MONGO_DB": MONGO_DB,
    # Encryption
    "DB_ENCRIPTION_SECRET_KEY": DB_ENCRIPTION_SECRET_KEY,   # used to encript user-level X credentials in DB
}

missing = [k for k, v in required_vars.items() if not v]
if missing:
    raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")


# ===== LOGGING =====
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
ENVIRONMENT = os.getenv("ENVIRONMENT", "local")

# Configure logging in JSON format
logger = logging.getLogger()
logger.setLevel(LOG_LEVEL)

# clean previous handlers
logger.handlers = []

# hide all APScheduler logging
logging.getLogger("apscheduler").setLevel(logging.CRITICAL + 1)

# silence WARNING logging from APScheduler (only show ERROR and CRITICAL)
# logging.getLogger("apscheduler").setLevel(logging.ERROR)

if ENVIRONMENT == "local":
    # Easy format to read in console
    console_handler = logging.StreamHandler(sys.stdout)
    formatter = ColoredFormatter(
    "%(log_color)s%(levelname)-5s%(reset)s | %(asctime)s | %(module)s | %(message)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "bold_red",
    })
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
else:
    # JSON format for cloud deployment
    json_handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    json_handler.setFormatter(formatter)
    logger.addHandler(json_handler)

# ===== DEBUG =====
def str_to_bool(value: str) -> bool:
    return str(value).lower() in ("1", "true", "yes", "y")

APP_DEBUG = str_to_bool(os.getenv("APP_DEBUG", "false"))