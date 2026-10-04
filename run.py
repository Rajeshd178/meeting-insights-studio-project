"""
Convenience launcher for Meeting Studio.
Runs the Flask application located in `meeting-studio-main/app.py`.
"""

import os
import sys
from pathlib import Path

# Add project directory to python path
project_dir = Path(__file__).resolve().parent / "meeting-studio-main"
if project_dir.exists():
    sys.path.insert(0, str(project_dir))
    os.chdir(str(project_dir))

from app import app, Config

if __name__ == "__main__":
    print(f"🚀 Launching Meeting Studio on http://{Config.HOST}:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
