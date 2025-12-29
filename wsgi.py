"""ASGI entry point for Uvicorn - ROOT LEVEL."""
import sys
from pathlib import Path

# Critical: Add parent of src to path so imports work
root = Path(__file__).parent
sys.path.insert(0, str(root / "src"))

# Now we can import
from presentation.api.app import app

# Export for uvicorn
__all__ = ["app"]
