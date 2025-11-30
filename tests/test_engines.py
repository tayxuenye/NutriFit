"""Tests for NutriFit engines."""

from datetime import date

import pytest

from nutrifit.engines.embedding_engine import EmbeddingEngine
from nutrifit.engines.llm_engine import LocalLLMEngine
from nutrifit.engines.meal_planner import MealPlannerEngine
from nutrifit.engines.workout_planner import WorkoutPlannerEngine
from nutrifit.models.user import DietaryPreference, FitnessGoal, UserProfile


class TestEmbeddingEngine:
    """Tests for EmbeddingEngine."""

    def test_embed_text(self):
        """Test embedding a single text."""
        engine = EmbeddingEngine()
        embedding = engine.embed("This is a test sentence")
        assert embedding is not None
        assert len(embedding) > 0

    def test_embed_batch(self):
        """Test batch embedding."""
        engine = EmbeddingEngine()
        texts = ["First sentence", "Second sentence", "Third sentence"]
        embeddings = engine.embed_batch(texts)
        assert len(embeddings) == 3

    def test_similarity(self):
        """Test cosine similarity calculation."""
        engine = EmbeddingEngine()
        emb1 = engine.embed("healthy breakfast oatmeal protein")
        emb2 = engine.embed("healthy breakfast oatmeal fiber")

        sim_similar = engine.similarity(emb1, emb2)
        sim_self = engine.similarity(emb1, emb1)

        # Same text should have similarity of 1
        assert sim_self > 0.99
        # Similar texts should have positive similarity
        assert sim_similar > 0

    def test_find_similar(self):
        """Test finding similar items."""
        engine = EmbeddingEngine()
        items = [
            "chicken salad with vegetables",
            "beef steak with potatoes",
            "vegetable stir fry",
            "chocolate cake dessert",
        ]
        results = engine.find_similar("healthy vegetarian meal", items, top_k=2)

        assert len(results) == 2
        # Each result should be (index, item, score)
        assert all(len(r) == 3 for r in results)


class TestLLMEngine:
    """Tests for LocalLLMEngine."""

    def test_fallback_mode(self):
        """Test that fallback mode works without a model."""
        engine = LocalLLMEngine(use_fallback=True)
        assert engine._use_fallback is True

    def test_suggest_meal_fallback(self):
        """Test meal suggestion in fallback mode."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_meal(
            dietary_preferences=["vegetarian"],
            available_ingredients=["rice", "beans", "vegetables"],
            meal_type="dinner",
            calorie_target=500,
        )
        assert suggestion is not None
        assert len(suggestion) > 0

    def test_suggest_workout_fallback(self):
        """Test workout suggestion in fallback mode."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_workout(
            fitness_goals=["strength"],
            available_equipment=["dumbbells"],
            duration_minutes=30,
            difficulty="intermediate",
        )
        assert suggestion is not None
        assert len(suggestion) > 0

    def test_get_status(self):
        """Test getting engine status."""
        engine = LocalLLMEngine(use_fallback=True)
        status = engine.get_status()
        assert "model_loaded" in status
        assert "using_fallback" in status


class TestMealPlannerEngine:
    """Tests for MealPlannerEngine."""

    @pytest.fixture
    def user_profile(self):
        """Create a test user profile."""
        return UserProfile(
            name="Test User",
            age=30,
            weight_kg=70.0,
            height_cm=175.0,
            dietary_preferences=[DietaryPreference.VEGETARIAN],
            fitness_goals=[FitnessGoal.MAINTENANCE],
            pantry_items=["rice", "vegetables", "tofu"],
        )

    def test_find_matching_recipes(self, user_profile):
        """Test finding recipes matching user preferences."""
        planner = MealPlannerEngine()
        matches = planner.find_matching_recipes(user_profile, "breakfast", top_k=3)

        assert len(matches) > 0
        assert all(isinstance(m, tuple) for m in matches)

    def test_generate_daily_plan(self, user_profile):
        """Test generating a daily meal plan."""
        planner = MealPlannerEngine()
        plan = planner.generate_daily_plan(user_profile, date.today())

        assert plan.date == date.today()
        # At least one meal should be present
        assert plan.breakfast is not None or plan.lunch is not None or plan.dinner is not None

    def test_generate_weekly_plan(self, user_profile):
        """Test generating a weekly meal plan."""
        planner = MealPlannerEngine()
        plan = planner.generate_weekly_plan(user_profile)

        assert plan is not None
        assert len(plan.daily_plans) == 7
        assert plan.id is not None

    def test_search_recipes(self):
        """Test recipe search functionality."""
        planner = MealPlannerEngine()
        results = planner.search_recipes("high protein chicken", top_k=5)

        assert len(results) > 0
        for recipe, score in results:
            assert recipe.id is not None
            assert 0 <= score <= 1


class TestWorkoutPlannerEngine:
    """Tests for WorkoutPlannerEngine."""

    @pytest.fixture
    def user_profile(self):
        """Create a test user profile for workouts."""
        return UserProfile(
            name="Fit User",
            age=25,
            weight_kg=75.0,
            height_cm=180.0,
            fitness_goals=[FitnessGoal.MUSCLE_GAIN],
            available_equipment=["dumbbells", "barbell", "bench"],
        )

    def test_find_matching_workouts(self, user_profile):
        """Test finding workouts matching user preferences."""
        planner = WorkoutPlannerEngine()
        matches = planner.find_matching_workouts(user_profile, top_k=3)

        assert len(matches) > 0
        assert all(isinstance(m, tuple) for m in matches)

    def test_generate_daily_plan(self, user_profile):
        """Test generating a daily workout plan."""
        planner = WorkoutPlannerEngine()
        plan = planner.generate_daily_plan(user_profile, date.today())

        assert plan.date == date.today()
        # Either a workout or rest day
        assert isinstance(plan.is_rest_day, bool)

    def test_generate_weekly_plan(self, user_profile):
        """Test generating a weekly workout plan."""
        planner = WorkoutPlannerEngine()
        plan = planner.generate_weekly_plan(user_profile, workout_days_per_week=4)

        assert plan is not None
        assert len(plan.daily_plans) == 7
        assert plan.total_workout_days > 0

    def test_search_workouts(self):
        """Test workout search functionality."""
        planner = WorkoutPlannerEngine()
        results = planner.search_workouts("upper body strength", top_k=5)

        assert len(results) > 0
        for workout, score in results:
            assert workout.id is not None
            assert 0 <= score <= 1

    def test_estimate_calories_burned(self, user_profile):
        """Test calorie burn estimation."""
        planner = WorkoutPlannerEngine()
        plan = planner.generate_weekly_plan(user_profile)
        calories = planner.estimate_weekly_calories_burned(plan, user_profile.weight_kg)

        assert calories >= 0
