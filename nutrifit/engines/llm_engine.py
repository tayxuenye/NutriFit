"""Local LLM engine for creative suggestions."""

from pathlib import Path


class LocalLLMEngine:
    """
    Lightweight local LLM engine for generating creative suggestions.

    Supports multiple backends:
    1. llama-cpp-python (for GGUF models)
    2. Template-based fallback (for offline use without models)

    The engine is designed to work completely offline without API keys.
    """

    def __init__(
        self,
        model_path: str | None = None,
        context_size: int = 2048,
        use_fallback: bool = False,
    ):
        """Initialize the LLM engine.

        Args:
            model_path: Path to GGUF model file
            context_size: Context window size for the model
            use_fallback: Force use of template-based fallback
        """
        self.model_path = model_path
        self.context_size = context_size
        self._llm = None
        self._use_fallback = use_fallback

        if not use_fallback:
            self._initialize_llm()

    def _initialize_llm(self) -> None:
        """Initialize the LLM if model is available."""
        if self.model_path and Path(self.model_path).exists():
            try:
                from llama_cpp import Llama

                self._llm = Llama(
                    model_path=self.model_path,
                    n_ctx=self.context_size,
                    n_threads=4,
                    verbose=False,
                )
            except ImportError:
                self._use_fallback = True
            except Exception:
                self._use_fallback = True
        else:
            self._use_fallback = True

    def _template_suggest_meal(
        self,
        dietary_preferences: list[str],
        available_ingredients: list[str],
        meal_type: str,
        calorie_target: int,
    ) -> str:
        """Template-based meal suggestion for fallback mode."""
        prefs = ", ".join(dietary_preferences) if dietary_preferences else "no specific"
        ingredients = ", ".join(available_ingredients[:5]) if available_ingredients else "various"

        suggestions = {
            "breakfast": [
                f"Try a nutritious {prefs} breakfast bowl featuring {ingredients}. "
                "This balanced meal provides sustained energy for your morning.",
                f"A protein-rich {prefs} scramble or smoothie using {ingredients} "
                "would be an excellent choice for starting your day.",
                f"Consider overnight oats or a veggie-packed frittata using {ingredients} "
                "for a filling {prefs} breakfast option.",
            ],
            "lunch": [
                f"A hearty salad or grain bowl with {ingredients} fits your {prefs} "
                "preferences perfectly for a satisfying midday meal.",
                f"Try a {prefs} wrap or sandwich featuring {ingredients} for a "
                "portable and nutritious lunch option.",
                f"A warm soup or stew using {ingredients} would provide comfort and "
                "nutrition while meeting your {prefs} requirements.",
            ],
            "dinner": [
                f"A protein-forward {prefs} main dish with {ingredients} and roasted "
                "vegetables creates a complete and satisfying dinner.",
                f"Consider a {prefs} stir-fry or one-pan meal featuring {ingredients} "
                "for a flavorful evening meal.",
                f"A slow-cooked or baked {prefs} dish with {ingredients} provides "
                "rich flavors and excellent nutrition for dinner.",
            ],
            "snack": [
                f"Energy balls or a trail mix using {ingredients} makes a perfect "
                "{prefs} snack between meals.",
                f"Fresh vegetables with hummus or a small portion of {ingredients} "
                "provides a healthy {prefs} snack option.",
                f"A {prefs} smoothie or Greek yogurt parfait with {ingredients} "
                "offers a nutritious pick-me-up.",
            ],
        }

        import random

        options = suggestions.get(meal_type.lower(), suggestions["lunch"])
        return random.choice(options)

    def _template_suggest_workout(
        self,
        fitness_goals: list[str],
        available_equipment: list[str],
        duration_minutes: int,
        difficulty: str,
    ) -> str:
        """Template-based workout suggestion for fallback mode."""
        goals = ", ".join(fitness_goals) if fitness_goals else "general fitness"
        equipment = ", ".join(available_equipment[:3]) if available_equipment else "bodyweight"

        suggestions = [
            f"For your {goals} goals, try a {duration_minutes}-minute {difficulty} "
            f"workout using {equipment}. Focus on compound movements for maximum efficiency.",
            f"A circuit-style {difficulty} workout targeting {goals} can be achieved in "
            f"{duration_minutes} minutes with {equipment}. Alternate between upper and lower body.",
            f"Consider a progressive {difficulty} routine for {goals} using {equipment}. "
            f"Aim for {duration_minutes} minutes with proper rest intervals.",
            f"An interval-based {difficulty} session focusing on {goals} with {equipment} "
            f"is perfect for your {duration_minutes}-minute time frame.",
        ]

        import random

        return random.choice(suggestions)

    def _template_suggest_modification(
        self,
        original_item: str,
        modification_type: str,
        constraints: list[str],
    ) -> str:
        """Template-based modification suggestion for fallback mode."""
        const = ", ".join(constraints) if constraints else "your preferences"

        if modification_type == "substitute":
            return (
                f"To modify '{original_item}' for {const}, consider swapping key "
                "ingredients with suitable alternatives that maintain nutritional balance."
            )
        elif modification_type == "scale":
            return (
                f"'{original_item}' can be adjusted for {const} by modifying portion "
                "sizes while keeping the same ingredient ratios."
            )
        else:
            return (
                f"'{original_item}' can be adapted for {const} with creative "
                "substitutions that preserve the dish's essence."
            )

    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        stop: list[str] | None = None,
    ) -> str:
        """Generate text based on prompt.

        Args:
            prompt: Input prompt for generation
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop: Stop sequences

        Returns:
            Generated text
        """
        if self._llm is not None and not self._use_fallback:
            try:
                response = self._llm(
                    prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    stop=stop or [],
                )
                return response["choices"][0]["text"].strip()
            except Exception:
                pass

        # Fallback: return a generic response
        return (
            "I'm running in offline mode without a language model. "
            "Please use the specific suggestion methods for meal and workout recommendations."
        )

    def suggest_meal(
        self,
        dietary_preferences: list[str],
        available_ingredients: list[str],
        meal_type: str = "lunch",
        calorie_target: int = 500,
    ) -> str:
        """Generate a meal suggestion.

        Args:
            dietary_preferences: User's dietary preferences
            available_ingredients: Ingredients available
            meal_type: Type of meal (breakfast, lunch, dinner, snack)
            calorie_target: Target calories for the meal

        Returns:
            Meal suggestion text
        """
        if self._llm is not None and not self._use_fallback:
            prompt = f"""You are a helpful nutrition assistant. Suggest a creative {meal_type} recipe.

Dietary Preferences: {', '.join(dietary_preferences) or 'None specified'}
Available Ingredients: {', '.join(available_ingredients[:10]) or 'General pantry items'}
Target Calories: {calorie_target}

Provide a brief, practical suggestion for a {meal_type} that fits these requirements.

Suggestion:"""
            try:
                return self.generate(prompt, max_tokens=200, temperature=0.7)
            except Exception:
                pass

        return self._template_suggest_meal(
            dietary_preferences, available_ingredients, meal_type, calorie_target
        )

    def suggest_workout(
        self,
        fitness_goals: list[str],
        available_equipment: list[str],
        duration_minutes: int = 30,
        difficulty: str = "intermediate",
    ) -> str:
        """Generate a workout suggestion.

        Args:
            fitness_goals: User's fitness goals
            available_equipment: Equipment available
            duration_minutes: Target workout duration
            difficulty: Workout difficulty level

        Returns:
            Workout suggestion text
        """
        if self._llm is not None and not self._use_fallback:
            prompt = f"""You are a helpful fitness coach. Suggest a workout routine.

Fitness Goals: {', '.join(fitness_goals) or 'General fitness'}
Available Equipment: {', '.join(available_equipment[:5]) or 'Bodyweight only'}
Duration: {duration_minutes} minutes
Difficulty: {difficulty}

Provide a brief, practical workout suggestion that fits these requirements.

Suggestion:"""
            try:
                return self.generate(prompt, max_tokens=200, temperature=0.7)
            except Exception:
                pass

        return self._template_suggest_workout(
            fitness_goals, available_equipment, duration_minutes, difficulty
        )

    def suggest_modification(
        self,
        original_item: str,
        modification_type: str = "substitute",
        constraints: list[str] | None = None,
    ) -> str:
        """Generate a modification suggestion for a recipe or workout.

        Args:
            original_item: Name of original recipe/workout
            modification_type: Type of modification (substitute, scale, adapt)
            constraints: List of constraints to consider

        Returns:
            Modification suggestion text
        """
        constraints = constraints or []

        if self._llm is not None and not self._use_fallback:
            prompt = f"""You are a helpful assistant. Suggest how to modify: {original_item}

Modification Type: {modification_type}
Constraints: {', '.join(constraints) or 'None specified'}

Provide a brief, practical suggestion for this modification.

Suggestion:"""
            try:
                return self.generate(prompt, max_tokens=150, temperature=0.7)
            except Exception:
                pass

        return self._template_suggest_modification(
            original_item, modification_type, constraints
        )

    def is_model_loaded(self) -> bool:
        """Check if a language model is loaded."""
        return self._llm is not None and not self._use_fallback

    def get_status(self) -> dict:
        """Get the status of the LLM engine."""
        return {
            "model_loaded": self.is_model_loaded(),
            "model_path": self.model_path,
            "using_fallback": self._use_fallback,
            "context_size": self.context_size,
        }
