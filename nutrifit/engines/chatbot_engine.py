"""AI Chatbot engine for conversational meal and workout planning."""

import json
import re
from datetime import date
from typing import Any

from nutrifit.engines.llm_engine import LocalLLMEngine
from nutrifit.engines.meal_planner import MealPlannerEngine
from nutrifit.engines.workout_planner import WorkoutPlannerEngine
from nutrifit.models.plan import MealPlan, WorkoutPlan
from nutrifit.models.user import DietaryPreference, FitnessGoal, UserProfile

# Try to import better LLM engines
try:
    from nutrifit.engines.openai_engine import OpenAIEngine
except ImportError:
    OpenAIEngine = None

try:
    from nutrifit.engines.ollama_engine import OllamaEngine
except ImportError:
    OllamaEngine = None


class ChatbotEngine:
    """
    Conversational AI chatbot for personalized nutrition and workout planning.
    
    Allows users to interact naturally to create and modify meal plans and workouts.
    """

    def __init__(
        self,
        llm_engine: Any = None,
        meal_planner: MealPlannerEngine | None = None,
        workout_planner: WorkoutPlannerEngine | None = None,
        use_openai: bool = False,
        use_ollama: bool = True,
        ollama_model: str = "llama3.2",
        use_llm_generation: bool = True,
    ):
        """Initialize the chatbot engine.

        Args:
            llm_engine: LLM engine for generating responses (auto-detected if None)
            meal_planner: Meal planner engine for generating meal plans
            workout_planner: Workout planner engine for generating workouts
            use_openai: Try to use OpenAI API (requires OPENAI_API_KEY env var)
            use_ollama: Try to use Ollama (default: True)
            ollama_model: Ollama model to use (default: llama3.2)
            use_llm_generation: Use LLM for plan generation (default: True)
        """
        # Auto-detect best available LLM engine
        if llm_engine is None:
            llm_engine = self._auto_detect_llm(use_openai, use_ollama, ollama_model)
        
        self.llm_engine = llm_engine
        self.meal_planner = meal_planner
        self.workout_planner = workout_planner
        self.use_llm_generation = use_llm_generation
        
        # Conversation state
        self.conversation_history: list[dict[str, str]] = []
        self.current_context: dict[str, Any] = {}
        self.user_profile: UserProfile | None = None
    
    def _auto_detect_llm(self, use_openai: bool, use_ollama: bool, ollama_model: str) -> Any:
        """Auto-detect the best available LLM engine.
        
        Priority:
        1. Ollama (if available and enabled)
        2. OpenAI (if API key set and enabled)
        3. LocalLLMEngine (GPT-2 or templates)
        """
        # Try Ollama first (best for offline, modern models)
        if use_ollama and OllamaEngine:
            try:
                ollama = OllamaEngine(model=ollama_model)
                if ollama.is_available():
                    print(f"✅ Using Ollama with {ollama_model}")
                    return ollama
            except Exception as e:
                print(f"⚠️ Ollama not available: {e}")
        
        # Try OpenAI (best quality, requires internet)
        if use_openai and OpenAIEngine:
            try:
                openai = OpenAIEngine()
                if openai.is_available():
                    print(f"✅ Using OpenAI API with {openai.model}")
                    return openai
            except Exception as e:
                print(f"⚠️ OpenAI not available: {e}")
        
        # Fall back to LocalLLMEngine (GPT-2 or templates)
        print("⚠️ Using LocalLLMEngine (GPT-2 or templates) - Consider installing Ollama for better responses")
        return LocalLLMEngine()
    
    def _generate_with_retry(self, operation, operation_name: str, max_retries: int = 2):
        """Execute an operation with retry logic for transient failures.
        
        Args:
            operation: Callable that performs the operation
            operation_name: Name of the operation for logging
            max_retries: Maximum number of retry attempts
            
        Returns:
            Result of the operation
            
        Raises:
            Exception: If all retries fail
        """
        import time
        
        last_exception = None
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    # Wait before retry (exponential backoff)
                    wait_time = 2 ** attempt
                    print(f"[CHATBOT] Retrying {operation_name} (attempt {attempt + 1}/{max_retries + 1}) after {wait_time}s...")
                    time.sleep(wait_time)
                
                result = operation()
                
                if attempt > 0:
                    print(f"[CHATBOT] {operation_name} succeeded on retry {attempt}")
                
                return result
                
            except Exception as e:
                last_exception = e
                error_msg = str(e)
                
                # Check if this is a transient error that should be retried
                is_transient = any(keyword in error_msg.lower() for keyword in [
                    'timeout', 'connection', 'network', 'temporary', 'unavailable', 'loading'
                ])
                
                if attempt < max_retries and is_transient:
                    print(f"[CHATBOT] {operation_name} failed with transient error: {error_msg}")
                    continue
                else:
                    # Non-transient error or max retries reached
                    if attempt >= max_retries:
                        print(f"[CHATBOT] {operation_name} failed after {max_retries + 1} attempts")
                    raise
        
        # Should never reach here, but just in case
        raise last_exception if last_exception else Exception(f"{operation_name} failed")

    def chat(self, user_message: str, user_profile: UserProfile | None = None) -> dict[str, Any]:
        """
        Process a user message and generate a response.

        Args:
            user_message: The user's message
            user_profile: Optional user profile for personalization

        Returns:
            Dict with response text and optional metadata:
            {
                "response": str,
                "plan_id": str (optional),
                "plan_type": str (optional, "meal" or "workout"),
                "has_plan": bool
            }
        """
        # Update user profile if provided
        if user_profile:
            self.user_profile = user_profile

        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Detect intent
        intent = self._detect_intent(user_message)

        # Generate response based on intent
        if intent == "meal_plan_request":
            response = self._handle_meal_plan_request(user_message)
        elif intent == "workout_plan_request":
            response = self._handle_workout_plan_request(user_message)
        elif intent == "show_full_plan":
            response = self._handle_show_full_plan(user_message)
        elif intent == "modify_meal":
            response = self._handle_meal_modification(user_message)
        elif intent == "modify_workout":
            response = self._handle_workout_modification(user_message)
        elif intent == "nutrition_question":
            response = self._handle_nutrition_question(user_message)
        elif intent == "workout_question":
            response = self._handle_workout_question(user_message)
        elif intent == "profile_update":
            response = self._handle_profile_update(user_message)
        else:
            response = self._generate_general_response(user_message)

        # Add to conversation history (store the text content)
        response_text = response.get("response", "") if isinstance(response, dict) else str(response)
        self.conversation_history.append({"role": "assistant", "content": response_text})

        return response

    def _extract_calorie_target(self, message: str) -> int | None:
        """Extract calorie target from user message.
        
        Handles formats like:
        - "2000 calories"
        - "2k calories"
        - "calorie target is 2000"
        - "target of 2000 kcal"
        """
        message_lower = message.lower()
        
        # Pattern 1: Look for "Xk" format (e.g., "2k", "1.5k")
        import re
        k_pattern = r'(\d+\.?\d*)\s*k\b'
        k_match = re.search(k_pattern, message_lower)
        if k_match:
            value = float(k_match.group(1))
            return int(value * 1000)
        
        # Pattern 2: Look for explicit numbers with calorie keywords
        calorie_keywords = ['calorie', 'kcal', 'cal']
        number_pattern = r'(\d{3,4})\s*(?:' + '|'.join(calorie_keywords) + ')'
        number_match = re.search(number_pattern, message_lower)
        if number_match:
            return int(number_match.group(1))
        
        # Pattern 3: Look for "target is/of X" format
        target_pattern = r'target\s+(?:is|of)\s+(\d{3,4})'
        target_match = re.search(target_pattern, message_lower)
        if target_match:
            return int(target_match.group(1))
        
        return None

    def _extract_macro_targets(self, message: str) -> dict[str, int] | None:
        """Extract macro-nutrient targets from user message.
        
        Handles formats like:
        - "protein 130g"
        - "carbs 30g"
        - "fat 100g"
        - "protein target is 130g"
        """
        import re
        message_lower = message.lower()
        macros = {}
        
        # Pattern for protein
        protein_pattern = r'protein\s+(?:target\s+(?:is|of)\s+)?(\d+)\s*g'
        protein_match = re.search(protein_pattern, message_lower)
        if protein_match:
            macros['protein_g'] = int(protein_match.group(1))
        
        # Pattern for carbs/carbohydrates
        carbs_pattern = r'carb(?:s|ohydrate)?(?:s)?\s+(?:target\s+(?:is|of)\s+)?(\d+)\s*g'
        carbs_match = re.search(carbs_pattern, message_lower)
        if carbs_match:
            macros['carbs_g'] = int(carbs_match.group(1))
        
        # Pattern for fat
        fat_pattern = r'fat\s+(?:target\s+(?:is|of)\s+)?(\d+)\s*g'
        fat_match = re.search(fat_pattern, message_lower)
        if fat_match:
            macros['fat_g'] = int(fat_match.group(1))
        
        return macros if macros else None

    def _detect_intent(self, message: str) -> str:
        """Detect the user's intent from their message."""
        message_lower = message.lower()

        # Show full plan (when user has a plan in context)
        if any(kw in message_lower for kw in ["show", "see", "view", "display"]):
            if any(kw in message_lower for kw in ["full", "complete", "entire", "whole", "all"]):
                if any(kw in message_lower for kw in ["plan", "meal", "workout"]):
                    # If they have a plan in context, show it
                    if "meal_plan" in self.current_context or "workout_plan" in self.current_context:
                        return "show_full_plan"
                    # Otherwise, treat as a request to create a plan
                    # Fall through to meal/workout plan request detection
        
        # Also detect simple affirmative responses after showing preview
        if message_lower in ["yes", "yeah", "yep", "sure", "ok", "okay", "show me", "yes please"]:
            if "meal_plan" in self.current_context or "workout_plan" in self.current_context:
                return "show_full_plan"

        # Meal plan requests
        meal_keywords = ["meal plan", "meal", "food", "recipe", "eat", "breakfast", "lunch", "dinner"]
        if any(kw in message_lower for kw in ["create", "generate", "make", "plan"]):
            if any(kw in message_lower for kw in meal_keywords):
                return "meal_plan_request"

        # Workout plan requests
        workout_keywords = ["workout", "exercise", "training", "fitness", "gym"]
        if any(kw in message_lower for kw in ["create", "generate", "make", "plan"]):
            if any(kw in message_lower for kw in workout_keywords):
                return "workout_plan_request"

        # Modifications
        if any(kw in message_lower for kw in ["change", "modify", "replace", "swap", "different"]):
            if any(kw in message_lower for kw in meal_keywords):
                return "modify_meal"
            if any(kw in message_lower for kw in workout_keywords):
                return "modify_workout"

        # Questions
        if any(kw in message_lower for kw in ["what", "how", "why", "when", "should", "?"]):
            if any(kw in message_lower for kw in ["calorie", "protein", "carb", "fat", "nutrition", "diet"]):
                return "nutrition_question"
            if any(kw in message_lower for kw in workout_keywords):
                return "workout_question"

        # Profile updates
        if any(kw in message_lower for kw in ["i am", "i'm", "my goal", "i want", "i need", "allergic"]):
            return "profile_update"

        return "general"

    def _handle_meal_plan_request(self, message: str) -> dict[str, Any]:
        """Handle meal plan generation requests.
        
        Returns:
            Dict with response and optional plan metadata
        """
        if not self.user_profile:
            return {
                "response": (
                    "I'd love to create a meal plan for you! First, I need to know a bit about you. "
                    "Could you tell me:\n"
                    "- Your dietary preferences (e.g., vegan, keto, high-protein)\n"
                    "- Your fitness goals (e.g., weight loss, muscle gain)\n"
                    "- Any allergies or foods to avoid\n"
                    "- What ingredients you have available\n\n"
                    "**Example:** 'I'm vegan, want to lose weight, allergic to nuts, and have basic pantry items'"
                ),
                "has_plan": False
            }

        # Extract calorie target from message if specified
        calorie_target = self._extract_calorie_target(message)
        if calorie_target:
            self.user_profile.daily_calorie_target = calorie_target
        
        # Extract macro targets from message if specified
        macro_targets = self._extract_macro_targets(message)
        if macro_targets:
            # Store custom macro targets in user profile
            # We'll need to override the calculated macros
            if not hasattr(self.user_profile, '_custom_macros'):
                self.user_profile._custom_macros = {}
            self.user_profile._custom_macros.update(macro_targets)
        
        # Check if request is ambiguous and ask clarifying questions (Requirement 10.3)
        if not calorie_target and not macro_targets:
            # Request is vague, ask for specifics
            return {
                "response": (
                    "I can create a meal plan for you! To make it perfect, could you specify:\n\n"
                    "**Calorie Target:** How many calories per day? (e.g., '2000 calories')\n"
                    "**Macro Targets (optional):** Protein, carbs, fat goals? (e.g., '150g protein, 50g carbs, 100g fat')\n"
                    "**Duration:** How many days? (default is 7 days)\n\n"
                    "**Example:** 'Create a 2000 calorie meal plan with 150g protein for 7 days'\n\n"
                    "Or I can use your profile defaults if you'd like to proceed without specifying!"
                ),
                "has_plan": False
            }

        # Extract duration from message
        duration_days = 7  # Default to weekly
        if any(word in message.lower() for word in ["daily", "today", "one day"]):
            duration_days = 1

        # Use LLM generation if enabled
        if self.use_llm_generation:
            try:
                # Prepare requirements dict
                requirements = {
                    'calorie_target': self.user_profile.daily_calorie_target,
                    'duration': duration_days
                }
                
                # Add macro targets if specified
                if hasattr(self.user_profile, '_custom_macros') and self.user_profile._custom_macros:
                    macros = self.user_profile.calculate_macro_grams()
                    macros.update(self.user_profile._custom_macros)
                    requirements['macro_targets'] = macros
                else:
                    requirements['macro_targets'] = self.user_profile.calculate_macro_grams()
                
                # Generate meal plan using LLM with retry logic (Requirement 9.4)
                llm_plan_text = self._generate_with_retry(
                    lambda: self.generate_llm_meal_plan(
                        user_profile=self.user_profile,
                        requirements=requirements
                    ),
                    operation_name="meal plan generation",
                    max_retries=2
                )
                
                # Store the generated plan
                plan_id = self.store_generated_plan(
                    plan_text=llm_plan_text,
                    plan_type='meal'
                )
                
                # Create response with plan and metadata (Requirement 10.4)
                response_text = f"Great! I've created a {duration_days}-day meal plan for you!\n\n"
                response_text += llm_plan_text
                response_text += "\n\n**💡 What's Next?**\n"
                response_text += "- **Save it:** Click the 'Save to Meal Plans' button below\n"
                response_text += "- **Modify it:** Ask me to change specific parts (e.g., 'Change Day 2 breakfast to something vegan')\n"
                response_text += "- **Regenerate:** Ask me to create a new version with different meals\n"
                response_text += "- **Adjust targets:** Request different calorie or macro targets"
                
                return {
                    "response": response_text,
                    "plan_id": plan_id,
                    "plan_type": "meal",
                    "has_plan": True
                }
                
            except Exception as e:
                # Log error for debugging (Requirement 9.4)
                import traceback
                error_trace = traceback.format_exc()
                print(f"[CHATBOT ERROR] LLM meal plan generation failed after retries: {e}")
                print(f"[CHATBOT ERROR] Traceback: {error_trace}")
                
                # Fall back to structured generation if LLM fails (Requirement 9.2)
                print(f"[CHATBOT] Falling back to structured generation")
                # Continue to structured generation below

        # Structured generation (original behavior or fallback)
        if not self.meal_planner:
            return {
                "response": (
                    "I understand you want a meal plan! Based on your profile:\n"
                    f"- Dietary preferences: {', '.join(p.value for p in self.user_profile.dietary_preferences) or 'None'}\n"
                    f"- Fitness goals: {', '.join(g.value for g in self.user_profile.fitness_goals) or 'None'}\n"
                    f"- Daily calorie target: {self.user_profile.daily_calorie_target} calories\n\n"
                    "I can create a personalized meal plan for you. Would you like a daily or weekly plan?"
                ),
                "has_plan": False
            }

        # Check if user wants to see the full/complete plan
        show_full_plan = any(word in message.lower() for word in ["full", "complete", "entire", "whole", "all", "show me"])

        # Generate meal plan using structured planner
        try:
            meal_plan = self.meal_planner.generate_weekly_plan(
                self.user_profile,
                start_date=date.today(),
            )
            self.current_context["meal_plan"] = meal_plan

            # Create response
            response = f"Great! I've created a {duration_days}-day meal plan for you!\n\n"
            response += f"📊 **Your Daily Targets:**\n"
            response += f"- Calories: {self.user_profile.daily_calorie_target} kcal\n"
            
            # Use custom macros if specified, otherwise calculate
            if hasattr(self.user_profile, '_custom_macros') and self.user_profile._custom_macros:
                macros = self.user_profile.calculate_macro_grams()
                # Override with custom values
                macros.update(self.user_profile._custom_macros)
            else:
                macros = self.user_profile.calculate_macro_grams()
            
            response += f"- Protein: {macros['protein_g']:.0f}g\n"
            response += f"- Carbs: {macros['carbs_g']:.0f}g\n"
            response += f"- Fat: {macros['fat_g']:.0f}g\n\n"

            # Show full plan or just preview
            if show_full_plan and meal_plan.daily_plans:
                # Show all days
                response += "**📅 Your Complete Weekly Meal Plan:**\n\n"
                for i, day_plan in enumerate(meal_plan.daily_plans, 1):
                    response += f"**Day {i} ({day_plan.date}):**\n"
                    if day_plan.breakfast:
                        response += f"  🍳 Breakfast: {day_plan.breakfast.name} ({day_plan.breakfast.nutrition.calories} kcal)\n"
                    if day_plan.lunch:
                        response += f"  🥗 Lunch: {day_plan.lunch.name} ({day_plan.lunch.nutrition.calories} kcal)\n"
                    if day_plan.dinner:
                        response += f"  🍽️ Dinner: {day_plan.dinner.name} ({day_plan.dinner.nutrition.calories} kcal)\n"
                    if day_plan.snacks:
                        for snack in day_plan.snacks:
                            response += f"  🍎 Snack: {snack.name} ({snack.nutrition.calories} kcal)\n"
                    response += f"  📊 Daily Total: {day_plan.total_calories} kcal\n\n"
                
                response += "Would you like me to change anything or generate a shopping list?"
            else:
                # Show first day as preview
                if meal_plan.daily_plans:
                    day1 = meal_plan.daily_plans[0]
                    response += f"**Day 1 Preview ({day1.date}):**\n"
                    if day1.breakfast:
                        response += f"🍳 Breakfast: {day1.breakfast.name} ({day1.breakfast.nutrition.calories} kcal)\n"
                    if day1.lunch:
                        response += f"🥗 Lunch: {day1.lunch.name} ({day1.lunch.nutrition.calories} kcal)\n"
                    if day1.dinner:
                        response += f"🍽️ Dinner: {day1.dinner.name} ({day1.dinner.nutrition.calories} kcal)\n"
                    response += f"\nTotal: {day1.total_calories} kcal\n\n"

                response += "Would you like to see the full plan, or would you like me to change anything?"
            
            return {
                "response": response,
                "has_plan": True
            }

        except Exception as e:
            return {
                "response": f"I encountered an issue creating your meal plan: {str(e)}. Could you provide more details about your preferences?",
                "has_plan": False
            }

    def _handle_show_full_plan(self, message: str) -> dict[str, Any]:
        """Handle requests to show the full meal or workout plan.
        
        Returns:
            Dict with response and optional plan metadata
        """
        message_lower = message.lower()
        
        # Check if they want to see meal plan
        if "meal_plan" in self.current_context and any(kw in message_lower for kw in ["meal", "food", "eat", "yes", "ok", "sure"]):
            meal_plan = self.current_context["meal_plan"]
            
            response = "**📅 Your Complete Weekly Meal Plan:**\n\n"
            response += f"📊 **Daily Targets:** {self.user_profile.daily_calorie_target} kcal\n\n"
            
            for i, day_plan in enumerate(meal_plan.daily_plans, 1):
                response += f"**Day {i} ({day_plan.date}):**\n"
                if day_plan.breakfast:
                    response += f"  🍳 Breakfast: {day_plan.breakfast.name} ({day_plan.breakfast.nutrition.calories} kcal)\n"
                if day_plan.lunch:
                    response += f"  🥗 Lunch: {day_plan.lunch.name} ({day_plan.lunch.nutrition.calories} kcal)\n"
                if day_plan.dinner:
                    response += f"  🍽️ Dinner: {day_plan.dinner.name} ({day_plan.dinner.nutrition.calories} kcal)\n"
                if day_plan.snacks:
                    for snack in day_plan.snacks:
                        response += f"  🍎 Snack: {snack.name} ({snack.nutrition.calories} kcal)\n"
                response += f"  📊 Daily Total: {day_plan.total_calories} kcal\n\n"
            
            response += "Would you like me to change anything or generate a shopping list?"
            return {
                "response": response,
                "has_plan": True
            }
        
        # Check if they want to see workout plan
        if "workout_plan" in self.current_context and any(kw in message_lower for kw in ["workout", "exercise", "training", "yes", "ok", "sure"]):
            workout_plan = self.current_context["workout_plan"]
            
            response = "**📅 Your Complete Weekly Workout Plan:**\n\n"
            
            for i, day_plan in enumerate(workout_plan.daily_plans, 1):
                day_name = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][i-1]
                response += f"**{day_name} (Day {i}):**\n"
                
                if day_plan.is_rest_day:
                    response += "  😴 Rest Day - Recovery and stretching\n\n"
                elif day_plan.workouts:
                    for workout in day_plan.workouts:
                        response += f"  💪 {workout.name}\n"
                        response += f"     Duration: {workout.total_duration_minutes} minutes\n"
                        response += f"     Type: {workout.workout_type}\n"
                        if workout.exercises:
                            response += f"     Exercises: {len(workout.exercises)} exercises\n"
                    response += "\n"
            
            response += "Would you like details on any specific day?"
            return {
                "response": response,
                "has_plan": True
            }
        
        # No plan in context
        return {
            "response": "I don't have a current plan to show you. Would you like me to create a meal plan or workout plan?",
            "has_plan": False
        }

    def _handle_workout_plan_request(self, message: str) -> dict[str, Any]:
        """Handle workout plan generation requests.
        
        Returns:
            Dict with response and optional plan metadata
        """
        if not self.user_profile:
            return {
                "response": (
                    "I'd love to create a workout plan for you! First, tell me:\n"
                    "- Your fitness goals (e.g., weight loss, muscle gain, endurance)\n"
                    "- Your fitness level (beginner, intermediate, advanced)\n"
                    "- Available equipment (e.g., dumbbells, resistance bands, bodyweight only)\n"
                    "- How many days per week you want to work out\n\n"
                    "**Example:** 'I'm a beginner, want to build muscle, have dumbbells, and can work out 4 days a week'"
                ),
                "has_plan": False
            }

        # Extract workout days from message
        workout_days = None
        numbers = re.findall(r'\d+', message)
        if numbers:
            workout_days = min(int(numbers[0]), 7)
        
        # Extract duration from message
        duration = None
        duration_match = re.search(r'(\d+)\s*(?:minute|min)', message.lower())
        if duration_match:
            duration = int(duration_match.group(1))
        
        # Extract fitness level from message
        fitness_level = None
        if 'beginner' in message.lower():
            fitness_level = 'beginner'
        elif 'advanced' in message.lower():
            fitness_level = 'advanced'
        elif 'intermediate' in message.lower():
            fitness_level = 'intermediate'
        
        # Extract focus areas from message
        focus_areas = []
        focus_keywords = {
            'upper body': ['upper body', 'arms', 'chest', 'back', 'shoulders'],
            'lower body': ['lower body', 'legs', 'glutes', 'quads', 'hamstrings'],
            'cardio': ['cardio', 'running', 'endurance', 'aerobic'],
            'core': ['core', 'abs', 'abdominal'],
            'full body': ['full body', 'total body']
        }
        for focus, keywords in focus_keywords.items():
            if any(kw in message.lower() for kw in keywords):
                focus_areas.append(focus)
        
        # Check if request is ambiguous and ask clarifying questions (Requirement 10.3)
        if not workout_days or not fitness_level:
            # Request is vague, ask for specifics
            missing_info = []
            if not workout_days:
                missing_info.append("**Workout Days:** How many days per week? (e.g., '4 days')")
            if not fitness_level:
                missing_info.append("**Fitness Level:** Beginner, intermediate, or advanced?")
            if not duration:
                missing_info.append("**Duration (optional):** How long per session? (e.g., '45 minutes')")
            if not focus_areas:
                missing_info.append("**Focus (optional):** Any specific areas? (e.g., 'upper body', 'cardio')")
            
            return {
                "response": (
                    "I can create a workout plan for you! To make it perfect, could you specify:\n\n"
                    + "\n".join(missing_info) +
                    "\n\n**Example:** 'Create a 4-day intermediate workout plan for upper body, 45 minutes per session'\n\n"
                    "Or I can use reasonable defaults if you'd like to proceed!"
                ),
                "has_plan": False
            }
        
        # Set defaults for optional parameters
        if not duration:
            duration = 45  # Default duration in minutes
        if not fitness_level:
            fitness_level = 'intermediate'  # Default
        if not workout_days:
            workout_days = 4  # Default

        # Use LLM generation if enabled
        if self.use_llm_generation:
            try:
                # Prepare requirements dict
                requirements = {
                    'workout_days': workout_days,
                    'duration': duration,
                    'focus_areas': focus_areas,
                    'fitness_level': fitness_level
                }
                
                # Generate workout plan using LLM with retry logic (Requirement 9.4)
                llm_plan_text = self._generate_with_retry(
                    lambda: self.generate_llm_workout_plan(
                        user_profile=self.user_profile,
                        requirements=requirements
                    ),
                    operation_name="workout plan generation",
                    max_retries=2
                )
                
                # Store the generated plan
                plan_id = self.store_generated_plan(
                    plan_text=llm_plan_text,
                    plan_type='workout'
                )
                
                # Create response with plan and metadata (Requirement 10.4)
                response_text = f"Perfect! I've created a {workout_days}-day per week workout plan for you!\n\n"
                response_text += llm_plan_text
                response_text += "\n\n**💡 What's Next?**\n"
                response_text += "- **Save it:** Click the 'Save to Workout Plans' button below\n"
                response_text += "- **Modify it:** Ask me to change specific days (e.g., 'Replace Monday with a cardio workout')\n"
                response_text += "- **Regenerate:** Ask me to create a new version with different exercises\n"
                response_text += "- **Adjust intensity:** Request easier or harder workouts"
                
                return {
                    "response": response_text,
                    "plan_id": plan_id,
                    "plan_type": "workout",
                    "has_plan": True
                }
                
            except Exception as e:
                # Log error for debugging (Requirement 9.4)
                import traceback
                error_trace = traceback.format_exc()
                print(f"[CHATBOT ERROR] LLM workout plan generation failed after retries: {e}")
                print(f"[CHATBOT ERROR] Traceback: {error_trace}")
                
                # Fall back to structured generation if LLM fails (Requirement 9.2)
                print(f"[CHATBOT] Falling back to structured generation")
                # Continue to structured generation below

        # Structured generation (original behavior or fallback)
        if not self.workout_planner:
            return {
                "response": (
                    "I understand you want a workout plan! Based on your profile:\n"
                    f"- Fitness goals: {', '.join(g.value for g in self.user_profile.fitness_goals) or 'None'}\n"
                    f"- Available equipment: {', '.join(self.user_profile.available_equipment) or 'Bodyweight only'}\n\n"
                    "I can create a personalized workout plan for you. How many days per week would you like to train?"
                ),
                "has_plan": False
            }

        # Generate workout plan using structured planner
        try:
            workout_plan = self.workout_planner.generate_weekly_plan(
                self.user_profile,
                start_date=date.today(),
                workout_days_per_week=workout_days,
            )
            self.current_context["workout_plan"] = workout_plan

            # Create response
            response = f"Perfect! I've created a {workout_days}-day per week workout plan for you!\n\n"
            response += f"🎯 **Your Goals:** {', '.join(g.value for g in self.user_profile.fitness_goals)}\n"
            response += f"🏋️ **Equipment:** {', '.join(self.user_profile.available_equipment) or 'Bodyweight only'}\n\n"

            # Show weekly overview
            response += "**Weekly Schedule:**\n"
            for i, day_plan in enumerate(workout_plan.daily_plans):
                day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i]
                if day_plan.is_rest_day:
                    response += f"{day_name}: 😴 Rest Day\n"
                elif day_plan.workouts:
                    workout = day_plan.workouts[0]
                    response += f"{day_name}: 💪 {workout.name} ({workout.total_duration_minutes} min)\n"

            response += "\nWould you like details on any specific day, or would you like me to adjust anything?"
            return {
                "response": response,
                "has_plan": True
            }

        except Exception as e:
            return {
                "response": f"I encountered an issue creating your workout plan: {str(e)}. Could you provide more details?",
                "has_plan": False
            }

    def _handle_meal_modification(self, message: str) -> dict[str, Any]:
        """Handle requests to modify meals.
        
        Returns:
            Dict with response and optional plan metadata
        """
        if "meal_plan" not in self.current_context:
            return {
                "response": "I don't have a current meal plan to modify. Would you like me to create one first?",
                "has_plan": False
            }

        # Extract what to change
        message_lower = message.lower()
        
        # Detect meal type
        meal_type = None
        if "breakfast" in message_lower:
            meal_type = "breakfast"
        elif "lunch" in message_lower:
            meal_type = "lunch"
        elif "dinner" in message_lower:
            meal_type = "dinner"

        if not meal_type:
            return {
                "response": "Which meal would you like to change? (breakfast, lunch, or dinner)",
                "has_plan": False
            }

        # Generate suggestion using LLM
        if self.user_profile:
            dietary_prefs = [p.value for p in self.user_profile.dietary_preferences]
            suggestion = self.llm_engine.suggest_meal(
                dietary_preferences=dietary_prefs,
                available_ingredients=self.user_profile.pantry_items,
                meal_type=meal_type,
                calorie_target=int(self.user_profile.daily_calorie_target * 0.3),
            )
            
            response = f"I can help you change your {meal_type}! Here's an alternative suggestion:\n\n"
            response += suggestion
            response += "\n\nWould you like me to update your plan with this, or would you like a different suggestion?"
            return {
                "response": response,
                "has_plan": False
            }

        return {
            "response": "I can help you modify your meal plan. What specific changes would you like?",
            "has_plan": False
        }

    def _handle_workout_modification(self, message: str) -> dict[str, Any]:
        """Handle requests to modify workouts.
        
        Returns:
            Dict with response and optional plan metadata
        """
        if "workout_plan" not in self.current_context:
            return {
                "response": "I don't have a current workout plan to modify. Would you like me to create one first?",
                "has_plan": False
            }

        # Extract day or workout type
        message_lower = message.lower()
        
        # Detect day
        days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        day_mentioned = None
        for day in days:
            if day in message_lower:
                day_mentioned = day
                break

        if not day_mentioned:
            return {
                "response": "Which day's workout would you like to change? (Monday through Sunday)",
                "has_plan": False
            }

        # Generate suggestion using LLM
        if self.user_profile:
            fitness_goals = [g.value for g in self.user_profile.fitness_goals]
            suggestion = self.llm_engine.suggest_workout(
                fitness_goals=fitness_goals,
                available_equipment=self.user_profile.available_equipment,
                duration_minutes=45,
                difficulty="intermediate",
            )
            
            response = f"I can help you change your {day_mentioned} workout! Here's an alternative:\n\n"
            response += suggestion
            response += "\n\nWould you like me to update your plan with this?"
            return {
                "response": response,
                "has_plan": False
            }

        return {
            "response": "I can help you modify your workout plan. What specific changes would you like?",
            "has_plan": False
        }

    def _handle_nutrition_question(self, message: str) -> dict[str, Any]:
        """Handle nutrition-related questions.
        
        Returns:
            Dict with response and optional plan metadata
        """
        # Use LLM to generate response
        prompt = f"""You are a knowledgeable nutrition assistant. Answer this question concisely and helpfully:

Question: {message}

Provide a clear, practical answer focused on nutrition and healthy eating."""

        # Try to use LLM if available
        try:
            if hasattr(self.llm_engine, 'is_model_loaded') and self.llm_engine.is_model_loaded():
                response = self.llm_engine.generate(prompt, max_tokens=200, temperature=0.7)
                return {
                    "response": response.strip(),
                    "has_plan": False
                }
            elif hasattr(self.llm_engine, 'is_available') and self.llm_engine.is_available():
                # For Ollama/OpenAI engines
                response = self.llm_engine.generate(prompt, max_tokens=200, temperature=0.7)
                return {
                    "response": response.strip(),
                    "has_plan": False
                }
        except Exception as e:
            print(f"[CHATBOT] LLM generation failed: {e}, using fallback")
        
        # Fallback responses
        message_lower = message.lower()
        if "protein" in message_lower:
            return {
                "response": (
                    "Protein is essential for muscle building and repair. Good sources include:\n"
                    "- Lean meats (chicken, turkey, fish)\n"
                    "- Eggs and dairy\n"
                    "- Legumes (beans, lentils)\n"
                    "- Tofu and tempeh\n"
                    "- Nuts and seeds\n\n"
                    "Aim for 1.6-2.2g per kg of body weight for muscle gain, or 0.8-1.2g for maintenance."
                ),
                "has_plan": False
            }
        elif "calorie" in message_lower:
            if self.user_profile:
                return {
                    "response": (
                        f"Based on your profile, your daily calorie target is {self.user_profile.daily_calorie_target} calories.\n"
                        f"This is calculated from your BMR and adjusted for your fitness goal of "
                        f"{', '.join(g.value for g in self.user_profile.fitness_goals)}."
                    ),
                    "has_plan": False
                }
            return {
                "response": "Calorie needs vary based on age, weight, height, and activity level. Would you like me to calculate yours?",
                "has_plan": False
            }
        
        return {
            "response": "That's a great nutrition question! Could you be more specific so I can give you the best answer?",
            "has_plan": False
        }

    def _handle_workout_question(self, message: str) -> dict[str, Any]:
        """Handle workout-related questions.
        
        Returns:
            Dict with response and optional plan metadata
        """
        # Use LLM to generate response
        prompt = f"""You are a knowledgeable fitness coach. Answer this question concisely and helpfully:

Question: {message}

Provide a clear, practical answer focused on exercise and fitness."""

        # Try to use LLM if available
        try:
            if hasattr(self.llm_engine, 'is_model_loaded') and self.llm_engine.is_model_loaded():
                response = self.llm_engine.generate(prompt, max_tokens=200, temperature=0.7)
                return {
                    "response": response.strip(),
                    "has_plan": False
                }
            elif hasattr(self.llm_engine, 'is_available') and self.llm_engine.is_available():
                # For Ollama/OpenAI engines
                response = self.llm_engine.generate(prompt, max_tokens=200, temperature=0.7)
                return {
                    "response": response.strip(),
                    "has_plan": False
                }
        except Exception as e:
            print(f"[CHATBOT] LLM generation failed: {e}, using fallback")
        
        # Fallback responses
        message_lower = message.lower()
        if "rest" in message_lower or "recovery" in message_lower:
            return {
                "response": (
                    "Rest and recovery are crucial for fitness progress! Here's why:\n"
                    "- Muscles grow during rest, not during workouts\n"
                    "- Prevents overtraining and injury\n"
                    "- Allows nervous system recovery\n\n"
                    "Aim for 1-2 rest days per week, and get 7-9 hours of sleep nightly."
                ),
                "has_plan": False
            }
        elif "beginner" in message_lower:
            return {
                "response": (
                    "Starting a fitness journey? Here are some tips:\n"
                    "- Start with 3 workouts per week\n"
                    "- Focus on form over weight\n"
                    "- Include both strength and cardio\n"
                    "- Progress gradually (10% increase per week)\n"
                    "- Listen to your body and rest when needed"
                ),
                "has_plan": False
            }
        
        return {
            "response": "That's a great fitness question! Could you be more specific so I can give you the best answer?",
            "has_plan": False
        }

    def _handle_profile_update(self, message: str) -> dict[str, Any]:
        """Handle user profile updates from conversation.
        
        Returns:
            Dict with response and optional plan metadata
        """
        message_lower = message.lower()
        updates = []

        # Detect dietary preferences
        for pref in DietaryPreference:
            if pref.value in message_lower:
                updates.append(f"dietary preference: {pref.value}")

        # Detect fitness goals
        for goal in FitnessGoal:
            if goal.value.replace("_", " ") in message_lower:
                updates.append(f"fitness goal: {goal.value}")

        # Detect allergies
        if "allergic" in message_lower or "allergy" in message_lower:
            # Extract potential allergens
            common_allergens = ["nuts", "dairy", "gluten", "soy", "eggs", "fish", "shellfish"]
            for allergen in common_allergens:
                if allergen in message_lower:
                    updates.append(f"allergy: {allergen}")

        if updates:
            response = "Got it! I've noted the following about you:\n"
            for update in updates:
                response += f"- {update}\n"
            response += "\nWould you like to create a meal plan or workout plan now?"
            return {
                "response": response,
                "has_plan": False
            }

        return {
            "response": (
                "I'd like to learn more about you! Could you tell me:\n"
                "- Your dietary preferences (vegan, keto, etc.)\n"
                "- Your fitness goals (weight loss, muscle gain, etc.)\n"
                "- Any allergies or restrictions"
            ),
            "has_plan": False
        }

    def _generate_general_response(self, message: str) -> dict[str, Any]:
        """Generate a general conversational response.
        
        Returns:
            Dict with response and optional plan metadata
        """
        message_lower = message.lower()

        # Greetings (Requirement 10.1, 10.2)
        if any(word in message_lower for word in ["hello", "hi", "hey", "greetings"]):
            return {
                "response": (
                    "Hello! 👋 I'm your NutriFit AI assistant. I can help you create personalized plans through natural conversation!\n\n"
                    "**🍽️ Meal Planning Examples:**\n"
                    "- 'Create a 2000 calorie meal plan with 130g protein'\n"
                    "- 'Generate a keto meal plan for weight loss'\n"
                    "- 'Make me a vegan meal plan for 7 days'\n\n"
                    "**💪 Workout Planning Examples:**\n"
                    "- 'Create a 4-day workout plan for muscle gain'\n"
                    "- 'Generate a beginner workout plan with no equipment'\n"
                    "- 'Make me a 30-minute cardio plan'\n\n"
                    "**💡 Tip:** Be specific about your targets (calories, macros, workout days) for best results!\n\n"
                    "What would you like to work on today?"
                ),
                "has_plan": False
            }

        # Thanks
        if any(word in message_lower for word in ["thank", "thanks", "appreciate"]):
            return {
                "response": "You're welcome! Let me know if you need anything else. I'm here to help!",
                "has_plan": False
            }

        # Help (Requirement 10.1, 10.2)
        if "help" in message_lower:
            return {
                "response": (
                    "I'm here to help with your nutrition and fitness journey! 🎯\n\n"
                    "**🍽️ Meal Planning Help:**\n"
                    "Try asking:\n"
                    "- 'Create a meal plan with 2000 calories and 150g protein'\n"
                    "- 'Generate a low-carb meal plan for 5 days'\n"
                    "- 'Make me a vegetarian meal plan'\n"
                    "- 'Change my breakfast to something high-protein'\n\n"
                    "**💪 Workout Planning Help:**\n"
                    "Try asking:\n"
                    "- 'Create a 4-day workout plan for muscle gain'\n"
                    "- 'Generate a beginner full-body workout'\n"
                    "- 'Make me a 45-minute upper body workout'\n"
                    "- 'Replace Monday's workout with cardio'\n\n"
                    "**💡 Tips:**\n"
                    "- Be specific about your targets (calories, macros, duration)\n"
                    "- Mention dietary preferences (vegan, keto, etc.)\n"
                    "- Specify fitness level (beginner, intermediate, advanced)\n"
                    "- You can modify plans by asking me to change specific parts\n\n"
                    "Just chat naturally and I'll understand what you need!"
                ),
                "has_plan": False
            }

        # Use LLM for general conversation
        # Check if using Ollama or OpenAI (better engines)
        if hasattr(self.llm_engine, 'is_available') and self.llm_engine.is_available():
            prompt = f"""You are a friendly fitness and nutrition assistant. Respond helpfully to:

User: {message}

Keep it brief and conversational."""
            try:
                response = self.llm_engine.generate(prompt, max_tokens=150, temperature=0.8)
                return {
                    "response": response.strip(),
                    "has_plan": False
                }
            except Exception:
                pass
        elif hasattr(self.llm_engine, 'is_model_loaded') and self.llm_engine.is_model_loaded():
            prompt = f"""You are a friendly fitness and nutrition assistant. Respond helpfully to:

User: {message}


Keep it brief and conversational."""
            response = self.llm_engine.generate(prompt, max_tokens=150, temperature=0.8)
            return {
                "response": response.strip(),
                "has_plan": False
            }

        return {
            "response": (
                "I'm your NutriFit AI assistant! I can help you create meal plans, design workouts, "
                "and answer your nutrition and fitness questions. What would you like to do?"
            ),
            "has_plan": False
        }

    def reset_conversation(self) -> None:
        """Reset the conversation history and context."""
        self.conversation_history = []
        self.current_context = {}

    def get_conversation_history(self) -> list[dict[str, str]]:
        """Get the full conversation history."""
        return self.conversation_history.copy()

    def export_context(self) -> dict[str, Any]:
        """Export the current context (meal plans, workout plans, etc.)."""
        return self.current_context.copy()

    def generate_llm_meal_plan(
        self,
        user_profile: UserProfile,
        requirements: dict
    ) -> str:
        """Generate a meal plan using LLM.
        
        Args:
            user_profile: User's profile with preferences
            requirements: Dict with calorie_target, macro_targets, duration, etc.
            
        Returns:
            Natural language meal plan description
        """
        # Extract requirements with defaults
        calorie_target = requirements.get('calorie_target', user_profile.daily_calorie_target)
        duration = requirements.get('duration', 7)
        
        # Calculate macro targets
        if 'macro_targets' in requirements:
            macros = requirements['macro_targets']
        else:
            macros = user_profile.calculate_macro_grams()
        
        # Build the prompt
        prompt = self._build_meal_plan_prompt(
            user_profile=user_profile,
            calorie_target=calorie_target,
            protein_target=macros.get('protein_g', 0),
            carbs_target=macros.get('carbs_g', 0),
            fat_target=macros.get('fat_g', 0),
            duration=duration
        )
        
        # Add system prompt to help model understand this is educational
        system_prompt = "You are a helpful assistant that provides sample meal plans for educational purposes. You always provide specific meal examples when asked, never refusing or giving general advice instead."
        
        # Generate using LLM with error handling (Requirement 9.1, 9.2)
        try:
            # Check if we have a real LLM or are in fallback mode
            if hasattr(self.llm_engine, 'is_model_loaded') and self.llm_engine.is_model_loaded():
                response = self.llm_engine.generate(prompt, max_tokens=2000, temperature=0.7, system_prompt=system_prompt)
                return response.strip()
            elif hasattr(self.llm_engine, 'is_available') and self.llm_engine.is_available():
                # For Ollama/OpenAI engines
                response = self.llm_engine.generate(prompt, max_tokens=2000, temperature=0.7, system_prompt=system_prompt)
                return response.strip()
            else:
                # LLM not available, use template fallback (Requirement 9.2)
                print("[CHATBOT] LLM not available, using template-based meal plan generation")
                return self._generate_template_meal_plan(
                    user_profile=user_profile,
                    calorie_target=calorie_target,
                    macros=macros,
                    duration=duration
                )
        except RuntimeError as e:
            # LLM-specific errors (timeout, unavailable, etc.) (Requirement 9.1)
            print(f"[CHATBOT] LLM error during meal plan generation: {e}")
            print("[CHATBOT] Falling back to template-based generation")
            return self._generate_template_meal_plan(
                user_profile=user_profile,
                calorie_target=calorie_target,
                macros=macros,
                duration=duration
            )
        except Exception as e:
            # Unexpected errors (Requirement 9.4)
            import traceback
            error_trace = traceback.format_exc()
            print(f"[CHATBOT ERROR] Unexpected error during meal plan generation: {e}")
            print(f"[CHATBOT ERROR] Traceback: {error_trace}")
            print("[CHATBOT] Falling back to template-based generation")
            return self._generate_template_meal_plan(
                user_profile=user_profile,
                calorie_target=calorie_target,
                macros=macros,
                duration=duration
            )

    def generate_llm_workout_plan(
        self,
        user_profile: UserProfile,
        requirements: dict
    ) -> str:
        """Generate a workout plan using LLM.
        
        Args:
            user_profile: User's profile with preferences
            requirements: Dict with workout_days, duration, intensity, etc.
            
        Returns:
            Natural language workout plan description
        """
        # Extract requirements with defaults
        workout_days = requirements.get('workout_days', 4)
        duration = requirements.get('duration', 45)
        focus_areas = requirements.get('focus_areas', [])
        fitness_level = requirements.get('fitness_level', 'intermediate')
        
        # Build the prompt
        prompt = self._build_workout_plan_prompt(
            user_profile=user_profile,
            workout_days=workout_days,
            duration=duration,
            focus_areas=focus_areas,
            fitness_level=fitness_level
        )
        
        # Generate using LLM with error handling (Requirement 9.1, 9.2)
        try:
            # Check if we have a real LLM or are in fallback mode
            if hasattr(self.llm_engine, 'is_model_loaded') and self.llm_engine.is_model_loaded():
                response = self.llm_engine.generate(prompt, max_tokens=2000, temperature=0.7)
                return response.strip()
            elif hasattr(self.llm_engine, 'is_available') and self.llm_engine.is_available():
                # For Ollama/OpenAI engines
                response = self.llm_engine.generate(prompt, max_tokens=2000, temperature=0.7)
                return response.strip()
            else:
                # LLM not available, use template fallback (Requirement 9.2)
                print("[CHATBOT] LLM not available, using template-based workout plan generation")
                return self._generate_template_workout_plan(
                    user_profile=user_profile,
                    workout_days=workout_days,
                    duration=duration,
                    focus_areas=focus_areas,
                    fitness_level=fitness_level
                )
        except RuntimeError as e:
            # LLM-specific errors (timeout, unavailable, etc.) (Requirement 9.1)
            print(f"[CHATBOT] LLM error during workout plan generation: {e}")
            print("[CHATBOT] Falling back to template-based generation")
            return self._generate_template_workout_plan(
                user_profile=user_profile,
                workout_days=workout_days,
                duration=duration,
                focus_areas=focus_areas,
                fitness_level=fitness_level
            )
        except Exception as e:
            # Unexpected errors (Requirement 9.4)
            import traceback
            error_trace = traceback.format_exc()
            print(f"[CHATBOT ERROR] Unexpected error during workout plan generation: {e}")
            print(f"[CHATBOT ERROR] Traceback: {error_trace}")
            print("[CHATBOT] Falling back to template-based generation")
            return self._generate_template_workout_plan(
                user_profile=user_profile,
                workout_days=workout_days,
                duration=duration,
                focus_areas=focus_areas,
                fitness_level=fitness_level
            )

    def store_generated_plan(
        self,
        plan_text: str,
        plan_type: str
    ) -> str:
        """Store generated plan in context for later saving.
        
        Args:
            plan_text: The LLM-generated plan text
            plan_type: "meal" or "workout"
            
        Returns:
            Unique plan ID for reference
        """
        import uuid
        from datetime import datetime
        
        # Generate unique plan ID
        plan_id = f"{plan_type}_{uuid.uuid4().hex[:8]}"
        
        # Store in context
        plan_data = {
            'plan_id': plan_id,
            'plan_type': plan_type,
            'llm_text': plan_text,
            'generated_at': datetime.now().isoformat(),
            'saved': False
        }
        
        # Store with plan_id as key
        self.current_context[f'generated_plan_{plan_id}'] = plan_data
        
        # Also store as current plan for easy access
        if plan_type == 'meal':
            self.current_context['current_meal_plan_id'] = plan_id
        elif plan_type == 'workout':
            self.current_context['current_workout_plan_id'] = plan_id
        
        return plan_id

    def _build_meal_plan_prompt(
        self,
        user_profile: UserProfile,
        calorie_target: int,
        protein_target: float,
        carbs_target: float,
        fat_target: float,
        duration: int
    ) -> str:
        """Build the meal plan prompt template with user profile injection.
        
        Args:
            user_profile: User's profile
            calorie_target: Daily calorie target
            protein_target: Daily protein target in grams
            carbs_target: Daily carbs target in grams
            fat_target: Daily fat target in grams
            duration: Number of days for the plan
            
        Returns:
            Formatted prompt string
        """
        # Format dietary preferences
        dietary_prefs = ', '.join([p.value.replace('_', ' ').title() for p in user_profile.dietary_preferences]) or 'None'
        
        # Format fitness goals
        fitness_goals = ', '.join([g.value.replace('_', ' ').title() for g in user_profile.fitness_goals]) or 'General fitness'
        
        # Format allergies
        allergies = ', '.join(user_profile.allergies) or 'None'
        
        prompt = f"""Create a detailed {duration}-day meal plan. You must provide specific meals with nutritional information.

User Requirements:
- Dietary Preferences: {dietary_prefs}
- Fitness Goals: {fitness_goals}
- Allergies: {allergies}
- Daily Calories: {calorie_target} kcal
- Protein: {protein_target:.0f}g | Carbs: {carbs_target:.0f}g | Fat: {fat_target:.0f}g

IMPORTANT: You must create a complete meal plan with specific meal names and nutritional values. Do not provide general advice or guidelines.

Format EXACTLY like this example:

**Day 1:**
- 🍳 Breakfast: Greek Yogurt Parfait with Berries (~400 kcal, Protein: 30g, Carbs: 45g, Fat: 12g)
- 🥗 Lunch: Grilled Chicken Salad with Quinoa (~550 kcal, Protein: 45g, Carbs: 50g, Fat: 18g)
- 🍽️ Dinner: Baked Salmon with Sweet Potato (~650 kcal, Protein: 50g, Carbs: 55g, Fat: 22g)
- 🍎 Snack: Apple with Almond Butter (~200 kcal, Protein: 6g, Carbs: 25g, Fat: 10g)
- 📊 Daily Total: ~1800 kcal

Now create {duration} days following this exact format. Include specific meal names, not general categories. Each meal must have approximate calories and macros."""

        # Include conversation history for regeneration context (Requirement 6.2)
        # Look for previous meal plans in conversation history
        previous_plans = []
        for i, msg in enumerate(self.conversation_history):
            if msg['role'] == 'assistant' and ('Day 1' in msg['content'] or 'Day X' in msg['content']):
                # Check if this looks like a meal plan (has meal emojis)
                if any(emoji in msg['content'] for emoji in ['🍳', '🥗', '🍽️', '🍎']):
                    previous_plans.append((i, msg['content']))
        
        # If there are previous plans, include the most recent one and any modification requests
        if previous_plans:
            last_plan_idx, last_plan = previous_plans[-1]
            
            # Get any user messages after the last plan (these are modification requests)
            modifications = []
            for msg in self.conversation_history[last_plan_idx + 1:]:
                if msg['role'] == 'user':
                    modifications.append(msg['content'])
            
            if modifications:
                prompt += f"\n\nPrevious Plan:\n{last_plan[:500]}...\n\n"  # Include first 500 chars
                prompt += f"User Modification Requests:\n"
                for mod in modifications[-3:]:  # Include last 3 modification requests
                    prompt += f"- {mod}\n"
                prompt += "\nPlease create a NEW meal plan that addresses these modification requests while maintaining the nutritional targets."

        return prompt

    def _build_workout_plan_prompt(
        self,
        user_profile: UserProfile,
        workout_days: int,
        duration: int,
        focus_areas: list[str],
        fitness_level: str
    ) -> str:
        """Build the workout plan prompt template with user profile injection.
        
        Args:
            user_profile: User's profile
            workout_days: Number of workout days per week
            duration: Session duration in minutes
            focus_areas: List of focus areas (e.g., ['upper body', 'cardio'])
            fitness_level: User's fitness level (beginner, intermediate, advanced)
            
        Returns:
            Formatted prompt string
        """
        # Format fitness goals
        fitness_goals = ', '.join([g.value.replace('_', ' ').title() for g in user_profile.fitness_goals]) or 'General fitness'
        
        # Format equipment
        equipment = ', '.join(user_profile.available_equipment) or 'Bodyweight only'
        
        # Format focus areas
        focus = ', '.join(focus_areas) if focus_areas else 'Full body'
        
        prompt = f"""Create a detailed {workout_days}-day workout plan. You must provide specific exercises with sets, reps, and rest periods.

User Requirements:
- Fitness Goals: {fitness_goals}
- Fitness Level: {fitness_level}
- Equipment: {equipment}
- Days per Week: {workout_days}
- Session Duration: {duration} minutes
- Focus: {focus}

IMPORTANT: You must create a complete workout plan with specific exercise names, sets, reps, and rest periods. Do not provide general advice.

Format EXACTLY like this example:

**Day 1 - Upper Body Strength:**
- Warm-up: Light cardio - 5 minutes
- Push-ups - 3 sets × 12 reps (Rest: 60s)
- Dumbbell Rows - 3 sets × 10 reps (Rest: 60s)
- Shoulder Press - 3 sets × 10 reps (Rest: 60s)
- Bicep Curls - 3 sets × 12 reps (Rest: 45s)
- Cool-down: Stretching - 5 minutes
- Total Duration: ~45 minutes
- Intensity: Medium

Now create {workout_days} days following this exact format. Include specific exercise names with sets, reps, and rest periods."""

        # Include conversation history for regeneration context (Requirement 6.2)
        # Look for previous workout plans in conversation history
        previous_plans = []
        for i, msg in enumerate(self.conversation_history):
            if msg['role'] == 'assistant' and ('Day 1' in msg['content'] or 'Day X' in msg['content']):
                # Check if this looks like a workout plan (has workout emojis or keywords)
                if any(keyword in msg['content'] for keyword in ['💪', 'Exercise', 'sets', 'reps', 'Workout']):
                    previous_plans.append((i, msg['content']))
        
        # If there are previous plans, include the most recent one and any modification requests
        if previous_plans:
            last_plan_idx, last_plan = previous_plans[-1]
            
            # Get any user messages after the last plan (these are modification requests)
            modifications = []
            for msg in self.conversation_history[last_plan_idx + 1:]:
                if msg['role'] == 'user':
                    modifications.append(msg['content'])
            
            if modifications:
                prompt += f"\n\nPrevious Plan:\n{last_plan[:500]}...\n\n"  # Include first 500 chars
                prompt += f"User Modification Requests:\n"
                for mod in modifications[-3:]:  # Include last 3 modification requests
                    prompt += f"- {mod}\n"
                prompt += "\nPlease create a NEW workout plan that addresses these modification requests while maintaining the workout parameters."

        return prompt

    def _generate_template_meal_plan(
        self,
        user_profile: UserProfile,
        calorie_target: int,
        macros: dict,
        duration: int
    ) -> str:
        """Generate a template-based meal plan when LLM is unavailable.
        
        Args:
            user_profile: User's profile
            calorie_target: Daily calorie target
            macros: Macro targets dict
            duration: Number of days
            
        Returns:
            Formatted meal plan text
        """
        from datetime import date, timedelta
        
        # Format dietary preferences
        dietary_prefs = ', '.join([p.value.replace('_', ' ').title() for p in user_profile.dietary_preferences]) or 'Balanced'
        
        plan_text = f"**{duration}-Day {dietary_prefs} Meal Plan**\n\n"
        plan_text += f"📊 **Daily Targets:** {calorie_target} kcal | "
        plan_text += f"Protein: {macros.get('protein_g', 0):.0f}g | "
        plan_text += f"Carbs: {macros.get('carbs_g', 0):.0f}g | "
        plan_text += f"Fat: {macros.get('fat_g', 0):.0f}g\n\n"
        
        # Generate meals for each day
        for day in range(1, duration + 1):
            current_date = date.today() + timedelta(days=day-1)
            plan_text += f"**Day {day} ({current_date.strftime('%A, %b %d')}):**\n"
            
            # Breakfast (~30% of calories)
            breakfast_cals = int(calorie_target * 0.30)
            plan_text += f"- 🍳 Breakfast: {self._suggest_meal_name('breakfast', user_profile)} "
            plan_text += f"(~{breakfast_cals} kcal, Protein: {int(macros.get('protein_g', 0) * 0.30)}g, "
            plan_text += f"Carbs: {int(macros.get('carbs_g', 0) * 0.30)}g, Fat: {int(macros.get('fat_g', 0) * 0.30)}g)\n"
            
            # Lunch (~35% of calories)
            lunch_cals = int(calorie_target * 0.35)
            plan_text += f"- 🥗 Lunch: {self._suggest_meal_name('lunch', user_profile)} "
            plan_text += f"(~{lunch_cals} kcal, Protein: {int(macros.get('protein_g', 0) * 0.35)}g, "
            plan_text += f"Carbs: {int(macros.get('carbs_g', 0) * 0.35)}g, Fat: {int(macros.get('fat_g', 0) * 0.35)}g)\n"
            
            # Dinner (~30% of calories)
            dinner_cals = int(calorie_target * 0.30)
            plan_text += f"- 🍽️ Dinner: {self._suggest_meal_name('dinner', user_profile)} "
            plan_text += f"(~{dinner_cals} kcal, Protein: {int(macros.get('protein_g', 0) * 0.30)}g, "
            plan_text += f"Carbs: {int(macros.get('carbs_g', 0) * 0.30)}g, Fat: {int(macros.get('fat_g', 0) * 0.30)}g)\n"
            
            # Snack (~5% of calories)
            snack_cals = int(calorie_target * 0.05)
            plan_text += f"- 🍎 Snack: {self._suggest_meal_name('snack', user_profile)} "
            plan_text += f"(~{snack_cals} kcal, Protein: {int(macros.get('protein_g', 0) * 0.05)}g, "
            plan_text += f"Carbs: {int(macros.get('carbs_g', 0) * 0.05)}g, Fat: {int(macros.get('fat_g', 0) * 0.05)}g)\n"
            
            plan_text += f"- 📊 Daily Total: ~{calorie_target} kcal\n\n"
        
        return plan_text

    def _generate_template_workout_plan(
        self,
        user_profile: UserProfile,
        workout_days: int,
        duration: int,
        focus_areas: list[str],
        fitness_level: str
    ) -> str:
        """Generate a template-based workout plan when LLM is unavailable.
        
        Args:
            user_profile: User's profile
            workout_days: Number of workout days per week
            duration: Session duration in minutes
            focus_areas: List of focus areas
            fitness_level: Fitness level
            
        Returns:
            Formatted workout plan text
        """
        # Format fitness goals
        fitness_goals = ', '.join([g.value.replace('_', ' ').title() for g in user_profile.fitness_goals]) or 'General Fitness'
        equipment = ', '.join(user_profile.available_equipment) or 'Bodyweight'
        focus = ', '.join(focus_areas) if focus_areas else 'Full Body'
        
        plan_text = f"**{workout_days}-Day Weekly Workout Plan**\n\n"
        plan_text += f"🎯 **Goals:** {fitness_goals}\n"
        plan_text += f"🏋️ **Equipment:** {equipment}\n"
        plan_text += f"💪 **Focus:** {focus}\n"
        plan_text += f"⏱️ **Duration:** {duration} minutes per session\n"
        plan_text += f"📈 **Level:** {fitness_level.title()}\n\n"
        
        # Define workout types
        workout_types = ['Upper Body', 'Lower Body', 'Full Body', 'Cardio', 'Core & Flexibility']
        
        # Generate workouts for the week
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        workout_count = 0
        
        for i, day in enumerate(days):
            if workout_count < workout_days:
                workout_type = workout_types[workout_count % len(workout_types)]
                plan_text += f"**{day} - {workout_type}:**\n"
                plan_text += f"- Exercise 1: {self._suggest_exercise(workout_type, equipment)} - 3 sets × 12 reps (Rest: 60s)\n"
                plan_text += f"- Exercise 2: {self._suggest_exercise(workout_type, equipment)} - 3 sets × 10 reps (Rest: 60s)\n"
                plan_text += f"- Exercise 3: {self._suggest_exercise(workout_type, equipment)} - 3 sets × 15 reps (Rest: 45s)\n"
                plan_text += f"- Total Duration: ~{duration} minutes\n"
                plan_text += f"- Intensity: {fitness_level.title()}\n\n"
                workout_count += 1
            else:
                plan_text += f"**{day}:**\n"
                plan_text += f"- 😴 Rest Day - Active recovery (light stretching, walking)\n\n"
        
        return plan_text

    def _suggest_meal_name(self, meal_type: str, user_profile: UserProfile) -> str:
        """Suggest a meal name based on meal type and dietary preferences."""
        import random
        
        is_vegan = DietaryPreference.VEGAN in user_profile.dietary_preferences
        is_vegetarian = DietaryPreference.VEGETARIAN in user_profile.dietary_preferences or is_vegan
        is_keto = DietaryPreference.KETO in user_profile.dietary_preferences
        
        meals = {
            'breakfast': {
                'vegan': ['Overnight Oats with Berries', 'Tofu Scramble', 'Smoothie Bowl', 'Avocado Toast'],
                'vegetarian': ['Greek Yogurt Parfait', 'Veggie Omelet', 'Protein Pancakes', 'Quinoa Breakfast Bowl'],
                'keto': ['Keto Egg Muffins', 'Bacon and Eggs', 'Bulletproof Coffee with Eggs', 'Cheese Omelet'],
                'default': ['Oatmeal with Protein', 'Scrambled Eggs with Toast', 'Breakfast Burrito', 'Protein Smoothie']
            },
            'lunch': {
                'vegan': ['Buddha Bowl', 'Lentil Soup', 'Chickpea Salad Wrap', 'Quinoa Veggie Bowl'],
                'vegetarian': ['Caprese Sandwich', 'Veggie Pasta', 'Greek Salad with Feta', 'Grilled Cheese with Soup'],
                'keto': ['Cobb Salad', 'Bunless Burger', 'Chicken Caesar Salad', 'Zucchini Noodles with Pesto'],
                'default': ['Grilled Chicken Salad', 'Turkey Sandwich', 'Pasta with Marinara', 'Stir-Fry Bowl']
            },
            'dinner': {
                'vegan': ['Tofu Stir-Fry', 'Lentil Curry', 'Veggie Pasta Primavera', 'Black Bean Tacos'],
                'vegetarian': ['Eggplant Parmesan', 'Veggie Lasagna', 'Mushroom Risotto', 'Stuffed Bell Peppers'],
                'keto': ['Grilled Salmon with Asparagus', 'Steak with Cauliflower Mash', 'Chicken Thighs with Broccoli', 'Pork Chops with Green Beans'],
                'default': ['Grilled Chicken with Rice', 'Baked Salmon with Quinoa', 'Beef Stir-Fry', 'Turkey Meatballs with Pasta']
            },
            'snack': {
                'vegan': ['Hummus with Veggies', 'Trail Mix', 'Apple with Almond Butter', 'Energy Balls'],
                'vegetarian': ['Greek Yogurt', 'Cheese and Crackers', 'Protein Bar', 'Cottage Cheese with Fruit'],
                'keto': ['Cheese Cubes', 'Nuts', 'Celery with Cream Cheese', 'Hard-Boiled Eggs'],
                'default': ['Protein Shake', 'Mixed Nuts', 'Fruit and Yogurt', 'Granola Bar']
            }
        }
        
        meal_options = meals.get(meal_type, meals['lunch'])
        
        if is_vegan:
            return random.choice(meal_options['vegan'])
        elif is_vegetarian:
            return random.choice(meal_options['vegetarian'])
        elif is_keto:
            return random.choice(meal_options['keto'])
        else:
            return random.choice(meal_options['default'])

    def _suggest_exercise(self, workout_type: str, equipment: str) -> str:
        """Suggest an exercise based on workout type and available equipment."""
        import random
        
        has_dumbbells = 'dumbbell' in equipment.lower()
        has_barbell = 'barbell' in equipment.lower()
        has_bands = 'band' in equipment.lower()
        
        exercises = {
            'Upper Body': {
                'weights': ['Dumbbell Bench Press', 'Barbell Rows', 'Overhead Press', 'Bicep Curls', 'Tricep Extensions'],
                'bodyweight': ['Push-ups', 'Pull-ups', 'Dips', 'Pike Push-ups', 'Diamond Push-ups']
            },
            'Lower Body': {
                'weights': ['Barbell Squats', 'Dumbbell Lunges', 'Romanian Deadlifts', 'Leg Press', 'Calf Raises'],
                'bodyweight': ['Bodyweight Squats', 'Lunges', 'Bulgarian Split Squats', 'Glute Bridges', 'Jump Squats']
            },
            'Full Body': {
                'weights': ['Deadlifts', 'Clean and Press', 'Thrusters', 'Dumbbell Snatches', 'Farmer Walks'],
                'bodyweight': ['Burpees', 'Mountain Climbers', 'Jumping Jacks', 'High Knees', 'Plank to Push-up']
            },
            'Cardio': {
                'weights': ['Kettlebell Swings', 'Dumbbell Thrusters', 'Battle Ropes', 'Box Jumps', 'Sled Pushes'],
                'bodyweight': ['Running', 'Jump Rope', 'High Knees', 'Burpees', 'Mountain Climbers']
            },
            'Core & Flexibility': {
                'weights': ['Weighted Crunches', 'Russian Twists', 'Dumbbell Side Bends', 'Cable Woodchops', 'Medicine Ball Slams'],
                'bodyweight': ['Planks', 'Bicycle Crunches', 'Leg Raises', 'Russian Twists', 'Dead Bug']
            }
        }
        
        exercise_options = exercises.get(workout_type, exercises['Full Body'])
        
        if has_dumbbells or has_barbell or has_bands:
            return random.choice(exercise_options['weights'])
        else:
            return random.choice(exercise_options['bodyweight'])
