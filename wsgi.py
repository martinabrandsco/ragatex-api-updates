#!/usr/bin/env python3
"""
WSGI entry point for Railway deployment
"""

import os
from dotenv import load_dotenv
from app import app

# Load environment variables
load_dotenv()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
