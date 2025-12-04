"""
Modular function interfaces for NutriFit.

This module provides high-level functions for common operations,
satisfying Requirement 11 for modular function interfaces.
"""

from datetime import date
from typing import Optional

from nutrifit.engines.embedding_engine import EmbeddingEngine
from nutrifit.engines.llm_engine import LocalLLMEngine
from nutrifit.engines.meal_planner import MealPlannerEngine
from nutrifit.engines.workout_planner import WorkoutPlannerEngine
from nutrifit.models.plan import MealPlan, WorkoutPlan
from nutrifit.models.progress import ProgressEntry
from nutrifit.models.user import UserProfile
from nutrifit.utils.shopping_list import ShoppingList, ShoppingListOptimizer
from nutrifit.utils.storage import DataStorage


# Global engines (initialized on first use)
_meal_planner: Optional[MealPlannerEngine] = None
_workout_planner: Optional[WorkoutPlannerEngine] = None
_shopping_optimizer: Optional[ShoppingListOptimizer] = None
_storage: Optional[DataStorage] = None


def _get_engines() -> tuple[MealPlannerEngine, WorkoutPlannerEngine, ShoppingListOptimizer, DataStorage]:
    """Initialize and return engines (lazy initialization)."""
    global _meal_planner, _workout_planner, _shopping_optimizer, _storage
    
    if _meal_planner is None:
        embedding_engine = EmbeddingEngine()
        # Auto-detect: use LLM if model path is available via env var
        llm_engine = LocalLLMEngine()
        _meal_planner = MealPlannerEngine(
            embedding_engine=embedding_engine,
            llm_engine=llm_engine,
        )
        _workout_planner = WorkoutPlannerEngine(
            embedding_engine=embedding_engine,
            llm_engine=llm_engine,
        )
        _shopping_optimizer = ShoppingListOptimizer()
        _storage = DataStorage()
    
    # Type narrowing - we know these are not None after initialization
    assert _meal_planner is not None
    assert _workout_planner is not None
    assert _shopping_optimizer is not None
    assert _storage is not None
    
    return _meal_planner, _workout_planner, _shopping_optimizer, _storage


def generate_meal_plan(
    user: UserProfile,
    duration_days: int = 7,
    start_date: Optional[date] = None,
    plan_name: Optional[str] = None,
) -> MealPlan:
    """
    Generate a meal plan for the specified duration.
    
    This function satisfies Requirement 11.2: generate_meal_plan function.
    
    Args:
        user: User profile with preferences and goals
        duration_days: Number of days for the plan (1 for daily, 7 for weekly)
        start_date: Start date for the plan (defaults to today)
        plan_name: Optional name for the plan
        
    Returns:
        Generated meal plan
        
    Raises:
        ValueError: If duration_days is invalid
    """
    if duration_days < 1:
        raise ValueError("Duration must be at least 1 day")
    
    meal_planner, _, _, _ = _get_engines()
    start_date = start_date or date.today()
    
    if duration_days == 1:
        daily_plan = meal_planner.generate_daily_plan(user, start_date)
        return MealPlan(
            id=f"mp_{start_date.isoformat()}",
            name=plan_name or f"Daily Plan - {start_date.isoformat()}",
            start_date=start_date,
            end_date=start_date,
            daily_plans=[daily_plan],
            target_calories_per_day=user.daily_calorie_target or 2000,
        )
    else:
        return meal_planner.generate_weekly_plan(user, start_date, plan_name)


def generate_workout_plan(
    user: UserProfile,
    duration_days: int = 7,
    start_date: Optional[date] = None,
    plan_name: Optional[str] = None,
    workout_days_per_week: int = 4,
) -> WorkoutPlan:
    """
    Generate a workout plan for the specified duration.
    
    This function satisfies Requirement 11.3: generate_workout_plan function.
    
    Args:
        user: User profile with preferences and goals
        duration_days: Number of days for the plan (defaults to 7 for weekly)
        start_date: Start date for the plan (defaults to today)
        plan_name: Optional name for the plan
        workout_days_per_week: Target workout days per week
        
    Returns:
        Generated workout plan
        
    Raises:
        ValueError: If duration_days is invalid
    """
    if duration_days < 1:
        raise ValueError("Duration must be at least 1 day")
    
    _, workout_planner, _, _ = _get_engines()
    start_date = start_date or date.today()
    
    if duration_days == 1:
        daily_plan = workout_planner.generate_daily_plan(
            user, start_date, day_number=start_date.weekday()
        )
        return WorkoutPlan(
            id=f"wp_{start_date.isoformat()}",
            name=plan_name or f"Daily Workout - {start_date.isoformat()}",
            start_date=start_date,
            end_date=start_date,
            daily_plans=[daily_plan],
            workout_days_per_week=1,
        )
    else:
        return workout_planner.generate_weekly_plan(
            user, start_date, plan_name, workout_days_per_week
        )


def optimize_shopping_list(
    meal_plan: MealPlan,
    pantry_items: Optional[list[str]] = None,
    user: Optional[UserProfile] = None,
) -> ShoppingList:
    """
    Generate and optimize a shopping list from a meal plan.
    
    This function satisfies Requirement 11.4: optimize_shopping_list function.
    
    Args:
        meal_plan: Meal plan to generate shopping list for
        pantry_items: Items already available in pantry (uses user.pantry_items if user provided)
        user: Optional user profile (used to get pantry items if not provided)
        
    Returns:
        Optimized shopping list with consolidated and categorized items
    """
    _, _, shopping_optimizer, _ = _get_engines()
    
    if pantry_items is None:
        if user:
            pantry_items = user.pantry_items
        else:
            pantry_items = []
    
    # Ensure pantry_items is a list, not a string
    if isinstance(pantry_items, str):
        # If it's a non-empty string, treat it as a single item or empty list
        pantry_items = [pantry_items] if pantry_items.strip() and len(pantry_items) > 3 else []
    
    return shopping_optimizer.generate_from_meal_plan(meal_plan, pantry_items)


def track_progress(
    entry_date: date,
    weight_kg: Optional[float] = None,
    calories_consumed: Optional[int] = None,
    calories_burned: Optional[int] = None,
    workouts_completed: int = 0,
    meals_followed: int = 0,
    user_id: str = "default",
    **kwargs,
) -> ProgressEntry:
    """
    Record progress data for a user.
    
    This function satisfies Requirement 11.5: track_progress function.
    
    Args:
        user_id: User identifier
        entry_date: Date for the progress entry
        weight_kg: Weight in kilograms
        calories_consumed: Calories consumed
        calories_burned: Calories burned
        workouts_completed: Number of workouts completed
        meals_followed: Number of meals followed from plan
        **kwargs: Additional progress fields (mood_rating, energy_rating, notes, etc.)
        
    Returns:
        Created progress entry
    """
    _, _, _, storage = _get_engines()
    
    entry = ProgressEntry(
        date=entry_date,
        weight_kg=weight_kg,
        calories_consumed=calories_consumed,
        calories_burned=calories_burned,
        workouts_completed=workouts_completed,
        meals_followed=meals_followed,
        **kwargs,
    )
    
    storage.add_progress_entry(entry, user_id=user_id)
    return entry

