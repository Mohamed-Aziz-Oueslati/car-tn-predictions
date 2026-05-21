from pathlib import Path
import os
import httpx
import joblib
from sqlalchemy import create_engine

DOWNLOAD_DIR = Path("3d_models")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

MODEL_PATH = "best_model.pkl"
model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/automarket")
engine = create_engine(
    DATABASE_URL,
    connect_args={"client_encoding": "utf8"},
    pool_pre_ping=True,
    echo=False,
)

SECRET_KEY = "ton_secret_key_change_moi"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

KAGGLE_API_URL = os.getenv("KAGGLE_API_URL", "https://stunt-wanting-agility.ngrok-free.dev")

try:
    from google import genai
    from PIL import Image

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except ImportError:
    genai = None
    Image = None
    gemini_client = None

try:
    from groq import Groq

    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

    if GROQ_API_KEY:
        custom_http_client = httpx.Client()
        groq_client = Groq(api_key=GROQ_API_KEY, http_client=custom_http_client)
    else:
        groq_client = None
except ImportError:
    groq_client = None

def kaggle_url(path: str) -> str:
    base = (KAGGLE_API_URL or "").rstrip("/")
    return f"{base}{path}"
