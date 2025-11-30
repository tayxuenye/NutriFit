"""User profile and preference models."""

from dataclasses import dataclass, field
from enum import Enum


class DietaryPreference(Enum):
    """Supported dietary preferences."""

    NONE = "none"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    PESCATARIAN = "pescatarian"
    KETO = "keto"
    PALEO = "paleo"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    LOW_CARB = "low_carb"
    HIGH_PROTEIN = "high_protein"


class FitnessGoal(Enum):
    """Supported fitness goals."""

    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"
    ENDURANCE = "endurance"
    STRENGTH = "strength"
    FLEXIBILITY = "flexibility"
    GENERAL_FITNESS = "general_fitness"


@dataclass
class UserProfile:
    """User profile containing preferences and goals."""

    name: str
    age: int
    weight_kg: float
    height_cm: float
    gender: str = "male"  # "male" or "female" for BMR calculation
    dietary_preferences: list[DietaryPreference] = field(default_factory=list)
    fitness_goals: list[FitnessGoal] = field(default_factory=list)
    allergies: list[str] = field(default_factory=list)
    pantry_items: list[str] = field(default_factory=list)
    available_equipment: list[str] = field(default_factory=list)
    daily_calorie_target: int | None = None
    meals_per_day: int = 3

    def __post_init__(self) -> None:
        """Calculate default calorie target if not provided and validate data."""
        self.validate()
        
        if self.daily_calorie_target is None:
            self.daily_calorie_target = self.calculate_calorie_target()
    
    def calculate_bmr(self) -> float:
        """Calculate Basal Metabolic Rate using Mifflin-St Jeor equation.
        
        Returns:
            float: BMR in calories per day
        """
        # Mifflin-St Jeor equation
        # Men: BMR = 10 * weight(kg) + 6.25 * height(cm) - 5 * age(years) + 5
        # Women: BMR = 10 * weight(kg) + 6.25 * height(cm) - 5 * age(years) - 161
        
        bmr = 10 * self.weight_kg + 6.25 * self.height_cm - 5 * self.age
        
        if self.gender.lower() == "male":
            bmr += 5
        else:  # female
            bmr -= 161
        
        return bmr
    
    def calculate_calorie_target(self) -> int:
        """Calculate daily calorie target based on BMR and fitness goals.
        
        Returns:
            int: Daily calorie target adjusted for fitness goals
        """
        # Calculate BMR
        bmr = self.calculate_bmr()
        
        # Assume moderate activity level (1.55 multiplier)
        # This is a reasonable default for someone following a fitness program
        maintenance_calories = bmr * 1.55
        
        # Adjust based on primary fitness goal
        # Priority: weight_loss > muscle_gain > maintenance
        if FitnessGoal.WEIGHT_LOSS in self.fitness_goals:
            # 15% deficit for weight loss
            return int(maintenance_calories * 0.85)
        elif FitnessGoal.MUSCLE_GAIN in self.fitness_goals:
            # 15% surplus for muscle gain
            return int(maintenance_calories * 1.15)
        else:
            # Maintenance for all other goals
            return int(maintenance_calories)
    
    def calculate_macro_ratios(self) -> dict[str, float]:
        """Calculate macro-nutrient ratios based on fitness goals.
        
        Returns:
            dict: Dictionary with keys 'protein', 'carbs', 'fat' as percentages (0-1)
        """
        # Default balanced ratios (maintenance)
        protein_ratio = 0.30  # 30% protein
        carbs_ratio = 0.40    # 40% carbs
        fat_ratio = 0.30      # 30% fat
        
        # Adjust based on primary fitness goal
        if FitnessGoal.WEIGHT_LOSS in self.fitness_goals:
            # Higher protein, lower carbs for weight loss
            protein_ratio = 0.35
            carbs_ratio = 0.30
            fat_ratio = 0.35
        elif FitnessGoal.MUSCLE_GAIN in self.fitness_goals:
            # Higher protein and carbs for muscle gain
            protein_ratio = 0.35
            carbs_ratio = 0.45
            fat_ratio = 0.20
        elif FitnessGoal.ENDURANCE in self.fitness_goals:
            # Higher carbs for endurance
            protein_ratio = 0.25
            carbs_ratio = 0.50
            fat_ratio = 0.25
        elif FitnessGoal.STRENGTH in self.fitness_goals:
            # Higher protein for strength
            protein_ratio = 0.40
            carbs_ratio = 0.35
            fat_ratio = 0.25
        
        # Adjust for dietary preferences
        if DietaryPreference.KETO in self.dietary_preferences:
            # Very low carb, high fat for keto
            protein_ratio = 0.25
            carbs_ratio = 0.05
            fat_ratio = 0.70
        elif DietaryPreference.LOW_CARB in self.dietary_preferences:
            # Low carb, moderate fat
            protein_ratio = 0.35
            carbs_ratio = 0.20
            fat_ratio = 0.45
        elif DietaryPreference.HIGH_PROTEIN in self.dietary_preferences:
            # High protein
            protein_ratio = 0.40
            carbs_ratio = 0.35
            fat_ratio = 0.25
        
        return {
            "protein": protein_ratio,
            "carbs": carbs_ratio,
            "fat": fat_ratio,
        }
    
    def calculate_macro_grams(self) -> dict[str, float]:
        """Calculate macro-nutrient targets in grams based on calorie target.
        
        Returns:
            dict: Dictionary with keys 'protein_g', 'carbs_g', 'fat_g'
        """
        ratios = self.calculate_macro_ratios()
        calories = self.daily_calorie_target or self.calculate_calorie_target()
        
        # Calories per gram: protein=4, carbs=4, fat=9
        protein_g = (calories * ratios["protein"]) / 4
        carbs_g = (calories * ratios["carbs"]) / 4
        fat_g = (calories * ratios["fat"]) / 9
        
        return {
            "protein_g": round(protein_g, 1),
            "carbs_g": round(carbs_g, 1),
            "fat_g": round(fat_g, 1),
        }
    
    def validate(self) -> None:
        """Validate user profile data for integrity.
        
        Raises:
            ValueError: If any validation check fails.
        """
        if not self.name or not self.name.strip():
            raise ValueError("Name cannot be empty")
        
        if self.age <= 0 or self.age > 150:
            raise ValueError("Age must be between 1 and 150")
        
        if self.weight_kg <= 0 or self.weight_kg > 500:
            raise ValueError("Weight must be between 0 and 500 kg")
        
        if self.height_cm <= 0 or self.height_cm > 300:
            raise ValueError("Height must be between 0 and 300 cm")
        
        if self.gender.lower() not in ["male", "female"]:
            raise ValueError("Gender must be 'male' or 'female'")
        
        if self.meals_per_day < 1 or self.meals_per_day > 10:
            raise ValueError("Meals per day must be between 1 and 10")
        
        if self.daily_calorie_target is not None and (
            self.daily_calorie_target < 0 or self.daily_calorie_target > 15000
        ):
            raise ValueError("Daily calorie target must be between 0 and 15000")
        
        # Validate dietary preference compatibility
        self._validate_dietary_preferences()
    
    def _validate_dietary_preferences(self) -> None:
        """Validate that dietary preferences are compatible with each other.
        
        Raises:
            ValueError: If incompatible dietary preferences are found.
        """
        prefs = set(self.dietary_preferences)
        
        # Vegan is incompatible with pescatarian
        if DietaryPreference.VEGAN in prefs and DietaryPreference.PESCATARIAN in prefs:
            raise ValueError("Vegan and pescatarian preferences are incompatible")
        
        # Vegan includes vegetarian restrictions
        if DietaryPreference.VEGAN in prefs and DietaryPreference.VEGETARIAN in prefs:
            # This is redundant but not incompatible - just warn by removing vegetarian
            self.dietary_preferences = [p for p in self.dietary_preferences 
                                       if p != DietaryPreference.VEGETARIAN]
        
        # Keto and high carb diets are incompatible
        # (Note: LOW_CARB and KETO are compatible as keto is a type of low carb)
    
    def is_valid_structure(self) -> bool:
        """Check if the data structure is valid for persistence.
        
        Returns:
            bool: True if structure is valid, False otherwise.
        """
        try:
            self.validate()
            return True
        except (ValueError, TypeError, AttributeError):
            return False

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "age": self.age,
            "weight_kg": self.weight_kg,
            "height_cm": self.height_cm,
            "gender": self.gender,
            "dietary_preferences": [p.value for p in self.dietary_preferences],
            "fitness_goals": [g.value for g in self.fitness_goals],
            "allergies": self.allergies,
            "pantry_items": self.pantry_items,
            "available_equipment": self.available_equipment,
            "daily_calorie_target": self.daily_calorie_target,
            "meals_per_day": self.meals_per_day,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        """Create from dictionary."""
        data["dietary_preferences"] = [
            DietaryPreference(p) for p in data.get("dietary_preferences", [])
        ]
        data["fitness_goals"] = [
            FitnessGoal(g) for g in data.get("fitness_goals", [])
        ]
        return cls(**data)
