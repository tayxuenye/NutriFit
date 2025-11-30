"""
Display formatting functions for NutriFit plans and data.

This module provides formatted display functions satisfying
Requirements 10.3 and 10.4 for readable plan display.
"""

from datetime import date

from nutrifit.models.plan import DailyMealPlan, DailyWorkoutPlan, MealPlan, WorkoutPlan
from nutrifit.models.progress import ProgressTracker
from nutrifit.utils.shopping_list import ShoppingList


def display_meal_plan(plan: MealPlan | DailyMealPlan, detailed: bool = True) -> str:
    """
    Display a meal plan in a readable format.
    
    This function satisfies Requirement 10.3: display meal plans with complete information.
    
    Args:
        plan: Meal plan to display (can be MealPlan or DailyMealPlan)
        detailed: Whether to show detailed nutritional information
        
    Returns:
        Formatted string representation of the meal plan
    """
    lines = []
    
    if isinstance(plan, MealPlan):
        lines.append("=" * 60)
        lines.append(f"📅 MEAL PLAN: {plan.name}")
        lines.append("=" * 60)
        lines.append(f"Period: {plan.start_date} to {plan.end_date}")
        lines.append(f"Duration: {plan.duration_days} days")
        lines.append(f"Target Calories: {plan.target_calories_per_day} kcal/day")
        lines.append(f"Average Daily Calories: {plan.average_daily_calories:.0f} kcal")
        lines.append("")
        
        for daily in plan.daily_plans:
            lines.append(display_meal_plan(daily, detailed))
            lines.append("")
    else:
        # DailyMealPlan
        day_name = plan.date.strftime("%A, %B %d, %Y")
        lines.append(f"\n📆 {day_name}")
        lines.append("-" * 60)
        
        if plan.breakfast:
            lines.append(f"\n🌅 BREAKFAST: {plan.breakfast.name}")
            if detailed:
                lines.append(f"   Description: {plan.breakfast.description[:80]}...")
                lines.append(f"   Calories: {plan.breakfast.nutrition.calories} kcal")
                lines.append(f"   Protein: {plan.breakfast.nutrition.protein_g:.1f}g | "
                           f"Carbs: {plan.breakfast.nutrition.carbs_g:.1f}g | "
                           f"Fat: {plan.breakfast.nutrition.fat_g:.1f}g")
                lines.append(f"   Prep Time: {plan.breakfast.prep_time_minutes} min | "
                           f"Cook Time: {plan.breakfast.cook_time_minutes} min")
                if plan.breakfast.ingredients:
                    lines.append(f"   Ingredients: {', '.join([i.name for i in plan.breakfast.ingredients[:5]])}")
                    if len(plan.breakfast.ingredients) > 5:
                        lines.append(f"   ... and {len(plan.breakfast.ingredients) - 5} more")
        
        if plan.lunch:
            lines.append(f"\n🌞 LUNCH: {plan.lunch.name}")
            if detailed:
                lines.append(f"   Description: {plan.lunch.description[:80]}...")
                lines.append(f"   Calories: {plan.lunch.nutrition.calories} kcal")
                lines.append(f"   Protein: {plan.lunch.nutrition.protein_g:.1f}g | "
                           f"Carbs: {plan.lunch.nutrition.carbs_g:.1f}g | "
                           f"Fat: {plan.lunch.nutrition.fat_g:.1f}g")
                lines.append(f"   Prep Time: {plan.lunch.prep_time_minutes} min | "
                           f"Cook Time: {plan.lunch.cook_time_minutes} min")
                if plan.lunch.ingredients:
                    lines.append(f"   Ingredients: {', '.join([i.name for i in plan.lunch.ingredients[:5]])}")
                    if len(plan.lunch.ingredients) > 5:
                        lines.append(f"   ... and {len(plan.lunch.ingredients) - 5} more")
        
        if plan.dinner:
            lines.append(f"\n🌙 DINNER: {plan.dinner.name}")
            if detailed:
                lines.append(f"   Description: {plan.dinner.description[:80]}...")
                lines.append(f"   Calories: {plan.dinner.nutrition.calories} kcal")
                lines.append(f"   Protein: {plan.dinner.nutrition.protein_g:.1f}g | "
                           f"Carbs: {plan.dinner.nutrition.carbs_g:.1f}g | "
                           f"Fat: {plan.dinner.nutrition.fat_g:.1f}g")
                lines.append(f"   Prep Time: {plan.dinner.prep_time_minutes} min | "
                           f"Cook Time: {plan.dinner.cook_time_minutes} min")
                if plan.dinner.ingredients:
                    lines.append(f"   Ingredients: {', '.join([i.name for i in plan.dinner.ingredients[:5]])}")
                    if len(plan.dinner.ingredients) > 5:
                        lines.append(f"   ... and {len(plan.dinner.ingredients) - 5} more")
        
        if plan.snacks:
            for snack in plan.snacks:
                lines.append(f"\n🍎 SNACK: {snack.name}")
                if detailed:
                    lines.append(f"   Calories: {snack.nutrition.calories} kcal")
        
        lines.append(f"\n📊 Daily Total: {plan.total_calories} kcal | "
                    f"Protein: {plan.total_protein:.1f}g")
    
    return "\n".join(lines)


def display_workout_plan(plan: WorkoutPlan | DailyWorkoutPlan, detailed: bool = True) -> str:
    """
    Display a workout plan in a readable format.
    
    This function satisfies Requirement 10.4: display workout plans with complete information.
    
    Args:
        plan: Workout plan to display (can be WorkoutPlan or DailyWorkoutPlan)
        detailed: Whether to show detailed exercise information
        
    Returns:
        Formatted string representation of the workout plan
    """
    lines = []
    
    if isinstance(plan, WorkoutPlan):
        lines.append("=" * 60)
        lines.append(f"💪 WORKOUT PLAN: {plan.name}")
        lines.append("=" * 60)
        lines.append(f"Period: {plan.start_date} to {plan.end_date}")
        lines.append(f"Duration: {plan.duration_days} days")
        lines.append(f"Workout Days: {plan.total_workout_days} days")
        lines.append(f"Target: {plan.workout_days_per_week} workouts/week")
        lines.append("")
        
        for daily in plan.daily_plans:
            lines.append(display_workout_plan(daily, detailed))
            lines.append("")
    else:
        # DailyWorkoutPlan
        day_name = plan.date.strftime("%A, %B %d, %Y")
        lines.append(f"\n📆 {day_name}")
        lines.append("-" * 60)
        
        if plan.is_rest_day:
            lines.append("\n🛌 REST DAY")
            if plan.notes:
                lines.append(f"   {plan.notes}")
        else:
            for workout in plan.workouts:
                lines.append(f"\n🏋️ {workout.name.upper()}")
                if detailed:
                    lines.append(f"   Type: {workout.workout_type} | "
                               f"Difficulty: {workout.difficulty}")
                    lines.append(f"   Duration: {workout.total_duration_minutes} minutes")
                    if workout.description:
                        lines.append(f"   Description: {workout.description[:80]}...")
                    
                    lines.append("\n   Exercises:")
                    for i, exercise in enumerate(workout.exercises, 1):
                        lines.append(f"   {i}. {exercise.name}")
                        if detailed:
                            if exercise.reps:
                                lines.append(f"      Sets: {exercise.sets} | "
                                           f"Reps: {exercise.reps} | "
                                           f"Rest: {exercise.rest_seconds}s")
                            elif exercise.duration_seconds:
                                lines.append(f"      Sets: {exercise.sets} | "
                                           f"Duration: {exercise.duration_seconds}s | "
                                           f"Rest: {exercise.rest_seconds}s")
                            if exercise.description:
                                lines.append(f"      {exercise.description[:60]}...")
            
            if not plan.workouts:
                lines.append("\n   No workouts scheduled for this day")
    
    return "\n".join(lines)


def display_shopping_list(shopping_list: ShoppingList, group_by_category: bool = True) -> str:
    """
    Display a shopping list in a readable format.
    
    Args:
        shopping_list: Shopping list to display
        group_by_category: Whether to group items by category
        
    Returns:
        Formatted string representation of the shopping list
    """
    from nutrifit.utils.shopping_list import ShoppingListOptimizer
    
    optimizer = ShoppingListOptimizer()
    return optimizer.format_for_display(shopping_list, group_by_category)


def display_progress(tracker: ProgressTracker, days: int = 7) -> str:
    """
    Display progress summary in a readable format.
    
    Args:
        tracker: Progress tracker with entries
        days: Number of days to summarize
        
    Returns:
        Formatted string representation of progress
    """
    lines = []
    lines.append("=" * 60)
    lines.append("📊 PROGRESS SUMMARY")
    lines.append("=" * 60)
    
    summary = tracker.get_summary()
    
    lines.append(f"\nTotal Entries: {summary['total_entries']}")
    
    if summary['latest_weight']:
        lines.append(f"Latest Weight: {summary['latest_weight']:.1f} kg")
    
    if summary['weight_trend_30d'] is not None:
        trend = summary['weight_trend_30d']
        direction = "↓" if trend < 0 else "↑" if trend > 0 else "→"
        lines.append(f"30-Day Weight Trend: {direction} {abs(trend):.1f} kg")
    
    if summary['average_calories_7d']:
        lines.append(f"Average Calories (7d): {summary['average_calories_7d']:.0f} kcal")
    
    lines.append(f"Workout Adherence (7d): {summary['workout_adherence_7d']:.0f}%")
    
    # Show recent entries
    recent_entries = tracker.get_entries_in_range(
        date.today() - timedelta(days=days),
        date.today()
    )
    
    if recent_entries:
        lines.append(f"\n📈 Recent Entries (Last {days} days):")
        lines.append("-" * 60)
        for entry in recent_entries[-7:]:  # Last 7 entries
            lines.append(f"\n{entry.date}:")
            if entry.weight_kg:
                lines.append(f"  Weight: {entry.weight_kg:.1f} kg")
            if entry.calories_consumed:
                lines.append(f"  Calories: {entry.calories_consumed} kcal")
            if entry.workouts_completed:
                lines.append(f"  Workouts: {entry.workouts_completed}")
            if entry.meals_followed:
                lines.append(f"  Meals: {entry.meals_followed}")
            if entry.mood_rating:
                lines.append(f"  Mood: {entry.mood_rating}/10")
            if entry.energy_rating:
                lines.append(f"  Energy: {entry.energy_rating}/10")
    
    return "\n".join(lines)


# Import timedelta for display_progress
from datetime import timedelta

