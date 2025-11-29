"""Workout and exercise models."""

from dataclasses import dataclass, field
from enum import Enum


class MuscleGroup(Enum):
    """Target muscle groups."""

    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    CORE = "core"
    QUADRICEPS = "quadriceps"
    HAMSTRINGS = "hamstrings"
    GLUTES = "glutes"
    CALVES = "calves"
    FULL_BODY = "full_body"
    CARDIO = "cardio"


class ExerciseType(Enum):
    """Types of exercises."""

    STRENGTH = "strength"
    CARDIO = "cardio"
    FLEXIBILITY = "flexibility"
    BALANCE = "balance"
    HIIT = "hiit"
    COMPOUND = "compound"
    ISOLATION = "isolation"


@dataclass
class Equipment:
    """Workout equipment."""

    name: str
    category: str  # free_weights, machines, bodyweight, cardio, etc.
    is_required: bool = True

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "category": self.category,
            "is_required": self.is_required,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Equipment":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Exercise:
    """Individual exercise within a workout."""

    id: str
    name: str
    description: str
    muscle_groups: list[MuscleGroup]
    exercise_type: ExerciseType
    equipment_needed: list[Equipment] = field(default_factory=list)
    sets: int = 3
    reps: int | None = 10
    duration_seconds: int | None = None
    rest_seconds: int = 60
    difficulty: str = "intermediate"
    instructions: list[str] = field(default_factory=list)
    tips: list[str] = field(default_factory=list)
    calories_per_minute: float = 5.0

    def get_equipment_names(self) -> list[str]:
        """Get list of equipment names needed."""
        return [eq.name.lower() for eq in self.equipment_needed]

    def requires_equipment(self, equipment_list: list[str]) -> bool:
        """Check if all required equipment is available."""
        if not self.equipment_needed:
            return True
        required_equipment = [
            eq.name.lower() for eq in self.equipment_needed if eq.is_required
        ]
        available = [e.lower() for e in equipment_list]
        return all(eq in available for eq in required_equipment)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "muscle_groups": [mg.value for mg in self.muscle_groups],
            "exercise_type": self.exercise_type.value,
            "equipment_needed": [eq.to_dict() for eq in self.equipment_needed],
            "sets": self.sets,
            "reps": self.reps,
            "duration_seconds": self.duration_seconds,
            "rest_seconds": self.rest_seconds,
            "difficulty": self.difficulty,
            "instructions": self.instructions,
            "tips": self.tips,
            "calories_per_minute": self.calories_per_minute,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Exercise":
        """Create from dictionary."""
        data["muscle_groups"] = [MuscleGroup(mg) for mg in data["muscle_groups"]]
        data["exercise_type"] = ExerciseType(data["exercise_type"])
        data["equipment_needed"] = [
            Equipment.from_dict(eq) for eq in data.get("equipment_needed", [])
        ]
        return cls(**data)

    def get_searchable_text(self) -> str:
        """Get text for embedding/search purposes."""
        muscle_groups = ", ".join(mg.value for mg in self.muscle_groups)
        equipment = ", ".join(self.get_equipment_names()) or "no equipment"
        return (
            f"{self.name}. {self.description}. "
            f"Targets: {muscle_groups}. "
            f"Type: {self.exercise_type.value}. "
            f"Equipment: {equipment}. "
            f"Difficulty: {self.difficulty}."
        )


@dataclass
class Workout:
    """Complete workout routine."""

    id: str
    name: str
    description: str
    exercises: list[Exercise]
    workout_type: str  # strength, cardio, flexibility, mixed
    difficulty: str = "intermediate"
    duration_minutes: int = 45
    target_muscle_groups: list[MuscleGroup] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    warmup_minutes: int = 5
    cooldown_minutes: int = 5

    @property
    def total_duration_minutes(self) -> int:
        """Total workout duration including warmup and cooldown."""
        return self.duration_minutes + self.warmup_minutes + self.cooldown_minutes

    def get_all_equipment_needed(self) -> list[str]:
        """Get all equipment needed for this workout."""
        equipment = set()
        for exercise in self.exercises:
            equipment.update(exercise.get_equipment_names())
        return list(equipment)

    def is_doable_with_equipment(self, available_equipment: list[str]) -> bool:
        """Check if workout can be done with available equipment."""
        return all(
            ex.requires_equipment(available_equipment) for ex in self.exercises
        )

    def estimate_calories_burned(self, weight_kg: float) -> int:
        """Estimate calories burned during workout."""
        # Simple estimation based on duration and exercise types
        base_calories = 0
        for exercise in self.exercises:
            exercise_duration = (
                exercise.duration_seconds / 60
                if exercise.duration_seconds
                else (exercise.sets * exercise.reps * 3 / 60 if exercise.reps else 5)
            )
            base_calories += exercise.calories_per_minute * exercise_duration

        # Adjust for body weight (reference: 70kg)
        weight_factor = weight_kg / 70.0
        return int(base_calories * weight_factor)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "exercises": [ex.to_dict() for ex in self.exercises],
            "workout_type": self.workout_type,
            "difficulty": self.difficulty,
            "duration_minutes": self.duration_minutes,
            "target_muscle_groups": [mg.value for mg in self.target_muscle_groups],
            "tags": self.tags,
            "warmup_minutes": self.warmup_minutes,
            "cooldown_minutes": self.cooldown_minutes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Workout":
        """Create from dictionary."""
        data["exercises"] = [Exercise.from_dict(ex) for ex in data["exercises"]]
        data["target_muscle_groups"] = [
            MuscleGroup(mg) for mg in data.get("target_muscle_groups", [])
        ]
        return cls(**data)

    def get_searchable_text(self) -> str:
        """Get text for embedding/search purposes."""
        muscle_groups = ", ".join(mg.value for mg in self.target_muscle_groups)
        equipment = ", ".join(self.get_all_equipment_needed()) or "no equipment"
        exercises = ", ".join(ex.name for ex in self.exercises)
        return (
            f"{self.name}. {self.description}. "
            f"Type: {self.workout_type}. "
            f"Targets: {muscle_groups}. "
            f"Equipment: {equipment}. "
            f"Exercises: {exercises}. "
            f"Difficulty: {self.difficulty}. "
            f"Duration: {self.total_duration_minutes} minutes."
        )
