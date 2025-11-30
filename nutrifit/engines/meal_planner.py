"""Meal planner engine for generating personalized meal plans."""

import random
import uuid
from datetime import date, timedelta
from typing import Any

from nutrifit.data.recipes import get_sample_recipes
from nutrifit.engines.embedding_engine import EmbeddingEngine
from nutrifit.engines.llm_engine import LocalLLMEngine
from nutrifit.models.plan import DailyMealPlan, MealPlan
from nutrifit.models.recipe import Recipe
from nutrifit.models.user import UserProfile


class MealPlannerEngine:
    """
    Engine for generating personalized meal plans.

    Uses embedding-based matching to find suitable recipes based on
    user preferences, available ingredients, and nutritional goals.
    """

    def __init__(
        self,
        embedding_engine: EmbeddingEngine | None = None,
        llm_engine: LocalLLMEngine | None = None,
        recipes: list[Recipe] | None = None,
    ):
        """Initialize the meal planner engine.

        Args:
            embedding_engine: Engine for semantic matching
            llm_engine: Engine for creative suggestions
            recipes: List of available recipes (defaults to sample recipes)
        """
        self.embedding_engine = embedding_engine or EmbeddingEngine()
        self.llm_engine = llm_engine or LocalLLMEngine()
        self.recipes = recipes or get_sample_recipes()
        self._recipe_embeddings: dict[str, Any] = {}
        self._initialize_recipe_embeddings()

    def _initialize_recipe_embeddings(self) -> None:
        """Pre-compute embeddings for all recipes."""
        texts = [recipe.get_searchable_text() for recipe in self.recipes]
        ids = [recipe.id for recipe in self.recipes]

        embeddings = self.embedding_engine.embed_batch(texts)

        for recipe_id, embedding in zip(ids, embeddings, strict=False):
            self._recipe_embeddings[recipe_id] = embedding

    def _get_dietary_filters(self, user: UserProfile) -> list[str]:
        """Convert user dietary preferences to filter strings."""
        filters = []
        for pref in user.dietary_preferences:
            filters.append(pref.value)
        return filters

    def _filter_recipes_by_diet(
        self, recipes: list[Recipe], dietary_filters: list[str]
    ) -> list[Recipe]:
        """Filter recipes based on dietary preferences.
        
        Implements strict filtering logic:
        - Vegan recipes must be marked as vegan
        - Vegetarian recipes can be vegan or vegetarian
        - Other preferences require exact match in dietary_info
        """
        if not dietary_filters:
            return recipes

        filtered = []
        for recipe in recipes:
            # Check if recipe matches ALL dietary preferences
            matches = True
            for diet_filter in dietary_filters:
                if diet_filter == "vegetarian":
                    # Vegetarian accepts both vegetarian and vegan recipes
                    if not any(
                        d in ["vegetarian", "vegan"] for d in recipe.dietary_info
                    ):
                        matches = False
                        break
                elif diet_filter == "vegan":
                    # Vegan requires strict vegan marking
                    if "vegan" not in recipe.dietary_info:
                        matches = False
                        break
                elif diet_filter == "pescatarian":
                    # Pescatarian accepts pescatarian, vegetarian, and vegan
                    if not any(
                        d in ["pescatarian", "vegetarian", "vegan"] 
                        for d in recipe.dietary_info
                    ):
                        matches = False
                        break
                else:
                    # For other preferences (keto, paleo, gluten_free, dairy_free, etc.)
                    # require exact match in dietary_info
                    if diet_filter not in recipe.dietary_info:
                        matches = False
                        break
            
            if matches:
                filtered.append(recipe)

        return filtered

    def _filter_recipes_by_allergies(
        self, recipes: list[Recipe], allergies: list[str]
    ) -> list[Recipe]:
        """Filter out recipes containing allergens.
        
        Strictly excludes any recipe that contains any allergen.
        Returns empty list if all recipes contain allergens.
        """
        if not allergies:
            return recipes

        filtered = []
        for recipe in recipes:
            contains_allergen = False
            for allergen in allergies:
                if recipe.contains_ingredient(allergen):
                    contains_allergen = True
                    break
            if not contains_allergen:
                filtered.append(recipe)

        return filtered

    def _get_recipes_by_meal_type(
        self, recipes: list[Recipe], meal_type: str
    ) -> list[Recipe]:
        """Filter recipes by meal type."""
        return [r for r in recipes if r.meal_type == meal_type]

    def _score_recipe_for_pantry(
        self, recipe: Recipe, pantry_items: list[str]
    ) -> float:
        """Score a recipe based on how many pantry items it uses.
        
        Returns a score between 0 and 1, where:
        - 1.0 means all ingredients are in pantry
        - 0.0 means no ingredients are in pantry
        - 0.5 is default when pantry is empty
        
        This ensures recipes with more pantry ingredients score higher.
        """
        if not pantry_items:
            return 0.5

        recipe_ingredients = recipe.get_ingredient_names()
        if not recipe_ingredients:
            return 0.0
        
        pantry_lower = [p.lower().strip() for p in pantry_items]

        matches = 0
        for ingredient in recipe_ingredients:
            ingredient_lower = ingredient.lower().strip()
            for pantry_item in pantry_lower:
                # Check for substring match in both directions
                if pantry_item in ingredient_lower or ingredient_lower in pantry_item:
                    matches += 1
                    break

        return matches / len(recipe_ingredients)

    def find_matching_recipes(
        self,
        user: UserProfile,
        meal_type: str,
        query: str | None = None,
        top_k: int = 5,
    ) -> list[tuple[Recipe, float]]:
        """Find recipes matching user preferences and optional query.

        Args:
            user: User profile with preferences
            meal_type: Type of meal to find recipes for
            query: Optional search query
            top_k: Number of top results to return

        Returns:
            List of (Recipe, score) tuples
        """
        # Apply filters
        dietary_filters = self._get_dietary_filters(user)
        candidates = self._filter_recipes_by_diet(self.recipes, dietary_filters)
        candidates = self._filter_recipes_by_allergies(candidates, user.allergies)
        candidates = self._get_recipes_by_meal_type(candidates, meal_type)

        if not candidates:
            # Fall back to just meal type filtering
            candidates = self._get_recipes_by_meal_type(self.recipes, meal_type)

        if not candidates:
            return []

        # Score recipes
        scored_recipes = []
        for recipe in candidates:
            # Base score from pantry matching
            pantry_score = self._score_recipe_for_pantry(recipe, user.pantry_items)

            # Semantic similarity score if query provided
            if query:
                recipe_text = recipe.get_searchable_text()
                similar = self.embedding_engine.find_similar(
                    query, [recipe_text], [recipe.id], top_k=1
                )
                semantic_score = similar[0][2] if similar else 0.5
            else:
                semantic_score = 0.5

            # Combined score
            combined_score = 0.4 * pantry_score + 0.6 * semantic_score
            scored_recipes.append((recipe, combined_score))

        # Sort by score and return top_k
        scored_recipes.sort(key=lambda x: x[1], reverse=True)
        return scored_recipes[:top_k]

    def _select_recipe_for_meal(
        self,
        user: UserProfile,
        meal_type: str,
        target_calories: int,
        used_recipe_ids: set[str],
        calorie_tolerance: float = 0.3,
    ) -> Recipe | None:
        """Select a single recipe for a meal.

        Args:
            user: User profile
            meal_type: Type of meal
            target_calories: Target calories for this meal
            used_recipe_ids: Set of already used recipe IDs
            calorie_tolerance: Tolerance for calorie matching (default 30%)

        Returns:
            Selected recipe or None
        """
        matches = self.find_matching_recipes(user, meal_type, top_k=10)

        # Filter out already used recipes
        available = [(r, s) for r, s in matches if r.id not in used_recipe_ids]

        if not available:
            available = matches  # Allow repeats if necessary

        if not available:
            return None

        # Filter by calorie target with specified tolerance
        min_cal = target_calories * (1 - calorie_tolerance)
        max_cal = target_calories * (1 + calorie_tolerance)

        calorie_appropriate = [
            (r, s)
            for r, s in available
            if min_cal <= r.nutrition.calories <= max_cal
        ]

        if calorie_appropriate:
            # Pick from top 3 with some randomness
            top_choices = calorie_appropriate[:3]
            return random.choice(top_choices)[0]

        # If no calorie-appropriate recipes, pick from available
        if available:
            return random.choice(available[:3])[0]

        return None

    def generate_daily_plan(
        self,
        user: UserProfile,
        plan_date: date,
        include_snacks: bool = True,
    ) -> DailyMealPlan:
        """Generate a meal plan for a single day.

        Args:
            user: User profile with preferences
            plan_date: Date for the plan
            include_snacks: Whether to include snack suggestions

        Returns:
            Daily meal plan
        """
        daily_calories = user.daily_calorie_target or 2000
        used_recipe_ids: set[str] = set()

        # Distribute calories: 25% breakfast, 35% lunch, 35% dinner, 5% snack
        breakfast_cal = int(daily_calories * 0.25)
        lunch_cal = int(daily_calories * 0.35)
        dinner_cal = int(daily_calories * 0.35)

        # Select recipes
        breakfast = self._select_recipe_for_meal(
            user, "breakfast", breakfast_cal, used_recipe_ids
        )
        if breakfast:
            used_recipe_ids.add(breakfast.id)

        lunch = self._select_recipe_for_meal(
            user, "lunch", lunch_cal, used_recipe_ids
        )
        if lunch:
            used_recipe_ids.add(lunch.id)

        dinner = self._select_recipe_for_meal(
            user, "dinner", dinner_cal, used_recipe_ids
        )
        if dinner:
            used_recipe_ids.add(dinner.id)

        snacks = []
        if include_snacks:
            snack = self._select_recipe_for_meal(
                user, "snack", int(daily_calories * 0.1), used_recipe_ids
            )
            if snack:
                snacks.append(snack)

        return DailyMealPlan(
            date=plan_date,
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner,
            snacks=snacks,
        )

    def generate_weekly_plan(
        self,
        user: UserProfile,
        start_date: date | None = None,
        plan_name: str | None = None,
    ) -> MealPlan:
        """Generate a meal plan for a week.

        Args:
            user: User profile with preferences
            start_date: Start date for the plan (defaults to today)
            plan_name: Optional name for the plan

        Returns:
            Weekly meal plan
        """
        start_date = start_date or date.today()
        end_date = start_date + timedelta(days=6)

        daily_plans = []
        for day_offset in range(7):
            plan_date = start_date + timedelta(days=day_offset)
            daily_plan = self.generate_daily_plan(user, plan_date)
            daily_plans.append(daily_plan)

        return MealPlan(
            id=f"mp_{uuid.uuid4().hex[:8]}",
            name=plan_name or f"Weekly Plan - {start_date.strftime('%Y-%m-%d')}",
            start_date=start_date,
            end_date=end_date,
            daily_plans=daily_plans,
            target_calories_per_day=user.daily_calorie_target or 2000,
        )

    def get_meal_suggestion(
        self,
        user: UserProfile,
        meal_type: str = "lunch",
    ) -> str:
        """Get a creative meal suggestion from the LLM.

        Args:
            user: User profile
            meal_type: Type of meal

        Returns:
            Suggestion text
        """
        dietary_prefs = [p.value for p in user.dietary_preferences]
        calorie_target = int((user.daily_calorie_target or 2000) * 0.3)

        return self.llm_engine.suggest_meal(
            dietary_preferences=dietary_prefs,
            available_ingredients=user.pantry_items,
            meal_type=meal_type,
            calorie_target=calorie_target,
        )

    def search_recipes(
        self,
        query: str,
        user: UserProfile | None = None,
        meal_type: str | None = None,
        top_k: int = 10,
    ) -> list[tuple[Recipe, float]]:
        """Search for recipes using semantic search.

        Args:
            query: Search query
            user: Optional user profile for filtering
            meal_type: Optional meal type filter
            top_k: Number of results to return

        Returns:
            List of (Recipe, score) tuples
        """
        candidates = self.recipes

        if meal_type:
            candidates = self._get_recipes_by_meal_type(candidates, meal_type)

        if user:
            dietary_filters = self._get_dietary_filters(user)
            candidates = self._filter_recipes_by_diet(candidates, dietary_filters)
            candidates = self._filter_recipes_by_allergies(candidates, user.allergies)

        if not candidates:
            return []

        # Perform semantic search
        texts = [r.get_searchable_text() for r in candidates]
        ids = [r.id for r in candidates]

        results = self.embedding_engine.find_similar(query, texts, ids, top_k=top_k)

        # Map back to recipes
        id_to_recipe = {r.id: r for r in candidates}
        return [(id_to_recipe[rid], score) for _, rid, score in results if rid in id_to_recipe]
