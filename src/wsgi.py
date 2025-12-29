"""WSGI entry point for Gunicorn."""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from presentation.api.app import create_app

app = create_app()
