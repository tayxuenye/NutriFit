"""Workout planner engine for generating personalized workout plans."""

import random
import uuid
from datetime import date, timedelta
from typing import Any

from nutrifit.data.workouts import get_sample_workouts
from nutrifit.engines.embedding_engine import EmbeddingEngine
from nutrifit.engines.llm_engine import LocalLLMEngine
from nutrifit.models.plan import DailyWorkoutPlan, WorkoutPlan
from nutrifit.models.user import FitnessGoal, UserProfile
from nutrifit.models.workout import MuscleGroup, Workout


class WorkoutPlannerEngine:
    """
    Engine for generating personalized workout plans.

    Uses embedding-based matching to find suitable workouts based on
    user goals, available equipment, and fitness level.
    """

    def __init__(
        self,
        embedding_engine: EmbeddingEngine | None = None,
        llm_engine: LocalLLMEngine | None = None,
        workouts: list[Workout] | None = None,
    ):
        """Initialize the workout planner engine.

        Args:
            embedding_engine: Engine for semantic matching
            llm_engine: Engine for creative suggestions
            workouts: List of available workouts (defaults to sample workouts)
        """
        self.embedding_engine = embedding_engine or EmbeddingEngine()
        self.llm_engine = llm_engine or LocalLLMEngine()
        self.workouts = workouts or get_sample_workouts()
        self._workout_embeddings: dict[str, Any] = {}
        self._initialize_workout_embeddings()

    def _initialize_workout_embeddings(self) -> None:
        """Pre-compute embeddings for all workouts."""
        texts = [workout.get_searchable_text() for workout in self.workouts]
        ids = [workout.id for workout in self.workouts]

        embeddings = self.embedding_engine.embed_batch(texts)

        for workout_id, embedding in zip(ids, embeddings, strict=False):
            self._workout_embeddings[workout_id] = embedding

    def _get_goal_workout_types(self, goals: list[FitnessGoal]) -> list[str]:
        """Map fitness goals to preferred workout types."""
        goal_to_types = {
            FitnessGoal.WEIGHT_LOSS: ["hiit", "cardio", "strength"],
            FitnessGoal.MUSCLE_GAIN: ["strength"],
            FitnessGoal.MAINTENANCE: ["strength", "cardio", "flexibility"],
            FitnessGoal.ENDURANCE: ["cardio", "hiit"],
            FitnessGoal.STRENGTH: ["strength"],
            FitnessGoal.FLEXIBILITY: ["flexibility"],
            FitnessGoal.GENERAL_FITNESS: ["strength", "cardio", "hiit", "flexibility"],
        }

        types = set()
        for goal in goals:
            types.update(goal_to_types.get(goal, ["strength", "cardio"]))

        return list(types) if types else ["strength", "cardio", "flexibility"]

    def _filter_workouts_by_equipment(
        self, workouts: list[Workout], available_equipment: list[str]
    ) -> list[Workout]:
        """Filter workouts based on available equipment."""
        if not available_equipment:
            # Include bodyweight workouts if no equipment specified
            available_equipment = ["bodyweight", "none"]

        # Always include bodyweight as available
        available_lower = [e.lower() for e in available_equipment]
        available_lower.extend(["bodyweight", "none"])

        filtered = []
        for workout in workouts:
            needed_equipment = workout.get_all_equipment_needed()
            if not needed_equipment:
                filtered.append(workout)
            elif all(eq in available_lower for eq in needed_equipment):
                filtered.append(workout)

        return filtered if filtered else workouts

    def _filter_workouts_by_type(
        self, workouts: list[Workout], workout_types: list[str]
    ) -> list[Workout]:
        """Filter workouts by type."""
        if not workout_types:
            return workouts

        return [w for w in workouts if w.workout_type in workout_types]

    def _filter_workouts_by_difficulty(
        self, workouts: list[Workout], difficulty: str
    ) -> list[Workout]:
        """Filter workouts by difficulty level."""
        difficulty_levels = {
            "beginner": ["beginner"],
            "intermediate": ["beginner", "intermediate"],
            "advanced": ["beginner", "intermediate", "advanced"],
        }

        allowed = difficulty_levels.get(difficulty.lower(), ["beginner", "intermediate"])
        return [w for w in workouts if w.difficulty in allowed]

    def _filter_workouts_by_duration(
        self, workouts: list[Workout], max_duration: int
    ) -> list[Workout]:
        """Filter workouts by maximum duration."""
        return [w for w in workouts if w.total_duration_minutes <= max_duration]

    def _get_muscle_groups_for_goals(
        self, goals: list[FitnessGoal]
    ) -> list[MuscleGroup]:
        """Get target muscle groups based on fitness goals."""
        goal_to_muscles = {
            FitnessGoal.WEIGHT_LOSS: [MuscleGroup.FULL_BODY, MuscleGroup.CARDIO],
            FitnessGoal.MUSCLE_GAIN: [
                MuscleGroup.CHEST,
                MuscleGroup.BACK,
                MuscleGroup.SHOULDERS,
                MuscleGroup.QUADRICEPS,
                MuscleGroup.HAMSTRINGS,
            ],
            FitnessGoal.MAINTENANCE: [MuscleGroup.FULL_BODY],
            FitnessGoal.ENDURANCE: [MuscleGroup.CARDIO, MuscleGroup.FULL_BODY],
            FitnessGoal.STRENGTH: [
                MuscleGroup.CHEST,
                MuscleGroup.BACK,
                MuscleGroup.QUADRICEPS,
                MuscleGroup.CORE,
            ],
            FitnessGoal.FLEXIBILITY: [MuscleGroup.FULL_BODY],
            FitnessGoal.GENERAL_FITNESS: [MuscleGroup.FULL_BODY, MuscleGroup.CARDIO],
        }

        muscles = set()
        for goal in goals:
            muscles.update(goal_to_muscles.get(goal, [MuscleGroup.FULL_BODY]))

        return list(muscles)

    def find_matching_workouts(
        self,
        user: UserProfile,
        workout_type: str | None = None,
        query: str | None = None,
        max_duration: int = 60,
        top_k: int = 5,
    ) -> list[tuple[Workout, float]]:
        """Find workouts matching user preferences and optional query.

        Args:
            user: User profile with preferences
            workout_type: Optional specific workout type
            query: Optional search query
            max_duration: Maximum workout duration in minutes
            top_k: Number of top results to return

        Returns:
            List of (Workout, score) tuples
        """
        # Get preferred workout types based on goals
        if workout_type:
            preferred_types = [workout_type]
        else:
            preferred_types = self._get_goal_workout_types(user.fitness_goals)

        # Apply filters
        candidates = self.workouts
        candidates = self._filter_workouts_by_equipment(
            candidates, user.available_equipment
        )
        candidates = self._filter_workouts_by_type(candidates, preferred_types)
        candidates = self._filter_workouts_by_duration(candidates, max_duration)

        # Determine user difficulty level (simplified)
        difficulty = "intermediate"  # Default
        if FitnessGoal.GENERAL_FITNESS in user.fitness_goals:
            difficulty = "beginner"

        candidates = self._filter_workouts_by_difficulty(candidates, difficulty)

        if not candidates:
            # Fall back to all workouts with equipment filter
            candidates = self._filter_workouts_by_equipment(
                self.workouts, user.available_equipment
            )

        if not candidates:
            return []

        # Score workouts
        scored_workouts = []
        target_muscles = self._get_muscle_groups_for_goals(user.fitness_goals)

        for workout in candidates:
            # Score based on muscle group match
            workout_muscles = set(workout.target_muscle_groups)
            target_muscles_set = set(target_muscles)
            muscle_score = (
                len(workout_muscles & target_muscles_set) / max(len(target_muscles_set), 1)
                if target_muscles_set
                else 0.5
            )

            # Semantic similarity if query provided
            if query:
                workout_text = workout.get_searchable_text()
                similar = self.embedding_engine.find_similar(
                    query, [workout_text], [workout.id], top_k=1
                )
                semantic_score = similar[0][2] if similar else 0.5
            else:
                semantic_score = 0.5

            # Combined score
            combined_score = 0.4 * muscle_score + 0.6 * semantic_score
            scored_workouts.append((workout, combined_score))

        # Sort by score and return top_k
        scored_workouts.sort(key=lambda x: x[1], reverse=True)
        return scored_workouts[:top_k]

    def _select_workout_for_day(
        self,
        user: UserProfile,
        day_number: int,
        used_workout_ids: set[str],
        max_duration: int = 60,
    ) -> Workout | None:
        """Select a workout for a specific day.

        Args:
            user: User profile
            day_number: Day of the week (0-6)
            used_workout_ids: Set of already used workout IDs
            max_duration: Maximum workout duration

        Returns:
            Selected workout or None
        """
        # Determine workout type based on day (example split)
        day_focus = {
            0: "strength",  # Monday: Full body strength
            1: "cardio",  # Tuesday: Cardio
            2: "strength",  # Wednesday: Upper body
            3: None,  # Thursday: Rest or flexibility
            4: "strength",  # Friday: Lower body
            5: "hiit",  # Saturday: HIIT
            6: None,  # Sunday: Rest or flexibility
        }

        workout_type = day_focus.get(day_number)

        if workout_type is None:
            # Rest day or flexibility
            matches = self.find_matching_workouts(
                user, workout_type="flexibility", max_duration=30, top_k=5
            )
        else:
            matches = self.find_matching_workouts(
                user, workout_type=workout_type, max_duration=max_duration, top_k=5
            )

        # Filter out already used workouts
        available = [(w, s) for w, s in matches if w.id not in used_workout_ids]

        if not available:
            available = matches  # Allow repeats if necessary

        if available:
            # Pick from top 3 with some randomness
            top_choices = available[:3]
            return random.choice(top_choices)[0]

        return None

    def generate_daily_plan(
        self,
        user: UserProfile,
        plan_date: date,
        day_number: int = 0,
        max_duration: int = 60,
    ) -> DailyWorkoutPlan:
        """Generate a workout plan for a single day.

        Args:
            user: User profile with preferences
            plan_date: Date for the plan
            day_number: Day of the week (0-6)
            max_duration: Maximum workout duration

        Returns:
            Daily workout plan
        """
        # Check if it should be a rest day
        is_rest_day = day_number in [3, 6]  # Thursday and Sunday

        if is_rest_day:
            return DailyWorkoutPlan(
                date=plan_date,
                workouts=[],
                is_rest_day=True,
                notes="Rest day - focus on recovery and light stretching",
            )

        workout = self._select_workout_for_day(
            user, day_number, set(), max_duration
        )

        return DailyWorkoutPlan(
            date=plan_date,
            workouts=[workout] if workout else [],
            is_rest_day=False,
        )

    def generate_weekly_plan(
        self,
        user: UserProfile,
        start_date: date | None = None,
        plan_name: str | None = None,
        workout_days_per_week: int = 4,
    ) -> WorkoutPlan:
        """Generate a workout plan for a week.

        Args:
            user: User profile with preferences
            start_date: Start date for the plan (defaults to today)
            plan_name: Optional name for the plan
            workout_days_per_week: Target workout days per week

        Returns:
            Weekly workout plan
        """
        start_date = start_date or date.today()
        end_date = start_date + timedelta(days=6)

        # Determine rest days based on workout_days_per_week
        rest_days = set()
        if workout_days_per_week <= 4:
            rest_days = {3, 6}  # Thursday and Sunday
            if workout_days_per_week <= 3:
                rest_days.add(1)  # Add Tuesday

        daily_plans = []
        used_workout_ids: set[str] = set()

        for day_offset in range(7):
            plan_date = start_date + timedelta(days=day_offset)
            day_number = (start_date.weekday() + day_offset) % 7

            if day_offset in rest_days:
                daily_plan = DailyWorkoutPlan(
                    date=plan_date,
                    workouts=[],
                    is_rest_day=True,
                    notes="Rest day - focus on recovery",
                )
            else:
                workout = self._select_workout_for_day(
                    user, day_number, used_workout_ids
                )
                if workout:
                    used_workout_ids.add(workout.id)

                daily_plan = DailyWorkoutPlan(
                    date=plan_date,
                    workouts=[workout] if workout else [],
                    is_rest_day=False,
                )

            daily_plans.append(daily_plan)

        return WorkoutPlan(
            id=f"wp_{uuid.uuid4().hex[:8]}",
            name=plan_name or f"Weekly Workout Plan - {start_date.strftime('%Y-%m-%d')}",
            start_date=start_date,
            end_date=end_date,
            daily_plans=daily_plans,
            workout_days_per_week=workout_days_per_week,
        )

    def get_workout_suggestion(
        self,
        user: UserProfile,
        duration_minutes: int = 30,
    ) -> str:
        """Get a creative workout suggestion from the LLM.

        Args:
            user: User profile
            duration_minutes: Target workout duration

        Returns:
            Suggestion text
        """
        fitness_goals = [g.value for g in user.fitness_goals]

        # Determine difficulty based on profile (simplified)
        difficulty = "intermediate"

        return self.llm_engine.suggest_workout(
            fitness_goals=fitness_goals,
            available_equipment=user.available_equipment,
            duration_minutes=duration_minutes,
            difficulty=difficulty,
        )

    def search_workouts(
        self,
        query: str,
        user: UserProfile | None = None,
        workout_type: str | None = None,
        max_duration: int = 120,
        top_k: int = 10,
    ) -> list[tuple[Workout, float]]:
        """Search for workouts using semantic search.

        Args:
            query: Search query
            user: Optional user profile for filtering
            workout_type: Optional workout type filter
            max_duration: Maximum workout duration
            top_k: Number of results to return

        Returns:
            List of (Workout, score) tuples
        """
        candidates = self.workouts

        if workout_type:
            candidates = self._filter_workouts_by_type(candidates, [workout_type])

        candidates = self._filter_workouts_by_duration(candidates, max_duration)

        if user:
            candidates = self._filter_workouts_by_equipment(
                candidates, user.available_equipment
            )

        if not candidates:
            return []

        # Perform semantic search
        texts = [w.get_searchable_text() for w in candidates]
        ids = [w.id for w in candidates]

        results = self.embedding_engine.find_similar(query, texts, ids, top_k=top_k)

        # Map back to workouts
        id_to_workout = {w.id: w for w in candidates}
        return [(id_to_workout[wid], score) for _, wid, score in results if wid in id_to_workout]

    def estimate_weekly_calories_burned(
        self, plan: WorkoutPlan, user_weight_kg: float
    ) -> int:
        """Estimate total calories burned for a weekly workout plan.

        Args:
            plan: Workout plan
            user_weight_kg: User's weight in kg

        Returns:
            Estimated calories burned
        """
        total_calories = 0

        for daily_plan in plan.daily_plans:
            for workout in daily_plan.workouts:
                total_calories += workout.estimate_calories_burned(user_weight_kg)

        return total_calories
