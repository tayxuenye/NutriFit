"""Utility functions for the web application."""

from nutrifit.models.user import FitnessGoal, UserProfile
from nutrifit.web import storage


def get_or_create_profile() -> UserProfile:
    """Get existing profile or create a default one."""
    profile = storage.load_user_profile()
    if profile:
        return profile
    
    # Create default profile with all required fields
    try:
        default_profile = UserProfile(
            name="User",
            age=30,
            weight_kg=70.0,
            height_cm=170.0,
            gender="male",
            fitness_goals=[FitnessGoal.MAINTENANCE],
            dietary_preferences=[],
            allergies=[],
            pantry_items=[],
            available_equipment=[],
        )
        # Save the default profile
        storage.save_user_profile(default_profile, user_id="default")
        return default_profile
    except Exception as e:
        print(f"Error creating default profile: {e}")
        raise

