"""Chatbot routes for conversational AI interface."""

from flask import Blueprint, jsonify, request

from nutrifit.engines.chatbot_engine import ChatbotEngine
from nutrifit.engines.embedding_engine import EmbeddingEngine
from nutrifit.engines.llm_engine import LocalLLMEngine
from nutrifit.engines.meal_planner import MealPlannerEngine
from nutrifit.engines.workout_planner import WorkoutPlannerEngine
from nutrifit.web.utils import get_or_create_profile

# Create blueprint
chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/api/chatbot")

# Initialize chatbot engine (singleton)
_chatbot_engine = None


def get_chatbot_engine() -> ChatbotEngine:
    """Get or create the chatbot engine."""
    global _chatbot_engine
    if _chatbot_engine is None:
        # Initialize AI engines
        embedding_engine = EmbeddingEngine()
        llm_engine = LocalLLMEngine()  # For meal/workout planners
        meal_planner = MealPlannerEngine(
            embedding_engine=embedding_engine,
            llm_engine=llm_engine,
        )
        workout_planner = WorkoutPlannerEngine(
            embedding_engine=embedding_engine,
            llm_engine=llm_engine,
        )
        
        # ChatbotEngine will auto-detect best LLM (Ollama, OpenAI, or fallback)
        _chatbot_engine = ChatbotEngine(
            llm_engine=None,  # Let it auto-detect!
            meal_planner=meal_planner,
            workout_planner=workout_planner,
            use_ollama=True,  # Enable Ollama
            use_openai=False,  # Disable OpenAI (set to True if you have API key)
            ollama_model="llama3.2",  # Model to use
        )
    return _chatbot_engine


@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    """
    Process a chat message and return a response.
    
    Request body:
        {
            "message": "Create a meal plan for me",
            "user_id": "default"  # optional
        }
    
    Response:
        {
            "response": "Great! I've created a meal plan...",
            "conversation_id": "abc123"
        }
    """
    try:
        data = request.get_json()
        
        if not data or "message" not in data:
            return jsonify({"error": "Message is required"}), 400
        
        message = data["message"]
        user_id = data.get("user_id", "default")
        
        print(f"[CHATBOT] Received message: {message}")
        
        # Get user profile
        user_profile = get_or_create_profile()
        print(f"[CHATBOT] User profile loaded: {user_profile.name}")
        
        # Get chatbot engine
        chatbot = get_chatbot_engine()
        print(f"[CHATBOT] Chatbot engine ready")
        
        # Process message with error handling (Requirement 9.1)
        try:
            response_data = chatbot.chat(message, user_profile=user_profile)
            print(f"[CHATBOT] Response generated successfully")
        except RuntimeError as e:
            # Handle LLM-specific errors (Requirement 9.1, 9.2)
            error_msg = str(e)
            print(f"[CHATBOT ERROR] LLM error: {error_msg}")
            
            # Check if this is an LLM unavailability error
            if "not available" in error_msg.lower() or "ollama" in error_msg.lower():
                # Provide helpful error message (Requirement 9.1)
                response_data = {
                    "response": (
                        "I'm having trouble connecting to the AI service. "
                        "I can still help you with basic questions and use the quick plan generator. "
                        "Would you like me to create a plan using the structured generator instead?"
                    ),
                    "has_plan": False,
                    "llm_unavailable": True
                }
            else:
                # Re-raise for general error handling
                raise
        
        # Build response JSON with metadata
        response_json = {
            "response": response_data.get("response", ""),
            "conversation_id": user_id,
            "has_plan": response_data.get("has_plan", False)
        }
        
        # Add plan metadata if present
        if "plan_id" in response_data:
            response_json["plan_id"] = response_data["plan_id"]
        if "plan_type" in response_data:
            response_json["plan_type"] = response_data["plan_type"]
        if "llm_unavailable" in response_data:
            response_json["llm_unavailable"] = response_data["llm_unavailable"]
        
        return jsonify(response_json)
    
    except Exception as e:
        # Log all errors for debugging (Requirement 9.4)
        import traceback
        error_trace = traceback.format_exc()
        print(f"[CHATBOT ERROR] Unexpected error in chat endpoint")
        print(f"[CHATBOT ERROR] {error_trace}")
        
        # Return user-friendly error message (Requirement 9.1)
        return jsonify({
            "error": "I encountered an unexpected error. Please try again or rephrase your message.",
            "details": str(e),
            "trace": error_trace
        }), 500


@chatbot_bp.route("/history", methods=["GET"])
def get_history():
    """
    Get the conversation history.
    
    Response:
        {
            "history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"}
            ]
        }
    """
    try:
        chatbot = get_chatbot_engine()
        history = chatbot.get_conversation_history()
        
        return jsonify({"history": history})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chatbot_bp.route("/reset", methods=["POST"])
def reset():
    """
    Reset the conversation history.
    
    Response:
        {
            "message": "Conversation reset successfully"
        }
    """
    try:
        chatbot = get_chatbot_engine()
        chatbot.reset_conversation()
        
        return jsonify({"message": "Conversation reset successfully"})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chatbot_bp.route("/context", methods=["GET"])
def get_context():
    """
    Get the current context (meal plans, workout plans, etc.).
    
    Response:
        {
            "context": {
                "meal_plan": {...},
                "workout_plan": {...}
            }
        }
    """
    try:
        chatbot = get_chatbot_engine()
        context = chatbot.export_context()
        
        # Convert plans to dict for JSON serialization
        serialized_context = {}
        for key, value in context.items():
            if hasattr(value, "to_dict"):
                serialized_context[key] = value.to_dict()
            else:
                serialized_context[key] = value
        
        return jsonify({"context": serialized_context})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@chatbot_bp.route("/save-plan", methods=["POST"])
def save_plan():
    """
    Save an LLM-generated plan to user's dashboard.
    
    Request body:
        {
            "plan_id": "meal_abc123",
            "plan_type": "meal" | "workout",
            "user_id": "default"  # optional
        }
    
    Response:
        {
            "success": true,
            "plan_id": "saved_plan_123",
            "message": "Plan saved successfully"
        }
    """
    try:
        from nutrifit.parsers.plan_parser import PlanParser
        from nutrifit.utils.storage import StorageManager
        
        data = request.get_json()
        
        if not data or "plan_id" not in data:
            return jsonify({"error": "plan_id is required"}), 400
        
        plan_id = data["plan_id"]
        plan_type = data.get("plan_type")
        user_id = data.get("user_id", "default")
        
        print(f"[SAVE_PLAN] Received request to save plan: {plan_id}, type: {plan_type}")
        
        # Get chatbot engine and retrieve plan from context
        chatbot = get_chatbot_engine()
        context = chatbot.export_context()
        
        # Look for the generated plan in context
        plan_key = f"generated_plan_{plan_id}"
        if plan_key not in context:
            return jsonify({"error": f"Plan {plan_id} not found in context"}), 404
        
        plan_data = context[plan_key]
        llm_text = plan_data.get("llm_text")
        actual_plan_type = plan_data.get("plan_type")
        
        # Use the plan type from the stored data if not provided
        if not plan_type:
            plan_type = actual_plan_type
        
        if not llm_text:
            return jsonify({"error": "Plan text not found"}), 404
        
        print(f"[SAVE_PLAN] Found plan in context, type: {plan_type}")
        
        # Get user profile
        user_profile = get_or_create_profile()
        
        # Initialize parser and storage
        parser = PlanParser()
        storage = StorageManager()
        
        # Parse and save based on plan type
        if plan_type == "meal":
            # Parse LLM text into structured MealPlan with retry logic (Requirement 9.4)
            max_retries = 1
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    meal_plan = parser.parse_meal_plan(llm_text, user_profile)
                    print(f"[SAVE_PLAN] Parsed meal plan: {meal_plan.id}")
                    
                    # Save to storage
                    was_replaced, saved_plan_id = storage.save_meal_plan(meal_plan, overwrite_existing=True)
                    
                    # Mark as saved in context
                    plan_data['saved'] = True
                    
                    message = "Meal plan saved successfully!"
                    if was_replaced:
                        message += " (Replaced existing plan for this date range)"
                    
                    # Add note if parsing had issues but succeeded
                    if attempt > 0:
                        message += " Note: Some nutritional data may be estimated."
                    
                    print(f"[SAVE_PLAN] Meal plan saved: {saved_plan_id}")
                    
                    return jsonify({
                        "success": True,
                        "plan_id": saved_plan_id,
                        "message": message
                    })
                    
                except ValueError as e:
                    last_error = e
                    print(f"[SAVE_PLAN] Parsing attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries:
                        # Try with more lenient parsing on retry
                        continue
                    else:
                        # All retries exhausted (Requirement 9.3)
                        import traceback
                        error_trace = traceback.format_exc()
                        print(f"[SAVE_PLAN ERROR] Parsing failed after {max_retries + 1} attempts")
                        print(f"[SAVE_PLAN ERROR] Traceback: {error_trace}")
                        
                        return jsonify({
                            "error": f"Failed to parse meal plan: {str(e)}",
                            "suggestion": "The plan format may be incompatible. Would you like me to regenerate it?",
                            "details": "I had trouble extracting the meal information. Try asking me to create a new plan with more specific details."
                        }), 400
                
                except Exception as e:
                    # Unexpected error during save (Requirement 9.4)
                    import traceback
                    error_trace = traceback.format_exc()
                    print(f"[SAVE_PLAN ERROR] Unexpected error: {e}")
                    print(f"[SAVE_PLAN ERROR] Traceback: {error_trace}")
                    
                    return jsonify({
                        "error": f"Failed to save meal plan: {str(e)}",
                        "suggestion": "An unexpected error occurred. Please try again or contact support if the issue persists."
                    }), 500
                
        elif plan_type == "workout":
            # Parse LLM text into structured WorkoutPlan with retry logic (Requirement 9.4)
            max_retries = 1
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    workout_plan = parser.parse_workout_plan(llm_text, user_profile)
                    print(f"[SAVE_PLAN] Parsed workout plan: {workout_plan.id}")
                    
                    # Save to storage
                    was_replaced, saved_plan_id = storage.save_workout_plan(workout_plan, overwrite_existing=True)
                    
                    # Mark as saved in context
                    plan_data['saved'] = True
                    
                    message = "Workout plan saved successfully!"
                    if was_replaced:
                        message += " (Replaced existing plan for this date range)"
                    
                    # Add note if parsing had issues but succeeded
                    if attempt > 0:
                        message += " Note: Some exercise details may be estimated."
                    
                    print(f"[SAVE_PLAN] Workout plan saved: {saved_plan_id}")
                    
                    return jsonify({
                        "success": True,
                        "plan_id": saved_plan_id,
                        "message": message
                    })
                    
                except ValueError as e:
                    last_error = e
                    print(f"[SAVE_PLAN] Parsing attempt {attempt + 1} failed: {e}")
                    
                    if attempt < max_retries:
                        # Try with more lenient parsing on retry
                        continue
                    else:
                        # All retries exhausted (Requirement 9.3)
                        import traceback
                        error_trace = traceback.format_exc()
                        print(f"[SAVE_PLAN ERROR] Parsing failed after {max_retries + 1} attempts")
                        print(f"[SAVE_PLAN ERROR] Traceback: {error_trace}")
                        
                        return jsonify({
                            "error": f"Failed to parse workout plan: {str(e)}",
                            "suggestion": "The plan format may be incompatible. Would you like me to regenerate it?",
                            "details": "I had trouble extracting the workout information. Try asking me to create a new plan with more specific details."
                        }), 400
                
                except Exception as e:
                    # Unexpected error during save (Requirement 9.4)
                    import traceback
                    error_trace = traceback.format_exc()
                    print(f"[SAVE_PLAN ERROR] Unexpected error: {e}")
                    print(f"[SAVE_PLAN ERROR] Traceback: {error_trace}")
                    
                    return jsonify({
                        "error": f"Failed to save workout plan: {str(e)}",
                        "suggestion": "An unexpected error occurred. Please try again or contact support if the issue persists."
                    }), 500
        else:
            return jsonify({"error": f"Invalid plan type: {plan_type}"}), 400
    
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[SAVE_PLAN ERROR] {error_trace}")
        return jsonify({"error": str(e), "trace": error_trace}), 500
