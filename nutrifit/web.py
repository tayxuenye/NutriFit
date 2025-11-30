"""
Web interface for NutriFit - Mobile-friendly web application.

This module provides a Flask-based web interface that can be accessed
from a phone browser, satisfying Requirement 10 for a basic web interface.

This file is now a backward-compatible entry point. The actual implementation
has been refactored into the nutrifit.web package.
"""

# Import everything from the new web package for backward compatibility
from nutrifit.web import app, run, storage  # noqa: F401

# Re-export for backward compatibility
__all__ = ["app", "run", "storage"]

# Allow direct execution: python -m nutrifit.web or python nutrifit/web.py
if __name__ == "__main__":
    run(debug=True)
