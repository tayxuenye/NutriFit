"""
Web interface for NutriFit - Mobile-friendly web application.

This module provides a Flask-based web interface that can be accessed
from a phone browser.
"""

from pathlib import Path

from flask import Flask

from nutrifit.utils.storage import DataStorage

# Initialize Flask app with correct template folder
template_dir = Path(__file__).parent.parent / "templates"
app = Flask(__name__, template_folder=str(template_dir))
app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

# Initialize storage
storage = DataStorage()

# Import routes to register them
from nutrifit.web import middleware, routes  # noqa: E402

# Register all routes
routes.register_routes(app)


def run(host="0.0.0.0", port=5000, debug=False):
    """Run the web server."""
    import sys
    print("=" * 50, file=sys.stderr)
    print("=" * 50)  # Also to stdout
    print("Starting NutriFit web server...", file=sys.stderr)
    print("Starting NutriFit web server...")  # Also to stdout
    print(f"Host: {host}, Port: {port}, Debug: {debug}", file=sys.stderr)
    print(f"Host: {host}, Port: {port}, Debug: {debug}")  # Also to stdout
    
    # Create templates directory if it doesn't exist
    template_dir = Path(__file__).parent.parent / "templates"
    template_dir.mkdir(exist_ok=True)
    print(f"Templates directory: {template_dir}", file=sys.stderr)
    print(f"Templates directory: {template_dir}")  # Also to stdout
    
    print("Flask app routes registered:", file=sys.stderr)
    print("Flask app routes registered:")  # Also to stdout
    for rule in app.url_map.iter_rules():
        methods_str = ', '.join(rule.methods) if rule.methods else 'GET'
        print(f"  {rule.rule} -> {rule.endpoint} [{methods_str}]", file=sys.stderr)
        print(f"  {rule.rule} -> {rule.endpoint} [{methods_str}]")  # Also to stdout
    
    print("=" * 50, file=sys.stderr)
    print("=" * 50)  # Also to stdout
    sys.stderr.flush()
    
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run(debug=True)

