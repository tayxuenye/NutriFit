"""Tests for NutriFit data models."""

from datetime import date

from nutrifit.models.plan import DailyMealPlan
from nutrifit.models.progress import ProgressEntry, ProgressTracker
from nutrifit.models.recipe import Ingredient, NutritionInfo, Recipe
from nutrifit.models.user import DietaryPreference, FitnessGoal, UserProfile
from nutrifit.models.workout import Equipment, Exercise, ExerciseType, MuscleGroup, Workout


class TestUserProfile:
    """Tests for UserProfile model."""

    def test_create_user_profile(self):
        """Test creating a basic user profile."""
        profile = UserProfile(
            name="Test User",
            age=30,
            weight_kg=70.0,
            height_cm=175.0,
        )
        assert profile.name == "Test User"
        assert profile.age == 30
        assert profile.daily_calorie_target is not None

    def test_user_profile_with_preferences(self):
        """Test user profile with dietary preferences and fitness goals."""
        profile = UserProfile(
            name="Fit User",
            age=25,
            weight_kg=65.0,
            height_cm=165.0,
            dietary_preferences=[DietaryPreference.VEGETARIAN],
            fitness_goals=[FitnessGoal.WEIGHT_LOSS],
        )
        assert DietaryPreference.VEGETARIAN in profile.dietary_preferences
        assert FitnessGoal.WEIGHT_LOSS in profile.fitness_goals

    def test_user_profile_calorie_adjustment_weight_loss(self):
        """Test that weight loss goal reduces calorie target."""
        profile_normal = UserProfile(
            name="Normal",
            age=30,
            weight_kg=70.0,
            height_cm=175.0,
        )
        profile_weight_loss = UserProfile(
            name="Weight Loss",
            age=30,
            weight_kg=70.0,
            height_cm=175.0,
            fitness_goals=[FitnessGoal.WEIGHT_LOSS],
        )
        assert profile_weight_loss.daily_calorie_target is not None
        assert profile_normal.daily_calorie_target is not None
        assert profile_weight_loss.daily_calorie_target < profile_normal.daily_calorie_target

    def test_user_profile_serialization(self):
        """Test user profile to_dict and from_dict."""
        profile = UserProfile(
            name="Test",
            age=30,
            weight_kg=70.0,
            height_cm=175.0,
            dietary_preferences=[DietaryPreference.VEGAN],
            fitness_goals=[FitnessGoal.MUSCLE_GAIN],
            allergies=["nuts"],
            pantry_items=["rice", "beans"],
        )
        data = profile.to_dict()
        restored = UserProfile.from_dict(data)

        assert restored.name == profile.name
        assert restored.age == profile.age
        assert restored.weight_kg == profile.weight_kg
        assert DietaryPreference.VEGAN in restored.dietary_preferences
        assert FitnessGoal.MUSCLE_GAIN in restored.fitness_goals


class TestRecipe:
    """Tests for Recipe model."""

    def test_create_recipe(self):
        """Test creating a recipe."""
        recipe = Recipe(
            id="test_001",
            name="Test Recipe",
            description="A test recipe",
            ingredients=[
                Ingredient("flour", 200, "g"),
                Ingredient("eggs", 2, "large"),
            ],
            instructions=["Mix ingredients", "Bake"],
            nutrition=NutritionInfo(
                calories=300,
                protein_g=10,
                carbs_g=40,
                fat_g=8,
            ),
            prep_time_minutes=10,
            cook_time_minutes=20,
            servings=4,
            meal_type="dinner",
        )
        assert recipe.name == "Test Recipe"
        assert recipe.total_time_minutes == 30
        assert len(recipe.ingredients) == 2

    def test_recipe_contains_ingredient(self):
        """Test checking for ingredient presence."""
        recipe = Recipe(
            id="test_002",
            name="Egg Recipe",
            description="Recipe with eggs",
            ingredients=[Ingredient("eggs", 2, "large")],
            instructions=["Cook eggs"],
            nutrition=NutritionInfo(calories=150, protein_g=12, carbs_g=1, fat_g=10),
            prep_time_minutes=5,
            cook_time_minutes=5,
            servings=1,
            meal_type="breakfast",
        )
        assert recipe.contains_ingredient("eggs")
        assert recipe.contains_ingredient("EGGS")
        assert not recipe.contains_ingredient("flour")

    def test_recipe_get_searchable_text(self):
        """Test generating searchable text."""
        recipe = Recipe(
            id="test_003",
            name="Healthy Salad",
            description="Fresh and nutritious",
            ingredients=[Ingredient("lettuce", 100, "g")],
            instructions=["Mix"],
            nutrition=NutritionInfo(calories=50, protein_g=2, carbs_g=8, fat_g=1),
            prep_time_minutes=10,
            cook_time_minutes=0,
            servings=1,
            meal_type="lunch",
            tags=["healthy", "quick"],
            dietary_info=["vegan", "gluten_free"],
        )
        text = recipe.get_searchable_text()
        assert "Healthy Salad" in text
        assert "lettuce" in text
        assert "vegan" in text


class TestWorkout:
    """Tests for Workout model."""

    def test_create_exercise(self):
        """Test creating an exercise."""
        exercise = Exercise(
            id="ex_001",
            name="Push-ups",
            description="Classic push-up",
            muscle_groups=[MuscleGroup.CHEST, MuscleGroup.TRICEPS],
            exercise_type=ExerciseType.COMPOUND,
            sets=3,
            reps=10,
        )
        assert exercise.name == "Push-ups"
        assert MuscleGroup.CHEST in exercise.muscle_groups

    def test_exercise_equipment_check(self):
        """Test equipment availability check."""
        exercise = Exercise(
            id="ex_002",
            name="Barbell Squat",
            description="Squat with barbell",
            muscle_groups=[MuscleGroup.QUADRICEPS],
            exercise_type=ExerciseType.COMPOUND,
            equipment_needed=[Equipment("barbell", "free_weights")],
        )
        assert exercise.requires_equipment(["barbell", "dumbbells"])
        assert not exercise.requires_equipment(["dumbbells"])

    def test_create_workout(self):
        """Test creating a complete workout."""
        exercises = [
            Exercise(
                id="ex_003",
                name="Squats",
                description="Bodyweight squats",
                muscle_groups=[MuscleGroup.QUADRICEPS],
                exercise_type=ExerciseType.COMPOUND,
            )
        ]
        workout = Workout(
            id="wrk_001",
            name="Quick Workout",
            description="A quick bodyweight workout",
            exercises=exercises,
            workout_type="strength",
            duration_minutes=20,
        )
        assert workout.name == "Quick Workout"
        assert workout.total_duration_minutes == 30  # 20 + 5 warmup + 5 cooldown


class TestMealPlan:
    """Tests for meal plan models."""

    def test_daily_meal_plan(self):
        """Test creating a daily meal plan."""
        breakfast = Recipe(
            id="b_001",
            name="Oatmeal",
            description="Healthy oatmeal",
            ingredients=[Ingredient("oats", 60, "g")],
            instructions=["Cook oats"],
            nutrition=NutritionInfo(calories=300, protein_g=10, carbs_g=50, fat_g=5),
            prep_time_minutes=5,
            cook_time_minutes=5,
            servings=1,
            meal_type="breakfast",
        )
        plan = DailyMealPlan(date=date.today(), breakfast=breakfast)
        assert plan.breakfast is not None
        assert plan.total_calories == 300

    def test_meal_plan_get_all_recipes(self):
        """Test getting all recipes from a meal plan."""
        recipes = [
            Recipe(
                id=f"r_{i}",
                name=f"Recipe {i}",
                description="Test",
                ingredients=[],
                instructions=[],
                nutrition=NutritionInfo(calories=100, protein_g=5, carbs_g=15, fat_g=3),
                prep_time_minutes=5,
                cook_time_minutes=5,
                servings=1,
                meal_type=["breakfast", "lunch", "dinner"][i % 3],
            )
            for i in range(3)
        ]
        daily_plan = DailyMealPlan(
            date=date.today(),
            breakfast=recipes[0],
            lunch=recipes[1],
            dinner=recipes[2],
        )
        all_recipes = daily_plan.get_all_recipes()
        assert len(all_recipes) == 3


class TestProgressTracker:
    """Tests for progress tracking."""

    def test_add_progress_entry(self):
        """Test adding a progress entry."""
        tracker = ProgressTracker(user_id="test_user")
        entry = ProgressEntry(
            date=date.today(),
            weight_kg=70.0,
            calories_consumed=2000,
        )
        tracker.add_entry(entry)
        assert len(tracker.entries) == 1

    def test_progress_summary(self):
        """Test getting progress summary."""
        tracker = ProgressTracker(user_id="test_user")
        entry = ProgressEntry(
            date=date.today(),
            weight_kg=70.0,
            workouts_completed=1,
        )
        tracker.add_entry(entry)
        summary = tracker.get_summary()
        assert summary["total_entries"] == 1
        assert summary["latest_weight"] == 70.0

    def test_progress_serialization(self):
        """Test progress tracker serialization."""
        tracker = ProgressTracker(user_id="test_user")
        tracker.add_entry(ProgressEntry(date=date.today(), weight_kg=70.0))

        data = tracker.to_dict()
        restored = ProgressTracker.from_dict(data)

        assert restored.user_id == tracker.user_id
        assert len(restored.entries) == len(tracker.entries)
