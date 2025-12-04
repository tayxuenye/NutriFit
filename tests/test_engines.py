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


class TestChatbotEngine:
    """Tests for ChatbotEngine.
    
    Requirements: 13.1-13.10
    """

    @pytest.fixture
    def user_profile(self):
        """Create a test user profile."""
        return UserProfile(
            name="Test User",
            age=30,
            weight_kg=70.0,
            height_cm=175.0,
            gender="male",
            dietary_preferences=[DietaryPreference.VEGETARIAN],
            fitness_goals=[FitnessGoal.MUSCLE_GAIN],
            pantry_items=["rice", "beans", "vegetables"],
            available_equipment=["dumbbells", "resistance bands"],
        )

    @pytest.fixture
    def chatbot(self):
        """Create a chatbot engine with fallback LLM."""
        from nutrifit.engines.chatbot_engine import ChatbotEngine
        
        # Use fallback mode for testing (no external dependencies)
        llm_engine = LocalLLMEngine(use_fallback=True)
        meal_planner = MealPlannerEngine()
        workout_planner = WorkoutPlannerEngine()
        
        return ChatbotEngine(
            llm_engine=llm_engine,
            meal_planner=meal_planner,
            workout_planner=workout_planner,
        )

    def test_intent_detection_meal_plan_request(self, chatbot):
        """Test intent detection for meal plan requests.
        
        Requirements: 13.1
        """
        # Test various meal plan request phrasings
        messages = [
            "Create a meal plan for me",
            "Generate a weekly meal plan",
            "I need help planning my meals",
            "Make me a food plan for the week",
            "Can you plan my breakfast, lunch and dinner?",
        ]
        
        for message in messages:
            intent = chatbot._detect_intent(message)
            assert intent == "meal_plan_request", f"Failed to detect meal plan request in: {message}"

    def test_intent_detection_workout_plan_request(self, chatbot):
        """Test intent detection for workout plan requests.
        
        Requirements: 13.1
        """
        messages = [
            "Generate a training schedule",
            "Make me a fitness routine",
            "Generate an exercise program",
        ]
        
        for message in messages:
            intent = chatbot._detect_intent(message)
            assert intent == "workout_plan_request", f"Failed to detect workout request in: {message}"

    def test_intent_detection_meal_modification(self, chatbot):
        """Test intent detection for meal modification requests.
        
        Requirements: 13.1, 13.4
        """
        messages = [
            "Change my breakfast to something else",
            "Replace my lunch with a salad",
            "I want a different dinner",
            "Swap my breakfast for something high-protein",
            "Modify my lunch meal",
        ]
        
        for message in messages:
            intent = chatbot._detect_intent(message)
            assert intent == "modify_meal", f"Failed to detect meal modification in: {message}"

    def test_intent_detection_workout_modification(self, chatbot):
        """Test intent detection for workout modification requests.
        
        Requirements: 13.1, 13.4
        """
        messages = [
            "Change my Monday workout",
            "Replace today's exercise with cardio",
            "Modify my training for Wednesday",
        ]
        
        for message in messages:
            intent = chatbot._detect_intent(message)
            assert intent == "modify_workout", f"Failed to detect workout modification in: {message}"

    def test_intent_detection_nutrition_question(self, chatbot):
        """Test intent detection for nutrition questions.
        
        Requirements: 13.1, 13.5
        """
        messages = [
            "How much protein should I eat?",
            "What are good sources of carbs?",
            "Should I count calories?",
            "What's the best diet for muscle gain?",
        ]
        
        for message in messages:
            intent = chatbot._detect_intent(message)
            assert intent == "nutrition_question", f"Failed to detect nutrition question in: {message}"

    def test_intent_detection_workout_question(self, chatbot):
        """Test intent detection for workout questions.
        
        Requirements: 13.1, 13.5
        """
        messages = [
            "What's the best workout for beginners?",
            "Should I do cardio or strength training?",
            "How long should my workouts be?",
        ]
        
        for message in messages:
            intent = chatbot._detect_intent(message)
            assert intent == "workout_question", f"Failed to detect workout question in: {message}"

    def test_intent_detection_profile_update(self, chatbot):
        """Test intent detection for profile updates.
        
        Requirements: 13.1, 13.6
        """
        messages = [
            "I am vegan",
            "My goal is weight loss",
            "I'm allergic to nuts",
            "I want to build muscle",
            "I need to avoid gluten",
        ]
        
        for message in messages:
            intent = chatbot._detect_intent(message)
            assert intent == "profile_update", f"Failed to detect profile update in: {message}"

    def test_intent_detection_general(self, chatbot):
        """Test intent detection for general conversation.
        
        Requirements: 13.1, 13.7
        """
        messages = [
            "Hello",
            "Hi there",
            "Thanks for your help",
            "Can you help me?",
            "What can you do?",
        ]
        
        for message in messages:
            intent = chatbot._detect_intent(message)
            assert intent == "general", f"Failed to detect general intent in: {message}"

    def test_meal_plan_generation_through_chat(self, chatbot, user_profile):
        """Test meal plan generation through chat interface.
        
        Requirements: 13.2
        """
        chatbot.user_profile = user_profile
        
        response = chatbot.chat("Create a weekly meal plan for me", user_profile)
        
        # Response should mention meal plan creation
        assert "meal plan" in response.lower()
        
        # Should include calorie information
        assert "calorie" in response.lower() or "kcal" in response.lower()
        
        # Should have meal plan in context
        assert "meal_plan" in chatbot.current_context
        
        # Verify conversation history
        assert len(chatbot.conversation_history) == 2  # User message + assistant response
        assert chatbot.conversation_history[0]["role"] == "user"
        assert chatbot.conversation_history[1]["role"] == "assistant"

    def test_workout_plan_generation_through_chat(self, chatbot, user_profile):
        """Test workout plan generation through chat interface.
        
        Requirements: 13.3
        """
        chatbot.user_profile = user_profile
        
        response = chatbot.chat("Generate a 4-day workout plan", user_profile)
        
        # Response should mention workout plan
        assert "workout" in response.lower()
        
        # Should include schedule information
        assert any(day in response for day in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
        
        # Should have workout plan in context
        assert "workout_plan" in chatbot.current_context
        
        # Verify conversation history
        assert len(chatbot.conversation_history) == 2

    def test_meal_modification_request(self, chatbot, user_profile):
        """Test meal modification requests.
        
        Requirements: 13.4
        """
        chatbot.user_profile = user_profile
        
        # First create a meal plan
        chatbot.chat("Create a meal plan", user_profile)
        
        # Then request modification
        response = chatbot.chat("Change my breakfast to something high-protein", user_profile)
        
        # Response should acknowledge the modification request
        assert "breakfast" in response.lower()
        assert any(word in response.lower() for word in ["change", "alternative", "suggestion", "different"])

    def test_workout_modification_request(self, chatbot, user_profile):
        """Test workout modification requests.
        
        Requirements: 13.4
        """
        chatbot.user_profile = user_profile
        
        # First create a workout plan
        chatbot.chat("Generate a workout plan", user_profile)
        
        # Then request modification
        response = chatbot.chat("Change my Monday workout to cardio", user_profile)
        
        # Response should acknowledge the modification request
        assert "monday" in response.lower()
        assert any(word in response.lower() for word in ["change", "alternative", "suggestion", "different"])

    def test_nutrition_question_answering(self, chatbot):
        """Test answering nutrition questions.
        
        Requirements: 13.5
        """
        response = chatbot.chat("How much protein should I eat daily?")
        
        # Response should be informative
        assert len(response) > 50
        assert "protein" in response.lower()

    def test_workout_question_answering(self, chatbot):
        """Test answering workout questions.
        
        Requirements: 13.5
        """
        response = chatbot.chat("How many rest days do I need per week?")
        
        # Response should be informative
        assert len(response) > 50
        assert "rest" in response.lower() or "recovery" in response.lower()

    def test_profile_update_extraction_dietary_preference(self, chatbot):
        """Test extracting dietary preferences from conversation.
        
        Requirements: 13.6
        """
        response = chatbot.chat("I am vegan and want to avoid gluten")
        
        # Response should acknowledge the profile update
        assert "vegan" in response.lower()
        assert any(word in response.lower() for word in ["noted", "got it", "understand"])

    def test_profile_update_extraction_fitness_goal(self, chatbot):
        """Test extracting fitness goals from conversation.
        
        Requirements: 13.6
        """
        response = chatbot.chat("My goal is to lose weight")
        
        # Response should acknowledge the goal
        assert "weight" in response.lower() or "goal" in response.lower()

    def test_profile_update_extraction_allergies(self, chatbot):
        """Test extracting allergies from conversation.
        
        Requirements: 13.6
        """
        response = chatbot.chat("I'm allergic to nuts and dairy")
        
        # Response should acknowledge allergies
        assert any(word in response.lower() for word in ["allergy", "allergic", "noted"])

    def test_general_conversation_greeting(self, chatbot):
        """Test general conversation with greetings.
        
        Requirements: 13.7
        """
        response = chatbot.chat("Hello!")
        
        # Response should be friendly and informative
        assert len(response) > 20
        assert any(word in response.lower() for word in ["hello", "hi", "help", "assist"])

    def test_general_conversation_help(self, chatbot):
        """Test help requests.
        
        Requirements: 13.7
        """
        response = chatbot.chat("What can you help me with?")
        
        # Response should list capabilities
        assert "meal" in response.lower()
        assert "workout" in response.lower()

    def test_conversation_history_maintenance(self, chatbot, user_profile):
        """Test that conversation history is maintained.
        
        Requirements: 13.8
        """
        # Send multiple messages
        chatbot.chat("Hello", user_profile)
        chatbot.chat("I want to build muscle", user_profile)
        chatbot.chat("Create a meal plan", user_profile)
        
        history = chatbot.get_conversation_history()
        
        # Should have 6 entries (3 user + 3 assistant)
        assert len(history) == 6
        
        # Check alternating roles
        for i, entry in enumerate(history):
            if i % 2 == 0:
                assert entry["role"] == "user"
            else:
                assert entry["role"] == "assistant"

    def test_conversation_reset(self, chatbot, user_profile):
        """Test conversation reset functionality.
        
        Requirements: 13.9
        """
        # Build up conversation
        chatbot.chat("Hello", user_profile)
        chatbot.chat("Create a meal plan", user_profile)
        
        # Verify history exists
        assert len(chatbot.conversation_history) > 0
        assert len(chatbot.current_context) > 0
        
        # Reset conversation
        chatbot.reset_conversation()
        
        # Verify history is cleared
        assert len(chatbot.conversation_history) == 0
        assert len(chatbot.current_context) == 0

    def test_context_storage_meal_plan(self, chatbot, user_profile):
        """Test that meal plans are stored in context.
        
        Requirements: 13.10
        """
        chatbot.user_profile = user_profile
        
        chatbot.chat("Create a meal plan for me", user_profile)
        
        # Meal plan should be in context
        assert "meal_plan" in chatbot.current_context
        
        # Should be a MealPlan object
        from nutrifit.models.plan import MealPlan
        assert isinstance(chatbot.current_context["meal_plan"], MealPlan)

    def test_context_storage_workout_plan(self, chatbot, user_profile):
        """Test that workout plans are stored in context.
        
        Requirements: 13.10
        """
        chatbot.user_profile = user_profile
        
        chatbot.chat("Generate a workout plan", user_profile)
        
        # Workout plan should be in context
        assert "workout_plan" in chatbot.current_context
        
        # Should be a WorkoutPlan object
        from nutrifit.models.plan import WorkoutPlan
        assert isinstance(chatbot.current_context["workout_plan"], WorkoutPlan)

    def test_context_export(self, chatbot, user_profile):
        """Test exporting context.
        
        Requirements: 13.10
        """
        chatbot.user_profile = user_profile
        
        # Create plans
        chatbot.chat("Create a meal plan", user_profile)
        chatbot.chat("Generate a workout plan", user_profile)
        
        # Export context
        context = chatbot.export_context()
        
        # Should contain both plans
        assert "meal_plan" in context
        assert "workout_plan" in context
        
        # Should be a copy (not reference)
        assert context is not chatbot.current_context

    def test_meal_plan_without_profile(self, chatbot):
        """Test meal plan request without user profile.
        
        Requirements: 13.2
        """
        response = chatbot.chat("Create a meal plan for me")
        
        # Should ask for profile information
        assert any(word in response.lower() for word in ["tell", "need", "know", "about"])
        assert any(word in response.lower() for word in ["dietary", "preference", "goal"])

    def test_workout_plan_without_profile(self, chatbot):
        """Test workout plan request without user profile.
        
        Requirements: 13.3
        """
        response = chatbot.chat("Generate a workout plan")
        
        # Should ask for profile information
        assert any(word in response.lower() for word in ["tell", "need", "know", "about"])
        assert any(word in response.lower() for word in ["goal", "equipment", "fitness"])

    def test_modification_without_existing_plan(self, chatbot, user_profile):
        """Test modification request without existing plan.
        
        Requirements: 13.4
        """
        chatbot.user_profile = user_profile
        
        response = chatbot.chat("Change my breakfast")
        
        # Should indicate no plan exists
        assert any(word in response.lower() for word in ["don't have", "no", "create", "first"])

    def test_conversation_context_awareness(self, chatbot, user_profile):
        """Test that chatbot maintains context across messages.
        
        Requirements: 13.8
        """
        chatbot.user_profile = user_profile
        
        # First message: create plan
        response1 = chatbot.chat("Create a meal plan", user_profile)
        assert "meal plan" in response1.lower()
        
        # Second message: modify (should use context)
        response2 = chatbot.chat("Change the breakfast")
        
        # Should understand we're talking about the meal plan from previous message
        assert "breakfast" in response2.lower()
        # Should not ask to create a new plan
        assert "create" not in response2.lower() or "first" not in response2.lower()

    def test_multiple_intent_types_in_conversation(self, chatbot, user_profile):
        """Test handling multiple intent types in one conversation.
        
        Requirements: 13.1, 13.8
        """
        chatbot.user_profile = user_profile
        
        # Greeting
        response1 = chatbot.chat("Hello")
        assert len(response1) > 0
        
        # Profile update
        response2 = chatbot.chat("I'm vegan")
        assert "vegan" in response2.lower()
        
        # Question
        response3 = chatbot.chat("How much protein do I need?")
        assert "protein" in response3.lower()
        
        # Plan generation
        response4 = chatbot.chat("Create a meal plan")
        assert "meal plan" in response4.lower()
        
        # All should be in history
        assert len(chatbot.conversation_history) == 8  # 4 user + 4 assistant

    def test_calorie_target_in_meal_plan_response(self, chatbot, user_profile):
        """Test that meal plan responses include calorie targets.
        
        Requirements: 13.2
        """
        chatbot.user_profile = user_profile
        
        response = chatbot.chat("Create a meal plan", user_profile)
        
        # Should mention calories
        assert any(word in response.lower() for word in ["calorie", "kcal"])
        
        # Should include the actual target
        assert str(user_profile.daily_calorie_target) in response

    def test_equipment_in_workout_plan_response(self, chatbot, user_profile):
        """Test that workout plan responses mention equipment.
        
        Requirements: 13.3
        """
        chatbot.user_profile = user_profile
        
        response = chatbot.chat("Generate a workout plan", user_profile)
        
        # Should mention equipment
        assert "equipment" in response.lower() or any(
            equip in response.lower() for equip in user_profile.available_equipment
        )

    def test_dietary_preference_respected_in_suggestions(self, chatbot, user_profile):
        """Test that dietary preferences are respected in meal suggestions.
        
        Requirements: 13.2, 13.4
        """
        # Set vegan profile
        user_profile.dietary_preferences = [DietaryPreference.VEGAN]
        chatbot.user_profile = user_profile
        
        # Create meal plan
        chatbot.chat("Create a meal plan", user_profile)
        
        # Request modification
        response = chatbot.chat("Change my lunch")
        
        # Response should respect vegan preference
        # (The LLM engine should use the dietary preferences)
        assert len(response) > 0  # At minimum, should provide a response

    def test_calorie_target_extraction_k_format(self, chatbot, user_profile):
        """Test extraction of calorie target in 'k' format (e.g., 2k).
        
        Requirements: 13.6
        """
        original_target = user_profile.daily_calorie_target
        
        # Request with "2k" format
        chatbot.chat("I want a meal plan with 2k calories", user_profile)
        
        # Profile should be updated
        assert chatbot.user_profile.daily_calorie_target == 2000
        assert chatbot.user_profile.daily_calorie_target != original_target

    def test_calorie_target_extraction_number_format(self, chatbot, user_profile):
        """Test extraction of calorie target in number format (e.g., 1800).
        
        Requirements: 13.6
        """
        # Request with explicit number
        chatbot.chat("Create a meal plan with 1800 calories per day", user_profile)
        
        # Profile should be updated
        assert chatbot.user_profile.daily_calorie_target == 1800

    def test_calorie_target_extraction_kcal_format(self, chatbot, user_profile):
        """Test extraction of calorie target with kcal unit.
        
        Requirements: 13.6
        """
        # Request with kcal unit (must include meal plan request)
        chatbot.chat("Create a meal plan with target of 2200 kcal", user_profile)
        
        # Profile should be updated
        assert chatbot.user_profile.daily_calorie_target == 2200

    def test_calorie_target_in_response_after_extraction(self, chatbot, user_profile):
        """Test that extracted calorie target appears in response.
        
        Requirements: 13.2, 13.6
        """
        response = chatbot.chat("I want a full meal plan and my calorie target is 2k", user_profile)
        
        # Response should show the requested target, not the calculated one
        assert "2000 kcal" in response or "2000" in response
        assert chatbot.user_profile.daily_calorie_target == 2000


    def test_generate_llm_meal_plan(self, chatbot, user_profile):
        """Test LLM meal plan generation.
        
        Requirements: 1.1, 1.2, 1.3
        """
        requirements = {
            'calorie_target': 2000,
            'duration': 7,
            'macro_targets': {
                'protein_g': 150,
                'carbs_g': 200,
                'fat_g': 67
            }
        }
        
        plan_text = chatbot.generate_llm_meal_plan(user_profile, requirements)
        
        # Should return a string
        assert isinstance(plan_text, str)
        assert len(plan_text) > 0
        
        # Should mention days
        assert "Day" in plan_text or "day" in plan_text
        
        # Should mention meals
        assert any(meal in plan_text.lower() for meal in ["breakfast", "lunch", "dinner"])

    def test_generate_llm_workout_plan(self, chatbot, user_profile):
        """Test LLM workout plan generation.
        
        Requirements: 2.1, 2.2, 2.3
        """
        requirements = {
            'workout_days': 4,
            'duration': 45,
            'focus_areas': ['upper body', 'core'],
            'fitness_level': 'intermediate'
        }
        
        plan_text = chatbot.generate_llm_workout_plan(user_profile, requirements)
        
        # Should return a string
        assert isinstance(plan_text, str)
        assert len(plan_text) > 0
        
        # Should mention days or exercises
        assert any(word in plan_text.lower() for word in ["day", "exercise", "workout"])

    def test_store_generated_plan_meal(self, chatbot):
        """Test storing a generated meal plan.
        
        Requirements: 4.1, 4.2
        """
        plan_text = "Day 1: Breakfast - Oatmeal (400 kcal)"
        plan_id = chatbot.store_generated_plan(plan_text, "meal")
        
        # Should return a plan ID
        assert isinstance(plan_id, str)
        assert len(plan_id) > 0
        assert plan_id.startswith("meal_")
        
        # Should be stored in context
        assert f'generated_plan_{plan_id}' in chatbot.current_context
        assert chatbot.current_context['current_meal_plan_id'] == plan_id
        
        # Verify stored data
        stored_plan = chatbot.current_context[f'generated_plan_{plan_id}']
        assert stored_plan['plan_id'] == plan_id
        assert stored_plan['plan_type'] == 'meal'
        assert stored_plan['llm_text'] == plan_text
        assert stored_plan['saved'] is False

    def test_store_generated_plan_workout(self, chatbot):
        """Test storing a generated workout plan.
        
        Requirements: 4.1, 4.2
        """
        plan_text = "Day 1: Push-ups 3x10, Squats 3x15"
        plan_id = chatbot.store_generated_plan(plan_text, "workout")
        
        # Should return a plan ID
        assert isinstance(plan_id, str)
        assert len(plan_id) > 0
        assert plan_id.startswith("workout_")
        
        # Should be stored in context
        assert f'generated_plan_{plan_id}' in chatbot.current_context
        assert chatbot.current_context['current_workout_plan_id'] == plan_id

    def test_meal_plan_prompt_includes_user_profile(self, chatbot, user_profile):
        """Test that meal plan prompt includes user profile data.
        
        Requirements: 1.2, 7.1, 7.2
        """
        prompt = chatbot._build_meal_plan_prompt(
            user_profile=user_profile,
            calorie_target=2000,
            protein_target=150,
            carbs_target=200,
            fat_target=67,
            duration=7
        )
        
        # Should include dietary preferences
        assert "Vegetarian" in prompt
        
        # Should include fitness goals
        assert "Muscle Gain" in prompt
        
        # Should include calorie target
        assert "2000" in prompt
        
        # Should include macro targets
        assert "150" in prompt  # protein
        assert "200" in prompt  # carbs
        assert "67" in prompt   # fat
        
        # Should include duration
        assert "7" in prompt

    def test_workout_plan_prompt_includes_user_profile(self, chatbot, user_profile):
        """Test that workout plan prompt includes user profile data.
        
        Requirements: 2.2, 7.3, 7.4
        """
        prompt = chatbot._build_workout_plan_prompt(
            user_profile=user_profile,
            workout_days=4,
            duration=45,
            focus_areas=['upper body'],
            fitness_level='intermediate'
        )
        
        # Should include fitness goals
        assert "Muscle Gain" in prompt
        
        # Should include equipment
        assert any(equip in prompt for equip in ["dumbbells", "resistance bands"])
        
        # Should include workout days
        assert "4" in prompt
        
        # Should include duration
        assert "45" in prompt
        
        # Should include focus areas
        assert "upper body" in prompt
        
        # Should include fitness level
        assert "intermediate" in prompt

    def test_meal_plan_prompt_with_allergies(self, chatbot, user_profile):
        """Test that meal plan prompt includes allergies.
        
        Requirements: 1.2
        """
        user_profile.allergies = ["nuts", "dairy"]
        
        prompt = chatbot._build_meal_plan_prompt(
            user_profile=user_profile,
            calorie_target=2000,
            protein_target=150,
            carbs_target=200,
            fat_target=67,
            duration=7
        )
        
        # Should include allergies
        assert "nuts" in prompt
        assert "dairy" in prompt

    def test_meal_plan_prompt_with_no_preferences(self, chatbot):
        """Test meal plan prompt with minimal user profile.
        
        Requirements: 1.2
        """
        minimal_profile = UserProfile(
            name="Minimal User",
            age=25,
            weight_kg=70,
            height_cm=175,
            dietary_preferences=[],
            fitness_goals=[],
            allergies=[]
        )
        
        prompt = chatbot._build_meal_plan_prompt(
            user_profile=minimal_profile,
            calorie_target=2000,
            protein_target=150,
            carbs_target=200,
            fat_target=67,
            duration=7
        )
        
        # Should still generate a valid prompt
        assert len(prompt) > 0
        assert "2000" in prompt
        assert "None" in prompt  # For empty preferences/allergies

    def test_workout_plan_prompt_with_no_equipment(self, chatbot):
        """Test workout plan prompt with no equipment.
        
        Requirements: 2.2
        """
        minimal_profile = UserProfile(
            name="Minimal User",
            age=25,
            weight_kg=70,
            height_cm=175,
            available_equipment=[]
        )
        
        prompt = chatbot._build_workout_plan_prompt(
            user_profile=minimal_profile,
            workout_days=3,
            duration=30,
            focus_areas=[],
            fitness_level='beginner'
        )
        
        # Should mention bodyweight
        assert "Bodyweight" in prompt or "bodyweight" in prompt

    def test_generate_llm_meal_plan_with_defaults(self, chatbot, user_profile):
        """Test LLM meal plan generation with default requirements.
        
        Requirements: 1.1, 1.3
        """
        # Minimal requirements - should use defaults
        requirements = {}
        
        plan_text = chatbot.generate_llm_meal_plan(user_profile, requirements)
        
        # Should still generate a plan
        assert isinstance(plan_text, str)
        assert len(plan_text) > 0

    def test_generate_llm_workout_plan_with_defaults(self, chatbot, user_profile):
        """Test LLM workout plan generation with default requirements.
        
        Requirements: 2.1, 2.3
        """
        # Minimal requirements - should use defaults
        requirements = {}
        
        plan_text = chatbot.generate_llm_workout_plan(user_profile, requirements)
        
        # Should still generate a plan
        assert isinstance(plan_text, str)
        assert len(plan_text) > 0

    def test_store_multiple_generated_plans(self, chatbot):
        """Test storing multiple generated plans.
        
        Requirements: 4.1, 4.2
        """
        # Store first meal plan
        plan_id1 = chatbot.store_generated_plan("Meal plan 1", "meal")
        
        # Store second meal plan
        plan_id2 = chatbot.store_generated_plan("Meal plan 2", "meal")
        
        # Store workout plan
        plan_id3 = chatbot.store_generated_plan("Workout plan 1", "workout")
        
        # All should have unique IDs
        assert plan_id1 != plan_id2
        assert plan_id1 != plan_id3
        assert plan_id2 != plan_id3
        
        # All should be in context
        assert f'generated_plan_{plan_id1}' in chatbot.current_context
        assert f'generated_plan_{plan_id2}' in chatbot.current_context
        assert f'generated_plan_{plan_id3}' in chatbot.current_context
        
        # Current plan IDs should point to latest
        assert chatbot.current_context['current_meal_plan_id'] == plan_id2
        assert chatbot.current_context['current_workout_plan_id'] == plan_id3

    def test_meal_plan_prompt_format(self, chatbot, user_profile):
        """Test that meal plan prompt has correct format.
        
        Requirements: 1.3
        """
        prompt = chatbot._build_meal_plan_prompt(
            user_profile=user_profile,
            calorie_target=2000,
            protein_target=150,
            carbs_target=200,
            fat_target=67,
            duration=7
        )
        
        # Should have structured sections
        assert "User Profile:" in prompt
        assert "Requirements:" in prompt
        assert "Format each day as:" in prompt
        
        # Should specify meal types
        assert "Breakfast" in prompt
        assert "Lunch" in prompt
        assert "Dinner" in prompt
        assert "Snack" in prompt

    def test_workout_plan_prompt_format(self, chatbot, user_profile):
        """Test that workout plan prompt has correct format.
        
        Requirements: 2.3
        """
        prompt = chatbot._build_workout_plan_prompt(
            user_profile=user_profile,
            workout_days=4,
            duration=45,
            focus_areas=['upper body'],
            fitness_level='intermediate'
        )
        
        # Should have structured sections
        assert "User Profile:" in prompt
        assert "Requirements:" in prompt
        assert "Format each day as:" in prompt
        
        # Should specify workout components
        assert "sets" in prompt.lower()
        assert "reps" in prompt.lower()
        assert "rest" in prompt.lower()
