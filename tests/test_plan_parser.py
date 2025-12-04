"""Tests for the plan parser module."""

import pytest
from datetime import date

from nutrifit.parsers.plan_parser import PlanParser
from nutrifit.models.user import UserProfile, FitnessGoal, DietaryPreference


@pytest.fixture
def parser():
    """Create a parser instance."""
    return PlanParser()


@pytest.fixture
def user_profile():
    """Create a test user profile."""
    return UserProfile(
        name="Test User",
        age=30,
        weight_kg=70,
        height_cm=175,
        gender="male",
        dietary_preferences=[DietaryPreference.NONE],
        fitness_goals=[FitnessGoal.MAINTENANCE],
        daily_calorie_target=2000
    )


def test_parse_single_day_meal_plan(parser, user_profile):
    """Test parsing a single-day meal plan."""
    llm_text = """
    Here's your meal plan for today:
    
    🍳 Breakfast: Oatmeal with berries (~400 kcal, Protein: 15g, Carbs: 60g, Fat: 10g)
    🥗 Lunch: Grilled chicken salad (~500 kcal, Protein: 40g, Carbs: 30g, Fat: 20g)
    🍽️ Dinner: Salmon with vegetables (~600 kcal, Protein: 45g, Carbs: 40g, Fat: 25g)
    🍎 Snack: Greek yogurt (~200 kcal, Protein: 15g, Carbs: 20g, Fat: 5g)
    """
    
    meal_plan = parser.parse_meal_plan(llm_text, user_profile)
    
    assert meal_plan is not None
    assert meal_plan.name.startswith("AI Generated Meal Plan")
    assert len(meal_plan.daily_plans) == 1
    
    daily_plan = meal_plan.daily_plans[0]
    assert daily_plan.breakfast is not None
    assert daily_plan.lunch is not None
    assert daily_plan.dinner is not None
    assert len(daily_plan.snacks) == 1
    
    # Check nutrition values
    assert daily_plan.breakfast.nutrition.calories == 400
    assert daily_plan.breakfast.nutrition.protein_g == 15
    assert daily_plan.lunch.nutrition.calories == 500


def test_parse_multi_day_meal_plan(parser, user_profile):
    """Test parsing a multi-day meal plan."""
    llm_text = """
    **Day 1:**
    🍳 Breakfast: Scrambled eggs (~350 kcal, Protein: 20g, Carbs: 10g, Fat: 25g)
    🥗 Lunch: Turkey sandwich (~450 kcal, Protein: 30g, Carbs: 50g, Fat: 15g)
    🍽️ Dinner: Pasta with marinara (~700 kcal, Protein: 25g, Carbs: 100g, Fat: 20g)
    
    **Day 2:**
    🍳 Breakfast: Smoothie bowl (~400 kcal, Protein: 15g, Carbs: 70g, Fat: 10g)
    🥗 Lunch: Quinoa salad (~500 kcal, Protein: 20g, Carbs: 60g, Fat: 20g)
    🍽️ Dinner: Grilled steak (~650 kcal, Protein: 50g, Carbs: 30g, Fat: 35g)
    """
    
    meal_plan = parser.parse_meal_plan(llm_text, user_profile)
    
    assert meal_plan is not None
    assert len(meal_plan.daily_plans) == 2
    assert meal_plan.duration_days == 2
    
    # Check first day
    day1 = meal_plan.daily_plans[0]
    assert day1.breakfast.name == "Scrambled eggs"
    assert day1.lunch.name == "Turkey sandwich"
    
    # Check second day
    day2 = meal_plan.daily_plans[1]
    assert day2.breakfast.name == "Smoothie bowl"
    assert day2.dinner.name == "Grilled steak"


def test_parse_workout_plan(parser, user_profile):
    """Test parsing a workout plan."""
    llm_text = """
    **Day 1 - Upper Body:**
    - Bench Press: 4 sets × 8 reps (Rest: 90s)
    - Pull-ups: 3 sets × 10 reps (Rest: 60s)
    - Shoulder Press: 3 sets × 12 reps (Rest: 60s)
    - Bicep Curls: 3 sets × 15 reps (Rest: 45s)
    
    **Day 2 - Lower Body:**
    - Squats: 4 sets × 10 reps (Rest: 90s)
    - Deadlifts: 3 sets × 8 reps (Rest: 120s)
    - Lunges: 3 sets × 12 reps (Rest: 60s)
    - Calf Raises: 3 sets × 20 reps (Rest: 45s)
    
    **Day 3 - Rest Day:**
    Active recovery - light stretching or walking
    """
    
    workout_plan = parser.parse_workout_plan(llm_text, user_profile)
    
    assert workout_plan is not None
    assert workout_plan.name.startswith("AI Generated Workout Plan")
    assert len(workout_plan.daily_plans) == 3
    
    # Check first day
    day1 = workout_plan.daily_plans[0]
    assert not day1.is_rest_day
    assert len(day1.workouts) == 1
    assert len(day1.workouts[0].exercises) == 4
    
    # Check exercises
    bench_press = day1.workouts[0].exercises[0]
    assert bench_press.name == "Bench Press"
    assert bench_press.sets == 4
    assert bench_press.reps == 8
    assert bench_press.rest_seconds == 90
    
    # Check rest day
    day3 = workout_plan.daily_plans[2]
    assert day3.is_rest_day
    assert len(day3.workouts) == 0


def test_parse_meal_plan_without_macros(parser, user_profile):
    """Test parsing a meal plan without explicit macro information."""
    llm_text = """
    🍳 Breakfast: Pancakes (~500 kcal)
    🥗 Lunch: Chicken wrap (~600 kcal)
    🍽️ Dinner: Beef stir-fry (~700 kcal)
    """
    
    meal_plan = parser.parse_meal_plan(llm_text, user_profile)
    
    assert meal_plan is not None
    assert len(meal_plan.daily_plans) == 1
    
    # Check that macros were estimated
    daily_plan = meal_plan.daily_plans[0]
    assert daily_plan.breakfast.nutrition.protein_g > 0
    assert daily_plan.breakfast.nutrition.carbs_g > 0
    assert daily_plan.breakfast.nutrition.fat_g > 0


def test_parse_workout_with_duration(parser, user_profile):
    """Test parsing a workout with duration-based exercises."""
    llm_text = """
    **Day 1 - Cardio:**
    - Running: 30 minutes
    - Cycling: 20 minutes
    - Jump Rope: 10 minutes
    """
    
    workout_plan = parser.parse_workout_plan(llm_text, user_profile)
    
    assert workout_plan is not None
    assert len(workout_plan.daily_plans) == 1
    
    day1 = workout_plan.daily_plans[0]
    assert len(day1.workouts[0].exercises) == 3
    
    running = day1.workouts[0].exercises[0]
    assert running.name == "Running"
    assert running.duration_seconds == 30 * 60


def test_parse_empty_text_raises_error(parser, user_profile):
    """Test that parsing empty text raises an error."""
    with pytest.raises(ValueError, match="Could not extract"):
        parser.parse_meal_plan("", user_profile)
    
    with pytest.raises(ValueError, match="Could not extract"):
        parser.parse_workout_plan("", user_profile)


def test_estimate_macros(parser):
    """Test macro estimation from calories."""
    protein, carbs, fat = parser._estimate_macros(2000)
    
    # Check that macros are reasonable
    assert protein > 0
    assert carbs > 0
    assert fat > 0
    
    # Check that they roughly add up to the calorie target
    # Protein: 4 cal/g, Carbs: 4 cal/g, Fat: 9 cal/g
    estimated_calories = protein * 4 + carbs * 4 + fat * 9
    assert abs(estimated_calories - 2000) < 100  # Within 100 calories


def test_extract_days(parser):
    """Test day extraction from text."""
    text = """
    **Day 1:**
    Some content for day 1
    
    **Day 2:**
    Some content for day 2
    
    **Day 3:**
    Some content for day 3
    """
    
    days = parser._extract_days(text)
    
    assert len(days) == 3
    assert 1 in days
    assert 2 in days
    assert 3 in days
    assert "content for day 1" in days[1]
    assert "content for day 2" in days[2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
