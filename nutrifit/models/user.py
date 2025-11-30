"""User profile and preference models."""

from dataclasses import dataclass, field
from enum import Enum


class DietaryPreference(Enum):
    """Supported dietary preferences."""

    NONE = "none"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    KETO = "keto"
    PALEO = "paleo"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    LOW_CARB = "low_carb"
    HIGH_PROTEIN = "high_protein"


class FitnessGoal(Enum):
    """Supported fitness goals."""

    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"
    ENDURANCE = "endurance"
    STRENGTH = "strength"
    FLEXIBILITY = "flexibility"
    GENERAL_FITNESS = "general_fitness"


@dataclass
class UserProfile:
    """User profile containing preferences and goals."""

    name: str
    age: int
    weight_kg: float
    height_cm: float
    dietary_preferences: list[DietaryPreference] = field(default_factory=list)
    fitness_goals: list[FitnessGoal] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    pantry_items: list[str] = field(default_factory=list)
    available_equipment: list[str] = field(default_factory=list)
    daily_calorie_target: int | None = None
    meals_per_day: int = 3

    def __post_init__(self) -> None:
        """Calculate default calorie target if not provided."""
        if self.daily_calorie_target is None:
            # Basic BMR calculation using Mifflin-St Jeor equation
            # This is a simplified version for the MVP
            bmr = 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age
            # Assume moderate activity level (1.55 multiplier)
            self.daily_calorie_target = int(bmr * 1.55)

            # Adjust based on fitness goals
            if FitnessGoal.WEIGHT_LOSS in self.fitness_goals:
                self.daily_calorie_target = int(self.daily_calorie_target * 0.85)
            elif FitnessGoal.MUSCLE_GAIN in self.fitness_goals:
                self.daily_calorie_target = int(self.daily_calorie_target * 1.15)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "age": self.age,
            "weight_kg": self.weight_kg,
            "height_cm": self.height_cm,
            "dietary_preferences": [p.value for p in self.dietary_preferences],
            "fitness_goals": [g.value for g in self.fitness_goals],
            "allergies": self.allergies,
            "pantry_items": self.pantry_items,
            "available_equipment": self.available_equipment,
            "daily_calorie_target": self.daily_calorie_target,
            "meals_per_day": self.meals_per_day,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        """Create from dictionary."""
        data["dietary_preferences"] = [
            DietaryPreference(p) for p in data.get("dietary_preferences", [])
        ]
        data["fitness_goals"] = [
            FitnessGoal(g) for g in data.get("fitness_goals", [])
        ]
        return cls(**data)
