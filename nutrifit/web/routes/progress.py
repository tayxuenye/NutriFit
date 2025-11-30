"""Progress tracking routes."""

from datetime import date, datetime

from flask import jsonify, request

from nutrifit.api import track_progress
from nutrifit.display import display_progress
from nutrifit.web import app, storage


@app.route("/api/progress", methods=["POST"])
def log_progress():
    """Log progress entry."""
    try:
        # Handle both JSON and form data
        data = request.json if request.is_json else (request.form.to_dict() if request.form else {})
        entry_date = date.today()
        if data and "date" in data:
            entry_date = datetime.fromisoformat(data["date"]).date()
        
        def to_float_or_none(val):
            return float(val) if val is not None and val != "" else None
        
        def to_int_or_none(val):
            return int(val) if val is not None and val != "" else None
        
        def to_int(val, default=0):
            return int(val) if val is not None and val != "" else default
        
        track_progress(
            entry_date=entry_date,
            weight_kg=to_float_or_none(data.get("weight_kg")) if data else None,
            calories_consumed=to_int_or_none(data.get("calories_consumed")) if data else None,
            calories_burned=to_int_or_none(data.get("calories_burned")) if data else None,
            workouts_completed=to_int(data.get("workouts_completed"), 0) if data else 0,
            meals_followed=to_int(data.get("meals_followed"), 0) if data else 0,
            mood_rating=to_int_or_none(data.get("mood_rating")) if data else None,
            energy_rating=to_int_or_none(data.get("energy_rating")) if data else None,
            notes=data.get("notes", "") if data else "",
        )
        
        return jsonify({"success": True, "message": "Progress logged"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/progress/summary", methods=["GET"])
def get_progress_summary():
    """Get progress summary."""
    tracker = storage.load_progress_tracker()
    if not tracker or not tracker.entries:
        return jsonify({"error": "No progress data found"}), 404
    
    summary = tracker.get_summary()
    return jsonify({
        "success": True,
        "summary": summary,
        "display": display_progress(tracker, days=7),
    })

