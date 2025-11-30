"""Meal and workout plan models."""

from dataclasses import dataclass, field
from datetime import date

from nutrifit.models.recipe import Recipe
from nutrifit.models.workout import Workout


@dataclass
class DailyMealPlan:
    """A single day's meal plan."""

    date: date
    breakfast: Recipe | None = None
    lunch: Recipe | None = None
    dinner: Recipe | None = None
    snacks: list[Recipe] = field(default_factory=list)
    notes: str = ""

    @property
    def total_calories(self) -> int:
        """Calculate total calories for the day."""
        total = 0
        if self.breakfast:
            total += self.breakfast.nutrition.calories
        if self.lunch:
            total += self.lunch.nutrition.calories
        if self.dinner:
            total += self.dinner.nutrition.calories
        for snack in self.snacks:
            total += snack.nutrition.calories
        return total

    @property
    def total_protein(self) -> float:
        """Calculate total protein for the day."""
        total = 0.0
        if self.breakfast:
            total += self.breakfast.nutrition.protein_g
        if self.lunch:
            total += self.lunch.nutrition.protein_g
        if self.dinner:
            total += self.dinner.nutrition.protein_g
        for snack in self.snacks:
            total += snack.nutrition.protein_g
        return total

    def get_all_recipes(self) -> list[Recipe]:
        """Get all recipes for this day."""
        recipes = []
        if self.breakfast:
            recipes.append(self.breakfast)
        if self.lunch:
            recipes.append(self.lunch)
        if self.dinner:
            recipes.append(self.dinner)
        recipes.extend(self.snacks)
        return recipes

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "date": self.date.isoformat(),
            "breakfast": self.breakfast.to_dict() if self.breakfast else None,
            "lunch": self.lunch.to_dict() if self.lunch else None,
            "dinner": self.dinner.to_dict() if self.dinner else None,
            "snacks": [s.to_dict() for s in self.snacks],
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DailyMealPlan":
        """Create from dictionary."""
        return cls(
            date=date.fromisoformat(data["date"]),
            breakfast=(
                Recipe.from_dict(data["breakfast"]) if data.get("breakfast") else None
            ),
            lunch=Recipe.from_dict(data["lunch"]) if data.get("lunch") else None,
            dinner=Recipe.from_dict(data["dinner"]) if data.get("dinner") else None,
            snacks=[Recipe.from_dict(s) for s in data.get("snacks", [])],
            notes=data.get("notes", ""),
        )


@dataclass
class MealPlan:
    """Weekly or custom duration meal plan."""

    id: str
    name: str
    start_date: date
    end_date: date
    daily_plans: list[DailyMealPlan] = field(default_factory=list)
    target_calories_per_day: int = 2000
    notes: str = ""

    @property
    def duration_days(self) -> int:
        """Number of days in the plan."""
        return (self.end_date - self.start_date).days + 1

    @property
    def average_daily_calories(self) -> float:
        """Average calories per day across the plan."""
        if not self.daily_plans:
            return 0.0
        total = sum(day.total_calories for day in self.daily_plans)
        return total / len(self.daily_plans)

    def get_all_recipes(self) -> list[Recipe]:
        """Get all unique recipes in the meal plan."""
        seen_ids = set()
        recipes = []
        for day in self.daily_plans:
            for recipe in day.get_all_recipes():
                if recipe.id not in seen_ids:
                    seen_ids.add(recipe.id)
                    recipes.append(recipe)
        return recipes

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "daily_plans": [dp.to_dict() for dp in self.daily_plans],
            "target_calories_per_day": self.target_calories_per_day,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MealPlan":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            start_date=date.fromisoformat(data["start_date"]),
            end_date=date.fromisoformat(data["end_date"]),
            daily_plans=[
                DailyMealPlan.from_dict(dp) for dp in data.get("daily_plans", [])
            ],
            target_calories_per_day=data.get("target_calories_per_day", 2000),
            notes=data.get("notes", ""),
        )


@dataclass
class DailyWorkoutPlan:
    """A single day's workout plan."""

    date: date
    workouts: list[Workout] = field(default_factory=list)
    is_rest_day: bool = False
    notes: str = ""

    @property
    def total_duration_minutes(self) -> int:
        """Total workout duration for the day."""
        return sum(w.total_duration_minutes for w in self.workouts)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "date": self.date.isoformat(),
            "workouts": [w.to_dict() for w in self.workouts],
            "is_rest_day": self.is_rest_day,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DailyWorkoutPlan":
        """Create from dictionary."""
        return cls(
            date=date.fromisoformat(data["date"]),
            workouts=[Workout.from_dict(w) for w in data.get("workouts", [])],
            is_rest_day=data.get("is_rest_day", False),
            notes=data.get("notes", ""),
        )


@dataclass
class WorkoutPlan:
    """Weekly or custom duration workout plan."""

    id: str
    name: str
    start_date: date
    end_date: date
    daily_plans: list[DailyWorkoutPlan] = field(default_factory=list)
    workout_days_per_week: int = 4
    notes: str = ""

    @property
    def duration_days(self) -> int:
        """Number of days in the plan."""
        return (self.end_date - self.start_date).days + 1

    @property
    def total_workout_days(self) -> int:
        """Number of actual workout days (non-rest days)."""
        return sum(1 for day in self.daily_plans if not day.is_rest_day)

    def get_all_workouts(self) -> list[Workout]:
        """Get all unique workouts in the plan."""
        seen_ids = set()
        workouts = []
        for day in self.daily_plans:
            for workout in day.workouts:
                if workout.id not in seen_ids:
                    seen_ids.add(workout.id)
                    workouts.append(workout)
        return workouts

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "daily_plans": [dp.to_dict() for dp in self.daily_plans],
            "workout_days_per_week": self.workout_days_per_week,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkoutPlan":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            start_date=date.fromisoformat(data["start_date"]),
            end_date=date.fromisoformat(data["end_date"]),
            daily_plans=[
                DailyWorkoutPlan.from_dict(dp) for dp in data.get("daily_plans", [])
            ],
            workout_days_per_week=data.get("workout_days_per_week", 4),
            notes=data.get("notes", ""),
        )
