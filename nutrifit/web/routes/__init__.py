"""Route modules for the web application."""

from nutrifit.web.routes import chatbot, main, meal_plans, profile, progress, shopping, workout_plans


def register_routes(app):
    """Register all route blueprints with the Flask app."""
    # Register chatbot blueprint
    app.register_blueprint(chatbot.chatbot_bp)
    
    # Import all route modules to register their routes
    # Routes are registered via decorators, so importing is enough
    _ = (main, meal_plans, profile, progress, shopping, workout_plans)

