"""Progress tracking models."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta


@dataclass
class ProgressEntry:
    """Single progress entry for tracking."""

    date: date
    weight_kg: float | None = None
    body_fat_percentage: float | None = None
    calories_consumed: int | None = None
    calories_burned: int | None = None
    workouts_completed: int = 0
    meals_followed: int = 0
    water_intake_ml: int | None = None
    sleep_hours: float | None = None
    mood_rating: int | None = None  # 1-10 scale
    energy_rating: int | None = None  # 1-10 scale
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "date": self.date.isoformat(),
            "weight_kg": self.weight_kg,
            "body_fat_percentage": self.body_fat_percentage,
            "calories_consumed": self.calories_consumed,
            "calories_burned": self.calories_burned,
            "workouts_completed": self.workouts_completed,
            "meals_followed": self.meals_followed,
            "water_intake_ml": self.water_intake_ml,
            "sleep_hours": self.sleep_hours,
            "mood_rating": self.mood_rating,
            "energy_rating": self.energy_rating,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProgressEntry":
        """Create from dictionary."""
        data["date"] = date.fromisoformat(data["date"])
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)
    
    def validate(self) -> None:
        """Validate progress entry data for integrity.
        
        Raises:
            ValueError: If any validation check fails.
        """
        if self.weight_kg is not None and (self.weight_kg <= 0 or self.weight_kg > 500):
            raise ValueError("Weight must be between 0 and 500 kg")
        
        if self.body_fat_percentage is not None and (
            self.body_fat_percentage < 0 or self.body_fat_percentage > 100
        ):
            raise ValueError("Body fat percentage must be between 0 and 100")
        
        if self.calories_consumed is not None and self.calories_consumed < 0:
            raise ValueError("Calories consumed cannot be negative")
        
        if self.calories_burned is not None and self.calories_burned < 0:
            raise ValueError("Calories burned cannot be negative")
        
        if self.workouts_completed < 0:
            raise ValueError("Workouts completed cannot be negative")
        
        if self.meals_followed < 0:
            raise ValueError("Meals followed cannot be negative")
        
        if self.water_intake_ml is not None and self.water_intake_ml < 0:
            raise ValueError("Water intake cannot be negative")
        
        if self.sleep_hours is not None and (self.sleep_hours < 0 or self.sleep_hours > 24):
            raise ValueError("Sleep hours must be between 0 and 24")
        
        if self.mood_rating is not None and (self.mood_rating < 1 or self.mood_rating > 10):
            raise ValueError("Mood rating must be between 1 and 10")
        
        if self.energy_rating is not None and (
            self.energy_rating < 1 or self.energy_rating > 10
        ):
            raise ValueError("Energy rating must be between 1 and 10")
    
    def is_valid_structure(self) -> bool:
        """Check if the data structure is valid for persistence.
        
        Returns:
            bool: True if structure is valid, False otherwise.
        """
        try:
            self.validate()
            return True
        except (ValueError, TypeError, AttributeError):
            return False


@dataclass
class ProgressTracker:
    """Tracks user progress over time."""

    user_id: str
    entries: list[ProgressEntry] = field(default_factory=list)
    goals: dict = field(default_factory=dict)

    def add_entry(self, entry: ProgressEntry) -> None:
        """Add a new progress entry."""
        self.entries.append(entry)
        # Sort entries by date
        self.entries.sort(key=lambda e: e.date)

    def get_entry_for_date(self, target_date: date) -> ProgressEntry | None:
        """Get entry for a specific date."""
        for entry in self.entries:
            if entry.date == target_date:
                return entry
        return None

    def get_entries_in_range(
        self, start_date: date, end_date: date
    ) -> list[ProgressEntry]:
        """Get all entries within a date range."""
        return [
            entry
            for entry in self.entries
            if start_date <= entry.date <= end_date
        ]

    def get_weight_trend(self, days: int = 30) -> float | None:
        """Calculate weight change over specified days.

        Returns change in kg (negative = weight loss).
        """
        weight_entries = [e for e in self.entries if e.weight_kg is not None]
        if len(weight_entries) < 2:
            return None

        # Get entries from last N days
        cutoff_date = date.today() - timedelta(days=days)
        recent_entries = [e for e in weight_entries if e.date >= cutoff_date]

        if len(recent_entries) < 2:
            return None

        first_weight = recent_entries[0].weight_kg
        last_weight = recent_entries[-1].weight_kg
        return last_weight - first_weight if first_weight and last_weight else None

    def get_average_calories(self, days: int = 7) -> float | None:
        """Calculate average calories consumed over specified days."""
        cutoff_date = date.today() - timedelta(days=days)
        calorie_entries = [
            e for e in self.entries
            if e.date >= cutoff_date and e.calories_consumed is not None
        ]

        if not calorie_entries:
            return None

        total = sum(e.calories_consumed for e in calorie_entries if e.calories_consumed)
        return total / len(calorie_entries)

    def get_workout_adherence(self, days: int = 7) -> float:
        """Calculate workout adherence percentage over specified days."""
        cutoff_date = date.today() - timedelta(days=days)
        recent_entries = [e for e in self.entries if e.date >= cutoff_date]

        if not recent_entries:
            return 0.0

        days_with_workouts = sum(
            1 for e in recent_entries if e.workouts_completed > 0
        )
        # Assume 4 workout days per week as target
        expected_workouts = min(4, len(recent_entries))
        return (days_with_workouts / expected_workouts * 100) if expected_workouts else 0.0

    def get_summary(self) -> dict:
        """Get a summary of progress."""
        return {
            "total_entries": len(self.entries),
            "weight_trend_30d": self.get_weight_trend(30),
            "average_calories_7d": self.get_average_calories(7),
            "workout_adherence_7d": self.get_workout_adherence(7),
            "latest_weight": (
                self.entries[-1].weight_kg
                if self.entries and self.entries[-1].weight_kg
                else None
            ),
        }

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "user_id": self.user_id,
            "entries": [e.to_dict() for e in self.entries],
            "goals": self.goals,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProgressTracker":
        """Create from dictionary."""
        return cls(
            user_id=data["user_id"],
            entries=[ProgressEntry.from_dict(e) for e in data.get("entries", [])],
            goals=data.get("goals", {}),
        )
    
    def validate(self) -> None:
        """Validate progress tracker data for integrity.
        
        Raises:
            ValueError: If any validation check fails.
        """
        if not self.user_id or not self.user_id.strip():
            raise ValueError("User ID cannot be empty")
        
        # Validate each entry
        for entry in self.entries:
            entry.validate()
    
    def is_valid_structure(self) -> bool:
        """Check if the data structure is valid for persistence.
        
        Returns:
            bool: True if structure is valid, False otherwise.
        """
        try:
            self.validate()
            return True
        except (ValueError, TypeError, AttributeError):
            return False
