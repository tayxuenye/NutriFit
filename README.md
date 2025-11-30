# NutriFit

NutriFit is an AI-powered **offline** mobile health assistant that generates personalized meal plans and workout routines based on user dietary preferences, fitness goals, and available ingredients or equipment. Users can receive weekly recommendations, optimize shopping lists, and track progress—all without requiring cloud services or API keys.

## ✨ Features

- **Personalized Meal Plans**: Generate weekly meal plans based on your dietary preferences, allergies, and pantry items
- **Custom Workout Routines**: Get weekly workout plans tailored to your fitness goals and available equipment
- **Semantic Recipe/Workout Search**: Find recipes and workouts using natural language queries with AI-powered matching
- **Auto-Generated Shopping Lists**: Automatically generate and update shopping lists from meal plans, organized by week
- **Progress Tracking**: Track weight, calories, workouts, and more over time
- **100% Offline**: Works completely offline using local AI models—no cloud or API keys required
- **Mobile-First Web Interface**: Beautiful, responsive UI optimized for mobile devices
- **Week-Based Planning**: Navigate between weeks to view and generate plans for any time period
- **Manual Editing**: Edit meal and workout plans directly in the app
- **Modular & Lightweight**: Minimal dependencies with optional AI enhancements

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
# Install the package and required dependencies
pip install -e .

# That's it! The app will automatically install transformers and GPT-2 on first run.
```

### Step 2: Run the Web App

```bash
# Start the web server
python -m nutrifit.web
```

The server will start on `http://localhost:5000` (or `http://0.0.0.0:5000`).

### Step 3: Access from Your Phone

1. **Find your computer's IP address:**
   - Windows: Open Command Prompt and run `ipconfig` (look for IPv4 Address)
   - Mac/Linux: Run `ifconfig` or `ip addr`

2. **On your phone's browser**, go to:
   ```
   http://YOUR_IP_ADDRESS:5000
   ```
   For example: `http://192.168.1.100:5000`

3. **Or use localhost** if testing on the same device:
   ```
   http://localhost:5000
   ```

**Note:** On first run, the app will automatically download GPT-2 (~500MB). This only happens once!

### Web Interface Features

- **Profile Management**: Create and update your profile with dietary preferences, fitness goals, allergies, and equipment
- **Meal Planning**: Generate weekly meal plans with week navigation. Edit meals directly in the app
- **Workout Planning**: Get personalized weekly workout routines. Edit workouts or mark rest days
- **Shopping Lists**: Automatically generated and updated shopping lists organized by week
- **Progress Tracking**: Log your daily progress and view summaries
- **Meal Instructions**: View detailed cooking instructions for each meal
- **Workout Details**: See detailed exercise information including sets, reps, and rest periods

## 📖 API Usage (For Developers)

You can also use NutriFit programmatically:

```python
from nutrifit.api import generate_meal_plan, generate_workout_plan, optimize_shopping_list
from nutrifit.models.user import UserProfile, DietaryPreference, FitnessGoal

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
meal_plan = generate_meal_plan(profile, duration_days=7)

# Generate a workout plan
workout_plan = generate_workout_plan(profile, duration_days=7)

# Generate shopping list
shopping_list = optimize_shopping_list(meal_plan, user=profile)
```

### Web API Endpoints

The web interface exposes RESTful API endpoints:

- `GET /api/profile` - Get user profile
- `POST /api/profile` - Update user profile
- `POST /api/meal-plan/weekly` - Generate weekly meal plan
- `GET /api/meal-plans` - List all meal plans
- `GET /api/meal-plan/<id>` - Get specific meal plan
- `PUT /api/meal-plan/<id>` - Update meal plan entry
- `POST /api/workout-plan/weekly` - Generate weekly workout plan
- `GET /api/workout-plans` - List all workout plans
- `GET /api/workout-plan/<id>` - Get specific workout plan
- `PUT /api/workout-plan/<id>` - Update workout plan entry
- `POST /api/shopping-list` - Generate shopping list
- `POST /api/progress` - Log progress
- `GET /api/progress/summary` - Get progress summary

## 🛠️ Tech Stack

### Backend
- **Python 3.10+** - Core programming language
- **Flask** - Web framework for RESTful API and web interface
- **NumPy** - Numerical operations and data processing
- **sentence-transformers** (optional) - Semantic search and embeddings
- **transformers + PyTorch** (optional) - Local LLM support (GPT-2)
- **llama-cpp-python** (optional) - Efficient GGUF model inference

### Frontend
- **HTML5** - Structure and semantic markup
- **CSS3** - Styling with CSS variables and responsive design
- **Vanilla JavaScript** - Client-side interactivity and API communication
- **Mobile-First Design** - Responsive UI optimized for mobile devices

### Data Storage
- **JSON** - Local file-based storage for profiles, plans, and progress
- **File System** - Data stored in `~/.nutrifit/data/` directory

### AI/ML
- **Embedding Engine** - Semantic similarity search for recipes and workouts
- **Local LLM** - GPT-2 or GGUF models for creative meal/workout suggestions
- **Fallback System** - Template-based suggestions when AI models unavailable

### Architecture Patterns
- **RESTful API** - Clean separation between frontend and backend
- **Modular Design** - Separate route handlers for each feature
- **MVC-like Structure** - Models, views (templates), and controllers (routes)

## 🏗️ Architecture

```
nutrifit/
├── models/              # Data models (User, Recipe, Workout, Plan, Progress)
├── data/               # Sample recipe and workout databases
├── engines/            # AI engines (Embedding, LLM, MealPlanner, WorkoutPlanner)
├── utils/              # Utilities (ShoppingList, Storage)
├── templates/          # Web interface HTML templates
│   └── index.html      # Main mobile-friendly UI
├── web/                # Web interface (Flask application)
│   ├── __init__.py     # Flask app initialization
│   ├── __main__.py     # Entry point for `python -m nutrifit.web`
│   ├── middleware.py   # Request logging and CORS handling
│   ├── utils.py        # Web utilities (profile management)
│   └── routes/         # API route handlers
│       ├── __init__.py # Route registration
│       ├── main.py     # Main routes (home, test)
│       ├── profile.py  # Profile management routes
│       ├── meal_plans.py    # Meal plan routes
│       ├── workout_plans.py # Workout plan routes
│       ├── shopping.py      # Shopping list routes
│       └── progress.py      # Progress tracking routes
├── api.py              # Modular function interfaces
└── display.py          # Display formatting functions
```

### Key Components

- **EmbeddingEngine**: Uses sentence-transformers for semantic search (falls back to simple matching if not installed)
- **LocalLLMEngine**: Optional local LLM for creative suggestions (llama-cpp-python)
- **MealPlannerEngine**: Generates meal plans based on preferences and nutritional goals
- **WorkoutPlannerEngine**: Creates workout routines based on fitness goals and equipment
- **Web Interface**: Modular Flask web app with separate route handlers for each feature
- **DataStorage**: Local file-based storage for profiles, plans, and progress data

## 🔧 Configuration

### Web Server Settings

You can customize the web server by editing `nutrifit/web/__init__.py` or passing parameters:

```python
from nutrifit.web import run

# Change host and port
run(host="0.0.0.0", port=8080, debug=False)
```

Or when running as a module:

```bash
# Run with custom settings
python -m nutrifit.web --host 0.0.0.0 --port 8080
```

### Data Storage

All data is stored locally in `~/.nutrifit/data/`:
- User profiles
- Meal plans
- Workout plans
- Progress tracking data

## 📝 Requirements

- Python 3.10+
- NumPy (required)
- Flask (for web interface)
- Optional: sentence-transformers (for better AI matching)
- Optional: transformers + torch (for GPT-2 and other Hugging Face models)
- Optional: llama-cpp-python (for GGUF model support)

Install with optional dependencies:

```bash
# Install with all optional AI features
pip install -e ".[all]"

# Or install specific features
pip install -e ".[embeddings]"  # For semantic search
pip install -e ".[llm]"         # For local LLM support
```

## 🤖 Using a Local LLM

The app automatically uses a local LLM if available - no configuration needed!

### Option 1: GPT-2 (Easiest - Recommended)

Just install transformers and the app will automatically use GPT-2:
```bash
pip install transformers torch
```

The app will detect and use GPT-2 on startup - no setup required!

### Option 2: GGUF Models (More Efficient)

1. **Install llama-cpp-python:**
   ```bash
   pip install llama-cpp-python
   ```

2. **Place a `.gguf` model file** in the `models/` directory:
   - Download from [Hugging Face](https://huggingface.co/models?library=gguf)
   - Recommended: Small models like `phi-2`, `tinyllama`, or `mistral-7b-instruct`
   - Place in `models/` directory in the project root

3. **Run the app** - it will automatically detect and use the GGUF model!

The app will gracefully fall back to template-based suggestions if:
- No model is found
- Required libraries are not installed
- The model fails to load

**Priority order:**
1. GGUF files in `models/` directory (if llama-cpp-python installed)
2. GPT-2 via transformers (if transformers installed)
3. Template-based fallback (always available)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see LICENSE file for details
