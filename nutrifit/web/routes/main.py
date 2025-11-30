"""Main routes (index, test, favicon)."""

import sys

from flask import jsonify, render_template

from nutrifit.web import app


@app.route("/")
def index():
    """Home page."""
    return render_template("index.html")


@app.route("/api/test", methods=["GET", "POST"])
def test_endpoint():
    """Test endpoint to verify server is running."""
    print("[TEST] Test endpoint called", file=sys.stderr)
    print("[TEST] Test endpoint called")  # Also to stdout
    sys.stderr.flush()
    return jsonify({"status": "ok", "message": "Server is running"})


@app.route("/favicon.ico")
def favicon():
    """Handle favicon requests."""
    return "", 204  # No content

