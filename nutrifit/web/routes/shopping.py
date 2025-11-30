"""Shopping list routes."""

from collections import defaultdict
from datetime import date, timedelta

from flask import jsonify, request

from nutrifit.api import optimize_shopping_list
from nutrifit.web import app, storage
from nutrifit.web.utils import get_or_create_profile


@app.route("/api/shopping-list", methods=["POST", "OPTIONS"])
def generate_shopping_list():
    """Generate shopping list from all meal plans, grouped by week."""
    from datetime import date, timedelta
    import sys
    import traceback
    
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response
    
    try:
        profile = get_or_create_profile()
    except Exception as e:
        print(f"Error getting profile: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        response = jsonify({"error": f"Error getting profile: {str(e)}"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 500
    
    try:
        # Handle both JSON and form data
        data = request.json if request.is_json else (request.form.to_dict() if request.form else {})
        plan_id = data.get("plan_id") if data else None
        
        if plan_id:
            # Single plan requested
            meal_plan = storage.load_meal_plan(plan_id)
            if not meal_plan:
                response = jsonify({"error": "Meal plan not found"})
                response.headers.add("Access-Control-Allow-Origin", "*")
                return response, 404
            
            shopping_list = optimize_shopping_list(meal_plan, user=profile)
            
            # Group items by category
            by_category = {}
            for item in shopping_list.items:
                if item.category not in by_category:
                    by_category[item.category] = []
                by_category[item.category].append({
                    "name": item.name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "is_optional": item.is_optional,
                })
            
            response = jsonify({
                "success": True,
                "shopping_list": {
                    "items": [item.to_dict() for item in shopping_list.items],
                    "by_category": by_category,
                    "total_items": len(shopping_list.items),
                }
            })
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response
        else:
            # Get all meal plans and group by week
            plans = storage.list_meal_plans()
            if not plans:
                response = jsonify({"success": True, "shopping_lists_by_week": {}, "total_weeks": 0, "message": "No meal plans found. Generate a meal plan first."})
                response.headers.add("Access-Control-Allow-Origin", "*")
                return response
            
            # Group plans by week (using start_date to determine week)
            plans_by_week = defaultdict(list)
            
            for plan_info in plans:
                plan = storage.load_meal_plan(plan_info["id"])
                if plan and plan.start_date:
                    # Calculate week start (Monday of the week)
                    days_since_monday = plan.start_date.weekday()
                    week_start = plan.start_date - timedelta(days=days_since_monday)
                    week_key = week_start.isoformat()
                    plans_by_week[week_key].append(plan)
            
            # Generate shopping lists for each week
            weekly_shopping_lists = {}
            
            for week_start_str, week_plans in plans_by_week.items():
                # Combine all plans for this week
                all_items = []
                for plan in week_plans:
                    shopping_list = optimize_shopping_list(plan, user=profile)
                    all_items.extend(shopping_list.items)
                
                # Consolidate items across plans in the same week
                item_dict = defaultdict(lambda: {"quantity": 0, "unit": "", "category": "other", "is_optional": False})
                
                for item in all_items:
                    key = item.name.lower()
                    item_dict[key]["name"] = item.name
                    item_dict[key]["quantity"] += item.quantity
                    item_dict[key]["unit"] = item.unit or item_dict[key]["unit"]
                    item_dict[key]["category"] = item.category
                    item_dict[key]["is_optional"] = item.is_optional
                
                # Group by category
                by_category = {}
                for item_data in item_dict.values():
                    category = item_data["category"]
                    if category not in by_category:
                        by_category[category] = []
                    by_category[category].append({
                        "name": item_data["name"],
                        "quantity": item_data["quantity"],
                        "unit": item_data["unit"],
                        "is_optional": item_data["is_optional"],
                    })
                
                week_start_date = date.fromisoformat(week_start_str)
                week_end_date = week_start_date + timedelta(days=6)
                
                weekly_shopping_lists[week_start_str] = {
                    "week_start": week_start_str,
                    "week_end": week_end_date.isoformat(),
                    "items": list(item_dict.values()),
                    "by_category": by_category,
                    "total_items": len(item_dict),
                }
            
            response = jsonify({
                "success": True,
                "shopping_lists_by_week": weekly_shopping_lists,
                "total_weeks": len(weekly_shopping_lists),
            })
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response
    except Exception as e:
        import traceback
        error_msg = f"Error generating shopping list: {str(e)}\n{traceback.format_exc()}"
        print(error_msg, file=sys.stderr)
        sys.stderr.flush()
        response = jsonify({"error": str(e), "traceback": traceback.format_exc()})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response, 500

