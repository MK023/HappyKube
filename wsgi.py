"""WSGI entry point for Gunicorn - ROOT LEVEL."""
import sys
from pathlib import Path

# Critical: Add parent of src to path so imports work
root = Path(__file__).parent
sys.path.insert(0, str(root / "src"))

# Now we can import
from presentation.api.app import create_app

app = create_app()
