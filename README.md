# NutriFit

NutriFit is an AI-powered mobile health assistant that generates personalized meal plans and workout routines based on user dietary preferences, fitness goals, and available ingredients or equipment. Users can receive weekly recommendations, optimize shopping lists, and track progress.

## ✨ Features

- **AI Chatbot Assistant**: Chat naturally to create meal plans, design workouts, and get nutrition advice
- **Personalized Meal Plans**: Generate weekly meal plans based on your dietary preferences, allergies, and pantry items
- **Custom Workout Routines**: Get weekly workout plans tailored to your fitness goals and available equipment
- **Conversational Modifications**: Ask the chatbot to change meals or workouts through natural language
- **Semantic Recipe/Workout Search**: Find recipes and workouts using natural language queries with AI-powered matching
- **Auto-Generated Shopping Lists**: Automatically generate and update shopping lists from meal plans, organized by week
- **Progress Tracking**: Track weight, calories, workouts, and more over time
- **Nutrition & Fitness Q&A**: Ask questions and get personalized answers from the AI assistant
- **Local AI Support**: Works with local AI models or cloud APIs (Ollama, OpenAI, or local models)
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

The server will start on `http://localhost:8000` (or `http://0.0.0.0:8000`).

### Step 3: Access from Your Phone

1. **Find your computer's IP address:**
   - Windows: Open Command Prompt and run `ipconfig` (look for IPv4 Address)
   - Mac/Linux: Run `ifconfig` or `ip addr`

2. **On your phone's browser**, go to:
   ```
   http://YOUR_IP_ADDRESS:8000
   ```
   For example: `http://192.168.1.100:8000`

3. **Or use localhost** if testing on the same device:
   ```
   http://localhost:8000
   ```

**Note:** On first run, the app will automatically download GPT-2 (~500MB). This only happens once!

### Web Interface Features

- **AI Chatbot**: Chat with the AI assistant to create plans, modify meals/workouts, and ask questions
- **Profile Management**: Create and update your profile with dietary preferences, fitness goals, allergies, and equipment
- **Meal Planning**: Generate weekly meal plans with week navigation. Edit meals directly in the app
- **Workout Planning**: Get personalized weekly workout routines. Edit workouts or mark rest days
- **Shopping Lists**: Automatically generated and updated shopping lists organized by week
- **Progress Tracking**: Log your daily progress and view summaries
- **Meal Instructions**: View detailed cooking instructions for each meal
- **Workout Details**: See detailed exercise information including sets, reps, and rest periods
- **Natural Language Interface**: Describe what you want and let the AI create it for you

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

**Chatbot:**
- `POST /api/chatbot/chat` - Send message and get AI response
- `GET /api/chatbot/history` - Get conversation history
- `POST /api/chatbot/reset` - Reset conversation
- `GET /api/chatbot/context` - Get current context (plans, etc.)

**Profile:**
- `GET /api/profile` - Get user profile
- `POST /api/profile` - Update user profile

**Meal Plans:**
- `POST /api/meal-plan/weekly` - Generate weekly meal plan
- `GET /api/meal-plans` - List all meal plans
- `GET /api/meal-plan/<id>` - Get specific meal plan
- `PUT /api/meal-plan/<id>` - Update meal plan entry

**Workout Plans:**
- `POST /api/workout-plan/weekly` - Generate weekly workout plan
- `GET /api/workout-plans` - List all workout plans
- `GET /api/workout-plan/<id>` - Get specific workout plan
- `PUT /api/workout-plan/<id>` - Update workout plan entry

**Shopping & Progress:**
- `POST /api/shopping-list` - Generate shopping list
- `POST /api/progress` - Log progress
- `GET /api/progress/summary` - Get progress summary

## 🛠️ Tech Stack

### Backend
- **Python 3.10+** - Core programming language
- **Flask** - Web framework for RESTful API and web interface
- **NumPy** - Numerical operations and data processing
- **sentence-transformers** (optional) - Semantic search and embeddings
- **llama-cpp-python** (optional) - Efficient GGUF model inference
- **Ollama** (optional) - Local modern LLM support via Ollama service (llama3.2, mistral, phi3, etc.)
- **openai** (optional) - OpenAI API client for cloud-based LLM support (requires API key)

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
- **Local LLM Engine** - GGUF models or GPT-2 (via transformers) for creative suggestions
- **Chatbot Engine** - Conversational AI for natural language plan creation and modification
  - Supports Ollama (local modern LLMs), OpenAI API (cloud), or LocalLLMEngine (fallback)
- **Plan Parser** - Converts LLM-generated text into structured meal/workout plans
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
├── engines/            # AI engines
│   ├── embedding_engine.py    # Semantic search
│   ├── llm_engine.py          # Local LLM (GPT-2, GGUF)
│   ├── ollama_engine.py       # Ollama integration
│   ├── openai_engine.py       # OpenAI API integration
│   ├── chatbot_engine.py      # Conversational AI assistant
│   ├── meal_planner.py        # Meal plan generation
│   └── workout_planner.py     # Workout plan generation
├── parsers/            # LLM output parsers
│   └── plan_parser.py  # Converts text to structured plans
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
│       ├── chatbot.py  # Chatbot API routes
│       ├── meal_plans.py    # Meal plan routes
│       ├── workout_plans.py # Workout plan routes
│       ├── shopping.py      # Shopping list routes
│       └── progress.py      # Progress tracking routes
├── api.py              # Modular function interfaces
└── display.py          # Display formatting functions
```

### Key Components

- **EmbeddingEngine**: Uses sentence-transformers for semantic search (falls back to simple matching if not installed)
- **LocalLLMEngine**: Optional local LLM for creative suggestions (GGUF via llama-cpp-python or GPT-2 via transformers)
- **ChatbotEngine**: Conversational AI assistant that uses Ollama, OpenAI API, or LocalLLMEngine for natural language plan creation and modification
- **PlanParser**: Converts LLM-generated text into structured MealPlan and WorkoutPlan objects
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
- Optional: llama-cpp-python (for GGUF model support)
- Optional: Ollama (for modern local LLMs - install separately from https://ollama.ai)
- Optional: openai (for OpenAI API support - requires API key)
- Optional: transformers + torch (auto-installed by LocalLLMEngine if using GPT-2)

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

### Option 1: Ollama (Best Quality - Recommended)

Ollama provides access to modern, high-quality LLMs like llama3.2, mistral, and phi3.

1. **Install Ollama:**
   - Visit https://ollama.ai and install for your platform
   - Or use: `curl -fsSL https://ollama.ai/install.sh | sh` (Linux/Mac)

2. **Pull a model:**
   ```bash
   ollama pull llama3.2
   # Or try: ollama pull mistral
   # Or try: ollama pull phi3
   ```

3. **Start Ollama** (usually runs automatically as a service)

4. **Run the app** - it will automatically detect and use Ollama!

The chatbot will use Ollama by default if it's available, providing the best conversational experience.

### Option 2: GGUF Models (Advanced)

1. **Install llama-cpp-python:**
   ```bash
   pip install llama-cpp-python
   ```

2. **Place a `.gguf` model file** in the `models/` directory:
   - Download from [Hugging Face](https://huggingface.co/models?library=gguf)
   - Recommended: Small models like `phi-2`, `tinyllama`, or `mistral-7b-instruct`
   - Place in `models/` directory in the project root

3. **Run the app** - it will automatically detect and use the GGUF model!

**Note:** GPT-2 support is available via transformers (auto-installed by LocalLLMEngine if needed), but GGUF models or Ollama are recommended for better quality.

### Option 3: OpenAI API (Cloud-based)

For cloud-based LLM support with GPT-3.5 or GPT-4:

1. **Install the OpenAI package:**
   ```bash
   pip install openai
   ```

2. **Set your API key:**
   ```bash
   # Linux/Mac
   export OPENAI_API_KEY="your-api-key-here"
   
   # Windows PowerShell
   $env:OPENAI_API_KEY="your-api-key-here"
   ```

3. **Run the app** - it will automatically use OpenAI if the API key is set!

**Note:** This requires an internet connection and API credits. The app will fall back to local options if the API is unavailable.

The app will gracefully fall back to template-based suggestions if:
- No model is found
- Required libraries are not installed
- The model fails to load

**Priority order (for chatbot and LLM features):**
1. Ollama (if installed and running - recommended for best results)
2. OpenAI API (if OPENAI_API_KEY is set and openai package installed)
3. GGUF files in `models/` directory (if llama-cpp-python installed)
4. GPT-2 via transformers (auto-installed by LocalLLMEngine if needed)
5. Template-based fallback (always available)

**Note:** The chatbot engine automatically detects and uses the best available LLM option. Ollama is recommended for the best conversational experience.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

MIT License - see LICENSE file for details
