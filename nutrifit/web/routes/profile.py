"""Profile management routes."""

from flask import jsonify, request

from nutrifit.models.user import DietaryPreference, FitnessGoal, UserProfile
from nutrifit.web import app, storage


@app.route("/api/profile", methods=["GET"])
def get_profile():
    """Get user profile."""
    profile = storage.load_user_profile()
    if not profile:
        return jsonify({"error": "No profile found"}), 404
    
    return jsonify({
        "name": profile.name,
        "age": profile.age,
        "weight_kg": profile.weight_kg,
        "height_cm": profile.height_cm,
        "gender": profile.gender,
        "dietary_preferences": [p.value for p in profile.dietary_preferences],
        "fitness_goals": [g.value for g in profile.fitness_goals],
        "allergies": profile.allergies,
        "pantry_items": profile.pantry_items,
        "available_equipment": profile.available_equipment,
        "daily_calorie_target": profile.daily_calorie_target,
    })


@app.route("/api/profile", methods=["POST"])
def create_profile():
    """Create or update user profile."""
    data = request.json or {}
    
    try:
        dietary_prefs = [
            DietaryPreference(pref) for pref in data.get("dietary_preferences", [])
        ]
        fitness_goals = [
            FitnessGoal(goal) for goal in data.get("fitness_goals", [])
        ]
        
        profile = UserProfile(
            name=data.get("name", "User"),
            age=int(data.get("age", 30)),
            weight_kg=float(data.get("weight_kg", 70.0)),
            height_cm=float(data.get("height_cm", 170.0)),
            gender=data.get("gender", "male"),
            dietary_preferences=dietary_prefs,
            fitness_goals=fitness_goals,
            allergies=data.get("allergies", []),
            pantry_items=data.get("pantry_items", []),
            available_equipment=data.get("available_equipment", []),
        )
        
        storage.save_user_profile(profile, user_id="default")
        return jsonify({"success": True, "message": "Profile saved"})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

