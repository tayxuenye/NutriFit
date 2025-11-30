"""Middleware for the Flask web application."""

import sys

from flask import request

from nutrifit.web import app


@app.before_request
def log_request_info():
    """Log all incoming requests for debugging."""
    print(f"[REQUEST] {request.method} {request.path}", file=sys.stderr)
    sys.stderr.flush()


@app.after_request
def after_request(response):
    """Add CORS headers to all responses."""
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
    return response

