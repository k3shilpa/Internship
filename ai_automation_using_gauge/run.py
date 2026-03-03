#!/usr/bin/env python3
"""Single entry point to start the AI Exploratory Tester."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from ui.app import create_app

if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    print(f"[AI Tester] Starting Flask UI at http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)