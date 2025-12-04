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


@app.route("/api/progress/entries", methods=["GET"])
def list_progress_entries():
    """List all progress entries."""
    try:
        tracker = storage.load_progress_tracker()
        if not tracker or not tracker.entries:
            return jsonify({"success": True, "entries": []})
        
        # Sort entries by date descending (most recent first)
        entries = sorted(tracker.entries, key=lambda e: e.date, reverse=True)
        
        return jsonify({
            "success": True,
            "entries": [e.to_dict() for e in entries]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/progress/<entry_date>", methods=["GET"])
def get_progress_entry(entry_date):
    """Get a specific progress entry by date."""
    try:
        tracker = storage.load_progress_tracker()
        if not tracker:
            return jsonify({"error": "No progress data found"}), 404
        
        target_date = datetime.fromisoformat(entry_date).date()
        entry = tracker.get_entry_for_date(target_date)
        
        if not entry:
            return jsonify({"error": "Entry not found"}), 404
        
        return jsonify({
            "success": True,
            "entry": entry.to_dict()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/progress/<entry_date>", methods=["PUT"])
def update_progress_entry(entry_date):
    """Update a progress entry."""
    try:
        tracker = storage.load_progress_tracker()
        if not tracker:
            return jsonify({"error": "No progress data found"}), 404
        
        target_date = datetime.fromisoformat(entry_date).date()
        
        # Find the entry
        entry = None
        entry_index = None
        for i, e in enumerate(tracker.entries):
            if e.date == target_date:
                entry = e
                entry_index = i
                break
        
        if not entry:
            return jsonify({"error": "Entry not found"}), 404
        
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        def to_float_or_none(val):
            return float(val) if val is not None and val != "" else None
        
        def to_int_or_none(val):
            return int(val) if val is not None and val != "" else None
        
        def to_int(val, default=0):
            return int(val) if val is not None and val != "" else default
        
        # Update entry fields
        if "weight_kg" in data:
            entry.weight_kg = to_float_or_none(data["weight_kg"])
        if "calories_consumed" in data:
            entry.calories_consumed = to_int_or_none(data["calories_consumed"])
        if "calories_burned" in data:
            entry.calories_burned = to_int_or_none(data["calories_burned"])
        if "workouts_completed" in data:
            entry.workouts_completed = to_int(data["workouts_completed"], 0)
        if "meals_followed" in data:
            entry.meals_followed = to_int(data["meals_followed"], 0)
        if "mood_rating" in data:
            entry.mood_rating = to_int_or_none(data["mood_rating"])
        if "energy_rating" in data:
            entry.energy_rating = to_int_or_none(data["energy_rating"])
        if "notes" in data:
            entry.notes = data["notes"] or ""
        
        # Save updated tracker
        storage.save_progress_tracker(tracker)
        
        return jsonify({"success": True, "message": "Progress entry updated"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/progress/<entry_date>", methods=["DELETE"])
def delete_progress_entry(entry_date):
    """Delete a progress entry."""
    try:
        tracker = storage.load_progress_tracker()
        if not tracker:
            return jsonify({"error": "No progress data found"}), 404
        
        target_date = datetime.fromisoformat(entry_date).date()
        
        # Find and remove the entry
        original_count = len(tracker.entries)
        tracker.entries = [e for e in tracker.entries if e.date != target_date]
        
        if len(tracker.entries) == original_count:
            return jsonify({"error": "Entry not found"}), 404
        
        # Save updated tracker
        storage.save_progress_tracker(tracker)
        
        return jsonify({"success": True, "message": "Progress entry deleted"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

