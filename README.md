# NutriFit 🏋️‍♀️🥗

NutriFit is an AI-powered **offline** health assistant that generates personalized meal plans and workout routines based on user dietary preferences, fitness goals, and available ingredients or equipment. Users can receive daily or weekly recommendations, optimize shopping lists, and track progress—all without requiring cloud services or API keys.

## ✨ Features

- **Personalized Meal Plans**: Generate daily or weekly meal plans based on your dietary preferences, allergies, and pantry items
- **Custom Workout Routines**: Get workout plans tailored to your fitness goals and available equipment
- **Semantic Recipe/Workout Search**: Find recipes and workouts using natural language queries with AI-powered matching
- **Shopping List Optimization**: Automatically generate and optimize shopping lists from meal plans
- **Progress Tracking**: Track weight, calories, workouts, and more over time
- **100% Offline**: Works completely offline using local AI models—no cloud or API keys required
- **Modular & Lightweight**: Minimal dependencies with optional AI enhancements

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/tayxuenye/NutriFit.git
cd NutriFit

# Install the package
pip install -e .

# Optional: Install with AI embeddings support
pip install -e ".[embeddings]"

# Optional: Install with local LLM support
pip install -e ".[llm]"

# Or install everything
pip install -e ".[all]"
```

### Basic Usage

```bash
# Create your profile
nutrifit profile create

# Generate a daily meal plan
nutrifit meal daily

# Generate a weekly meal plan
nutrifit meal weekly

# Search for recipes
nutrifit meal search --query "high protein vegetarian"

# Generate a weekly workout plan
nutrifit workout weekly

# Generate a shopping list
nutrifit shopping generate

# Track your progress
nutrifit progress log --weight 70 --calories 2000 --workouts 1

# View progress summary
nutrifit progress summary
```

## 📖 CLI Commands

### Profile Management

```bash
# Show current profile
nutrifit profile show

# Create a new profile (interactive)
nutrifit profile create

# Update pantry items
nutrifit profile update-pantry --items "rice,beans,chicken"

# Update available equipment
nutrifit profile update-equipment --items "dumbbells,barbell,bench"
```

### Meal Planning

```bash
# Generate today's meal plan
nutrifit meal daily

# Generate a weekly meal plan (saved automatically)
nutrifit meal weekly

# Search for recipes
nutrifit meal search --query "quick healthy dinner"

# Search with filters
nutrifit meal search --query "breakfast" --meal-type breakfast --limit 10

# Get AI meal suggestion
nutrifit meal suggest --meal-type lunch
```

### Workout Planning

```bash
# Generate today's workout
nutrifit workout daily

# Generate a weekly workout plan
nutrifit workout weekly --days 4

# Search for workouts
nutrifit workout search --query "upper body strength"

# Filter by workout type
nutrifit workout search --workout-type hiit --limit 5

# Get AI workout suggestion
nutrifit workout suggest --duration 30
```

### Shopping Lists

```bash
# Generate shopping list from latest meal plan
nutrifit shopping generate

# Generate optimized shopping list
nutrifit shopping generate --optimize

# Generate from specific plan
nutrifit shopping generate --plan-id mp_abc123
```

### Progress Tracking

```bash
# Log daily progress
nutrifit progress log --weight 70.5 --calories 1800 --workouts 1

# Log with mood and energy
nutrifit progress log --weight 70 --mood 8 --energy 7

# View summary
nutrifit progress summary

# View history
nutrifit progress history
```

## 🐍 Python API

```python
from nutrifit.models.user import UserProfile, DietaryPreference, FitnessGoal
from nutrifit.engines.meal_planner import MealPlannerEngine
from nutrifit.engines.workout_planner import WorkoutPlannerEngine
from nutrifit.utils.shopping_list import ShoppingListOptimizer

# Create a user profile
profile = UserProfile(
    name="John",
    age=30,
    weight_kg=75.0,
    height_cm=180.0,
    dietary_preferences=[DietaryPreference.HIGH_PROTEIN],
    fitness_goals=[FitnessGoal.MUSCLE_GAIN],
    pantry_items=["chicken", "rice", "vegetables"],
    available_equipment=["dumbbells", "bench"],
)

# Generate a weekly meal plan
meal_planner = MealPlannerEngine()
meal_plan = meal_planner.generate_weekly_plan(profile)

print(f"Generated meal plan: {meal_plan.name}")
for day in meal_plan.daily_plans:
    print(f"{day.date}: {day.breakfast.name if day.breakfast else 'No breakfast'}")

# Generate a workout plan
workout_planner = WorkoutPlannerEngine()
workout_plan = workout_planner.generate_weekly_plan(profile)

# Generate shopping list
optimizer = ShoppingListOptimizer()
shopping_list = optimizer.generate_from_meal_plan(
    meal_plan,
    pantry_items=profile.pantry_items
)

# Search for recipes
results = meal_planner.search_recipes("quick healthy breakfast")
for recipe, score in results[:5]:
    print(f"{recipe.name}: {score:.2f}")
```

## 🏗️ Architecture

```
nutrifit/
├── models/           # Data models (User, Recipe, Workout, Plan, Progress)
├── data/            # Sample recipe and workout databases
├── engines/         # AI engines (Embedding, LLM, MealPlanner, WorkoutPlanner)
├── utils/           # Utilities (ShoppingList, Storage)
└── cli.py           # Command-line interface
```

### Key Components

- **EmbeddingEngine**: Uses sentence-transformers for semantic search (falls back to simple matching if not installed)
- **LocalLLMEngine**: Optional local LLM for creative suggestions (llama-cpp-python)
- **MealPlannerEngine**: Generates meal plans based on preferences and nutritional goals
- **WorkoutPlannerEngine**: Creates workout routines based on fitness goals and equipment
- **ShoppingListOptimizer**: Consolidates and categorizes shopping lists
- **DataStorage**: JSON-based local storage for offline data persistence

## 📊 Supported Features

### Dietary Preferences
- Vegetarian, Vegan, Pescatarian
- Keto, Paleo, Low-Carb
- Gluten-Free, Dairy-Free
- High-Protein

### Fitness Goals
- Weight Loss, Muscle Gain
- Strength, Endurance, Flexibility
- General Fitness, Maintenance

### Workout Types
- Strength Training
- HIIT (High-Intensity Interval Training)
- Cardio
- Flexibility/Yoga
- Bodyweight/Home Workouts

## 🧪 Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=nutrifit
```

## 🤖 AI Configuration

### Embeddings (Recommended)

Install sentence-transformers for improved recipe/workout matching:

```bash
pip install sentence-transformers
```

The system uses the `all-MiniLM-L6-v2` model by default, which is lightweight (~80MB) and works well offline.

### Local LLM (Optional)

For creative AI suggestions, you can use a local LLM:

```bash
pip install llama-cpp-python
```

Then download a GGUF model and configure:

```python
from nutrifit.engines.llm_engine import LocalLLMEngine

llm = LocalLLMEngine(model_path="/path/to/model.gguf")
suggestion = llm.suggest_meal(
    dietary_preferences=["vegetarian"],
    available_ingredients=["rice", "beans"],
    meal_type="dinner",
    calorie_target=500,
)
```

**Note**: Without a local LLM, the system uses template-based suggestions that still provide helpful recommendations.

## 📁 Data Storage

All data is stored locally in `~/.nutrifit/`:

```
~/.nutrifit/
├── data/
│   ├── users/          # User profiles
│   ├── meal_plans/     # Saved meal plans
│   ├── workout_plans/  # Saved workout plans
│   └── progress/       # Progress tracking data
└── embeddings/         # Cached embeddings
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Recipe and workout databases are for demonstration purposes
- Uses sentence-transformers for semantic search
- Designed for complete offline functionality
