"""
Meeting Studio — Root Entry Point
Delegates execution to the backend application (backend/app.py).
"""

import sys
from pathlib import Path

# Configure utf-8 encoding for Windows terminals
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root and backend to sys.path
root_dir = Path(__file__).resolve().parent
backend_dir = root_dir / "backend"

if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from backend.app import app, Config

if __name__ == "__main__":
    print(f">> Meeting Studio starting on http://{Config.HOST}:{Config.PORT}")
    print(f">> Environment: {Config.LOADED_ENV_PATH}")
    print(f">> Model 1 (Transcription & Diarization): {Config.MODEL_TRANSCRIBE_DIARIZE}")
    print(f">> Model 2 (Dense Embeddings):            {Config.MODEL_EMBEDDING}")
    print(f">> Model 3 (Reasoning & Summarization):   {Config.MODEL_CHAT_ANALYSIS}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG, use_reloader=False)


