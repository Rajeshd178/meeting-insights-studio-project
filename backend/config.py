"""
Configuration loader for Meeting Studio Backend.
Searches and loads environment variables from the `envs/` directory.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Check env files in order of precedence:
env_paths = [
    PROJECT_ROOT / "envs" / ".env",
    PROJECT_ROOT / "envs" / ".env.local",
    PROJECT_ROOT / ".env",
    BASE_DIR / "envs" / ".env",
    BASE_DIR / ".env",
]

loaded_env_path = None
for p in env_paths:
    if p.exists():
        load_dotenv(dotenv_path=p, override=True)
        loaded_env_path = str(p)
        break

if not loaded_env_path:
    load_dotenv()


class Config:
    PROJECT_ROOT = PROJECT_ROOT
    BACKEND_DIR = BASE_DIR
    FRONTEND_DIR = PROJECT_ROOT / "frontend"
    ENV_DIR = PROJECT_ROOT / "envs"
    LOADED_ENV_PATH = loaded_env_path

    # OpenAI API Key & Base URL
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "").strip() or None

    # The 3 Configured Models
    MODEL_TRANSCRIBE_DIARIZE = os.getenv("MODEL_TRANSCRIBE_DIARIZE", "gpt-4o-transcribe-diarize").strip()
    MODEL_EMBEDDING = os.getenv("MODEL_EMBEDDING", "text-embedding-3-small").strip()
    MODEL_CHAT_ANALYSIS = os.getenv("MODEL_CHAT_ANALYSIS", "gpt-4.1-mini").strip()

    # Flask Server Settings
    HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    PORT = int(os.getenv("FLASK_PORT", 5000))
    DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "meeting-studio-secret-key-2026-openai-rag")

    @classmethod
    def has_api_key(cls) -> bool:
        return bool(cls.OPENAI_API_KEY and cls.OPENAI_API_KEY != "your_openai_api_key_here")

    @classmethod
    def get_model_info(cls):
        return {
            "transcribe_model": cls.MODEL_TRANSCRIBE_DIARIZE,
            "embedding_model": cls.MODEL_EMBEDDING,
            "chat_model": cls.MODEL_CHAT_ANALYSIS,
            "has_api_key": cls.has_api_key(),
            "env_path": cls.LOADED_ENV_PATH,
        }
