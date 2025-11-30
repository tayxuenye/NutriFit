"""Workout plan routes."""

import traceback
from datetime import date, datetime

from flask import jsonify, request

from nutrifit.api import generate_workout_plan
from nutrifit.models.workout import Exercise, ExerciseType, MuscleGroup, Workout
from nutrifit.web import app, storage
from nutrifit.web.utils import get_or_create_profile


@app.route("/api/workout-plan/daily", methods=["POST"])
def generate_daily_workout_plan():
    """Generate a daily workout plan."""
    try:
        profile = get_or_create_profile()
        
        plan_date = date.today()
        # Handle both JSON and form data
        data = request.json if request.is_json else (request.form.to_dict() if request.form else {})
        if data and "date" in data:
            plan_date = datetime.fromisoformat(data["date"]).date()
        
        plan = generate_workout_plan(profile, duration_days=1, start_date=plan_date)
        
        daily_plan = plan.daily_plans[0] if plan.daily_plans else None
        if daily_plan:
            plan_data = {
                "id": plan.id,
                "name": plan.name,
                "date": plan.start_date.isoformat(),
                "is_rest_day": daily_plan.is_rest_day,
                "notes": daily_plan.notes,
                "workouts": []
            }
            
            for workout in daily_plan.workouts:
                workout_data = {
                    "name": workout.name,
                    "type": workout.workout_type,
                    "difficulty": workout.difficulty,
                    "duration_minutes": workout.total_duration_minutes,
                    "description": workout.description,
                    "exercises": []
                }
                
                for exercise in workout.exercises:
                    exercise_data = {
                        "name": exercise.name,
                        "sets": exercise.sets,
                        "reps": exercise.reps,
                        "duration_seconds": exercise.duration_seconds,
                        "rest_seconds": exercise.rest_seconds,
                        "description": exercise.description,
                    }
                    workout_data["exercises"].append(exercise_data)
                
                plan_data["workouts"].append(workout_data)
        else:
            plan_data = None
        
        return jsonify({
            "success": True,
            "plan": plan_data
        })
    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error generating daily workout plan: {error_msg}")
        return jsonify({"error": str(e), "details": error_msg}), 500


@app.route("/api/workout-plan/weekly", methods=["POST"])
def generate_weekly_workout_plan():
    """Generate a weekly workout plan."""
    profile = get_or_create_profile()
    
    try:
        start_date = date.today()
        workout_days = 4
        # Handle both JSON and form data
        data = request.json if request.is_json else (request.form.to_dict() if request.form else {})
        if data:
            if "start_date" in data:
                start_date = datetime.fromisoformat(data["start_date"]).date()
            if "workout_days" in data:
                workout_days = int(data["workout_days"])
        
        plan = generate_workout_plan(
            profile, duration_days=7, start_date=start_date, workout_days_per_week=workout_days
        )
        # Save with overwrite to replace any existing plan with same date range
        was_replaced, plan_id = storage.save_workout_plan(plan, overwrite_existing=True)
        import sys
        print(f"[WORKOUT PLAN] Saved plan {plan_id}, replaced existing: {was_replaced}", file=sys.stderr)
        print(f"[WORKOUT PLAN] Plan date range: {plan.start_date} to {plan.end_date}", file=sys.stderr)
        
        plan_data = {
            "id": plan.id,
            "name": plan.name,
            "start_date": plan.start_date.isoformat(),
            "end_date": plan.end_date.isoformat(),
            "workout_days": plan.total_workout_days,
            "days": []
        }
        
        for daily_plan in plan.daily_plans:
            day_data = {
                "date": daily_plan.date.isoformat(),
                "is_rest_day": daily_plan.is_rest_day,
                "notes": daily_plan.notes,
                "workouts": []
            }
            
            for workout in daily_plan.workouts:
                workout_data = {
                    "name": workout.name,
                    "type": workout.workout_type,
                    "duration_minutes": workout.total_duration_minutes,
                    "difficulty": workout.difficulty,
                    "description": workout.description or "",
                    "exercises": []
                }
                for exercise in workout.exercises:
                    workout_data["exercises"].append({
                        "name": exercise.name,
                        "sets": exercise.sets,
                        "reps": exercise.reps,
                        "duration_seconds": exercise.duration_seconds,
                        "rest_seconds": exercise.rest_seconds,
                        "description": exercise.description or "",
                    })
                day_data["workouts"].append(workout_data)
            
            plan_data["days"].append(day_data)
        
        return jsonify({
            "success": True,
            "plan": plan_data,
            "replaced": was_replaced,
            "status": "replaced" if was_replaced else "created"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/workout-plans", methods=["GET"])
def list_workout_plans():
    """List all saved workout plans."""
    try:
        plans = storage.list_workout_plans()
        return jsonify({
            "success": True,
            "plans": plans
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/workout-plan/<plan_id>", methods=["GET"])
def get_workout_plan(plan_id):
    """Get a specific workout plan by ID."""
    try:
        plan = storage.load_workout_plan(plan_id)
        if not plan:
            return jsonify({"error": "Workout plan not found"}), 404
        
        # Convert to same format as generate endpoints
        if len(plan.daily_plans) == 1:
            # Daily plan
            daily_plan = plan.daily_plans[0]
            plan_data = {
                "id": plan.id,
                "name": plan.name,
                "date": plan.start_date.isoformat(),
                "is_rest_day": daily_plan.is_rest_day,
                "notes": daily_plan.notes,
                "workouts": []
            }
            
            for workout in daily_plan.workouts:
                workout_data = {
                    "name": workout.name,
                    "type": workout.workout_type,
                    "difficulty": workout.difficulty,
                    "duration_minutes": workout.total_duration_minutes,
                    "description": workout.description,
                    "exercises": []
                }
                
                for exercise in workout.exercises:
                    exercise_data = {
                        "name": exercise.name,
                        "sets": exercise.sets,
                        "reps": exercise.reps,
                        "duration_seconds": exercise.duration_seconds,
                        "rest_seconds": exercise.rest_seconds,
                        "description": exercise.description,
                    }
                    workout_data["exercises"].append(exercise_data)
                
                plan_data["workouts"].append(workout_data)
        else:
            # Weekly plan
            plan_data = {
                "id": plan.id,
                "name": plan.name,
                "start_date": plan.start_date.isoformat(),
                "end_date": plan.end_date.isoformat(),
                "workout_days": plan.total_workout_days,
                "days": []
            }
            
            for daily_plan in plan.daily_plans:
                day_data = {
                    "date": daily_plan.date.isoformat(),
                    "is_rest_day": daily_plan.is_rest_day,
                    "notes": daily_plan.notes,
                    "workouts": []
                }
                
                for workout in daily_plan.workouts:
                    workout_data = {
                        "name": workout.name,
                        "type": workout.workout_type,
                        "duration_minutes": workout.total_duration_minutes,
                        "difficulty": workout.difficulty,
                        "description": workout.description or "",
                        "exercises": []
                    }
                    for exercise in workout.exercises:
                        workout_data["exercises"].append({
                            "name": exercise.name,
                            "sets": exercise.sets,
                            "reps": exercise.reps,
                            "duration_seconds": exercise.duration_seconds,
                            "rest_seconds": exercise.rest_seconds,
                            "description": exercise.description or "",
                        })
                    day_data["workouts"].append(workout_data)
                
                plan_data["days"].append(day_data)
        
        return jsonify({
            "success": True,
            "plan": plan_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/workout-plan/<plan_id>", methods=["PUT"])
def update_workout_plan(plan_id):
    """Update a workout plan entry."""
    try:
        plan = storage.load_workout_plan(plan_id)
        if not plan:
            return jsonify({"error": "Workout plan not found"}), 404
        
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Update workout entry
        date_str = data.get("date")
        workout_data = data.get("workout")
        
        if not date_str:
            return jsonify({"error": "Date required"}), 400
        
        target_date = datetime.fromisoformat(date_str).date()
        
        # Find the daily plan for this date
        daily_plan = None
        for dp in plan.daily_plans:
            if dp.date == target_date:
                daily_plan = dp
                break
        
        if not daily_plan:
            return jsonify({"error": "Date not found in plan"}), 404
        
        if workout_data:
            # Create exercises
            exercises = []
            for idx, ex_data in enumerate(workout_data.get("exercises", [])):
                exercise = Exercise(
                    id=ex_data.get("id", f"ex_{target_date}_{idx}"),
                    name=ex_data.get("name", ""),
                    description=ex_data.get("description", ""),
                    muscle_groups=[MuscleGroup.FULL_BODY],  # Default to full body
                    exercise_type=ExerciseType.STRENGTH,  # Default to strength
                    sets=ex_data.get("sets", 0),
                    reps=ex_data.get("reps", 10) if ex_data.get("reps") else None,
                    duration_seconds=ex_data.get("duration_seconds", 0) if ex_data.get("duration_seconds") else None,
                    rest_seconds=ex_data.get("rest_seconds", 60),
                )
                exercises.append(exercise)
            
            workout = Workout(
                id=workout_data.get("id", f"workout_{target_date}"),
                name=workout_data.get("name", ""),
                workout_type=workout_data.get("type", "general"),
                difficulty=workout_data.get("difficulty", "medium"),
                description=workout_data.get("description", ""),
                exercises=exercises,
            )
            
            daily_plan.workouts = [workout]
            daily_plan.is_rest_day = False
        else:
            # Remove workout (make it a rest day)
            daily_plan.workouts = []
            daily_plan.is_rest_day = True
        
        # Save updated plan (don't overwrite on update, just save)
        storage.save_workout_plan(plan, overwrite_existing=False)
        
        return jsonify({"success": True, "message": "Workout plan updated"})
    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

