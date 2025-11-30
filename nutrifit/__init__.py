"""
NutriFit - AI-powered offline nutrition and workout assistant.

This package provides personalized meal plans and workout routines
based on user preferences, fitness goals, and available resources.
"""

__version__ = "0.1.0"
__author__ = "NutriFit Team"

# Export main API functions (Requirement 11)
from nutrifit.api import (
    generate_meal_plan,
    generate_workout_plan,
    optimize_shopping_list,
    track_progress,
)

# Export display functions (Requirement 10.3, 10.4)
from nutrifit.display import (
    display_meal_plan,
    display_workout_plan,
    display_shopping_list,
    display_progress,
)

__all__ = [
    "generate_meal_plan",
    "generate_workout_plan",
    "optimize_shopping_list",
    "track_progress",
    "display_meal_plan",
    "display_workout_plan",
    "display_shopping_list",
    "display_progress",
]