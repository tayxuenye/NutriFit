"""Recipe and ingredient models."""

from dataclasses import dataclass, field


@dataclass
class NutritionInfo:
    """Nutritional information for a recipe."""

    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float = 0.0
    sugar_g: float = 0.0
    sodium_mg: float = 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "calories": self.calories,
            "protein_g": self.protein_g,
            "carbs_g": self.carbs_g,
            "fat_g": self.fat_g,
            "fiber_g": self.fiber_g,
            "sugar_g": self.sugar_g,
            "sodium_mg": self.sodium_mg,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NutritionInfo":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Ingredient:
    """Recipe ingredient with quantity and unit."""

    name: str
    quantity: float
    unit: str
    optional: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "quantity": self.quantity,
            "unit": self.unit,
            "optional": self.optional,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Ingredient":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Recipe:
    """Recipe with ingredients and instructions."""

    id: str
    name: str
    description: str
    ingredients: list[Ingredient]
    instructions: list[str]
    nutrition: NutritionInfo
    prep_time_minutes: int
    cook_time_minutes: int
    servings: int
    meal_type: str  # breakfast, lunch, dinner, snack
    tags: list[str] = field(default_factory=list)
    dietary_info: list[str] = field(default_factory=list)
    difficulty: str = "medium"
    image_url: str | None = None

    @property
    def total_time_minutes(self) -> int:
        """Total preparation and cooking time."""
        return self.prep_time_minutes + self.cook_time_minutes

    def matches_dietary_preferences(self, preferences: list[str]) -> bool:
        """Check if recipe matches dietary preferences."""
        if not preferences:
            return True
        return all(pref in self.dietary_info for pref in preferences)

    def contains_ingredient(self, ingredient_name: str) -> bool:
        """Check if recipe contains a specific ingredient."""
        ingredient_name = ingredient_name.lower()
        return any(
            ingredient_name in ing.name.lower() for ing in self.ingredients
        )

    def get_ingredient_names(self) -> list[str]:
        """Get list of ingredient names."""
        return [ing.name.lower() for ing in self.ingredients]

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "ingredients": [ing.to_dict() for ing in self.ingredients],
            "instructions": self.instructions,
            "nutrition": self.nutrition.to_dict(),
            "prep_time_minutes": self.prep_time_minutes,
            "cook_time_minutes": self.cook_time_minutes,
            "servings": self.servings,
            "meal_type": self.meal_type,
            "tags": self.tags,
            "dietary_info": self.dietary_info,
            "difficulty": self.difficulty,
            "image_url": self.image_url,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Recipe":
        """Create from dictionary."""
        data["ingredients"] = [
            Ingredient.from_dict(ing) for ing in data["ingredients"]
        ]
        data["nutrition"] = NutritionInfo.from_dict(data["nutrition"])
        return cls(**data)

    def get_searchable_text(self) -> str:
        """Get text for embedding/search purposes."""
        ingredient_names = ", ".join(self.get_ingredient_names())
        tags = ", ".join(self.tags)
        dietary = ", ".join(self.dietary_info)
        return (
            f"{self.name}. {self.description}. "
            f"Ingredients: {ingredient_names}. "
            f"Tags: {tags}. Dietary info: {dietary}. "
            f"Meal type: {self.meal_type}."
        )
