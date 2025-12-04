# Design Document

## Overview

The NutriFit AI Assistant is an offline-capable application that leverages pre-trained AI models to generate personalized meal and workout plans. The system architecture emphasizes modularity, offline operation, and local data storage to ensure privacy and independence from cloud services.

The application uses two primary AI components:
1. **Embedding Engine**: Utilizes pre-trained sentence transformers (all-MiniLM-L6-v2) for semantic recipe and workout matching
2. **LLM Engine**: Employs local language models (GPT4All/LLaMA via llama-cpp-python) for creative suggestions, with template-based fallback

The system is designed around a clear separation of concerns with distinct layers for data models, AI engines, business logic (planners), utilities, and user interface.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interface Layer                     │
│                  (CLI / Basic Web Interface)                 │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                    Application Layer                         │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Meal Planner    │  │ Workout Planner  │                │
│  │     Engine       │  │     Engine       │                │
│  └────────┬─────────┘  └────────┬─────────┘                │
│           │                     │                            │
│  ┌────────┴─────────────────────┴─────────┐                │
│  │         Shopping List Optimizer         │                │
│  └────────────────┬────────────────────────┘                │
└───────────────────┼─────────────────────────────────────────┘
                    │
┌───────────────────┴─────────────────────────────────────────┐
│                      AI Engine Layer                         │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ Embedding Engine │  │   LLM Engine     │                │
│  │  (Transformers)  │  │ (llama-cpp-py)   │                │
│  └──────────────────┘  └──────────────────┘                │
└──────────────────────────────────────────────────────────────┘
                    │
┌───────────────────┴─────────────────────────────────────────┐
│                     Data Layer                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │  Models  │  │  Recipes │  │ Workouts │  │ Progress │   │
│  │  (User,  │  │   Data   │  │   Data   │  │ Tracking │   │
│  │ Recipe,  │  │          │  │          │  │          │   │
│  │ Workout) │  │          │  │          │  │          │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└──────────────────────────────────────────────────────────────┘
                    │
┌───────────────────┴─────────────────────────────────────────┐
│                  Storage Layer (Local)                       │
│              JSON/CSV Files + Model Cache                    │
└──────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

1. **User Input Collection**: CLI/Web interface collects user preferences and stores them in UserProfile model
2. **Plan Generation**: Planner engines use AI engines to match and generate plans
3. **AI Processing**: Embedding engine performs semantic matching; LLM engine generates creative content
4. **Data Persistence**: All user data, plans, and progress stored locally in JSON format
5. **Progress Tracking**: User actions recorded and aggregated for adherence monitoring

## Components and Interfaces

### 1. Data Models (`nutrifit/models/`)

#### UserProfile
```python
class UserProfile:
    name: str
    age: int
    weight_kg: float
    height_cm: float
    dietary_preferences: list[DietaryPreference]
    fitness_goals: list[FitnessGoal]
    allergies: list[str]
    pantry_items: list[str]
    available_equipment: list[str]
    daily_calorie_target: int | None
    meals_per_day: int
    
    def to_dict() -> dict
    def from_dict(data: dict) -> UserProfile
```

#### Recipe
```python
class Recipe:
    id: str
    name: str
    description: str
    ingredients: list[Ingredient]
    instructions: list[str]
    nutrition: NutritionInfo
    prep_time_minutes: int
    cook_time_minutes: int
    servings: int
    meal_type: str
    tags: list[str]
    dietary_info: list[str]
    
    def get_searchable_text() -> str
    def matches_dietary_preferences(preferences: list[str]) -> bool
    def to_dict() -> dict
    def from_dict(data: dict) -> Recipe
```

#### Workout
```python
class Workout:
    id: str
    name: str
    description: str
    exercises: list[Exercise]
    workout_type: str
    difficulty: str
    duration_minutes: int
    target_muscle_groups: list[MuscleGroup]
    
    def get_searchable_text() -> str
    def is_doable_with_equipment(available: list[str]) -> bool
    def estimate_calories_burned(weight_kg: float) -> int
    def to_dict() -> dict
    def from_dict(data: dict) -> Workout
```

#### MealPlan & WorkoutPlan
```python
class MealPlan:
    id: str
    name: str
    start_date: date
    end_date: date
    daily_plans: list[DailyMealPlan]
    target_calories_per_day: int
    
    def to_dict() -> dict
    def from_dict(data: dict) -> MealPlan

class WorkoutPlan:
    id: str
    name: str
    start_date: date
    end_date: date
    daily_plans: list[DailyWorkoutPlan]
    workout_days_per_week: int
    
    def to_dict() -> dict
    def from_dict(data: dict) -> WorkoutPlan
```

### 2. AI Engine Layer

#### EmbeddingEngine (`nutrifit/engines/embedding_engine.py`)
```python
class EmbeddingEngine:
    def __init__(cache_dir: Path | None)
    def embed(text: str, use_cache: bool) -> np.ndarray
    def embed_batch(texts: list[str], use_cache: bool) -> np.ndarray
    def similarity(embedding1: np.ndarray, embedding2: np.ndarray) -> float
    def find_similar(query: str, items: list[str], top_k: int) -> list[tuple[int, str, float]]
    def clear_cache() -> None
```

**Implementation Details**:
- Primary: Uses sentence-transformers library with all-MiniLM-L6-v2 model (384-dimensional embeddings)
- Fallback: Simple TF-IDF-like bag-of-words approach if transformers unavailable
- Caching: Embeddings cached both in-memory and on disk (as .npy files) for performance
- Offline: Model downloaded once, then operates completely offline

#### LocalLLMEngine (`nutrifit/engines/llm_engine.py`)
```python
class LocalLLMEngine:
    def __init__(model_path: str | None, context_size: int, use_fallback: bool)
    def generate(prompt: str, max_tokens: int, temperature: float) -> str
    def suggest_meal(dietary_prefs: list[str], ingredients: list[str], meal_type: str, calorie_target: int) -> str
    def suggest_workout(fitness_goals: list[str], equipment: list[str], duration: int, difficulty: str) -> str
    def suggest_modification(original_item: str, modification_type: str, constraints: list[str]) -> str
    def is_model_loaded() -> bool
    def get_status() -> dict
```

**Implementation Details**:
- Primary: Uses llama-cpp-python to run GGUF format models (GPT4All, LLaMA, Mistral)
- Fallback: Template-based suggestion system with randomized responses
- Model Loading: Lazy loading with graceful degradation to fallback mode
- Context: Configurable context window (default 2048 tokens)

### 3. Planner Engines

#### MealPlannerEngine (`nutrifit/engines/meal_planner.py`)
```python
class MealPlannerEngine:
    def __init__(embedding_engine: EmbeddingEngine, llm_engine: LocalLLMEngine, recipes: list[Recipe])
    def find_matching_recipes(user: UserProfile, meal_type: str, query: str | None, top_k: int) -> list[tuple[Recipe, float]]
    def generate_daily_plan(user: UserProfile, plan_date: date, include_snacks: bool) -> DailyMealPlan
    def generate_weekly_plan(user: UserProfile, start_date: date | None, plan_name: str | None) -> MealPlan
    def get_meal_suggestion(user: UserProfile, meal_type: str) -> str
    def search_recipes(query: str, user: UserProfile | None, meal_type: str | None, top_k: int) -> list[tuple[Recipe, float]]
```

**Matching Algorithm**:
1. Filter recipes by dietary preferences and allergies
2. Filter by meal type
3. Score recipes based on:
   - Pantry ingredient overlap (40% weight)
   - Semantic similarity to query (60% weight)
4. Select recipes within calorie target range (±30%)
5. Avoid repetition within the same plan

#### WorkoutPlannerEngine (`nutrifit/engines/workout_planner.py`)
```python
class WorkoutPlannerEngine:
    def __init__(embedding_engine: EmbeddingEngine, llm_engine: LocalLLMEngine, workouts: list[Workout])
    def find_matching_workouts(user: UserProfile, workout_type: str | None, query: str | None, max_duration: int, top_k: int) -> list[tuple[Workout, float]]
    def generate_daily_plan(user: UserProfile, plan_date: date, day_number: int, max_duration: int) -> DailyWorkoutPlan
    def generate_weekly_plan(user: UserProfile, start_date: date | None, plan_name: str | None, workout_days_per_week: int) -> WorkoutPlan
    def get_workout_suggestion(user: UserProfile, duration_minutes: int) -> str
    def search_workouts(query: str, user: UserProfile | None, workout_type: str | None, max_duration: int, top_k: int) -> list[tuple[Workout, float]]
```

**Matching Algorithm**:
1. Map fitness goals to preferred workout types
2. Filter by available equipment
3. Filter by difficulty level (based on user profile)
4. Filter by duration constraints
5. Score workouts based on:
   - Target muscle group alignment (40% weight)
   - Semantic similarity to query (60% weight)
6. Implement weekly split (e.g., strength/cardio/rest rotation)

### 4. Utility Components

#### ShoppingListOptimizer (`nutrifit/utils/shopping_list.py`)
```python
class ShoppingListOptimizer:
    def generate_shopping_list(meal_plan: MealPlan, pantry_items: list[str]) -> ShoppingList
    def consolidate_ingredients(ingredients: list[Ingredient]) -> list[Ingredient]
    def categorize_ingredients(ingredients: list[Ingredient]) -> dict[str, list[Ingredient]]
    def optimize_for_cost(shopping_list: ShoppingList, price_data: dict | None) -> ShoppingList
```

**Optimization Strategy**:
1. Extract all ingredients from meal plan
2. Exclude items present in pantry inventory
3. Consolidate duplicate ingredients (sum quantities)
4. Categorize by food type (produce, proteins, grains, dairy, pantry)
5. Optional: Sort by store layout or cost optimization

#### StorageManager (`nutrifit/utils/storage.py`)
```python
class StorageManager:
    def __init__(storage_dir: Path)
    def save_user_profile(profile: UserProfile) -> None
    def load_user_profile(user_id: str) -> UserProfile | None
    def save_meal_plan(plan: MealPlan) -> None
    def load_meal_plan(plan_id: str) -> MealPlan | None
    def save_workout_plan(plan: WorkoutPlan) -> None
    def load_workout_plan(plan_id: str) -> WorkoutPlan | None
    def save_progress(progress: ProgressTracker) -> None
    def load_progress(user_id: str) -> ProgressTracker | None
    def list_plans(user_id: str, plan_type: str) -> list[dict]
```

**Storage Structure**:
```
~/.nutrifit/
├── users/
│   └── {user_id}.json
├── meal_plans/
│   └── {plan_id}.json
├── workout_plans/
│   └── {plan_id}.json
├── progress/
│   └── {user_id}.json
├── embeddings/
│   └── {hash}.npy
└── models/
    └── {model_name}.gguf
```

#### ProgressTracker (`nutrifit/models/progress.py`)
```python
class ProgressTracker:
    user_id: str
    meal_completions: list[MealCompletion]
    workout_completions: list[WorkoutCompletion]
    
    def record_meal(meal_id: str, date: date, calories: int, macros: dict) -> None
    def record_workout(workout_id: str, date: date, duration: int) -> None
    def get_weekly_summary(start_date: date) -> dict
    def calculate_adherence(start_date: date, end_date: date) -> float
    def to_dict() -> dict
    def from_dict(data: dict) -> ProgressTracker
```

### 5. User Interface Layer

#### CLI Interface (`nutrifit/cli.py`)
```python
def main() -> None
def get_user_inputs() -> UserProfile
def display_meal_plan(plan: MealPlan) -> None
def display_workout_plan(plan: WorkoutPlan) -> None
def display_shopping_list(shopping_list: ShoppingList) -> None
def display_progress(progress: ProgressTracker) -> None
def interactive_menu() -> None
```

**CLI Commands**:
- `nutrifit init` - Initialize user profile
- `nutrifit meal-plan [--days 7]` - Generate meal plan
- `nutrifit workout-plan [--days 7]` - Generate workout plan
- `nutrifit shopping-list` - Generate shopping list from current meal plan
- `nutrifit track meal <meal_id>` - Mark meal as completed
- `nutrifit track workout <workout_id>` - Mark workout as completed
- `nutrifit progress` - View progress summary
- `nutrifit search recipes <query>` - Search recipes
- `nutrifit search workouts <query>` - Search workouts

## Data Models

### Core Data Structures

#### NutritionInfo
```python
@dataclass
class NutritionInfo:
    calories: int
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sugar_g: float
    sodium_mg: float
```

#### Ingredient
```python
@dataclass
class Ingredient:
    name: str
    quantity: float
    unit: str
    optional: bool
```

#### Exercise
```python
@dataclass
class Exercise:
    id: str
    name: str
    description: str
    muscle_groups: list[MuscleGroup]
    exercise_type: ExerciseType
    equipment_needed: list[Equipment]
    sets: int
    reps: int | None
    duration_seconds: int | None
    rest_seconds: int
    difficulty: str
    instructions: list[str]
    calories_per_minute: float
```

#### DailyMealPlan
```python
@dataclass
class DailyMealPlan:
    date: date
    breakfast: Recipe | None
    lunch: Recipe | None
    dinner: Recipe | None
    snacks: list[Recipe]
    
    def total_calories() -> int
    def total_macros() -> dict[str, float]
```

#### DailyWorkoutPlan
```python
@dataclass
class DailyWorkoutPlan:
    date: date
    workouts: list[Workout]
    is_rest_day: bool
    notes: str
    
    def total_duration() -> int
    def estimated_calories_burned(weight_kg: float) -> int
```

### Enumerations

```python
class DietaryPreference(Enum):
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
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    MAINTENANCE = "maintenance"
    ENDURANCE = "endurance"
    STRENGTH = "strength"
    FLEXIBILITY = "flexibility"
    GENERAL_FITNESS = "general_fitness"

class MuscleGroup(Enum):
    CHEST = "chest"
    BACK = "back"
    SHOULDERS = "shoulders"
    BICEPS = "biceps"
    TRICEPS = "triceps"
    CORE = "core"
    QUADRICEPS = "quadriceps"
    HAMSTRINGS = "hamstrings"
    GLUTES = "glutes"
    CALVES = "calves"
    FULL_BODY = "full_body"
    CARDIO = "cardio"
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Dietary Preference Persistence Round-Trip
*For any* user profile with dietary preferences, saving the profile to storage then loading it back should produce an equivalent profile with the same dietary preferences.
**Validates: Requirements 1.1, 1.3**

### Property 2: Meal Plans Respect Dietary Preferences
*For any* user profile with dietary preferences and any generated meal plan, all recipes in the meal plan should match the user's dietary preferences.
**Validates: Requirements 1.4**

### Property 3: Fitness Goal Caloric Adjustment
*For any* user profile, when the fitness goal is set to weight loss, the calculated caloric target should be less than the maintenance baseline; when set to muscle gain, it should be greater than the baseline; when set to maintenance, it should equal the baseline.
**Validates: Requirements 2.2**

### Property 4: Fitness Goal Macro-Nutrient Adjustment
*For any* user profile, different fitness goals should produce different macro-nutrient ratios (protein, carbohydrates, fats).
**Validates: Requirements 2.3**

### Property 5: Meal Plans Align with Fitness Goals
*For any* user profile with a fitness goal and any generated meal plan, the meal plan's caloric and macro-nutrient targets should align with the fitness goal's requirements.
**Validates: Requirements 2.4**

### Property 6: Ingredient Inventory Persistence Round-Trip
*For any* list of pantry ingredients, saving the inventory to storage then loading it back should produce the same list.
**Validates: Requirements 3.1**

### Property 7: Pantry Ingredient Prioritization
*For any* two recipes where one uses more pantry ingredients than the other, the recipe with more pantry ingredients should score higher in the matching algorithm.
**Validates: Requirements 3.2**

### Property 8: Ingredient Consumption Tracking
*For any* meal plan and pantry inventory, after generating the meal plan, the pantry inventory should be reduced by the ingredients used in the plan.
**Validates: Requirements 3.3**

### Property 9: Pantry Inventory Add/Remove Operations
*For any* pantry inventory, adding an item should increase the inventory count, and removing an item should decrease the inventory count.
**Validates: Requirements 3.4**

### Property 10: Equipment Compatibility in Workout Plans
*For any* user profile with specified available equipment and any generated workout plan, all exercises in the plan should require only the equipment available to the user.
**Validates: Requirements 4.4**

### Property 11: Meal Plan Duration Correctness
*For any* meal plan generation request with a specified duration, the generated plan should contain exactly the requested number of days (1 for daily, 7 for weekly).
**Validates: Requirements 5.1**

### Property 12: Daily Caloric Target Adherence
*For any* generated meal plan and user profile, the total daily calories in each day of the plan should be within ±10% of the user's daily caloric target.
**Validates: Requirements 5.4**

### Property 13: Macro-Nutrient Ratio Adherence
*For any* generated meal plan and user profile with a fitness goal, the macro-nutrient ratios (protein, carbs, fats) should be within ±15% of the goal's target ratios.
**Validates: Requirements 5.5**

### Property 14: Workout Plan Duration Correctness
*For any* workout plan generation request with a specified duration, the generated plan should contain exactly the requested number of days.
**Validates: Requirements 6.1**

### Property 15: Exercise Fitness Level and Equipment Match
*For any* user profile with a fitness level and available equipment, and any generated workout plan, all exercises should match the user's fitness level and require only available equipment.
**Validates: Requirements 6.3**

### Property 16: Exercise Completeness
*For any* generated workout plan, all exercises should have duration, intensity level, and rest periods specified.
**Validates: Requirements 6.4**

### Property 17: Workout Intensity Balance
*For any* weekly workout plan, high-intensity workouts should not be scheduled on consecutive days.
**Validates: Requirements 6.5**

### Property 18: Shopping List Ingredient Completeness
*For any* meal plan, the generated shopping list should contain all ingredients required by all recipes in the meal plan.
**Validates: Requirements 7.1**

### Property 19: Shopping List Pantry Exclusion
*For any* shopping list and pantry inventory, no ingredient in the shopping list should be present in the pantry inventory.
**Validates: Requirements 7.2**

### Property 20: Shopping List Ingredient Consolidation
*For any* meal plan where an ingredient appears in multiple recipes, that ingredient should appear only once in the shopping list with the summed quantity.
**Validates: Requirements 7.3**

### Property 21: Shopping List Categorization
*For any* generated shopping list, all items should have a category assigned (produce, proteins, grains, dairy, or pantry staples).
**Validates: Requirements 7.4**

### Property 22: Meal Completion Recording
*For any* meal marked as consumed, the progress tracker should contain that meal's caloric and macro-nutrient data.
**Validates: Requirements 8.1**

### Property 23: Workout Completion Recording
*For any* workout marked as completed, the progress tracker should contain that workout's completion date and duration.
**Validates: Requirements 8.2**

### Property 24: Weekly Progress Aggregation
*For any* set of completed meals and workouts within a week, the weekly summary should correctly sum the total calories consumed and total workout time.
**Validates: Requirements 8.3**

### Property 25: Adherence Percentage Calculation
*For any* set of planned and completed meals and workouts, the adherence percentage should equal (completed / planned) × 100.
**Validates: Requirements 8.4**

### Property 26: Progress Data Persistence Round-Trip
*For any* progress data, saving it to storage then loading it back should produce equivalent data.
**Validates: Requirements 8.5**

### Property 27: Input Validation Error Messages
*For any* invalid user input, the system should reject the input and provide a clear error message.
**Validates: Requirements 10.2**

### Property 28: Meal Plan Display Completeness
*For any* generated meal plan, the formatted display output should contain meal names, ingredients, and nutritional information for all meals.
**Validates: Requirements 10.3**

### Property 29: Workout Plan Display Completeness
*For any* generated workout plan, the formatted display output should contain exercise names, duration, sets, reps, and intensity for all exercises.
**Validates: Requirements 10.4**

### Property 30: Data Storage Format Validity
*For any* user data saved to storage, the saved files should be valid JSON or CSV format.
**Validates: Requirements 12.1**

### Property 31: Data Structure Validation Before Persistence
*For any* data structure being saved, invalid structures should be rejected before persisting to disk.
**Validates: Requirements 12.4**

## Error Handling

### Error Categories

#### 1. Input Validation Errors
- **Invalid Dietary Preferences**: User provides unrecognized dietary preference
  - Response: Return error with list of valid preferences
- **Invalid Fitness Goal**: User provides unrecognized fitness goal
  - Response: Return error with list of valid goals
- **Invalid Equipment**: User provides unrecognized equipment type
  - Response: Return error with list of valid equipment types
- **Invalid Duration**: User provides negative or zero duration
  - Response: Return error indicating duration must be positive

#### 2. Data Persistence Errors
- **File Not Found**: Requested user profile or plan doesn't exist
  - Response: Return None and log warning, allow user to create new profile
- **Corrupted Data**: JSON file is malformed or incomplete
  - Response: Log error, return None, prompt user to reinitialize
- **Permission Denied**: Cannot write to storage directory
  - Response: Return error with suggestion to check permissions
- **Disk Full**: Cannot save data due to insufficient space
  - Response: Return error indicating storage issue

#### 3. AI Engine Errors
- **Model Not Found**: Embedding or LLM model files missing
  - Response: Fall back to simpler algorithms (TF-IDF for embeddings, templates for LLM)
- **Model Loading Failed**: Model file corrupted or incompatible
  - Response: Fall back to simpler algorithms, log warning
- **Inference Error**: Error during model inference
  - Response: Retry once, then fall back to simpler algorithms

#### 4. Plan Generation Errors
- **No Matching Recipes**: Cannot find recipes matching user constraints
  - Response: Relax constraints progressively (first dietary, then pantry, then calorie range)
- **No Matching Workouts**: Cannot find workouts matching user constraints
  - Response: Relax constraints progressively (first equipment, then duration, then difficulty)
- **Insufficient Data**: Recipe or workout database is empty
  - Response: Return error indicating system needs to be initialized with data

#### 5. Progress Tracking Errors
- **Invalid Meal ID**: User tries to mark non-existent meal as completed
  - Response: Return error indicating meal not found in current plan
- **Invalid Workout ID**: User tries to mark non-existent workout as completed
  - Response: Return error indicating workout not found in current plan
- **Date Out of Range**: User tries to track progress for date outside plan range
  - Response: Return error indicating date must be within plan period

### Error Handling Strategy

1. **Graceful Degradation**: System should continue operating with reduced functionality rather than crashing
2. **Clear Error Messages**: All errors should include actionable information for the user
3. **Logging**: All errors logged to `~/.nutrifit/logs/nutrifit.log` with timestamps
4. **Retry Logic**: Transient errors (file I/O, model inference) retried once before failing
5. **Fallback Mechanisms**: AI engines have fallback implementations when models unavailable
6. **Validation**: All user inputs validated before processing
7. **Data Integrity**: All data validated before persistence to prevent corruption

## Testing Strategy

The NutriFit AI Assistant will employ a comprehensive testing strategy combining unit tests and property-based tests to ensure correctness and reliability.

### Property-Based Testing

**Framework**: Hypothesis (Python)

Property-based tests will verify universal properties that should hold across all valid inputs. Each property test will run a minimum of 100 iterations with randomly generated inputs.

**Test Configuration**:
```python
from hypothesis import given, settings
import hypothesis.strategies as st

@settings(max_examples=100)
@given(user_profile=st.builds(UserProfile, ...))
def test_property_X(user_profile):
    # Test implementation
    pass
```

**Property Test Coverage**:
- Each correctness property from the design document will be implemented as a property-based test
- Tests will be tagged with comments referencing the specific property: `# Feature: nutrifit-ai-assistant, Property X: <property_text>`
- Generators will be created for all data models (UserProfile, Recipe, Workout, etc.)
- Edge cases (empty lists, boundary values, special characters) will be handled by generators

**Key Property Tests**:
1. **Persistence Round-Trips** (Properties 1, 6, 26): Serialize/deserialize operations preserve data
2. **Filtering Logic** (Properties 2, 10, 15): Generated plans respect user constraints
3. **Calculation Correctness** (Properties 3, 4, 12, 13, 24, 25): Numeric calculations are accurate
4. **Data Completeness** (Properties 16, 18, 21, 28, 29): Generated outputs contain all required fields
5. **Business Rules** (Properties 7, 17, 19, 20): Domain-specific rules are enforced

### Unit Testing

**Framework**: pytest

Unit tests will verify specific examples, edge cases, and integration points between components.

**Unit Test Coverage**:
- **Model Tests**: Serialization, validation, helper methods
- **Engine Tests**: Embedding similarity, LLM fallback behavior, caching
- **Planner Tests**: Recipe/workout selection, scoring algorithms, plan generation
- **Utility Tests**: Shopping list consolidation, storage operations, progress calculations
- **CLI Tests**: Command parsing, output formatting, error handling

**Example Unit Tests**:
```python
def test_user_profile_calorie_calculation():
    """Test that BMR calculation produces expected results for known inputs."""
    profile = UserProfile(name="Test", age=30, weight_kg=70, height_cm=175, ...)
    assert 1500 <= profile.daily_calorie_target <= 2500

def test_embedding_engine_fallback():
    """Test that embedding engine falls back to TF-IDF when transformers unavailable."""
    engine = EmbeddingEngine()
    embedding = engine.embed("test text")
    assert embedding.shape == (384,)

def test_shopping_list_consolidation():
    """Test that duplicate ingredients are consolidated with summed quantities."""
    ingredients = [
        Ingredient("flour", 2, "cups"),
        Ingredient("flour", 1, "cup"),
    ]
    consolidated = consolidate_ingredients(ingredients)
    assert len(consolidated) == 1
    assert consolidated[0].quantity == 3
```

### Integration Testing

Integration tests will verify end-to-end workflows:
- Complete meal plan generation from user input to display
- Complete workout plan generation from user input to display
- Shopping list generation from meal plan
- Progress tracking workflow (mark meals/workouts, view summary)
- Offline operation (no network calls during plan generation)

### Test Data

**Sample Data**:
- 50+ sample recipes covering various dietary preferences and meal types
- 30+ sample workouts covering various equipment and difficulty levels
- Pre-generated embeddings for sample data to speed up tests

**Test Fixtures**:
- Sample user profiles with various combinations of preferences
- Pre-generated meal and workout plans for testing display and tracking
- Mock storage directories for testing persistence

### Continuous Testing

- All tests run on every commit
- Property-based tests use fixed random seeds for reproducibility
- Test coverage target: 80% for core business logic
- Performance benchmarks for plan generation (target: <5 seconds for weekly plan)

### Manual Testing Checklist

- [ ] Install on fresh system without models (verify fallback mode works)
- [ ] Download and install models (verify offline operation)
- [ ] Create user profile with various dietary preferences
- [ ] Generate meal plans for different durations and goals
- [ ] Generate workout plans for different equipment and goals
- [ ] Generate shopping lists and verify accuracy
- [ ] Track meals and workouts, verify progress calculations
- [ ] Test CLI commands and help text
- [ ] Verify data persistence across sessions
- [ ] Test error handling for invalid inputs and corrupted data


## Chatbot Engine

### Overview

The Chatbot Engine provides a conversational AI interface that allows users to interact with NutriFit using natural language. It integrates with the Meal Planner, Workout Planner, and LLM Engine to provide an intuitive, chat-based experience for creating and modifying plans.

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User (Web Interface)                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Chatbot Engine                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Intent Detection                                     │  │
│  │  - Meal plan requests                                 │  │
│  │  - Workout plan requests                              │  │
│  │  - Modifications                                      │  │
│  │  - Questions (nutrition/fitness)                      │  │
│  │  - Profile updates                                    │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Conversation State                                   │  │
│  │  - History (user/assistant messages)                  │  │
│  │  - Context (current meal/workout plans)               │  │
│  │  - User profile                                       │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────┬──────────────┬──────────────┬─────────────────┘
             │              │              │
             ▼              ▼              ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │   Meal     │  │  Workout   │  │    LLM     │
    │  Planner   │  │  Planner   │  │   Engine   │
    └────────────┘  └────────────┘  └────────────┘
```

### Component Interface

#### ChatbotEngine Class

```python
class ChatbotEngine:
    """Conversational AI chatbot for personalized nutrition and workout planning."""
    
    def __init__(
        self,
        llm_engine: LocalLLMEngine | None = None,
        meal_planner: MealPlannerEngine | None = None,
        workout_planner: WorkoutPlannerEngine | None = None,
    )
    
    def chat(
        self,
        user_message: str,
        user_profile: UserProfile | None = None
    ) -> str
    
    def reset_conversation() -> None
    def get_conversation_history() -> list[dict[str, str]]
    def export_context() -> dict[str, Any]
```

### Intent Detection

The chatbot uses keyword-based intent detection to classify user messages:

**Intent Types:**
1. **meal_plan_request**: User wants to create a meal plan
   - Keywords: "meal plan", "food", "recipe", "eat" + "create", "generate", "make"
   
2. **workout_plan_request**: User wants to create a workout plan
   - Keywords: "workout", "exercise", "training" + "create", "generate", "make"
   
3. **modify_meal**: User wants to change a meal
   - Keywords: "change", "modify", "replace", "swap" + meal keywords
   
4. **modify_workout**: User wants to change a workout
   - Keywords: "change", "modify", "replace", "swap" + workout keywords
   
5. **nutrition_question**: User has a nutrition question
   - Keywords: "what", "how", "why" + "calorie", "protein", "carb", "nutrition"
   
6. **workout_question**: User has a fitness question
   - Keywords: "what", "how", "why" + "workout", "exercise", "training"
   
7. **profile_update**: User is providing profile information
   - Keywords: "i am", "i'm", "my goal", "i want", "allergic"
   
8. **general**: General conversation or greeting

### Response Generation

#### Meal Plan Request Flow:
1. Check if user profile exists
2. If no profile: Request profile information
3. If profile exists: Generate meal plan using MealPlannerEngine
4. Store plan in context
5. Return formatted response with:
   - Daily calorie targets
   - Macro breakdown
   - Day 1 preview
   - Offer to show more or modify

#### Workout Plan Request Flow:
1. Check if user profile exists
2. If no profile: Request profile information
3. If profile exists: Generate workout plan using WorkoutPlannerEngine
4. Store plan in context
5. Return formatted response with:
   - Weekly schedule
   - Workout days per week
   - Equipment used
   - Offer to show details or modify

#### Modification Flow:
1. Check if plan exists in context
2. If no plan: Offer to create one
3. If plan exists: Use LLM to generate alternative suggestion
4. Return suggestion with option to apply

#### Question Flow:
1. Use LLM to generate response (if available)
2. Fall back to template-based responses
3. Personalize based on user profile if available

### Conversation State

The chatbot maintains state across messages:

```python
{
    "conversation_history": [
        {"role": "user", "content": "Create a meal plan"},
        {"role": "assistant", "content": "Great! I've created..."}
    ],
    "current_context": {
        "meal_plan": MealPlan(...),
        "workout_plan": WorkoutPlan(...)
    },
    "user_profile": UserProfile(...)
}
```

### API Endpoints

#### POST /api/chatbot/chat
Send a message and receive a response.

**Request:**
```json
{
    "message": "Create a weekly meal plan for me",
    "user_id": "default"
}
```

**Response:**
```json
{
    "response": "Great! I've created a 7-day meal plan for you!...",
    "conversation_id": "default"
}
```

#### GET /api/chatbot/history
Get conversation history.

**Response:**
```json
{
    "history": [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
}
```

#### POST /api/chatbot/reset
Reset conversation.

**Response:**
```json
{
    "message": "Conversation reset successfully"
}
```

#### GET /api/chatbot/context
Get current context (plans, etc.).

**Response:**
```json
{
    "context": {
        "meal_plan": {...},
        "workout_plan": {...}
    }
}
```

### Web Interface

The chatbot is accessible through a dedicated tab in the web interface:

**Features:**
- Chat message display (user/assistant bubbles)
- Text input with send button
- Quick action buttons for common requests
- Typing indicator during response generation
- Markdown formatting support
- Auto-scroll to latest message

**UI Components:**
- `#chatMessages`: Scrollable message container
- `#chatForm`: Message input form
- `#chatInput`: Text input field
- Quick action buttons for common tasks

### Example Conversations

#### Example 1: Creating a Meal Plan
```
User: "Create a weekly meal plan for me"

B
ot: "Great! I've created a 7-day meal plan for you!

📊 **Your Daily Targets:**
- Calories: 2100 kcal
- Protein: 157g
- Carbs: 210g
- Fat: 70g

**Day 1 Preview (2024-12-02):**
🍳 Breakfast: Greek Yogurt Parfait (350 kcal)
🥗 Lunch: Grilled Chicken Salad (450 kcal)
🍽️ Dinner: Salmon with Quinoa (550 kcal)

Total: 1350 kcal

Would you like to see the full plan, or would you like me to change anything?"
```

#### Example 2: Modifying a Meal
```
User: "Change my breakfast to something high-protein"

Bot: "I can help you change your breakfast! Here's an alternative suggestion:

Try a protein-rich scramble or smoothie using eggs, Greek yogurt, and protein powder. This balanced meal provides sustained energy for your morning.

Would you like me to update your plan with this, or would you like a different suggestion?"
```

#### Example 3: Nutrition Question
```
User: "How much protein do I need?"

Bot: "Based on your profile, you should aim for approximately 157g of protein per day. This is calculated for your muscle gain goal.

Good protein sources include:
- Lean meats (chicken, turkey, fish)
- Eggs and dairy
- Legumes (beans, lentils)
- Tofu and tempeh
- Nuts and seeds

For muscle gain, aim for 1.6-2.2g per kg of body weight."
```

#### Example 4: Workout Plan Request
```
User: "Generate a 4-day workout plan"

Bot: "Perfect! I've created a 4-day per week workout plan for you!

🎯 **Your Goals:** muscle_gain
🏋️ **Equipment:** dumbbells, resistance bands

**Weekly Schedule:**
Mon: 💪 Full Body Strength (45 min)
Tue: 😴 Rest Day
Wed: 💪 Upper Body Focus (50 min)
Thu: 😴 Rest Day
Fri: 💪 Lower Body Focus (45 min)
Sat: 💪 HIIT Circuit (30 min)
Sun: 😴 Rest Day

Would you like details on any specific day, or would you like me to adjust anything?"
```

### Error Handling

The chatbot handles various error scenarios gracefully:

1. **No User Profile**: Requests profile information before generating plans
2. **No Planners Available**: Provides information about what can be created
3. **LLM Unavailable**: Falls back to template-based responses
4. **Invalid Requests**: Asks clarifying questions
5. **API Errors**: Returns user-friendly error messages

### Benefits

1. **Natural Interaction**: Users describe what they want in plain language
2. **Lower Barrier to Entry**: No need to navigate complex forms
3. **Contextual**: Remembers conversation and can refine plans iteratively
4. **Educational**: Answers questions and provides explanations
5. **Flexible**: Handles various phrasings and requests
6. **Personalized**: Responses tailored to user profile and goals

### Future Enhancements

Potential improvements for the chatbot:

1. **Voice Input**: Add speech-to-text for hands-free interaction
2. **Image Support**: Allow users to upload food/exercise photos
3. **Multi-turn Planning**: More sophisticated conversation flows
4. **Sentiment Analysis**: Detect user satisfaction and adjust responses
5. **Proactive Suggestions**: Chatbot initiates conversations based on user behavior
6. **Chat History Persistence**: Save conversations across sessions
7. **Multi-language Support**: Translate conversations to other languages
8. **Integration with Calendar**: Schedule meals and workouts automatically
