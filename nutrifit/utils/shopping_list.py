"""Shopping list optimizer for NutriFit."""

from collections import defaultdict
from dataclasses import dataclass, field

from nutrifit.models.plan import MealPlan
from nutrifit.models.recipe import Recipe


@dataclass
class ShoppingItem:
    """An item on the shopping list."""

    name: str
    quantity: float
    unit: str
    category: str = "other"
    recipes_used_in: list[str] = field(default_factory=list)
    is_optional: bool = False
    notes: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit,
            "category": self.category,
            "recipes_used_in": self.recipes_used_in,
            "is_optional": self.is_optional,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ShoppingItem":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ShoppingList:
    """Consolidated shopping list."""

    items: list[ShoppingItem] = field(default_factory=list)
    notes: str = ""
    pantry_items_available: list[str] = field(default_factory=list)

    def get_items_by_category(self) -> dict[str, list[ShoppingItem]]:
        """Group items by category."""
        by_category: dict[str, list[ShoppingItem]] = defaultdict(list)
        for item in self.items:
            by_category[item.category].append(item)
        return dict(by_category)

    def get_required_items(self) -> list[ShoppingItem]:
        """Get only required (non-optional) items."""
        return [item for item in self.items if not item.is_optional]

    def remove_pantry_items(self) -> "ShoppingList":
        """Create a new list without items already in pantry."""
        pantry_lower = [p.lower() for p in self.pantry_items_available]
        filtered_items = []

        for item in self.items:
            in_pantry = False
            for pantry_item in pantry_lower:
                if pantry_item in item.name.lower() or item.name.lower() in pantry_item:
                    in_pantry = True
                    break
            if not in_pantry:
                filtered_items.append(item)

        return ShoppingList(
            items=filtered_items,
            notes=self.notes,
            pantry_items_available=self.pantry_items_available,
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "items": [item.to_dict() for item in self.items],
            "notes": self.notes,
            "pantry_items_available": self.pantry_items_available,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ShoppingList":
        """Create from dictionary."""
        return cls(
            items=[ShoppingItem.from_dict(item) for item in data.get("items", [])],
            notes=data.get("notes", ""),
            pantry_items_available=data.get("pantry_items_available", []),
        )


class ShoppingListOptimizer:
    """
    Optimizes shopping lists by consolidating ingredients,
    categorizing, and removing pantry items.
    """

    # Common ingredient categories
    CATEGORY_MAP = {
        # Proteins
        "chicken": "proteins",
        "beef": "proteins",
        "pork": "proteins",
        "turkey": "proteins",
        "salmon": "proteins",
        "tuna": "proteins",
        "tofu": "proteins",
        "eggs": "proteins",
        "fish": "proteins",
        "steak": "proteins",
        "lamb": "proteins",
        "shrimp": "proteins",
        "bacon": "proteins",
        "sausage": "proteins",
        # Dairy
        "milk": "dairy",
        "cheese": "dairy",
        "yogurt": "dairy",
        "butter": "dairy",
        "cream": "dairy",
        "cottage cheese": "dairy",
        "feta": "dairy",
        "parmesan": "dairy",
        # Produce
        "lettuce": "produce",
        "spinach": "produce",
        "tomato": "produce",
        "cucumber": "produce",
        "onion": "produce",
        "garlic": "produce",
        "bell pepper": "produce",
        "broccoli": "produce",
        "carrot": "produce",
        "celery": "produce",
        "avocado": "produce",
        "banana": "produce",
        "apple": "produce",
        "berries": "produce",
        "lemon": "produce",
        "lime": "produce",
        "zucchini": "produce",
        "sweet potato": "produce",
        "asparagus": "produce",
        "mushroom": "produce",
        "greens": "produce",
        "kale": "produce",
        "cabbage": "produce",
        "cauliflower": "produce",
        "eggplant": "produce",
        "ginger": "produce",
        "parsley": "produce",
        "cilantro": "produce",
        "basil": "produce",
        "mint": "produce",
        "rosemary": "produce",
        "thyme": "produce",
        "olives": "produce",
        # Grains
        "rice": "grains",
        "bread": "grains",
        "oats": "grains",
        "quinoa": "grains",
        "pasta": "grains",
        "tortilla": "grains",
        "granola": "grains",
        # Pantry
        "olive oil": "pantry",
        "sesame oil": "pantry",
        "soy sauce": "pantry",
        "honey": "pantry",
        "salt": "pantry",
        "pepper": "pantry",
        "sugar": "pantry",
        "flour": "pantry",
        "vinegar": "pantry",
        "spices": "pantry",
        "curry powder": "pantry",
        "turmeric": "pantry",
        "cumin": "pantry",
        "cinnamon": "pantry",
        "oregano": "pantry",
        "basil": "pantry",
        "dill": "pantry",
        "ginger": "pantry",
        # Vegetables (legumes)
        "chickpeas": "vegetables",
        "lentils": "vegetables",
        "beans": "vegetables",
        "hummus": "vegetables",
        "coconut milk": "canned",
        "diced tomatoes": "canned",
        "tomato paste": "canned",
        "broth": "canned",
        # Nuts/Seeds
        "almonds": "Nuts/Seeds",
        "walnuts": "Nuts/Seeds",
        "peanut butter": "Nuts/Seeds",
        "almond butter": "Nuts/Seeds",
        "tahini": "Nuts/Seeds",
        "chia seeds": "Nuts/Seeds",
        "pine nuts": "Nuts/Seeds",
        "coconut flakes": "Nuts/Seeds",
        # Frozen
        "frozen berries": "frozen",
        "frozen vegetables": "frozen",
        # Other
        "protein powder": "supplements",
        "nutritional yeast": "supplements",
        "chocolate chips": "baking",
    }

    # Unit normalization
    UNIT_CONVERSIONS = {
        "tbsp": "tablespoon",
        "tsp": "teaspoon",
        "oz": "ounce",
        "lb": "pound",
        "g": "gram",
        "kg": "kilogram",
        "ml": "milliliter",
        "l": "liter",
    }

    def __init__(self) -> None:
        """Initialize the shopping list optimizer."""
        pass

    def _categorize_ingredient(self, ingredient_name: str) -> str:
        """Determine the category of an ingredient."""
        name_lower = ingredient_name.lower()

        for key, category in self.CATEGORY_MAP.items():
            if key in name_lower:
                return category

        return "other"

    def _normalize_unit(self, unit: str) -> str:
        """Normalize unit names."""
        unit_lower = unit.lower().strip()
        return self.UNIT_CONVERSIONS.get(unit_lower, unit_lower)

    def _can_combine(
        self, item1: ShoppingItem, item2: ShoppingItem
    ) -> bool:
        """Check if two items can be combined."""
        # Same name and compatible units
        if item1.name.lower() != item2.name.lower():
            return False

        # Check if units are the same or compatible
        unit1 = self._normalize_unit(item1.unit)
        unit2 = self._normalize_unit(item2.unit)

        return unit1 == unit2

    def _combine_items(
        self, item1: ShoppingItem, item2: ShoppingItem
    ) -> ShoppingItem:
        """Combine two compatible shopping items."""
        combined_recipes = list(set(item1.recipes_used_in + item2.recipes_used_in))

        return ShoppingItem(
            name=item1.name,
            quantity=item1.quantity + item2.quantity,
            unit=item1.unit,
            category=item1.category,
            recipes_used_in=combined_recipes,
            is_optional=item1.is_optional and item2.is_optional,
            notes=item1.notes or item2.notes,
        )

    def generate_from_recipes(
        self,
        recipes: list[Recipe],
        pantry_items: list[str] | None = None,
    ) -> ShoppingList:
        """Generate a shopping list from a list of recipes.

        Args:
            recipes: List of recipes to generate list for
            pantry_items: Items already available in pantry

        Returns:
            Consolidated shopping list
        """
        pantry_items = pantry_items or []

        # Collect all ingredients
        items: list[ShoppingItem] = []
        
        # Items to skip (generic placeholders and meal names used as ingredients)
        skip_patterns = [
            "various ingredients",
            "as described",
            "mixed ingredients",
        ]
        
        # Patterns that indicate this is a meal name, not an ingredient
        meal_name_patterns = [
            " bowl",
            " salad",
            " wrap",
            " sandwich",
            " smoothie",
            " shake",
            " parfait",
            " omelette",
            " omelet",
            " stir fry",
            " stir-fry",
            " curry",
            " soup",
            " stew",
        ]

        for recipe in recipes:
            for ingredient in recipe.ingredients:
                # Skip generic placeholder ingredients
                ing_lower = ingredient.name.lower()
                if any(pattern in ing_lower for pattern in skip_patterns):
                    continue
                
                # Skip items that look like meal names (not actual ingredients)
                if any(pattern in ing_lower for pattern in meal_name_patterns):
                    continue
                
                item = ShoppingItem(
                    name=ingredient.name,
                    quantity=ingredient.quantity,
                    unit=ingredient.unit,
                    category=self._categorize_ingredient(ingredient.name),
                    recipes_used_in=[recipe.name],
                    is_optional=ingredient.optional,
                )
                items.append(item)

        # Consolidate items
        consolidated = self._consolidate_items(items)

        shopping_list = ShoppingList(
            items=consolidated,
            pantry_items_available=pantry_items,
        )

        # Remove items already in pantry if requested
        if pantry_items:
            shopping_list = shopping_list.remove_pantry_items()

        return shopping_list

    def generate_from_meal_plan(
        self,
        meal_plan: MealPlan,
        pantry_items: list[str] | None = None,
    ) -> ShoppingList:
        """Generate a shopping list from a meal plan.

        Args:
            meal_plan: Meal plan to generate list for
            pantry_items: Items already available in pantry

        Returns:
            Consolidated shopping list
        """
        # Get all recipes including duplicates for proper quantity calculation
        all_recipes = []
        for daily_plan in meal_plan.daily_plans:
            all_recipes.extend(daily_plan.get_all_recipes())
        return self.generate_from_recipes(all_recipes, pantry_items)

    def _consolidate_items(
        self, items: list[ShoppingItem]
    ) -> list[ShoppingItem]:
        """Consolidate duplicate items in the list."""
        # Group by normalized name and unit
        groups: dict[str, list[ShoppingItem]] = defaultdict(list)

        for item in items:
            key = f"{item.name.lower()}|{self._normalize_unit(item.unit)}"
            groups[key].append(item)

        # Combine items in each group
        consolidated = []
        for group_items in groups.values():
            combined = group_items[0]
            for item in group_items[1:]:
                combined = self._combine_items(combined, item)
            consolidated.append(combined)

        # Sort by category then name
        consolidated.sort(key=lambda x: (x.category, x.name.lower()))

        return consolidated

    def optimize(
        self,
        shopping_list: ShoppingList,
        budget: float | None = None,
        prefer_bulk: bool = False,
    ) -> ShoppingList:
        """Optimize the shopping list.

        Args:
            shopping_list: List to optimize
            budget: Optional budget constraint
            prefer_bulk: Whether to suggest bulk buying

        Returns:
            Optimized shopping list
        """
        # For MVP, optimization focuses on:
        # 1. Consolidating duplicates
        # 2. Categorizing for efficient shopping
        # 3. Marking optional items

        optimized_items = self._consolidate_items(shopping_list.items)

        # Add notes for bulk items if quantities are high
        if prefer_bulk:
            for item in optimized_items:
                if item.quantity > 5:
                    item.notes = "Consider buying in bulk"

        return ShoppingList(
            items=optimized_items,
            notes=shopping_list.notes,
            pantry_items_available=shopping_list.pantry_items_available,
        )

    def format_for_display(
        self, shopping_list: ShoppingList, group_by_category: bool = True
    ) -> str:
        """Format shopping list for display.

        Args:
            shopping_list: List to format
            group_by_category: Whether to group by category

        Returns:
            Formatted string
        """
        lines = ["=" * 40, "SHOPPING LIST", "=" * 40]

        if group_by_category:
            by_category = shopping_list.get_items_by_category()

            for category, items in sorted(by_category.items()):
                lines.append(f"\n📦 {category.upper().replace('_', ' ')}")
                lines.append("-" * 30)

                for item in items:
                    optional_mark = " (optional)" if item.is_optional else ""
                    lines.append(
                        f"  • {item.name}: {item.quantity:.1f} {item.unit}{optional_mark}"
                    )
        else:
            for item in shopping_list.items:
                optional_mark = " (optional)" if item.is_optional else ""
                lines.append(
                    f"• {item.name}: {item.quantity:.1f} {item.unit}{optional_mark}"
                )

        lines.append("\n" + "=" * 40)
        lines.append(f"Total items: {len(shopping_list.items)}")

        return "\n".join(lines)
