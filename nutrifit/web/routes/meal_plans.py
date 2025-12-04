"""Meal plan routes."""

import sys
import traceback
from datetime import date, datetime

from flask import Response, jsonify, request

from nutrifit.api import generate_meal_plan
from nutrifit.models.recipe import Ingredient, NutritionInfo, Recipe
from nutrifit.web import app, storage
from nutrifit.web.utils import get_or_create_profile


@app.route("/api/meal-plan/daily", methods=["POST", "OPTIONS"])
def generate_daily_meal_plan():
    """Generate a daily meal plan."""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response
    
    try:
        profile = get_or_create_profile()
        
        plan_date = date.today()
        # Handle both JSON and form data
        data = request.json if request.is_json else (request.form.to_dict() if request.form else {})
        if data and "date" in data:
            plan_date = datetime.fromisoformat(data["date"]).date()
        
        plan = generate_meal_plan(profile, duration_days=1, start_date=plan_date)
        
        daily_plan = plan.daily_plans[0] if plan.daily_plans else None
        if daily_plan:
            plan_data = {
                "id": plan.id,
                "name": plan.name,
                "date": plan.start_date.isoformat(),
                "total_calories": daily_plan.total_calories or 0,
                "total_protein": daily_plan.total_protein or 0,
                "meals": []
            }
            
            if daily_plan.breakfast:
                plan_data["meals"].append({
                    "type": "breakfast",
                    "name": daily_plan.breakfast.name or "",
                    "description": daily_plan.breakfast.description or "",
                    "calories": daily_plan.breakfast.nutrition.calories if daily_plan.breakfast.nutrition else 0,
                    "protein": daily_plan.breakfast.nutrition.protein_g if daily_plan.breakfast.nutrition else 0,
                    "carbs": daily_plan.breakfast.nutrition.carbs_g if daily_plan.breakfast.nutrition else 0,
                    "fat": daily_plan.breakfast.nutrition.fat_g if daily_plan.breakfast.nutrition else 0,
                    "prep_time": daily_plan.breakfast.prep_time_minutes or 0,
                    "cook_time": daily_plan.breakfast.cook_time_minutes or 0,
                    "ingredients": [ing.name for ing in (daily_plan.breakfast.ingredients or [])],
                })
            
            if daily_plan.lunch:
                plan_data["meals"].append({
                    "type": "lunch",
                    "name": daily_plan.lunch.name or "",
                    "description": daily_plan.lunch.description or "",
                    "calories": daily_plan.lunch.nutrition.calories if daily_plan.lunch.nutrition else 0,
                    "protein": daily_plan.lunch.nutrition.protein_g if daily_plan.lunch.nutrition else 0,
                    "carbs": daily_plan.lunch.nutrition.carbs_g if daily_plan.lunch.nutrition else 0,
                    "fat": daily_plan.lunch.nutrition.fat_g if daily_plan.lunch.nutrition else 0,
                    "prep_time": daily_plan.lunch.prep_time_minutes or 0,
                    "cook_time": daily_plan.lunch.cook_time_minutes or 0,
                    "ingredients": [ing.name for ing in (daily_plan.lunch.ingredients or [])],
                })
            
            if daily_plan.dinner:
                plan_data["meals"].append({
                    "type": "dinner",
                    "name": daily_plan.dinner.name or "",
                    "description": daily_plan.dinner.description or "",
                    "calories": daily_plan.dinner.nutrition.calories if daily_plan.dinner.nutrition else 0,
                    "protein": daily_plan.dinner.nutrition.protein_g if daily_plan.dinner.nutrition else 0,
                    "carbs": daily_plan.dinner.nutrition.carbs_g if daily_plan.dinner.nutrition else 0,
                    "fat": daily_plan.dinner.nutrition.fat_g if daily_plan.dinner.nutrition else 0,
                    "prep_time": daily_plan.dinner.prep_time_minutes or 0,
                    "cook_time": daily_plan.dinner.cook_time_minutes or 0,
                    "ingredients": [ing.name for ing in (daily_plan.dinner.ingredients or [])],
                })
            
            for snack in (daily_plan.snacks or []):
                plan_data["meals"].append({
                    "type": "snack",
                    "name": snack.name or "",
                    "description": snack.description or "",
                    "calories": snack.nutrition.calories if snack.nutrition else 0,
                    "protein": snack.nutrition.protein_g if snack.nutrition else 0,
                    "carbs": snack.nutrition.carbs_g if snack.nutrition else 0,
                    "fat": snack.nutrition.fat_g if snack.nutrition else 0,
                    "prep_time": snack.prep_time_minutes or 0,
                    "cook_time": snack.prep_time_minutes or 0,
                    "ingredients": [ing.name for ing in (snack.ingredients or [])],
                })
        else:
            plan_data = None
        
        response = jsonify({
            "success": True,
            "plan": plan_data
        })
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Error generating daily meal plan: {error_msg}", file=sys.stderr)
        sys.stderr.flush()
        try:
            response = jsonify({"error": str(e), "details": error_msg})
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response, 500
        except Exception as json_error:
            print(f"Error creating error response: {json_error}", file=sys.stderr)
            sys.stderr.flush()
            return f"Error: {str(e)}", 500


@app.route("/api/meal-plan/weekly", methods=["POST", "OPTIONS"])
def generate_weekly_meal_plan():
    """Generate a weekly meal plan. Replaces existing plan for same date range."""
    # Log immediately when function is called
    print("=" * 50, file=sys.stderr)
    print(f"[WEEKLY MEAL PLAN] Function called - Method: {request.method}", file=sys.stderr)
    print(f"[WEEKLY MEAL PLAN] Request path: {request.path}", file=sys.stderr)
    print(f"[WEEKLY MEAL PLAN] Request headers: {dict(request.headers)}", file=sys.stderr)
    sys.stderr.flush()
    
    if request.method == "OPTIONS":
        print("[WEEKLY MEAL PLAN] Handling OPTIONS request", file=sys.stderr)
        sys.stderr.flush()
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response
    
    print("[WEEKLY MEAL PLAN] Starting POST request handling...", file=sys.stderr)
    print("[WEEKLY MEAL PLAN] Starting POST request handling...")  # Also to stdout
    sys.stderr.flush()
    
    try:
        print("[WEEKLY MEAL PLAN] Starting weekly meal plan generation...", file=sys.stderr)
        print("[WEEKLY MEAL PLAN] Starting weekly meal plan generation...")  # Also to stdout
        sys.stderr.flush()
        
        try:
            print("[WEEKLY MEAL PLAN] Loading profile...", file=sys.stderr)
            print("[WEEKLY MEAL PLAN] Loading profile...")  # Also to stdout
            sys.stderr.flush()
            profile = get_or_create_profile()
            print(f"[WEEKLY MEAL PLAN] Profile loaded: {profile.name}", file=sys.stderr)
            print(f"[WEEKLY MEAL PLAN] Profile loaded: {profile.name}")  # Also to stdout
            sys.stderr.flush()
        except Exception as profile_error:
            error_msg = f"Error loading/creating profile: {profile_error}"
            print(error_msg, file=sys.stderr)
            print(error_msg)  # Also to stdout
            traceback.print_exc(file=sys.stderr)
            traceback.print_exc()  # Also to stdout
            sys.stderr.flush()
            response = jsonify({"error": f"Failed to load profile: {str(profile_error)}"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response, 500
        
        start_date = date.today()
        # Handle both JSON and form data
        data = request.json if request.is_json else (request.form.to_dict() if request.form else {})
        if data and "start_date" in data:
            start_date = datetime.fromisoformat(data["start_date"]).date()
        
        print(f"[WEEKLY MEAL PLAN] Generating meal plan for {start_date}...", file=sys.stderr)
        print(f"[WEEKLY MEAL PLAN] Generating meal plan for {start_date}...")  # Also to stdout
        sys.stderr.flush()
        
        try:
            plan = generate_meal_plan(profile, duration_days=7, start_date=start_date)
            print(f"[WEEKLY MEAL PLAN] Meal plan generated: {plan.id} with {len(plan.daily_plans)} days", file=sys.stderr)
            print(f"[WEEKLY MEAL PLAN] Meal plan generated: {plan.id} with {len(plan.daily_plans)} days")  # Also to stdout
            sys.stderr.flush()
        except Exception as gen_error:
            error_msg = f"Error generating meal plan: {gen_error}"
            print(error_msg, file=sys.stderr)
            print(error_msg)  # Also to stdout
            traceback.print_exc(file=sys.stderr)
            traceback.print_exc()  # Also to stdout
            sys.stderr.flush()
            response = jsonify({"error": f"Failed to generate meal plan: {str(gen_error)}"})
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response, 500
        
        try:
            print("[WEEKLY MEAL PLAN] Saving meal plan...", file=sys.stderr)
            print("[WEEKLY MEAL PLAN] Saving meal plan...")  # Also to stdout
            sys.stderr.flush()
            was_replaced, _ = storage.save_meal_plan(plan, overwrite_existing=True)
            print(f"[WEEKLY MEAL PLAN] Meal plan saved (replaced: {was_replaced})", file=sys.stderr)
            print(f"[WEEKLY MEAL PLAN] Meal plan saved (replaced: {was_replaced})")  # Also to stdout
            sys.stderr.flush()
        except Exception as save_error:
            error_msg = f"Error saving meal plan: {save_error}"
            print(error_msg, file=sys.stderr)
            print(error_msg)  # Also to stdout
            traceback.print_exc(file=sys.stderr)
            traceback.print_exc()  # Also to stdout
            sys.stderr.flush()
            # Continue anyway - we can still return the plan even if saving failed
            was_replaced = False
        
        print("[WEEKLY MEAL PLAN] Building response data...", file=sys.stderr)
        print("[WEEKLY MEAL PLAN] Building response data...")  # Also to stdout
        sys.stderr.flush()
        
        plan_data = {
            "id": plan.id or "",
            "name": plan.name or "",
            "start_date": plan.start_date.isoformat() if plan.start_date else date.today().isoformat(),
            "end_date": plan.end_date.isoformat() if plan.end_date else date.today().isoformat(),
            "average_calories": plan.average_daily_calories or 0.0,
            "days": []
        }
        
        print(f"[WEEKLY MEAL PLAN] Processing {len(plan.daily_plans)} daily plans...", file=sys.stderr)
        print(f"[WEEKLY MEAL PLAN] Processing {len(plan.daily_plans)} daily plans...")  # Also to stdout
        sys.stderr.flush()
        
        for idx, daily_plan in enumerate(plan.daily_plans):
            day_data = {
                "date": daily_plan.date.isoformat(),
                "total_calories": daily_plan.total_calories or 0,
                "total_protein": daily_plan.total_protein or 0.0,
                "meals": []
            }
            
            if daily_plan.breakfast:
                day_data["meals"].append({
                    "type": "breakfast",
                    "name": daily_plan.breakfast.name or "",
                    "description": daily_plan.breakfast.description or "",
                    "calories": daily_plan.breakfast.nutrition.calories if daily_plan.breakfast.nutrition else 0,
                    "protein": daily_plan.breakfast.nutrition.protein_g if daily_plan.breakfast.nutrition else 0.0,
                    "carbs": daily_plan.breakfast.nutrition.carbs_g if daily_plan.breakfast.nutrition else 0.0,
                    "fat": daily_plan.breakfast.nutrition.fat_g if daily_plan.breakfast.nutrition else 0.0,
                    "instructions": daily_plan.breakfast.instructions or [],
                    "ingredients": [ing.name for ing in (daily_plan.breakfast.ingredients or [])],
                })
            if daily_plan.lunch:
                day_data["meals"].append({
                    "type": "lunch",
                    "name": daily_plan.lunch.name or "",
                    "description": daily_plan.lunch.description or "",
                    "calories": daily_plan.lunch.nutrition.calories if daily_plan.lunch.nutrition else 0,
                    "protein": daily_plan.lunch.nutrition.protein_g if daily_plan.lunch.nutrition else 0.0,
                    "carbs": daily_plan.lunch.nutrition.carbs_g if daily_plan.lunch.nutrition else 0.0,
                    "fat": daily_plan.lunch.nutrition.fat_g if daily_plan.lunch.nutrition else 0.0,
                    "instructions": daily_plan.lunch.instructions or [],
                    "ingredients": [ing.name for ing in (daily_plan.lunch.ingredients or [])],
                })
            if daily_plan.dinner:
                day_data["meals"].append({
                    "type": "dinner",
                    "name": daily_plan.dinner.name or "",
                    "description": daily_plan.dinner.description or "",
                    "calories": daily_plan.dinner.nutrition.calories if daily_plan.dinner.nutrition else 0,
                    "protein": daily_plan.dinner.nutrition.protein_g if daily_plan.dinner.nutrition else 0.0,
                    "carbs": daily_plan.dinner.nutrition.carbs_g if daily_plan.dinner.nutrition else 0.0,
                    "fat": daily_plan.dinner.nutrition.fat_g if daily_plan.dinner.nutrition else 0.0,
                    "instructions": daily_plan.dinner.instructions or [],
                    "ingredients": [ing.name for ing in (daily_plan.dinner.ingredients or [])],
                })
            for snack in (daily_plan.snacks or []):
                day_data["meals"].append({
                    "type": "snack",
                    "name": snack.name or "",
                    "description": snack.description or "",
                    "calories": snack.nutrition.calories if snack.nutrition else 0,
                    "protein": snack.nutrition.protein_g if snack.nutrition else 0.0,
                    "carbs": snack.nutrition.carbs_g if snack.nutrition else 0.0,
                    "fat": snack.nutrition.fat_g if snack.nutrition else 0.0,
                    "instructions": snack.instructions or [],
                    "ingredients": [ing.name for ing in (snack.ingredients or [])],
                })
            
            plan_data["days"].append(day_data)
            if idx % 2 == 0:  # Log every other day to avoid too much output
                print(f"[WEEKLY MEAL PLAN] Processed day {idx + 1}/7", file=sys.stderr)
                print(f"[WEEKLY MEAL PLAN] Processed day {idx + 1}/7")  # Also to stdout
                sys.stderr.flush()
        
        print("[WEEKLY MEAL PLAN] Creating JSON response...", file=sys.stderr)
        print("[WEEKLY MEAL PLAN] Creating JSON response...")  # Also to stdout
        sys.stderr.flush()
        
        response = jsonify({
            "success": True,
            "plan": plan_data,
            "replaced": was_replaced,
            "status": "replaced" if was_replaced else "created"
        })
        response.headers.add("Access-Control-Allow-Origin", "*")
        print("[WEEKLY MEAL PLAN] Response created successfully, returning...", file=sys.stderr)
        print("[WEEKLY MEAL PLAN] Response created successfully, returning...")  # Also to stdout
        sys.stderr.flush()
        return response
    except Exception as e:
        error_msg = f"Error generating weekly meal plan: {str(e)}\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        print(error_msg)  # Also to stdout
        sys.stderr.flush()
        try:
            response = jsonify({"error": str(e), "details": error_msg})
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response, 500
        except Exception as json_error:
            print(f"Error creating error response: {json_error}", file=sys.stderr)
            sys.stderr.flush()
            # Return a simple text response if JSON serialization fails
            return Response(
                f"Error: {str(e)}",
                status=500,
                mimetype="text/plain",
                headers={"Access-Control-Allow-Origin": "*"}
            )


@app.route("/api/meal-plans", methods=["GET", "OPTIONS"])
def list_meal_plans():
    """List all saved meal plans."""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "*")
        response.headers.add("Access-Control-Allow-Methods", "*")
        return response
    
    try:
        plans = storage.list_meal_plans()
        response = jsonify({
            "success": True,
            "plans": plans
        })
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    except Exception as e:
        response = jsonify({"error": str(e)})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 500


@app.route("/api/meal-plan/<plan_id>", methods=["GET"])
def get_meal_plan(plan_id):
    """Get a specific meal plan by ID."""
    try:
        plan = storage.load_meal_plan(plan_id)
        if not plan:
            return jsonify({"error": "Meal plan not found"}), 404
        
        # Convert to same format as generate endpoints
        if len(plan.daily_plans) == 1:
            # Daily plan
            daily_plan = plan.daily_plans[0]
            plan_data = {
                "id": plan.id,
                "name": plan.name,
                "date": plan.start_date.isoformat(),
                "total_calories": daily_plan.total_calories,
                "total_protein": daily_plan.total_protein,
                "meals": []
            }
            
            if daily_plan.breakfast:
                plan_data["meals"].append({
                    "type": "breakfast",
                    "name": daily_plan.breakfast.name,
                    "description": daily_plan.breakfast.description or "",
                    "calories": daily_plan.breakfast.nutrition.calories,
                    "protein": daily_plan.breakfast.nutrition.protein_g,
                    "carbs": daily_plan.breakfast.nutrition.carbs_g,
                    "fat": daily_plan.breakfast.nutrition.fat_g,
                    "prep_time": daily_plan.breakfast.prep_time_minutes,
                    "cook_time": daily_plan.breakfast.cook_time_minutes,
                    "ingredients": [ing.name for ing in (daily_plan.breakfast.ingredients or [])],
                    "instructions": daily_plan.breakfast.instructions or [],
                })
            
            if daily_plan.lunch:
                plan_data["meals"].append({
                    "type": "lunch",
                    "name": daily_plan.lunch.name,
                    "description": daily_plan.lunch.description or "",
                    "calories": daily_plan.lunch.nutrition.calories,
                    "protein": daily_plan.lunch.nutrition.protein_g,
                    "carbs": daily_plan.lunch.nutrition.carbs_g,
                    "fat": daily_plan.lunch.nutrition.fat_g,
                    "prep_time": daily_plan.lunch.prep_time_minutes,
                    "cook_time": daily_plan.lunch.cook_time_minutes,
                    "ingredients": [ing.name for ing in (daily_plan.lunch.ingredients or [])],
                    "instructions": daily_plan.lunch.instructions or [],
                })
            
            if daily_plan.dinner:
                plan_data["meals"].append({
                    "type": "dinner",
                    "name": daily_plan.dinner.name,
                    "description": daily_plan.dinner.description or "",
                    "calories": daily_plan.dinner.nutrition.calories,
                    "protein": daily_plan.dinner.nutrition.protein_g,
                    "carbs": daily_plan.dinner.nutrition.carbs_g,
                    "fat": daily_plan.dinner.nutrition.fat_g,
                    "prep_time": daily_plan.dinner.prep_time_minutes,
                    "cook_time": daily_plan.dinner.cook_time_minutes,
                    "ingredients": [ing.name for ing in (daily_plan.dinner.ingredients or [])],
                    "instructions": daily_plan.dinner.instructions or [],
                })
            
            for snack in daily_plan.snacks:
                plan_data["meals"].append({
                    "type": "snack",
                    "name": snack.name,
                    "description": snack.description or "",
                    "calories": snack.nutrition.calories,
                    "protein": snack.nutrition.protein_g,
                    "carbs": snack.nutrition.carbs_g,
                    "fat": snack.nutrition.fat_g,
                    "prep_time": snack.prep_time_minutes,
                    "cook_time": snack.cook_time_minutes,
                    "ingredients": [ing.name for ing in (snack.ingredients or [])],
                    "instructions": snack.instructions or [],
                })
        else:
            # Weekly plan
            plan_data = {
                "id": plan.id,
                "name": plan.name,
                "start_date": plan.start_date.isoformat(),
                "end_date": plan.end_date.isoformat(),
                "average_calories": plan.average_daily_calories,
                "days": []
            }
            
            for daily_plan in plan.daily_plans:
                day_data = {
                    "date": daily_plan.date.isoformat(),
                    "total_calories": daily_plan.total_calories,
                    "total_protein": daily_plan.total_protein,
                    "meals": []
                }
                
                if daily_plan.breakfast:
                    day_data["meals"].append({
                        "type": "breakfast",
                        "name": daily_plan.breakfast.name,
                        "description": daily_plan.breakfast.description or "",
                        "calories": daily_plan.breakfast.nutrition.calories,
                        "protein": daily_plan.breakfast.nutrition.protein_g,
                        "carbs": daily_plan.breakfast.nutrition.carbs_g,
                        "fat": daily_plan.breakfast.nutrition.fat_g,
                        "instructions": daily_plan.breakfast.instructions or [],
                        "ingredients": [ing.name for ing in (daily_plan.breakfast.ingredients or [])],
                    })
                if daily_plan.lunch:
                    day_data["meals"].append({
                        "type": "lunch",
                        "name": daily_plan.lunch.name,
                        "description": daily_plan.lunch.description or "",
                        "calories": daily_plan.lunch.nutrition.calories,
                        "protein": daily_plan.lunch.nutrition.protein_g,
                        "carbs": daily_plan.lunch.nutrition.carbs_g,
                        "fat": daily_plan.lunch.nutrition.fat_g,
                        "instructions": daily_plan.lunch.instructions or [],
                        "ingredients": [ing.name for ing in (daily_plan.lunch.ingredients or [])],
                    })
                if daily_plan.dinner:
                    day_data["meals"].append({
                        "type": "dinner",
                        "name": daily_plan.dinner.name,
                        "description": daily_plan.dinner.description or "",
                        "calories": daily_plan.dinner.nutrition.calories,
                        "protein": daily_plan.dinner.nutrition.protein_g,
                        "carbs": daily_plan.dinner.nutrition.carbs_g,
                        "fat": daily_plan.dinner.nutrition.fat_g,
                        "instructions": daily_plan.dinner.instructions or [],
                        "ingredients": [ing.name for ing in (daily_plan.dinner.ingredients or [])],
                    })
                for snack in daily_plan.snacks:
                    day_data["meals"].append({
                        "type": "snack",
                        "name": snack.name,
                        "description": snack.description or "",
                        "calories": snack.nutrition.calories,
                        "protein": snack.nutrition.protein_g,
                        "carbs": snack.nutrition.carbs_g,
                        "fat": snack.nutrition.fat_g,
                        "instructions": snack.instructions or [],
                        "ingredients": [ing.name for ing in (snack.ingredients or [])],
                    })
                
                plan_data["days"].append(day_data)
        
        return jsonify({
            "success": True,
            "plan": plan_data
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/meal-plan/<plan_id>", methods=["PUT"])
def update_meal_plan(plan_id):
    """Update a meal plan entry."""
    try:
        plan = storage.load_meal_plan(plan_id)
        if not plan:
            return jsonify({"error": "Meal plan not found"}), 404
        
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Update meal entry
        date_str = data.get("date")
        meal_type = data.get("meal_type")  # breakfast, lunch, dinner, snack
        meal_data = data.get("meal")
        
        if not date_str or not meal_type:
            return jsonify({"error": "Date and meal_type required"}), 400
        
        target_date = datetime.fromisoformat(date_str).date()
        
        # Find the daily plan for this date
        daily_plan = None
        for dp in plan.daily_plans:
            if dp.date == target_date:
                daily_plan = dp
                break
        
        if not daily_plan:
            return jsonify({"error": "Date not found in plan"}), 404
        
        # Create recipe from meal data
        if meal_data:
            nutrition = NutritionInfo(
                calories=meal_data.get("calories", 0),
                protein_g=meal_data.get("protein", 0),
                carbs_g=meal_data.get("carbs", 0),
                fat_g=meal_data.get("fat", 0),
            )
            
            # Ensure at least one ingredient (required by validation)
            ingredients_list = meal_data.get("ingredients", [])
            if not ingredients_list:
                ingredients_list = [meal_data.get("name", "Ingredients")]
            
            ingredients = [
                Ingredient(name=ing, quantity=1, unit="") 
                for ing in ingredients_list
            ]
            
            # Ensure at least one instruction (required by validation)
            instructions_list = meal_data.get("instructions", [])
            if not instructions_list:
                instructions_list = ["Prepare as desired"]
            
            recipe = Recipe(
                id=meal_data.get("id", f"meal_{target_date}_{meal_type}"),
                name=meal_data.get("name", ""),
                description=meal_data.get("description", ""),
                ingredients=ingredients,
                instructions=instructions_list,
                nutrition=nutrition,
                prep_time_minutes=meal_data.get("prep_time", 0),
                cook_time_minutes=meal_data.get("cook_time", 0),
                servings=1,
                meal_type=meal_type
            )
            
            # Update the meal in the daily plan
            if meal_type == "breakfast":
                daily_plan.breakfast = recipe
            elif meal_type == "lunch":
                daily_plan.lunch = recipe
            elif meal_type == "dinner":
                daily_plan.dinner = recipe
            elif meal_type == "snack":
                # For snacks, replace or add
                if not daily_plan.snacks:
                    daily_plan.snacks = []
                daily_plan.snacks = [recipe]  # Replace all snacks with this one
        else:
            # Remove meal
            if meal_type == "breakfast":
                daily_plan.breakfast = None
            elif meal_type == "lunch":
                daily_plan.lunch = None
            elif meal_type == "dinner":
                daily_plan.dinner = None
            elif meal_type == "snack":
                daily_plan.snacks = []
        
        # Save updated plan
        storage.save_meal_plan(plan, overwrite_existing=True)
        
        return jsonify({"success": True, "message": "Meal plan updated"})
    except Exception as e:
        return jsonify({"error": str(e), "traceback": traceback.format_exc()}), 500

