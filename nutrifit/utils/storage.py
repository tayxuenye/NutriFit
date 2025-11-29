"""Data storage utilities for NutriFit."""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any, TypeVar

from nutrifit.models.plan import MealPlan, WorkoutPlan
from nutrifit.models.progress import ProgressEntry, ProgressTracker
from nutrifit.models.user import UserProfile

T = TypeVar("T")


class DataStorage:
    """
    Local file-based storage for NutriFit data.

    Stores user profiles, plans, and progress data in JSON format.
    """

    def __init__(self, data_dir: Path | None = None):
        """Initialize data storage.

        Args:
            data_dir: Directory for data storage. Defaults to ~/.nutrifit/data
        """
        self.data_dir = data_dir or Path.home() / ".nutrifit" / "data"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories."""
        (self.data_dir / "users").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "meal_plans").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "workout_plans").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "progress").mkdir(parents=True, exist_ok=True)

    def _serialize(self, obj: Any) -> Any:
        """Serialize objects for JSON storage."""
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        elif hasattr(obj, "to_dict"):
            return obj.to_dict()
        elif isinstance(obj, dict):
            return {k: self._serialize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._serialize(item) for item in obj]
        return obj

    def _save_json(self, path: Path, data: dict) -> None:
        """Save data to JSON file."""
        serialized = self._serialize(data)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2, default=str)

    def _load_json(self, path: Path) -> dict | None:
        """Load data from JSON file."""
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    # User Profile Methods
    def save_user_profile(self, user: UserProfile, user_id: str = "default") -> None:
        """Save user profile.

        Args:
            user: User profile to save
            user_id: Unique identifier for the user
        """
        path = self.data_dir / "users" / f"{user_id}.json"
        self._save_json(path, user.to_dict())

    def load_user_profile(self, user_id: str = "default") -> UserProfile | None:
        """Load user profile.

        Args:
            user_id: Unique identifier for the user

        Returns:
            User profile or None if not found
        """
        path = self.data_dir / "users" / f"{user_id}.json"
        data = self._load_json(path)
        if data:
            return UserProfile.from_dict(data)
        return None

    def list_user_profiles(self) -> list[str]:
        """List all saved user profile IDs."""
        profiles_dir = self.data_dir / "users"
        return [p.stem for p in profiles_dir.glob("*.json")]

    def delete_user_profile(self, user_id: str) -> bool:
        """Delete a user profile.

        Args:
            user_id: Unique identifier for the user

        Returns:
            True if deleted, False if not found
        """
        path = self.data_dir / "users" / f"{user_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    # Meal Plan Methods
    def save_meal_plan(self, plan: MealPlan) -> None:
        """Save a meal plan.

        Args:
            plan: Meal plan to save
        """
        path = self.data_dir / "meal_plans" / f"{plan.id}.json"
        self._save_json(path, plan.to_dict())

    def load_meal_plan(self, plan_id: str) -> MealPlan | None:
        """Load a meal plan.

        Args:
            plan_id: Unique identifier for the plan

        Returns:
            Meal plan or None if not found
        """
        path = self.data_dir / "meal_plans" / f"{plan_id}.json"
        data = self._load_json(path)
        if data:
            return MealPlan.from_dict(data)
        return None

    def list_meal_plans(self) -> list[dict]:
        """List all saved meal plans with basic info."""
        plans_dir = self.data_dir / "meal_plans"
        plans = []
        for path in plans_dir.glob("*.json"):
            data = self._load_json(path)
            if data:
                plans.append({
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "start_date": data.get("start_date"),
                    "end_date": data.get("end_date"),
                })
        return sorted(plans, key=lambda x: x.get("start_date", ""), reverse=True)

    def delete_meal_plan(self, plan_id: str) -> bool:
        """Delete a meal plan.

        Args:
            plan_id: Unique identifier for the plan

        Returns:
            True if deleted, False if not found
        """
        path = self.data_dir / "meal_plans" / f"{plan_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    # Workout Plan Methods
    def save_workout_plan(self, plan: WorkoutPlan) -> None:
        """Save a workout plan.

        Args:
            plan: Workout plan to save
        """
        path = self.data_dir / "workout_plans" / f"{plan.id}.json"
        self._save_json(path, plan.to_dict())

    def load_workout_plan(self, plan_id: str) -> WorkoutPlan | None:
        """Load a workout plan.

        Args:
            plan_id: Unique identifier for the plan

        Returns:
            Workout plan or None if not found
        """
        path = self.data_dir / "workout_plans" / f"{plan_id}.json"
        data = self._load_json(path)
        if data:
            return WorkoutPlan.from_dict(data)
        return None

    def list_workout_plans(self) -> list[dict]:
        """List all saved workout plans with basic info."""
        plans_dir = self.data_dir / "workout_plans"
        plans = []
        for path in plans_dir.glob("*.json"):
            data = self._load_json(path)
            if data:
                plans.append({
                    "id": data.get("id"),
                    "name": data.get("name"),
                    "start_date": data.get("start_date"),
                    "end_date": data.get("end_date"),
                })
        return sorted(plans, key=lambda x: x.get("start_date", ""), reverse=True)

    def delete_workout_plan(self, plan_id: str) -> bool:
        """Delete a workout plan.

        Args:
            plan_id: Unique identifier for the plan

        Returns:
            True if deleted, False if not found
        """
        path = self.data_dir / "workout_plans" / f"{plan_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    # Progress Tracking Methods
    def save_progress_tracker(
        self, tracker: ProgressTracker, user_id: str = "default"
    ) -> None:
        """Save progress tracker for a user.

        Args:
            tracker: Progress tracker to save
            user_id: User identifier
        """
        path = self.data_dir / "progress" / f"{user_id}.json"
        self._save_json(path, tracker.to_dict())

    def load_progress_tracker(
        self, user_id: str = "default"
    ) -> ProgressTracker | None:
        """Load progress tracker for a user.

        Args:
            user_id: User identifier

        Returns:
            Progress tracker or None if not found
        """
        path = self.data_dir / "progress" / f"{user_id}.json"
        data = self._load_json(path)
        if data:
            return ProgressTracker.from_dict(data)
        return None

    def add_progress_entry(
        self, entry: ProgressEntry, user_id: str = "default"
    ) -> None:
        """Add a progress entry for a user.

        Args:
            entry: Progress entry to add
            user_id: User identifier
        """
        tracker = self.load_progress_tracker(user_id)
        if tracker is None:
            tracker = ProgressTracker(user_id=user_id)

        tracker.add_entry(entry)
        self.save_progress_tracker(tracker, user_id)

    def get_progress_summary(self, user_id: str = "default") -> dict | None:
        """Get progress summary for a user.

        Args:
            user_id: User identifier

        Returns:
            Summary dict or None if no data
        """
        tracker = self.load_progress_tracker(user_id)
        if tracker:
            return tracker.get_summary()
        return None

    # Utility Methods
    def export_all_data(self, user_id: str = "default") -> dict:
        """Export all data for a user.

        Args:
            user_id: User identifier

        Returns:
            Dictionary with all user data
        """
        data = {
            "user_profile": None,
            "meal_plans": [],
            "workout_plans": [],
            "progress": None,
        }

        # User profile
        profile = self.load_user_profile(user_id)
        if profile:
            data["user_profile"] = profile.to_dict()

        # Meal plans
        for plan_info in self.list_meal_plans():
            plan = self.load_meal_plan(plan_info["id"])
            if plan:
                data["meal_plans"].append(plan.to_dict())

        # Workout plans
        for plan_info in self.list_workout_plans():
            plan = self.load_workout_plan(plan_info["id"])
            if plan:
                data["workout_plans"].append(plan.to_dict())

        # Progress
        tracker = self.load_progress_tracker(user_id)
        if tracker:
            data["progress"] = tracker.to_dict()

        return data

    def import_data(self, data: dict, user_id: str = "default") -> None:
        """Import data for a user.

        Args:
            data: Dictionary with user data
            user_id: User identifier
        """
        # User profile
        if data.get("user_profile"):
            profile = UserProfile.from_dict(data["user_profile"])
            self.save_user_profile(profile, user_id)

        # Meal plans
        for plan_data in data.get("meal_plans", []):
            plan = MealPlan.from_dict(plan_data)
            self.save_meal_plan(plan)

        # Workout plans
        for plan_data in data.get("workout_plans", []):
            plan = WorkoutPlan.from_dict(plan_data)
            self.save_workout_plan(plan)

        # Progress
        if data.get("progress"):
            tracker = ProgressTracker.from_dict(data["progress"])
            self.save_progress_tracker(tracker, user_id)

    def clear_all_data(self) -> None:
        """Clear all stored data. Use with caution!"""
        import shutil

        for subdir in ["users", "meal_plans", "workout_plans", "progress"]:
            dir_path = self.data_dir / subdir
            if dir_path.exists():
                shutil.rmtree(dir_path)

        self._ensure_directories()
