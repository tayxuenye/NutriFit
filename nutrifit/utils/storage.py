"""Data storage utilities for NutriFit."""

import json
import logging
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any, TypeVar

from nutrifit.models.plan import MealPlan, WorkoutPlan
from nutrifit.models.progress import ProgressEntry, ProgressTracker
from nutrifit.models.user import UserProfile

T = TypeVar("T")

# Configure logging
logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Base exception for storage-related errors."""
    pass


class FileNotFoundError(StorageError):
    """Raised when a requested file is not found."""
    pass


class CorruptedDataError(StorageError):
    """Raised when data file is corrupted or invalid."""
    pass


class PermissionError(StorageError):
    """Raised when file operations fail due to permissions."""
    pass


class ValidationError(StorageError):
    """Raised when data validation fails before persistence."""
    pass


class StorageManager:
    """
    Enhanced storage manager with comprehensive error handling and validation.
    
    Provides robust file-based storage for NutriFit data with:
    - Data validation before persistence
    - Comprehensive error handling
    - Automatic directory structure initialization
    - Graceful handling of corrupted data
    """

    def __init__(self, data_dir: Path | None = None):
        """Initialize storage manager.

        Args:
            data_dir: Directory for data storage. Defaults to ~/.nutrifit/data
            
        Raises:
            PermissionError: If unable to create storage directories
        """
        self.data_dir = data_dir or Path.home() / ".nutrifit" / "data"
        self._ensure_directories()
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Set up logging for storage operations."""
        log_dir = self.data_dir.parent / "logs"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "nutrifit.log"
            
            # Configure file handler
            handler = logging.FileHandler(log_file)
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        except OSError as e:
            # If we can't set up logging, continue without it
            print(f"Warning: Could not set up logging: {e}")

    def _ensure_directories(self) -> None:
        """Create necessary directories.
        
        Raises:
            PermissionError: If unable to create directories
        """
        try:
            (self.data_dir / "users").mkdir(parents=True, exist_ok=True)
            (self.data_dir / "meal_plans").mkdir(parents=True, exist_ok=True)
            (self.data_dir / "workout_plans").mkdir(parents=True, exist_ok=True)
            (self.data_dir / "progress").mkdir(parents=True, exist_ok=True)
            logger.info(f"Storage directories initialized at {self.data_dir}")
        except OSError as e:
            error_msg = f"Failed to create storage directories: {e}"
            logger.error(error_msg)
            raise PermissionError(error_msg) from e

    def _validate_data(self, obj: Any) -> None:
        """Validate data structure before persistence.
        
        Args:
            obj: Object to validate
            
        Raises:
            ValidationError: If data structure is invalid
        """
        if hasattr(obj, 'is_valid_structure'):
            if not obj.is_valid_structure():
                error_msg = f"Invalid data structure for {type(obj).__name__}"
                logger.error(error_msg)
                raise ValidationError(error_msg)
        
        if hasattr(obj, 'validate'):
            try:
                obj.validate()
            except (ValueError, TypeError, AttributeError) as e:
                error_msg = f"Validation failed for {type(obj).__name__}: {e}"
                logger.error(error_msg)
                raise ValidationError(error_msg) from e

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
        """Save data to JSON file with error handling.
        
        Args:
            path: Path to save file
            data: Data to save
            
        Raises:
            PermissionError: If unable to write file
            ValidationError: If data is invalid
        """
        try:
            serialized = self._serialize(data)
            # Write to temporary file first
            temp_path = path.with_suffix('.tmp')
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(serialized, f, indent=2, default=str)
            
            # Verify the file is valid JSON
            with open(temp_path, encoding="utf-8") as f:
                json.load(f)
            
            # Move temp file to final location
            temp_path.replace(path)
            logger.info(f"Successfully saved data to {path}")
        except OSError as e:
            error_msg = f"Failed to write file {path}: {e}"
            logger.error(error_msg)
            raise PermissionError(error_msg) from e
        except (TypeError, ValueError) as e:
            error_msg = f"Failed to serialize data: {e}"
            logger.error(error_msg)
            raise ValidationError(error_msg) from e

    def _load_json(self, path: Path) -> dict | None:
        """Load data from JSON file with error handling.
        
        Args:
            path: Path to load file from
            
        Returns:
            Loaded data or None if file not found
            
        Raises:
            CorruptedDataError: If file is corrupted or invalid JSON
            PermissionError: If unable to read file
        """
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return None
        
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Successfully loaded data from {path}")
            return data
        except json.JSONDecodeError as e:
            error_msg = f"Corrupted JSON file {path}: {e}"
            logger.error(error_msg)
            raise CorruptedDataError(error_msg) from e
        except OSError as e:
            error_msg = f"Failed to read file {path}: {e}"
            logger.error(error_msg)
            raise PermissionError(error_msg) from e

    # User Profile Methods
    def save_user_profile(self, user: UserProfile, user_id: str = "default") -> None:
        """Save user profile with validation.

        Args:
            user: User profile to save
            user_id: Unique identifier for the user
            
        Raises:
            ValidationError: If user profile is invalid
            PermissionError: If unable to write file
        """
        self._validate_data(user)
        path = self.data_dir / "users" / f"{user_id}.json"
        self._save_json(path, user.to_dict())

    def load_user_profile(self, user_id: str = "default") -> UserProfile | None:
        """Load user profile with error handling.

        Args:
            user_id: Unique identifier for the user

        Returns:
            User profile or None if not found
            
        Raises:
            CorruptedDataError: If file is corrupted
            PermissionError: If unable to read file
        """
        path = self.data_dir / "users" / f"{user_id}.json"
        data = self._load_json(path)
        if data:
            try:
                return UserProfile.from_dict(data)
            except (KeyError, ValueError, TypeError) as e:
                error_msg = f"Failed to deserialize user profile: {e}"
                logger.error(error_msg)
                raise CorruptedDataError(error_msg) from e
        return None

    def list_user_profiles(self) -> list[str]:
        """List all saved user profile IDs."""
        profiles_dir = self.data_dir / "users"
        try:
            return [p.stem for p in profiles_dir.glob("*.json")]
        except OSError as e:
            logger.error(f"Failed to list user profiles: {e}")
            return []

    def delete_user_profile(self, user_id: str) -> bool:
        """Delete a user profile.

        Args:
            user_id: Unique identifier for the user

        Returns:
            True if deleted, False if not found
            
        Raises:
            PermissionError: If unable to delete file
        """
        path = self.data_dir / "users" / f"{user_id}.json"
        if path.exists():
            try:
                path.unlink()
                logger.info(f"Deleted user profile: {user_id}")
                return True
            except OSError as e:
                error_msg = f"Failed to delete user profile {user_id}: {e}"
                logger.error(error_msg)
                raise PermissionError(error_msg) from e
        return False

    # Meal Plan Methods
    def find_meal_plan_by_date_range(self, start_date: date, end_date: date) -> str | None:
        """Find a meal plan ID by date range.
        
        Args:
            start_date: Start date of the plan
            end_date: End date of the plan
            
        Returns:
            Plan ID if found, None otherwise
        """
        plans_dir = self.data_dir / "meal_plans"
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        
        for path in plans_dir.glob("*.json"):
            try:
                data = self._load_json(path)
                if data:
                    plan_start = data.get("start_date")
                    plan_end = data.get("end_date")
                    if plan_start == start_str and plan_end == end_str:
                        return data.get("id")
            except (CorruptedDataError, PermissionError):
                continue
        return None

    def save_meal_plan(self, plan: MealPlan, overwrite_existing: bool = True) -> tuple[bool, str]:
        """Save a meal plan with validation. Optionally overwrite existing plan for same date range.

        Args:
            plan: Meal plan to save
            overwrite_existing: If True, delete existing plan with same date range before saving
            
        Returns:
            Tuple of (was_replaced: bool, plan_id: str)
            
        Raises:
            ValidationError: If meal plan is invalid
            PermissionError: If unable to write file
        """
        self._validate_data(plan)
        
        was_replaced = False
        if overwrite_existing:
            existing_id = self.find_meal_plan_by_date_range(plan.start_date, plan.end_date)
            if existing_id and existing_id != plan.id:
                # Delete the old plan
                old_path = self.data_dir / "meal_plans" / f"{existing_id}.json"
                if old_path.exists():
                    try:
                        old_path.unlink()
                        was_replaced = True
                        logger.info(f"Replaced existing meal plan {existing_id} with {plan.id}")
                    except OSError:
                        pass  # Continue even if deletion fails
        
        path = self.data_dir / "meal_plans" / f"{plan.id}.json"
        self._save_json(path, plan.to_dict())
        return was_replaced, plan.id

    def load_meal_plan(self, plan_id: str) -> MealPlan | None:
        """Load a meal plan with error handling.

        Args:
            plan_id: Unique identifier for the plan

        Returns:
            Meal plan or None if not found
            
        Raises:
            CorruptedDataError: If file is corrupted
            PermissionError: If unable to read file
        """
        path = self.data_dir / "meal_plans" / f"{plan_id}.json"
        data = self._load_json(path)
        if data:
            try:
                return MealPlan.from_dict(data)
            except (KeyError, ValueError, TypeError) as e:
                error_msg = f"Failed to deserialize meal plan: {e}"
                logger.error(error_msg)
                raise CorruptedDataError(error_msg) from e
        return None

    def list_meal_plans(self) -> list[dict]:
        """List all saved meal plans with basic info. Returns only one plan per date range (latest)."""
        plans_dir = self.data_dir / "meal_plans"
        plans_by_range: dict[tuple[str, str], dict] = {}
        
        for path in plans_dir.glob("*.json"):
            try:
                data = self._load_json(path)
                if data:
                    # Get file modification time
                    mtime = path.stat().st_mtime if path.exists() else None
                    start_date = data.get("start_date") or ""
                    end_date = data.get("end_date") or ""
                    
                    # Skip if dates are missing
                    if not start_date or not end_date:
                        continue
                    
                    range_key = (start_date, end_date)
                    
                    plan_info = {
                        "id": data.get("id"),
                        "name": data.get("name"),
                        "start_date": start_date,
                        "end_date": end_date,
                        "created_at": mtime,
                    }
                    
                    # Keep only the latest plan for each date range
                    if range_key not in plans_by_range:
                        plans_by_range[range_key] = plan_info
                    else:
                        existing_mtime = plans_by_range[range_key].get("created_at") or 0
                        if (mtime or 0) > existing_mtime:
                            plans_by_range[range_key] = plan_info
                            
            except (CorruptedDataError, PermissionError) as e:
                logger.warning(f"Skipping corrupted meal plan {path}: {e}")
                continue
        
        # Convert to list and sort by start_date descending (newest first)
        plans = list(plans_by_range.values())
        return sorted(plans, key=lambda x: x.get("start_date", ""), reverse=True)

    def delete_meal_plan(self, plan_id: str) -> bool:
        """Delete a meal plan.

        Args:
            plan_id: Unique identifier for the plan

        Returns:
            True if deleted, False if not found
            
        Raises:
            PermissionError: If unable to delete file
        """
        path = self.data_dir / "meal_plans" / f"{plan_id}.json"
        if path.exists():
            try:
                path.unlink()
                logger.info(f"Deleted meal plan: {plan_id}")
                return True
            except OSError as e:
                error_msg = f"Failed to delete meal plan {plan_id}: {e}"
                logger.error(error_msg)
                raise PermissionError(error_msg) from e
        return False

    # Workout Plan Methods
    def save_workout_plan(self, plan: WorkoutPlan, overwrite_existing: bool = True) -> tuple[bool, str]:
        """Save a workout plan with validation. Optionally overwrite existing plan for same date range.

        Args:
            plan: Workout plan to save
            overwrite_existing: If True, delete existing plan with same date range before saving
            
        Returns:
            Tuple of (was_replaced: bool, plan_id: str)
            
        Raises:
            ValidationError: If workout plan is invalid
            PermissionError: If unable to write file
        """
        self._validate_data(plan)
        
        was_replaced = False
        if overwrite_existing:
            existing_id = self.find_workout_plan_by_date_range(plan.start_date, plan.end_date)
            if existing_id:
                # Always delete existing plan if found, even if IDs match (in case of regeneration)
                old_path = self.data_dir / "workout_plans" / f"{existing_id}.json"
                if old_path.exists():
                    try:
                        old_path.unlink()
                        was_replaced = True
                        logger.info(f"Replaced existing workout plan {existing_id} with {plan.id} (date range: {plan.start_date} to {plan.end_date})")
                    except OSError as e:
                        logger.warning(f"Failed to delete old workout plan {existing_id}: {e}")
        
        path = self.data_dir / "workout_plans" / f"{plan.id}.json"
        self._save_json(path, plan.to_dict())
        return was_replaced, plan.id

    def load_workout_plan(self, plan_id: str) -> WorkoutPlan | None:
        """Load a workout plan with error handling.

        Args:
            plan_id: Unique identifier for the plan

        Returns:
            Workout plan or None if not found
            
        Raises:
            CorruptedDataError: If file is corrupted
            PermissionError: If unable to read file
        """
        path = self.data_dir / "workout_plans" / f"{plan_id}.json"
        data = self._load_json(path)
        if data:
            try:
                return WorkoutPlan.from_dict(data)
            except (KeyError, ValueError, TypeError) as e:
                error_msg = f"Failed to deserialize workout plan: {e}"
                logger.error(error_msg)
                raise CorruptedDataError(error_msg) from e
        return None

    def find_workout_plan_by_date_range(self, start_date: date, end_date: date) -> str | None:
        """Find a workout plan ID by date range.
        
        Args:
            start_date: Start date of the plan
            end_date: End date of the plan
            
        Returns:
            Plan ID if found, None otherwise
        """
        plans_dir = self.data_dir / "workout_plans"
        if not plans_dir.exists():
            return None
            
        start_str = start_date.isoformat()
        end_str = end_date.isoformat()
        
        for path in plans_dir.glob("*.json"):
            try:
                data = self._load_json(path)
                if data:
                    plan_start = data.get("start_date")
                    plan_end = data.get("end_date")
                    # Compare as strings (ISO format) for exact match
                    if plan_start == start_str and plan_end == end_str:
                        plan_id = data.get("id")
                        logger.debug(f"Found existing workout plan {plan_id} with date range {plan_start} to {plan_end}")
                        return plan_id
            except (CorruptedDataError, PermissionError) as e:
                logger.warning(f"Error reading workout plan file {path}: {e}")
                continue
        return None

    def list_workout_plans(self) -> list[dict]:
        """List all saved workout plans with basic info."""
        plans_dir = self.data_dir / "workout_plans"
        plans = []
        for path in plans_dir.glob("*.json"):
            try:
                data = self._load_json(path)
                if data:
                    # Get file modification time to distinguish plans with same date
                    mtime = path.stat().st_mtime if path.exists() else None
                    plans.append({
                        "id": data.get("id"),
                        "name": data.get("name"),
                        "start_date": data.get("start_date"),
                        "end_date": data.get("end_date"),
                        "workout_days_per_week": data.get("workout_days_per_week"),
                        "created_at": mtime,
                    })
            except (CorruptedDataError, PermissionError) as e:
                logger.warning(f"Skipping corrupted workout plan {path}: {e}")
                continue
        # Sort by creation time (newest first), then by start_date
        return sorted(plans, key=lambda x: (x.get("created_at") or 0, x.get("start_date", "")), reverse=True)

    def delete_workout_plan(self, plan_id: str) -> bool:
        """Delete a workout plan.

        Args:
            plan_id: Unique identifier for the plan

        Returns:
            True if deleted, False if not found
            
        Raises:
            PermissionError: If unable to delete file
        """
        path = self.data_dir / "workout_plans" / f"{plan_id}.json"
        if path.exists():
            try:
                path.unlink()
                logger.info(f"Deleted workout plan: {plan_id}")
                return True
            except OSError as e:
                error_msg = f"Failed to delete workout plan {plan_id}: {e}"
                logger.error(error_msg)
                raise PermissionError(error_msg) from e
        return False

    # Progress Tracking Methods
    def save_progress_tracker(
        self, tracker: ProgressTracker, user_id: str = "default"
    ) -> None:
        """Save progress tracker for a user with validation.

        Args:
            tracker: Progress tracker to save
            user_id: User identifier
            
        Raises:
            ValidationError: If progress tracker is invalid
            PermissionError: If unable to write file
        """
        self._validate_data(tracker)
        path = self.data_dir / "progress" / f"{user_id}.json"
        self._save_json(path, tracker.to_dict())

    def load_progress_tracker(
        self, user_id: str = "default"
    ) -> ProgressTracker | None:
        """Load progress tracker for a user with error handling.

        Args:
            user_id: User identifier

        Returns:
            Progress tracker or None if not found
            
        Raises:
            CorruptedDataError: If file is corrupted
            PermissionError: If unable to read file
        """
        path = self.data_dir / "progress" / f"{user_id}.json"
        data = self._load_json(path)
        if data:
            try:
                return ProgressTracker.from_dict(data)
            except (KeyError, ValueError, TypeError) as e:
                error_msg = f"Failed to deserialize progress tracker: {e}"
                logger.error(error_msg)
                raise CorruptedDataError(error_msg) from e
        return None

    def add_progress_entry(
        self, entry: ProgressEntry, user_id: str = "default"
    ) -> None:
        """Add a progress entry for a user with validation.

        Args:
            entry: Progress entry to add
            user_id: User identifier
            
        Raises:
            ValidationError: If progress entry is invalid
            PermissionError: If unable to write file
        """
        self._validate_data(entry)
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
        try:
            tracker = self.load_progress_tracker(user_id)
            if tracker:
                return tracker.get_summary()
        except (CorruptedDataError, PermissionError) as e:
            logger.error(f"Failed to get progress summary: {e}")
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

        try:
            # User profile
            profile = self.load_user_profile(user_id)
            if profile:
                data["user_profile"] = profile.to_dict()

            # Meal plans
            for plan_info in self.list_meal_plans():
                try:
                    plan = self.load_meal_plan(plan_info["id"])
                    if plan:
                        data["meal_plans"].append(plan.to_dict())
                except (CorruptedDataError, PermissionError) as e:
                    logger.warning(f"Skipping meal plan {plan_info['id']}: {e}")

            # Workout plans
            for plan_info in self.list_workout_plans():
                try:
                    plan = self.load_workout_plan(plan_info["id"])
                    if plan:
                        data["workout_plans"].append(plan.to_dict())
                except (CorruptedDataError, PermissionError) as e:
                    logger.warning(f"Skipping workout plan {plan_info['id']}: {e}")

            # Progress
            tracker = self.load_progress_tracker(user_id)
            if tracker:
                data["progress"] = tracker.to_dict()
        except Exception as e:
            logger.error(f"Error during data export: {e}")

        return data

    def import_data(self, data: dict, user_id: str = "default") -> None:
        """Import data for a user with validation.

        Args:
            data: Dictionary with user data
            user_id: User identifier
            
        Raises:
            ValidationError: If data is invalid
            PermissionError: If unable to write files
        """
        # User profile
        if data.get("user_profile"):
            try:
                profile = UserProfile.from_dict(data["user_profile"])
                self.save_user_profile(profile, user_id)
            except Exception as e:
                logger.error(f"Failed to import user profile: {e}")

        # Meal plans
        for plan_data in data.get("meal_plans", []):
            try:
                plan = MealPlan.from_dict(plan_data)
                self.save_meal_plan(plan)
            except Exception as e:
                logger.error(f"Failed to import meal plan: {e}")

        # Workout plans
        for plan_data in data.get("workout_plans", []):
            try:
                plan = WorkoutPlan.from_dict(plan_data)
                self.save_workout_plan(plan)
            except Exception as e:
                logger.error(f"Failed to import workout plan: {e}")

        # Progress
        if data.get("progress"):
            try:
                tracker = ProgressTracker.from_dict(data["progress"])
                self.save_progress_tracker(tracker, user_id)
            except Exception as e:
                logger.error(f"Failed to import progress tracker: {e}")

    def clear_all_data(self) -> None:
        """Clear all stored data. Use with caution!
        
        Raises:
            PermissionError: If unable to delete directories
        """
        try:
            for subdir in ["users", "meal_plans", "workout_plans", "progress"]:
                dir_path = self.data_dir / subdir
                if dir_path.exists():
                    shutil.rmtree(dir_path)
            self._ensure_directories()
            logger.warning("All data cleared")
        except OSError as e:
            error_msg = f"Failed to clear data: {e}"
            logger.error(error_msg)
            raise PermissionError(error_msg) from e


# Keep DataStorage as an alias for backward compatibility
class DataStorage(StorageManager):
    """
    Local file-based storage for NutriFit data.
    
    This class is an alias for StorageManager for backward compatibility.
    """
    pass
