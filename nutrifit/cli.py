#!/usr/bin/env python3
"""
NutriFit CLI - Command line interface for the AI nutrition and workout assistant.

Usage:
    python -m nutrifit.cli [command] [options]

Commands:
    profile     - Manage user profile
    meal        - Generate meal plans and search recipes
    workout     - Generate workout plans and search workouts
    shopping    - Generate shopping lists
    progress    - Track and view progress
    suggest     - Get AI-powered suggestions
"""

import argparse
from datetime import date

from nutrifit.engines.embedding_engine import EmbeddingEngine
from nutrifit.engines.llm_engine import LocalLLMEngine
from nutrifit.engines.meal_planner import MealPlannerEngine
from nutrifit.engines.workout_planner import WorkoutPlannerEngine
from nutrifit.models.progress import ProgressEntry
from nutrifit.models.user import DietaryPreference, FitnessGoal, UserProfile
from nutrifit.utils.shopping_list import ShoppingListOptimizer
from nutrifit.utils.storage import DataStorage


class NutriFitCLI:
    """Command line interface for NutriFit."""

    def __init__(self) -> None:
        """Initialize the CLI with required engines."""
        self.storage = DataStorage()
        self.embedding_engine = EmbeddingEngine()
        self.llm_engine = LocalLLMEngine(use_fallback=True)
        self.meal_planner = MealPlannerEngine(
            embedding_engine=self.embedding_engine,
            llm_engine=self.llm_engine,
        )
        self.workout_planner = WorkoutPlannerEngine(
            embedding_engine=self.embedding_engine,
            llm_engine=self.llm_engine,
        )
        self.shopping_optimizer = ShoppingListOptimizer()

    def _get_or_create_profile(self) -> UserProfile:
        """Get existing profile or prompt to create one."""
        profile = self.storage.load_user_profile()
        if profile:
            return profile

        print("\n🏋️ Welcome to NutriFit! Let's set up your profile.\n")
        return self._create_profile_interactive()

    def _create_profile_interactive(self) -> UserProfile:
        """Create a user profile interactively."""
        print("Please provide the following information:\n")

        name = input("Your name: ").strip() or "User"
        age = int(input("Your age: ") or "30")
        weight = float(input("Your weight (kg): ") or "70")
        height = float(input("Your height (cm): ") or "170")

        print("\nDietary preferences (comma-separated):")
        print("Options: vegetarian, vegan, keto, paleo, gluten_free, dairy_free, low_carb, high_protein")
        diet_input = input("Your preferences: ").strip()
        dietary_prefs = []
        if diet_input:
            for pref in diet_input.split(","):
                pref = pref.strip().lower().replace("-", "_").replace(" ", "_")
                try:
                    dietary_prefs.append(DietaryPreference(pref))
                except ValueError:
                    print(f"Unknown preference: {pref}, skipping...")

        print("\nFitness goals (comma-separated):")
        print("Options: weight_loss, muscle_gain, maintenance, endurance, strength, flexibility, general_fitness")
        goals_input = input("Your goals: ").strip()
        fitness_goals = []
        if goals_input:
            for goal in goals_input.split(","):
                goal = goal.strip().lower().replace("-", "_").replace(" ", "_")
                try:
                    fitness_goals.append(FitnessGoal(goal))
                except ValueError:
                    print(f"Unknown goal: {goal}, skipping...")

        allergies_input = input("\nAny food allergies (comma-separated, or press Enter to skip): ").strip()
        allergies = [a.strip() for a in allergies_input.split(",")] if allergies_input else []

        pantry_input = input("\nItems in your pantry (comma-separated, or press Enter to skip): ").strip()
        pantry_items = [p.strip() for p in pantry_input.split(",")] if pantry_input else []

        equipment_input = input("\nAvailable workout equipment (comma-separated, or press Enter for bodyweight): ").strip()
        equipment = [e.strip() for e in equipment_input.split(",")] if equipment_input else []

        profile = UserProfile(
            name=name,
            age=age,
            weight_kg=weight,
            height_cm=height,
            dietary_preferences=dietary_prefs,
            fitness_goals=fitness_goals,
            allergies=allergies,
            pantry_items=pantry_items,
            available_equipment=equipment,
        )

        self.storage.save_user_profile(profile)
        print(f"\n✅ Profile created! Daily calorie target: {profile.daily_calorie_target} kcal")
        return profile

    def cmd_profile(self, args: argparse.Namespace) -> None:
        """Handle profile commands."""
        if args.action == "show":
            profile = self.storage.load_user_profile()
            if profile:
                print("\n📋 Your Profile")
                print("=" * 40)
                print(f"Name: {profile.name}")
                print(f"Age: {profile.age}")
                print(f"Weight: {profile.weight_kg} kg")
                print(f"Height: {profile.height_cm} cm")
                print(f"Daily Calorie Target: {profile.daily_calorie_target} kcal")
                print(f"Dietary Preferences: {', '.join(p.value for p in profile.dietary_preferences) or 'None'}")
                print(f"Fitness Goals: {', '.join(g.value for g in profile.fitness_goals) or 'None'}")
                print(f"Allergies: {', '.join(profile.allergies) or 'None'}")
                print(f"Pantry Items: {len(profile.pantry_items)} items")
                print(f"Equipment: {', '.join(profile.available_equipment) or 'Bodyweight only'}")
            else:
                print("No profile found. Run 'nutrifit profile create' to create one.")

        elif args.action == "create":
            self._create_profile_interactive()

        elif args.action == "delete":
            if self.storage.delete_user_profile():
                print("✅ Profile deleted.")
            else:
                print("No profile to delete.")

        elif args.action == "update-pantry":
            profile = self._get_or_create_profile()
            if args.items:
                new_items = [i.strip() for i in args.items.split(",")]
                profile.pantry_items = list(set(profile.pantry_items + new_items))
                self.storage.save_user_profile(profile)
                print(f"✅ Pantry updated. Total items: {len(profile.pantry_items)}")

        elif args.action == "update-equipment":
            profile = self._get_or_create_profile()
            if args.items:
                new_items = [i.strip() for i in args.items.split(",")]
                profile.available_equipment = list(set(profile.available_equipment + new_items))
                self.storage.save_user_profile(profile)
                print(f"✅ Equipment updated. Total items: {len(profile.available_equipment)}")

    def cmd_meal(self, args: argparse.Namespace) -> None:
        """Handle meal planning commands."""
        profile = self._get_or_create_profile()

        if args.action == "daily":
            plan = self.meal_planner.generate_daily_plan(profile, date.today())
            print("\n🍽️ Daily Meal Plan")
            print("=" * 40)
            print(f"Date: {plan.date}")
            print(f"Total Calories: ~{plan.total_calories} kcal")
            print()

            if plan.breakfast:
                print(f"🌅 Breakfast: {plan.breakfast.name}")
                print(f"   Calories: {plan.breakfast.nutrition.calories} kcal")
            if plan.lunch:
                print(f"🌞 Lunch: {plan.lunch.name}")
                print(f"   Calories: {plan.lunch.nutrition.calories} kcal")
            if plan.dinner:
                print(f"🌙 Dinner: {plan.dinner.name}")
                print(f"   Calories: {plan.dinner.nutrition.calories} kcal")
            if plan.snacks:
                for snack in plan.snacks:
                    print(f"🍎 Snack: {snack.name}")
                    print(f"   Calories: {snack.nutrition.calories} kcal")

        elif args.action == "weekly":
            plan = self.meal_planner.generate_weekly_plan(profile)
            self.storage.save_meal_plan(plan)

            print("\n📅 Weekly Meal Plan")
            print("=" * 40)
            print(f"Plan ID: {plan.id}")
            print(f"Period: {plan.start_date} to {plan.end_date}")
            print(f"Avg Daily Calories: ~{int(plan.average_daily_calories)} kcal")
            print()

            for daily in plan.daily_plans:
                day_name = daily.date.strftime("%A")
                print(f"\n📆 {day_name} ({daily.date}):")
                if daily.breakfast:
                    print(f"   🌅 {daily.breakfast.name}")
                if daily.lunch:
                    print(f"   🌞 {daily.lunch.name}")
                if daily.dinner:
                    print(f"   🌙 {daily.dinner.name}")

            print(f"\n✅ Plan saved with ID: {plan.id}")

        elif args.action == "search":
            query = args.query or input("Search for recipes: ")
            results = self.meal_planner.search_recipes(
                query, user=profile, meal_type=args.meal_type, top_k=args.limit
            )

            print(f"\n🔍 Found {len(results)} recipes for '{query}'")
            print("=" * 40)
            for recipe, score in results:
                print(f"\n📖 {recipe.name} (Score: {score:.2f})")
                print(f"   {recipe.description[:80]}...")
                print(f"   Calories: {recipe.nutrition.calories} | Prep: {recipe.total_time_minutes} min")
                print(f"   Tags: {', '.join(recipe.tags[:3])}")

        elif args.action == "suggest":
            meal_type = args.meal_type or "lunch"
            suggestion = self.meal_planner.get_meal_suggestion(profile, meal_type)
            print(f"\n💡 {meal_type.title()} Suggestion:")
            print("=" * 40)
            print(suggestion)

    def cmd_workout(self, args: argparse.Namespace) -> None:
        """Handle workout planning commands."""
        profile = self._get_or_create_profile()

        if args.action == "daily":
            plan = self.workout_planner.generate_daily_plan(
                profile, date.today(), day_number=date.today().weekday()
            )
            print("\n💪 Daily Workout Plan")
            print("=" * 40)
            print(f"Date: {plan.date}")

            if plan.is_rest_day:
                print("\n🛌 Rest Day!")
                print(plan.notes)
            else:
                for workout in plan.workouts:
                    print(f"\n🏋️ {workout.name}")
                    print(f"   Duration: {workout.total_duration_minutes} minutes")
                    print(f"   Type: {workout.workout_type}")
                    print(f"   Difficulty: {workout.difficulty}")
                    print("\n   Exercises:")
                    for ex in workout.exercises:
                        if ex.reps:
                            print(f"   - {ex.name}: {ex.sets}x{ex.reps}")
                        else:
                            print(f"   - {ex.name}: {ex.sets}x{ex.duration_seconds}s")

        elif args.action == "weekly":
            plan = self.workout_planner.generate_weekly_plan(
                profile, workout_days_per_week=args.days or 4
            )
            self.storage.save_workout_plan(plan)

            print("\n📅 Weekly Workout Plan")
            print("=" * 40)
            print(f"Plan ID: {plan.id}")
            print(f"Period: {plan.start_date} to {plan.end_date}")
            print(f"Workout Days: {plan.total_workout_days}")
            print()

            for daily in plan.daily_plans:
                day_name = daily.date.strftime("%A")
                if daily.is_rest_day:
                    print(f"📆 {day_name}: 🛌 Rest Day")
                else:
                    for workout in daily.workouts:
                        print(f"📆 {day_name}: {workout.name} ({workout.duration_minutes} min)")

            est_calories = self.workout_planner.estimate_weekly_calories_burned(
                plan, profile.weight_kg
            )
            print(f"\n🔥 Estimated weekly calorie burn: {est_calories} kcal")
            print(f"✅ Plan saved with ID: {plan.id}")

        elif args.action == "search":
            query = args.query or input("Search for workouts: ")
            results = self.workout_planner.search_workouts(
                query, user=profile, workout_type=args.workout_type, top_k=args.limit
            )

            print(f"\n🔍 Found {len(results)} workouts for '{query}'")
            print("=" * 40)
            for workout, score in results:
                print(f"\n🏋️ {workout.name} (Score: {score:.2f})")
                print(f"   {workout.description[:80]}...")
                print(f"   Duration: {workout.total_duration_minutes} min | Type: {workout.workout_type}")
                print(f"   Equipment: {', '.join(workout.get_all_equipment_needed()) or 'None'}")

        elif args.action == "suggest":
            duration = args.duration or 30
            suggestion = self.workout_planner.get_workout_suggestion(profile, duration)
            print(f"\n💡 Workout Suggestion ({duration} min):")
            print("=" * 40)
            print(suggestion)

    def cmd_shopping(self, args: argparse.Namespace) -> None:
        """Handle shopping list commands."""
        if args.action == "generate":
            # Get the most recent meal plan
            plans = self.storage.list_meal_plans()
            if not plans:
                print("No meal plans found. Generate a meal plan first with 'nutrifit meal weekly'")
                return

            plan_id = args.plan_id or plans[0]["id"]
            meal_plan = self.storage.load_meal_plan(plan_id)

            if not meal_plan:
                print(f"Could not load meal plan: {plan_id}")
                return

            profile = self.storage.load_user_profile()
            pantry = profile.pantry_items if profile else []

            shopping_list = self.shopping_optimizer.generate_from_meal_plan(
                meal_plan, pantry_items=pantry
            )

            if args.optimize:
                shopping_list = self.shopping_optimizer.optimize(
                    shopping_list, prefer_bulk=True
                )

            print(self.shopping_optimizer.format_for_display(shopping_list))

    def cmd_progress(self, args: argparse.Namespace) -> None:
        """Handle progress tracking commands."""
        if args.action == "log":
            entry = ProgressEntry(
                date=date.today(),
                weight_kg=args.weight,
                calories_consumed=args.calories,
                workouts_completed=args.workouts or 0,
                meals_followed=args.meals or 0,
                mood_rating=args.mood,
                energy_rating=args.energy,
                notes=args.notes or "",
            )
            self.storage.add_progress_entry(entry)
            print("✅ Progress logged successfully!")

        elif args.action == "summary":
            summary = self.storage.get_progress_summary()
            if summary:
                print("\n📊 Progress Summary")
                print("=" * 40)
                print(f"Total entries: {summary['total_entries']}")
                if summary['latest_weight']:
                    print(f"Latest weight: {summary['latest_weight']} kg")
                if summary['weight_trend_30d'] is not None:
                    trend = summary['weight_trend_30d']
                    direction = "↓" if trend < 0 else "↑" if trend > 0 else "→"
                    print(f"30-day weight trend: {direction} {abs(trend):.1f} kg")
                if summary['average_calories_7d']:
                    print(f"Avg calories (7d): {int(summary['average_calories_7d'])} kcal")
                print(f"Workout adherence (7d): {summary['workout_adherence_7d']:.0f}%")
            else:
                print("No progress data found. Start logging with 'nutrifit progress log --weight 70'")

        elif args.action == "history":
            tracker = self.storage.load_progress_tracker()
            if tracker and tracker.entries:
                print("\n📈 Progress History")
                print("=" * 40)
                for entry in tracker.entries[-10:]:  # Last 10 entries
                    print(f"\n{entry.date}:")
                    if entry.weight_kg:
                        print(f"  Weight: {entry.weight_kg} kg")
                    if entry.calories_consumed:
                        print(f"  Calories: {entry.calories_consumed}")
                    if entry.workouts_completed:
                        print(f"  Workouts: {entry.workouts_completed}")
            else:
                print("No progress history found.")

    def run(self) -> None:
        """Run the CLI."""
        parser = argparse.ArgumentParser(
            description="NutriFit - AI Nutrition & Workout Assistant",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )
        subparsers = parser.add_subparsers(dest="command", help="Available commands")

        # Profile commands
        profile_parser = subparsers.add_parser("profile", help="Manage user profile")
        profile_parser.add_argument(
            "action",
            choices=["show", "create", "delete", "update-pantry", "update-equipment"],
            help="Profile action",
        )
        profile_parser.add_argument("--items", help="Comma-separated items for update")

        # Meal commands
        meal_parser = subparsers.add_parser("meal", help="Meal planning")
        meal_parser.add_argument(
            "action",
            choices=["daily", "weekly", "search", "suggest"],
            help="Meal action",
        )
        meal_parser.add_argument("--query", help="Search query")
        meal_parser.add_argument("--meal-type", choices=["breakfast", "lunch", "dinner", "snack"])
        meal_parser.add_argument("--limit", type=int, default=5, help="Number of results")

        # Workout commands
        workout_parser = subparsers.add_parser("workout", help="Workout planning")
        workout_parser.add_argument(
            "action",
            choices=["daily", "weekly", "search", "suggest"],
            help="Workout action",
        )
        workout_parser.add_argument("--query", help="Search query")
        workout_parser.add_argument("--workout-type", choices=["strength", "cardio", "hiit", "flexibility"])
        workout_parser.add_argument("--days", type=int, help="Workout days per week")
        workout_parser.add_argument("--duration", type=int, help="Target duration in minutes")
        workout_parser.add_argument("--limit", type=int, default=5, help="Number of results")

        # Shopping commands
        shopping_parser = subparsers.add_parser("shopping", help="Shopping list")
        shopping_parser.add_argument(
            "action", choices=["generate"], help="Shopping action"
        )
        shopping_parser.add_argument("--plan-id", help="Meal plan ID")
        shopping_parser.add_argument("--optimize", action="store_true", help="Optimize list")

        # Progress commands
        progress_parser = subparsers.add_parser("progress", help="Track progress")
        progress_parser.add_argument(
            "action", choices=["log", "summary", "history"], help="Progress action"
        )
        progress_parser.add_argument("--weight", type=float, help="Weight in kg")
        progress_parser.add_argument("--calories", type=int, help="Calories consumed")
        progress_parser.add_argument("--workouts", type=int, help="Workouts completed")
        progress_parser.add_argument("--meals", type=int, help="Meals followed from plan")
        progress_parser.add_argument("--mood", type=int, choices=range(1, 11), help="Mood (1-10)")
        progress_parser.add_argument("--energy", type=int, choices=range(1, 11), help="Energy (1-10)")
        progress_parser.add_argument("--notes", help="Additional notes")

        args = parser.parse_args()

        if not args.command:
            parser.print_help()
            print("\n🏋️ Welcome to NutriFit! Use one of the commands above to get started.")
            print("   Example: nutrifit profile create")
            return

        # Route to appropriate handler
        handlers = {
            "profile": self.cmd_profile,
            "meal": self.cmd_meal,
            "workout": self.cmd_workout,
            "shopping": self.cmd_shopping,
            "progress": self.cmd_progress,
        }

        handler = handlers.get(args.command)
        if handler:
            handler(args)
        else:
            parser.print_help()


def main() -> None:
    """Main entry point."""
    cli = NutriFitCLI()
    cli.run()


if __name__ == "__main__":
    main()
