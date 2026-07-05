"""Vercel Python giris noktasi — FastAPI uygulamasini servis eder."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import app  # noqa: E402,F401  (Vercel `app` ASGI nesnesini arar)
