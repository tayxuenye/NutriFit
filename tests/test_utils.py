"""Tests for NutriFit utilities."""

import tempfile
from datetime import date
from pathlib import Path

import pytest

from nutrifit.models.progress import ProgressEntry
from nutrifit.models.recipe import Ingredient, NutritionInfo, Recipe
from nutrifit.models.user import DietaryPreference, UserProfile
from nutrifit.utils.shopping_list import ShoppingListOptimizer
from nutrifit.utils.storage import DataStorage


class TestShoppingListOptimizer:
    """Tests for ShoppingListOptimizer."""

    @pytest.fixture
    def sample_recipes(self):
        """Create sample recipes for testing."""
        return [
            Recipe(
                id="r1",
                name="Recipe 1",
                description="Test recipe 1",
                ingredients=[
                    Ingredient("chicken breast", 200, "g"),
                    Ingredient("olive oil", 2, "tbsp"),
                    Ingredient("garlic", 2, "cloves"),
                ],
                instructions=["Cook"],
                nutrition=NutritionInfo(calories=300, protein_g=30, carbs_g=5, fat_g=15),
                prep_time_minutes=10,
                cook_time_minutes=20,
                servings=2,
                meal_type="dinner",
            ),
            Recipe(
                id="r2",
                name="Recipe 2",
                description="Test recipe 2",
                ingredients=[
                    Ingredient("chicken breast", 150, "g"),
                    Ingredient("rice", 100, "g"),
                    Ingredient("olive oil", 1, "tbsp"),
                ],
                instructions=["Cook"],
                nutrition=NutritionInfo(calories=400, protein_g=35, carbs_g=40, fat_g=12),
                prep_time_minutes=15,
                cook_time_minutes=25,
                servings=2,
                meal_type="dinner",
            ),
        ]

    def test_generate_shopping_list(self, sample_recipes):
        """Test generating a shopping list from recipes."""
        optimizer = ShoppingListOptimizer()
        shopping_list = optimizer.generate_from_recipes(sample_recipes)

        assert len(shopping_list.items) > 0
        # Should have consolidated chicken breast
        chicken_items = [i for i in shopping_list.items if "chicken" in i.name.lower()]
        assert len(chicken_items) == 1
        # Total chicken should be 350g (200 + 150)
        assert chicken_items[0].quantity == 350

    def test_categorize_ingredients(self, sample_recipes):
        """Test ingredient categorization."""
        optimizer = ShoppingListOptimizer()
        shopping_list = optimizer.generate_from_recipes(sample_recipes)

        by_category = shopping_list.get_items_by_category()
        assert "proteins" in by_category
        assert "grains" in by_category

    def test_remove_pantry_items(self, sample_recipes):
        """Test removing pantry items from shopping list."""
        optimizer = ShoppingListOptimizer()
        shopping_list = optimizer.generate_from_recipes(
            sample_recipes, pantry_items=["olive oil", "garlic"]
        )

        # Olive oil and garlic should be removed
        item_names = [i.name.lower() for i in shopping_list.items]
        assert "olive oil" not in item_names
        assert "garlic" not in item_names

    def test_format_for_display(self, sample_recipes):
        """Test formatting shopping list for display."""
        optimizer = ShoppingListOptimizer()
        shopping_list = optimizer.generate_from_recipes(sample_recipes)
        formatted = optimizer.format_for_display(shopping_list)

        assert "SHOPPING LIST" in formatted
        assert "chicken breast" in formatted.lower()


class TestDataStorage:
    """Tests for DataStorage."""

    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = DataStorage(data_dir=Path(tmpdir))
            yield storage

    def test_save_and_load_user_profile(self, temp_storage):
        """Test saving and loading user profile."""
        profile = UserProfile(
            name="Test User",
            age=30,
            weight_kg=70.0,
            height_cm=175.0,
            dietary_preferences=[DietaryPreference.VEGETARIAN],
        )

        temp_storage.save_user_profile(profile, "test_user")
        loaded = temp_storage.load_user_profile("test_user")

        assert loaded is not None
        assert loaded.name == "Test User"
        assert DietaryPreference.VEGETARIAN in loaded.dietary_preferences

    def test_list_user_profiles(self, temp_storage):
        """Test listing user profiles."""
        profile = UserProfile(
            name="User 1", age=25, weight_kg=65.0, height_cm=165.0
        )
        temp_storage.save_user_profile(profile, "user1")
        temp_storage.save_user_profile(profile, "user2")

        profiles = temp_storage.list_user_profiles()
        assert "user1" in profiles
        assert "user2" in profiles

    def test_delete_user_profile(self, temp_storage):
        """Test deleting user profile."""
        profile = UserProfile(
            name="To Delete", age=30, weight_kg=70.0, height_cm=175.0
        )
        temp_storage.save_user_profile(profile, "to_delete")
        assert temp_storage.delete_user_profile("to_delete")
        assert temp_storage.load_user_profile("to_delete") is None

    def test_add_progress_entry(self, temp_storage):
        """Test adding progress entries."""
        entry = ProgressEntry(
            date=date.today(),
            weight_kg=70.0,
            calories_consumed=2000,
        )
        temp_storage.add_progress_entry(entry, "test_user")

        tracker = temp_storage.load_progress_tracker("test_user")
        assert tracker is not None
        assert len(tracker.entries) == 1
        assert tracker.entries[0].weight_kg == 70.0

    def test_get_progress_summary(self, temp_storage):
        """Test getting progress summary."""
        entry = ProgressEntry(
            date=date.today(),
            weight_kg=70.0,
            workouts_completed=1,
        )
        temp_storage.add_progress_entry(entry, "test_user")

        summary = temp_storage.get_progress_summary("test_user")
        assert summary is not None
        assert summary["total_entries"] == 1

    def test_export_import_data(self, temp_storage):
        """Test exporting and importing all data."""
        # Create some data
        profile = UserProfile(
            name="Export Test", age=30, weight_kg=70.0, height_cm=175.0
        )
        temp_storage.save_user_profile(profile, "export_user")
        temp_storage.add_progress_entry(
            ProgressEntry(date=date.today(), weight_kg=70.0),
            "export_user",
        )

        # Export
        data = temp_storage.export_all_data("export_user")
        assert data["user_profile"] is not None
        assert data["progress"] is not None

        # Clear and reimport
        temp_storage.clear_all_data()
        temp_storage.import_data(data, "import_user")

        # Verify
        imported_profile = temp_storage.load_user_profile("import_user")
        assert imported_profile is not None
        assert imported_profile.name == "Export Test"
