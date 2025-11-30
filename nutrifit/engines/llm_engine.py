"""Local LLM engine for creative suggestions."""

import os
import random
import subprocess
import sys
from pathlib import Path


class LocalLLMEngine:
    """
    Lightweight local LLM engine for generating creative suggestions.

    Supports multiple backends:
    1. Hugging Face transformers (GPT-2 by default if installed)
    2. llama-cpp-python (for GGUF models in models/ directory)
    3. Template-based fallback (always available)

    The engine automatically detects and uses available models on startup.
    No configuration required - just install transformers for GPT-2 support.
    """

    def __init__(
        self,
        model_path: str | None = None,
        context_size: int = 2048,
        use_fallback: bool | None = None,
    ):
        """Initialize the LLM engine.

        Args:
            model_path: Path to GGUF model file, or Hugging Face model name (e.g., "gpt2")
                       Auto-discovered if not provided
            context_size: Context window size for the model
            use_fallback: Force use of template-based fallback (None = auto-detect)
        """
        # Auto-discover model path if not provided
        if model_path is None:
            model_path = self._find_model()
        
        self.model_path = model_path
        self.context_size = context_size
        self._llm = None
        self._backend_type = None  # "transformers", "llama_cpp", or None
        self._model_load_error = None
        
        # Auto-detect: use fallback only if explicitly requested or no model path
        if use_fallback is None:
            self._use_fallback = (model_path is None)
        else:
            self._use_fallback = use_fallback

        if not self._use_fallback:
            self._initialize_llm()
        else:
            if model_path is None:
                self._model_load_error = "No model found (install transformers for GPT-2 or place a .gguf file in models/)"
            else:
                self._model_load_error = "Fallback mode explicitly enabled"

    def _find_model(self) -> str | None:
        """Automatically find a model file or use default model name.
        
        Returns:
            Path to model file or model name if found, None otherwise
        """
        # 1. Check models/ directory in project root for GGUF files (highest priority)
        project_root = Path(__file__).parent.parent.parent
        models_dir = project_root / "models"
        if models_dir.exists():
            for model_file in models_dir.glob("*.gguf"):
                return str(model_file)
        
        # 2. Check ~/.nutrifit/models/ directory
        home_models = Path.home() / ".nutrifit" / "models"
        if home_models.exists():
            for model_file in home_models.glob("*.gguf"):
                return str(model_file)
        
        # 3. Check current directory
        current_dir = Path.cwd()
        for model_file in current_dir.glob("*.gguf"):
            return str(model_file)
        
        # 4. Default: Try GPT-2 (auto-install transformers if needed)
        return "gpt2"

    def _initialize_llm(self) -> None:
        """Initialize the LLM if model is available with graceful fallback."""
        self._model_load_error = None
        
        if not self.model_path:
            self._use_fallback = True
            self._model_load_error = "No model path specified"
            return
        
        # Check if it's a file path or a model name
        model_file = Path(self.model_path)
        is_file_path = model_file.exists() and model_file.suffix == ".gguf"
        
        # Try Hugging Face transformers first (for model names like "gpt2")
        if not is_file_path:
            try:
                from transformers import pipeline  # type: ignore[import-untyped]
                
                # Use text generation pipeline
                self._llm = pipeline(
                    "text-generation",
                    model=self.model_path,
                    max_length=self.context_size,
                    device=-1,  # Use CPU (-1) or GPU (0+)
                )
                self._backend_type = "transformers"
                self._model_load_error = None
                return
            except ImportError:
                # transformers not installed - try to install it automatically
                print("Installing transformers library for GPT-2 support...")
                try:
                    subprocess.check_call(
                        [sys.executable, "-m", "pip", "install", "transformers", "torch", "--quiet"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    print("Transformers installed successfully! Loading GPT-2...")
                    # Try again after installation
                    from transformers import pipeline  # type: ignore[import-untyped]
                    
                    self._llm = pipeline(
                        "text-generation",
                        model=self.model_path,
                        max_length=self.context_size,
                        device=-1,
                    )
                    self._backend_type = "transformers"
                    self._model_load_error = None
                    return
                except Exception as install_error:
                    # Installation failed, try GGUF as fallback
                    self._model_load_error = f"Could not install transformers: {str(install_error)}"
                    print(f"Warning: {self._model_load_error}. Falling back to templates.")
            except Exception as e:
                # Model loading failed, try GGUF as fallback
                self._model_load_error = f"Transformers model loading failed: {str(e)}"
        
        # Try GGUF model (llama-cpp-python)
        if is_file_path:
            try:
                from llama_cpp import Llama  # type: ignore[import-untyped]

                self._llm = Llama(
                    model_path=self.model_path,
                    n_ctx=self.context_size,
                    n_threads=4,
                    verbose=False,
                )
                self._backend_type = "llama_cpp"
                self._model_load_error = None
                return
            except ImportError:
                self._use_fallback = True
                self._model_load_error = "Neither transformers nor llama-cpp-python installed"
            except Exception as e:
                self._use_fallback = True
                self._model_load_error = f"Model loading failed: {str(e)}"
        else:
            # Not a file path and transformers failed
            self._use_fallback = True
            if not self._model_load_error:
                self._model_load_error = f"Model '{self.model_path}' not found and transformers not available"

    def _template_suggest_meal(
        self,
        dietary_preferences: list[str],
        available_ingredients: list[str],
        meal_type: str,
        calorie_target: int,
    ) -> str:
        """Template-based meal suggestion for fallback mode with enhanced variety."""
        prefs = ", ".join(dietary_preferences) if dietary_preferences else "no specific"
        ingredients = ", ".join(available_ingredients[:5]) if available_ingredients else "various"
        
        # Add calorie context
        calorie_context = ""
        if calorie_target < 400:
            calorie_context = "light and balanced"
        elif calorie_target < 600:
            calorie_context = "moderately filling"
        else:
            calorie_context = "hearty and substantial"

        suggestions = {
            "breakfast": [
                f"Try a {calorie_context} {prefs} breakfast bowl featuring {ingredients}. "
                "This balanced meal provides sustained energy for your morning.",
                f"A protein-rich {prefs} scramble or smoothie using {ingredients} "
                f"would be an excellent {calorie_context} choice for starting your day.",
                f"Consider overnight oats or a veggie-packed frittata using {ingredients} "
                f"for a {calorie_context} {prefs} breakfast option.",
                f"Start your day with a {calorie_context} {prefs} breakfast featuring {ingredients}. "
                "Perfect for maintaining energy levels throughout the morning.",
                f"A creative {prefs} breakfast using {ingredients} offers both nutrition and flavor. "
                f"This {calorie_context} meal sets a positive tone for your day.",
                f"Fuel your morning with a {calorie_context} {prefs} breakfast incorporating {ingredients}. "
                "Balanced macros ensure steady energy release.",
            ],
            "lunch": [
                f"A {calorie_context} salad or grain bowl with {ingredients} fits your {prefs} "
                "preferences perfectly for a satisfying midday meal.",
                f"Try a {prefs} wrap or sandwich featuring {ingredients} for a "
                f"{calorie_context} and portable lunch option.",
                f"A warm soup or stew using {ingredients} would provide comfort and "
                f"nutrition while meeting your {prefs} requirements. This {calorie_context} meal is ideal for lunch.",
                f"Consider a {calorie_context} {prefs} Buddha bowl with {ingredients}. "
                "This colorful lunch provides diverse nutrients and sustained energy.",
                f"A {prefs} pasta or noodle dish using {ingredients} creates a {calorie_context} "
                "and flavorful midday meal that satisfies.",
                f"Build a {calorie_context} {prefs} plate with {ingredients} as the foundation. "
                "This balanced lunch keeps you energized for the afternoon.",
            ],
            "dinner": [
                f"A {calorie_context} protein-forward {prefs} main dish with {ingredients} and roasted "
                "vegetables creates a complete and satisfying dinner.",
                f"Consider a {prefs} stir-fry or one-pan meal featuring {ingredients} "
                f"for a {calorie_context} and flavorful evening meal.",
                f"A slow-cooked or baked {prefs} dish with {ingredients} provides "
                f"rich flavors and excellent nutrition for a {calorie_context} dinner.",
                f"Create a {calorie_context} {prefs} dinner plate featuring {ingredients} "
                "with complementary sides for a well-rounded evening meal.",
                f"A {prefs} curry or casserole using {ingredients} offers comfort and nutrition "
                f"in a {calorie_context} dinner portion.",
                f"Prepare a {calorie_context} {prefs} sheet pan dinner with {ingredients}. "
                "Simple preparation, maximum flavor and nutrition.",
            ],
            "snack": [
                f"Energy balls or a trail mix using {ingredients} makes a perfect "
                f"{calorie_context} {prefs} snack between meals.",
                f"Fresh vegetables with hummus or a small portion of {ingredients} "
                f"provides a {calorie_context} {prefs} snack option.",
                f"A {prefs} smoothie or Greek yogurt parfait with {ingredients} "
                f"offers a {calorie_context} and nutritious pick-me-up.",
                f"Try a {calorie_context} {prefs} snack plate featuring {ingredients}. "
                "Perfect for maintaining energy between main meals.",
                f"Prepare a {prefs} dip or spread using {ingredients} for a {calorie_context} "
                "snack that's both satisfying and nutritious.",
                f"A {calorie_context} {prefs} snack combining {ingredients} provides "
                "the perfect balance of nutrients to tide you over.",
            ],
        }

        options = suggestions.get(meal_type.lower(), suggestions["lunch"])
        return random.choice(options)

    def _template_suggest_workout(
        self,
        fitness_goals: list[str],
        available_equipment: list[str],
        duration_minutes: int,
        difficulty: str,
    ) -> str:
        """Template-based workout suggestion for fallback mode with enhanced variety."""
        goals = ", ".join(fitness_goals) if fitness_goals else "general fitness"
        equipment = ", ".join(available_equipment[:3]) if available_equipment else "bodyweight"
        
        # Add duration context
        duration_context = ""
        if duration_minutes < 20:
            duration_context = "quick and efficient"
        elif duration_minutes < 45:
            duration_context = "well-balanced"
        else:
            duration_context = "comprehensive"

        suggestions = [
            f"For your {goals} goals, try a {duration_context} {duration_minutes}-minute {difficulty} "
            f"workout using {equipment}. Focus on compound movements for maximum efficiency.",
            f"A circuit-style {difficulty} workout targeting {goals} can be achieved in "
            f"{duration_minutes} minutes with {equipment}. Alternate between upper and lower body for a {duration_context} session.",
            f"Consider a progressive {difficulty} routine for {goals} using {equipment}. "
            f"This {duration_context} {duration_minutes}-minute workout includes proper rest intervals.",
            f"An interval-based {difficulty} session focusing on {goals} with {equipment} "
            f"is perfect for your {duration_minutes}-minute time frame. This {duration_context} approach maximizes results.",
            f"Build a {duration_context} {difficulty} workout for {goals} using {equipment}. "
            f"Structure your {duration_minutes} minutes with warm-up, main sets, and cool-down.",
            f"Try a {difficulty} HIIT-style workout targeting {goals} with {equipment}. "
            f"This {duration_context} {duration_minutes}-minute session alternates intensity for optimal results.",
            f"Design a {duration_context} {difficulty} strength routine for {goals} using {equipment}. "
            f"Your {duration_minutes}-minute workout should focus on progressive overload.",
            f"A {difficulty} functional fitness workout for {goals} with {equipment} provides "
            f"a {duration_context} {duration_minutes}-minute session that builds real-world strength.",
            f"Create a {duration_context} {difficulty} workout targeting {goals} using {equipment}. "
            f"This {duration_minutes}-minute routine balances intensity with recovery.",
            f"For {goals}, implement a {difficulty} training split using {equipment}. "
            f"This {duration_context} {duration_minutes}-minute approach ensures balanced development.",
        ]

        return random.choice(suggestions)

    def _template_suggest_modification(
        self,
        original_item: str,
        modification_type: str,
        constraints: list[str],
    ) -> str:
        """Template-based modification suggestion for fallback mode with enhanced variety."""
        const = ", ".join(constraints) if constraints else "your preferences"

        if modification_type == "substitute":
            suggestions = [
                f"To modify '{original_item}' for {const}, consider swapping key "
                "ingredients with suitable alternatives that maintain nutritional balance.",
                f"Adapt '{original_item}' to meet {const} by replacing incompatible ingredients "
                "with similar alternatives that preserve flavor and texture.",
                f"Transform '{original_item}' for {const} by identifying substitutable ingredients "
                "and selecting appropriate replacements that maintain the dish's character.",
                f"Customize '{original_item}' for {const} through strategic ingredient substitutions "
                "that honor both the original recipe and your requirements.",
            ]
        elif modification_type == "scale":
            suggestions = [
                f"'{original_item}' can be adjusted for {const} by modifying portion "
                "sizes while keeping the same ingredient ratios.",
                f"Scale '{original_item}' to fit {const} by proportionally adjusting all ingredients "
                "while maintaining the recipe's balance.",
                f"Resize '{original_item}' for {const} by calculating new quantities "
                "that preserve the original proportions and flavors.",
                f"Adapt the serving size of '{original_item}' for {const} by scaling ingredients "
                "uniformly to achieve your desired portion.",
            ]
        else:
            suggestions = [
                f"'{original_item}' can be adapted for {const} with creative "
                "substitutions that preserve the dish's essence.",
                f"Modify '{original_item}' to accommodate {const} through thoughtful adjustments "
                "that maintain the core appeal of the original.",
                f"Customize '{original_item}' for {const} by making strategic changes "
                "that respect both the recipe's foundation and your needs.",
                f"Transform '{original_item}' to suit {const} with modifications "
                "that enhance rather than compromise the dish.",
            ]
        
        return random.choice(suggestions)

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
                if self._backend_type == "transformers":
                    # Hugging Face transformers pipeline
                    pad_token_id = None
                    if hasattr(self._llm, "tokenizer") and self._llm.tokenizer is not None:
                        pad_token_id = getattr(self._llm.tokenizer, "eos_token_id", None)
                    
                    result = self._llm(
                        prompt,
                        max_length=len(prompt.split()) + max_tokens,
                        temperature=temperature,
                        do_sample=True,
                        num_return_sequences=1,
                        pad_token_id=pad_token_id,
                    )
                    if isinstance(result, list) and len(result) > 0:
                        generated_text = result[0].get("generated_text", "")
                        # Remove the prompt from the response
                        if generated_text.startswith(prompt):
                            generated_text = generated_text[len(prompt):].strip()
                        return generated_text
                elif self._backend_type == "llama_cpp":
                    # llama-cpp-python
                    response = self._llm(
                        prompt,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        stop=stop or [],
                    )
                    if isinstance(response, dict) and "choices" in response:
                        choices = response["choices"]
                        if isinstance(choices, list) and len(choices) > 0:
                            return choices[0].get("text", "").strip()
            except Exception as e:
                # If generation fails, fall through to template
                print(f"LLM generation error: {e}")

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
        """Get the status of the LLM engine with detailed information.
        
        Returns:
            Dictionary containing:
                - model_loaded: Whether a model is successfully loaded
                - model_path: Path to the model file (if specified)
                - using_fallback: Whether fallback mode is active
                - context_size: Context window size
                - model_load_error: Error message if model loading failed (None if successful)
                - backend: Which backend is being used ('llama-cpp' or 'template-fallback')
        """
        if self._use_fallback:
            backend = "template-fallback"
        elif self._backend_type:
            backend = self._backend_type
        else:
            backend = "unknown"
        
        return {
            "model_loaded": self.is_model_loaded(),
            "model_path": self.model_path,
            "using_fallback": self._use_fallback,
            "context_size": self.context_size,
            "model_load_error": self._model_load_error,
            "backend": backend,
        }
