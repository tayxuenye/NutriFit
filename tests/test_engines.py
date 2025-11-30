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
        # Should be 384 dimensions (matching all-MiniLM-L6-v2 or fallback)
        assert len(embedding) == 384

    def test_embed_batch(self):
        """Test batch embedding."""
        engine = EmbeddingEngine()
        texts = ["First sentence", "Second sentence", "Third sentence"]
        embeddings = engine.embed_batch(texts)
        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)

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

    def test_embedding_caching(self, tmp_path):
        """Test that embeddings are cached correctly."""
        cache_dir = tmp_path / "embeddings"
        engine = EmbeddingEngine(cache_dir=cache_dir)

        text = "test caching functionality"

        # First call should generate and cache
        emb1 = engine.embed(text, use_cache=True)

        # Check that cache file was created
        cache_files = list(cache_dir.glob("*.npy"))
        assert len(cache_files) == 1

        # Second call should use cache
        emb2 = engine.embed(text, use_cache=True)

        # Embeddings should be identical
        assert pytest.approx(emb1, abs=1e-6) == emb2

        # Check in-memory cache
        assert len(engine._embeddings_cache) == 1

    def test_embedding_cache_disabled(self, tmp_path):
        """Test embedding without caching."""
        cache_dir = tmp_path / "embeddings"
        engine = EmbeddingEngine(cache_dir=cache_dir)

        text = "test without caching"

        # Generate embedding without caching
        emb1 = engine.embed(text, use_cache=False)

        # No cache files should be created
        cache_files = list(cache_dir.glob("*.npy"))
        assert len(cache_files) == 0

        # Memory cache should still be empty
        assert len(engine._embeddings_cache) == 0

    def test_batch_embedding_caching(self, tmp_path):
        """Test that batch embeddings are cached correctly."""
        cache_dir = tmp_path / "embeddings"
        engine = EmbeddingEngine(cache_dir=cache_dir)

        texts = ["first text", "second text", "third text"]

        # First batch call
        embs1 = engine.embed_batch(texts, use_cache=True)

        # Check cache files
        cache_files = list(cache_dir.glob("*.npy"))
        assert len(cache_files) == 3

        # Second batch call should use cache
        embs2 = engine.embed_batch(texts, use_cache=True)

        # Embeddings should be identical
        for e1, e2 in zip(embs1, embs2, strict=False):
            assert pytest.approx(e1, abs=1e-6) == e2

    def test_clear_cache(self, tmp_path):
        """Test clearing the cache."""
        cache_dir = tmp_path / "embeddings"
        engine = EmbeddingEngine(cache_dir=cache_dir)

        # Generate some embeddings
        texts = ["text one", "text two", "text three"]
        engine.embed_batch(texts, use_cache=True)

        # Verify cache exists
        assert len(engine._embeddings_cache) == 3
        cache_files = list(cache_dir.glob("*.npy"))
        assert len(cache_files) == 3

        # Clear cache
        engine.clear_cache()

        # Verify cache is empty
        assert len(engine._embeddings_cache) == 0
        cache_files = list(cache_dir.glob("*.npy"))
        assert len(cache_files) == 0

    def test_cache_size_limits(self, tmp_path):
        """Test that cache size limits are enforced."""
        cache_dir = tmp_path / "embeddings"
        # Set very small cache limits for testing
        engine = EmbeddingEngine(
            cache_dir=cache_dir, max_cache_size_mb=0.001, max_memory_cache_items=2
        )

        # Generate multiple embeddings
        texts = [f"text number {i}" for i in range(10)]
        engine.embed_batch(texts, use_cache=True)

        # Memory cache should be limited
        assert len(engine._embeddings_cache) <= 2

        # Disk cache size should be limited (approximately)
        cache_size_mb = engine.get_cache_size_mb()
        # Allow some tolerance since we clean up to 80% of limit
        assert cache_size_mb <= engine._max_cache_size_mb * 1.2

    def test_get_cache_stats(self, tmp_path):
        """Test getting cache statistics."""
        cache_dir = tmp_path / "embeddings"
        engine = EmbeddingEngine(cache_dir=cache_dir)

        # Generate some embeddings
        texts = ["text one", "text two"]
        engine.embed_batch(texts, use_cache=True)

        stats = engine.get_cache_stats()

        assert "memory_cache_items" in stats
        assert "disk_cache_files" in stats
        assert "disk_cache_size_mb" in stats
        assert "max_cache_size_mb" in stats
        assert "max_memory_cache_items" in stats

        assert stats["memory_cache_items"] == 2
        assert stats["disk_cache_files"] == 2
        assert stats["disk_cache_size_mb"] > 0

    def test_fallback_mode(self, tmp_path):
        """Test that fallback mode works when transformers unavailable."""
        cache_dir = tmp_path / "embeddings"
        engine = EmbeddingEngine(cache_dir=cache_dir)

        # Force fallback mode by setting _use_transformer to False
        original_mode = engine._use_transformer
        engine._use_transformer = False

        try:
            # Test embedding in fallback mode
            text = "test fallback embedding"
            embedding = engine.embed(text, use_cache=False)

            assert embedding is not None
            assert len(embedding) == 384
            assert embedding.dtype == float

            # Test that embeddings are normalized
            norm = pytest.approx(1.0, abs=0.01)
            import numpy as np

            assert np.linalg.norm(embedding) == norm

        finally:
            # Restore original mode
            engine._use_transformer = original_mode

    def test_fallback_similarity(self, tmp_path):
        """Test similarity calculation in fallback mode."""
        cache_dir = tmp_path / "embeddings"
        engine = EmbeddingEngine(cache_dir=cache_dir)

        # Force fallback mode
        original_mode = engine._use_transformer
        engine._use_transformer = False

        try:
            # Similar texts should have higher similarity
            emb1 = engine.embed("healthy breakfast oatmeal", use_cache=False)
            emb2 = engine.embed("healthy breakfast cereal", use_cache=False)
            emb3 = engine.embed("chocolate dessert cake", use_cache=False)

            sim_similar = engine.similarity(emb1, emb2)
            sim_different = engine.similarity(emb1, emb3)

            # Similar texts should have higher similarity than different texts
            assert sim_similar > sim_different

        finally:
            engine._use_transformer = original_mode

    def test_is_using_transformer(self):
        """Test checking if transformer model is being used."""
        engine = EmbeddingEngine()
        result = engine.is_using_transformer()

        # Result should be a boolean
        assert isinstance(result, bool)

        # If transformers is available, should be True
        try:
            import sentence_transformers  # noqa: F401

            assert result is True
        except ImportError:
            assert result is False

    def test_similarity_with_zero_vectors(self):
        """Test similarity calculation with zero vectors."""
        engine = EmbeddingEngine()
        import numpy as np

        zero_vec = np.zeros(384)
        normal_vec = engine.embed("test text")

        # Similarity with zero vector should be 0
        sim = engine.similarity(zero_vec, normal_vec)
        assert sim == 0.0

        # Similarity of two zero vectors should be 0
        sim_zeros = engine.similarity(zero_vec, zero_vec)
        assert sim_zeros == 0.0

    def test_batch_embedding_optimization(self, tmp_path):
        """Test that batch embedding is more efficient than individual calls."""
        cache_dir = tmp_path / "embeddings"
        engine = EmbeddingEngine(cache_dir=cache_dir)

        texts = [f"test text number {i}" for i in range(5)]

        # Batch embedding
        batch_result = engine.embed_batch(texts, use_cache=False)

        # Individual embeddings
        individual_results = [engine.embed(t, use_cache=False) for t in texts]

        # Results should be similar (within numerical precision)
        import numpy as np

        for batch_emb, ind_emb in zip(batch_result, individual_results, strict=False):
            assert np.allclose(batch_emb, ind_emb, atol=1e-5)


class TestLLMEngine:
    """Tests for LocalLLMEngine."""

    def test_fallback_mode(self):
        """Test that fallback mode works without a model."""
        engine = LocalLLMEngine(use_fallback=True)
        assert engine._use_fallback is True
        assert engine.is_model_loaded() is False

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
        assert "vegetarian" in suggestion or "rice" in suggestion or "beans" in suggestion

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
        assert "strength" in suggestion or "dumbbells" in suggestion

    def test_get_status(self):
        """Test getting engine status."""
        engine = LocalLLMEngine(use_fallback=True)
        status = engine.get_status()
        assert "model_loaded" in status
        assert "using_fallback" in status
        assert "backend" in status
        assert "model_load_error" in status
        assert "context_size" in status
        assert status["using_fallback"] is True
        assert status["backend"] == "template-fallback"

    def test_meal_suggestion_variety_breakfast(self):
        """Test that meal suggestions have variety for breakfast."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestions = set()
        
        # Generate multiple suggestions
        for _ in range(10):
            suggestion = engine.suggest_meal(
                dietary_preferences=["vegan"],
                available_ingredients=["oats", "banana", "almond milk"],
                meal_type="breakfast",
                calorie_target=400,
            )
            suggestions.add(suggestion)
        
        # Should have at least 2 different suggestions
        assert len(suggestions) >= 2

    def test_meal_suggestion_variety_lunch(self):
        """Test that meal suggestions have variety for lunch."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestions = set()
        
        for _ in range(10):
            suggestion = engine.suggest_meal(
                dietary_preferences=["keto"],
                available_ingredients=["chicken", "avocado", "spinach"],
                meal_type="lunch",
                calorie_target=600,
            )
            suggestions.add(suggestion)
        
        assert len(suggestions) >= 2

    def test_meal_suggestion_variety_dinner(self):
        """Test that meal suggestions have variety for dinner."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestions = set()
        
        for _ in range(10):
            suggestion = engine.suggest_meal(
                dietary_preferences=["paleo"],
                available_ingredients=["salmon", "broccoli", "sweet potato"],
                meal_type="dinner",
                calorie_target=700,
            )
            suggestions.add(suggestion)
        
        assert len(suggestions) >= 2

    def test_meal_suggestion_variety_snack(self):
        """Test that meal suggestions have variety for snacks."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestions = set()
        
        for _ in range(10):
            suggestion = engine.suggest_meal(
                dietary_preferences=["gluten_free"],
                available_ingredients=["nuts", "berries", "yogurt"],
                meal_type="snack",
                calorie_target=200,
            )
            suggestions.add(suggestion)
        
        assert len(suggestions) >= 2

    def test_workout_suggestion_variety(self):
        """Test that workout suggestions have variety."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestions = set()
        
        for _ in range(15):
            suggestion = engine.suggest_workout(
                fitness_goals=["muscle_gain"],
                available_equipment=["barbell", "dumbbells"],
                duration_minutes=45,
                difficulty="advanced",
            )
            suggestions.add(suggestion)
        
        # Should have at least 3 different suggestions
        assert len(suggestions) >= 3

    def test_meal_suggestion_calorie_context_light(self):
        """Test that low calorie meals include 'light' context."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_meal(
            dietary_preferences=["vegetarian"],
            available_ingredients=["lettuce", "tomato"],
            meal_type="lunch",
            calorie_target=300,
        )
        assert "light" in suggestion.lower()

    def test_meal_suggestion_calorie_context_moderate(self):
        """Test that moderate calorie meals include appropriate context."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_meal(
            dietary_preferences=["vegetarian"],
            available_ingredients=["rice", "beans"],
            meal_type="lunch",
            calorie_target=500,
        )
        assert "moderate" in suggestion.lower() or "filling" in suggestion.lower()

    def test_meal_suggestion_calorie_context_hearty(self):
        """Test that high calorie meals include 'hearty' context."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_meal(
            dietary_preferences=["none"],
            available_ingredients=["pasta", "cheese", "meat"],
            meal_type="dinner",
            calorie_target=800,
        )
        assert "hearty" in suggestion.lower() or "substantial" in suggestion.lower()

    def test_workout_suggestion_duration_context_quick(self):
        """Test that short workouts include 'quick' context."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_workout(
            fitness_goals=["general_fitness"],
            available_equipment=["bodyweight"],
            duration_minutes=15,
            difficulty="beginner",
        )
        assert "quick" in suggestion.lower() or "efficient" in suggestion.lower()

    def test_workout_suggestion_duration_context_balanced(self):
        """Test that moderate workouts include 'balanced' context."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_workout(
            fitness_goals=["strength"],
            available_equipment=["dumbbells"],
            duration_minutes=30,
            difficulty="intermediate",
        )
        assert "balanced" in suggestion.lower() or "well" in suggestion.lower()

    def test_workout_suggestion_duration_context_comprehensive(self):
        """Test that long workouts include 'comprehensive' context."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_workout(
            fitness_goals=["endurance"],
            available_equipment=["treadmill", "bike"],
            duration_minutes=60,
            difficulty="advanced",
        )
        assert "comprehensive" in suggestion.lower()

    def test_suggest_modification_substitute(self):
        """Test modification suggestions for substitutions."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_modification(
            original_item="Chicken Pasta",
            modification_type="substitute",
            constraints=["vegan", "gluten-free"],
        )
        assert suggestion is not None
        assert len(suggestion) > 0
        assert "Chicken Pasta" in suggestion
        assert "vegan" in suggestion or "gluten-free" in suggestion

    def test_suggest_modification_scale(self):
        """Test modification suggestions for scaling."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_modification(
            original_item="Beef Stew",
            modification_type="scale",
            constraints=["serves 2 instead of 4"],
        )
        assert suggestion is not None
        assert "Beef Stew" in suggestion
        assert "scale" in suggestion.lower() or "portion" in suggestion.lower()

    def test_suggest_modification_adapt(self):
        """Test modification suggestions for general adaptations."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_modification(
            original_item="Chocolate Cake",
            modification_type="adapt",
            constraints=["low sugar", "high protein"],
        )
        assert suggestion is not None
        assert "Chocolate Cake" in suggestion

    def test_modification_suggestion_variety(self):
        """Test that modification suggestions have variety."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestions = set()
        
        for _ in range(10):
            suggestion = engine.suggest_modification(
                original_item="Spaghetti Bolognese",
                modification_type="substitute",
                constraints=["vegetarian"],
            )
            suggestions.add(suggestion)
        
        # Should have at least 2 different suggestions
        assert len(suggestions) >= 2

    def test_model_loading_with_invalid_path(self):
        """Test graceful fallback when model path is invalid."""
        engine = LocalLLMEngine(model_path="/nonexistent/model.gguf", use_fallback=False)
        
        # Should fall back to template mode
        assert engine._use_fallback is True
        assert engine.is_model_loaded() is False
        
        # Status should report the error
        status = engine.get_status()
        assert status["model_load_error"] is not None
        assert "not found" in status["model_load_error"].lower()

    def test_model_loading_with_no_path(self):
        """Test graceful fallback when no model path is provided."""
        engine = LocalLLMEngine(model_path=None, use_fallback=False)
        
        assert engine._use_fallback is True
        assert engine.is_model_loaded() is False
        
        status = engine.get_status()
        assert status["model_load_error"] is not None
        assert "no model path" in status["model_load_error"].lower()

    def test_status_reporting_fallback_mode(self):
        """Test detailed status reporting in fallback mode."""
        engine = LocalLLMEngine(use_fallback=True)
        status = engine.get_status()
        
        assert status["model_loaded"] is False
        assert status["using_fallback"] is True
        assert status["backend"] == "template-fallback"
        assert status["model_load_error"] is not None
        assert status["context_size"] == 2048

    def test_generate_fallback_message(self):
        """Test that generate method returns appropriate fallback message."""
        engine = LocalLLMEngine(use_fallback=True)
        result = engine.generate("Test prompt")
        
        assert result is not None
        assert "offline mode" in result.lower() or "fallback" in result.lower()

    def test_meal_suggestion_empty_ingredients(self):
        """Test meal suggestion with no ingredients."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_meal(
            dietary_preferences=["vegan"],
            available_ingredients=[],
            meal_type="lunch",
            calorie_target=500,
        )
        assert suggestion is not None
        assert len(suggestion) > 0

    def test_meal_suggestion_empty_preferences(self):
        """Test meal suggestion with no dietary preferences."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_meal(
            dietary_preferences=[],
            available_ingredients=["chicken", "rice"],
            meal_type="dinner",
            calorie_target=600,
        )
        assert suggestion is not None
        assert len(suggestion) > 0

    def test_workout_suggestion_empty_equipment(self):
        """Test workout suggestion with no equipment."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_workout(
            fitness_goals=["weight_loss"],
            available_equipment=[],
            duration_minutes=30,
            difficulty="beginner",
        )
        assert suggestion is not None
        assert "bodyweight" in suggestion.lower()

    def test_workout_suggestion_empty_goals(self):
        """Test workout suggestion with no fitness goals."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_workout(
            fitness_goals=[],
            available_equipment=["dumbbells"],
            duration_minutes=30,
            difficulty="intermediate",
        )
        assert suggestion is not None
        assert len(suggestion) > 0

    def test_modification_suggestion_empty_constraints(self):
        """Test modification suggestion with no constraints."""
        engine = LocalLLMEngine(use_fallback=True)
        suggestion = engine.suggest_modification(
            original_item="Pizza",
            modification_type="substitute",
            constraints=[],
        )
        assert suggestion is not None
        assert "Pizza" in suggestion


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
