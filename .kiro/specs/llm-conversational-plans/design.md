# Design Document

## Overview

The LLM-Based Conversational Plan Generation feature transforms the chatbot from a structured plan generator into a conversational planning assistant. Users can explore meal and workout options through natural dialogue with the LLM (Llama via Ollama), refine their requirements iteratively, and save plans only when satisfied.

This design maintains the benefits of structured data (tracking, progress monitoring) while providing a more natural, exploratory user experience.

## Architecture

### High-Level Flow

```
User Request → Intent Detection → LLM Plan Generation → Display with Save Button
                                                              ↓
                                                    User Clicks Save
                                                              ↓
                                            Parse LLM Text → Structured Data
                                                              ↓
                                            Save to Database → Confirmation
```

### Component Interaction

```
┌─────────────────────────────────────────────────────────────┐
│                     Chat Interface (UI)                      │
│  - Message Display                                           │
│  - Save Plan Buttons                                         │
│  - Confirmation Messages                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────┐
│                  Chatbot Engine (Enhanced)                   │
│  - LLM Prompt Engineering                                    │
│  - Plan Generation Orchestration                             │
│  - Context Management                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┴────────────────┐
        │                                  │
┌───────┴────────┐              ┌─────────┴──────────┐
│  LLM Engine    │              │  Plan Parser       │
│  (Ollama)      │              │  - Text → Struct   │
│                │              │  - Validation      │
└────────────────┘              └─────────┬──────────┘
                                          │
                                ┌─────────┴──────────┐
                                │  Storage Layer     │
                                │  - Save Plans      │
                                │  - Retrieve Plans  │
                                └────────────────────┘
```

## Components and Interfaces

### 1. Enhanced Chatbot Engine

#### New Methods

```python
class ChatbotEngine:
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
```

### 2. Plan Parser Module

```python
class PlanParser:
    """Parse LLM-generated plans into structured data."""
    
    def parse_meal_plan(self, llm_text: str, user_profile: UserProfile) -> MealPlan:
        """Parse LLM meal plan text into MealPlan object.
        
        Extracts:
        - Daily meal names
        - Ingredients (approximate)
        - Nutritional estimates
        - Meal timing
        
        Returns:
            MealPlan object with structured data
        """
        
    def parse_workout_plan(self, llm_text: str, user_profile: UserProfile) -> WorkoutPlan:
        """Parse LLM workout plan text into WorkoutPlan object.
        
        Extracts:
        - Exercise names
        - Sets and reps
        - Duration
        - Rest periods
        - Workout type
        
        Returns:
            WorkoutPlan object with structured data
        """
        
    def extract_meals_from_text(self, text: str) -> list[dict]:
        """Extract meal information using regex and NLP."""
        
    def extract_exercises_from_text(self, text: str) -> list[dict]:
        """Extract exercise information using regex and NLP."""
        
    def estimate_nutrition(self, meal_description: str) -> NutritionInfo:
        """Estimate nutritional values from meal description."""
```

### 3. Enhanced Chat API

#### New Endpoints

```python
@chatbot_bp.route("/save-plan", methods=["POST"])
def save_plan():
    """
    Save an LLM-generated plan to user's dashboard.
    
    Request:
        {
            "plan_id": "abc123",
            "plan_type": "meal" | "workout",
            "user_id": "default"
        }
    
    Response:
        {
            "success": true,
            "plan_id": "saved_plan_123",
            "message": "Plan saved successfully"
        }
    """
```

### 4. UI Components

#### Save Button Component

```javascript
function createSaveButton(planId, planType) {
    return `
        <div class="plan-save-actions">
            <button 
                class="btn-save-plan" 
                onclick="savePlanToDashboard('${planId}', '${planType}')"
                data-plan-id="${planId}"
            >
                💾 Save to ${planType === 'meal' ? 'Meal' : 'Workout'} Plans
            </button>
            <button 
                class="btn-regenerate" 
                onclick="regeneratePlan('${planType}')"
            >
                🔄 Regenerate
            </button>
        </div>
    `;
}
```

#### Enhanced Message Formatting

```javascript
function formatPlanMessage(response, planId, planType) {
    // Format the LLM response
    let formatted = formatMessage(response);
    
    // Add save button if this is a plan
    if (planId && planType) {
        formatted += createSaveButton(planId, planType);
    }
    
    return formatted;
}
```

## Data Models

### Plan Context Storage

```python
@dataclass
class GeneratedPlan:
    """Temporary storage for LLM-generated plans."""
    plan_id: str
    plan_type: str  # "meal" or "workout"
    llm_text: str
    user_profile: UserProfile
    generated_at: datetime
    requirements: dict
    saved: bool = False
```

### Parsed Plan Metadata

```python
@dataclass
class ParsedPlanMetadata:
    """Metadata for plans generated from LLM."""
    source: str = "ai_chat"
    llm_model: str = "llama3.2"
    generated_at: datetime
    original_text: str
    parsing_confidence: float  # 0.0 to 1.0
```

## LLM Prompt Engineering

### Meal Plan Prompt Template

```python
MEAL_PLAN_PROMPT = """You are a professional nutritionist creating a personalized meal plan.

User Profile:
- Dietary Preferences: {dietary_preferences}
- Fitness Goals: {fitness_goals}
- Allergies: {allergies}

Requirements:
- Daily Calorie Target: {calorie_target} kcal
- Protein Target: {protein_target}g
- Carbs Target: {carbs_target}g
- Fat Target: {fat_target}g
- Duration: {duration} days

Create a detailed {duration}-day meal plan that:
1. Meets the calorie and macro targets (within 10%)
2. Respects dietary preferences and allergies
3. Includes breakfast, lunch, dinner, and snacks
4. Provides variety across days
5. Lists approximate calories and macros for each meal

Format each day as:
**Day X (Date):**
- 🍳 Breakfast: [Meal name] (~XXX kcal, Protein: XXg, Carbs: XXg, Fat: XXg)
- 🥗 Lunch: [Meal name] (~XXX kcal, Protein: XXg, Carbs: XXg, Fat: XXg)
- 🍽️ Dinner: [Meal name] (~XXX kcal, Protein: XXg, Carbs: XXg, Fat: XXg)
- 🍎 Snack: [Snack name] (~XXX kcal, Protein: XXg, Carbs: XXg, Fat: XXg)
- 📊 Daily Total: ~XXXX kcal

Be specific with meal names and provide realistic nutritional estimates.
"""
```

### Workout Plan Prompt Template

```python
WORKOUT_PLAN_PROMPT = """You are a certified personal trainer creating a personalized workout plan.

User Profile:
- Fitness Goals: {fitness_goals}
- Fitness Level: {fitness_level}
- Available Equipment: {equipment}

Requirements:
- Workout Days per Week: {workout_days}
- Session Duration: {duration} minutes
- Focus Areas: {focus_areas}

Create a detailed {workout_days}-day per week workout plan that:
1. Matches the user's fitness level
2. Uses only available equipment
3. Targets the specified focus areas
4. Includes warm-up and cool-down
5. Provides sets, reps, and rest periods

Format each day as:
**Day X - [Workout Type]:**
- Exercise 1: [Name] - X sets × X reps (Rest: Xs)
- Exercise 2: [Name] - X sets × X reps (Rest: Xs)
- Exercise 3: [Name] - X minutes
- Total Duration: ~XX minutes
- Intensity: [Low/Medium/High]

For rest days, suggest active recovery activities.
"""
```

## Parsing Strategy

### Regex Patterns

```python
# Meal extraction patterns
MEAL_PATTERN = r'(?:🍳|🥗|🍽️|🍎)\s*(\w+):\s*([^(]+)\s*\(~?(\d+)\s*kcal'
MACRO_PATTERN = r'Protein:\s*(\d+)g,\s*Carbs:\s*(\d+)g,\s*Fat:\s*(\d+)g'
DAY_PATTERN = r'\*\*Day\s+(\d+)'

# Exercise extraction patterns
EXERCISE_PATTERN = r'-\s*([^:]+):\s*([^-\n]+)'
SETS_REPS_PATTERN = r'(\d+)\s*sets?\s*[×x]\s*(\d+)\s*reps?'
DURATION_PATTERN = r'(\d+)\s*(?:minutes?|mins?)'
```

### Fallback Strategy

1. **Primary**: Regex-based extraction
2. **Secondary**: Keyword matching and heuristics
3. **Tertiary**: Use LLM to reformat its own output into JSON
4. **Final**: Create minimal plan with user confirmation

## Error Handling

### Parsing Failures

```python
class PlanParsingError(Exception):
    """Raised when plan parsing fails."""
    
    def __init__(self, message: str, partial_data: dict = None):
        self.message = message
        self.partial_data = partial_data
```

### User Notifications

- **Parsing Failed**: "I generated a plan, but had trouble structuring it. Would you like me to try again?"
- **Incomplete Data**: "I saved your plan, but some nutritional data is estimated. You can edit it in your dashboard."
- **LLM Unavailable**: "I'm having trouble generating a custom plan. Would you like me to use the quick plan generator instead?"

## UI/UX Design

### Save Button States

```css
.btn-save-plan {
    /* Default state */
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
    color: white;
}

.btn-save-plan:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}

.btn-save-plan.saving {
    /* Loading state */
    opacity: 0.7;
    cursor: wait;
}

.btn-save-plan.saved {
    /* Success state */
    background: #6b7280;
    cursor: not-allowed;
}
```

### Confirmation Messages

```javascript
function showSaveConfirmation(planType) {
    showToast(
        `✅ ${planType === 'meal' ? 'Meal' : 'Workout'} plan saved! Check your ${planType === 'meal' ? 'Meals' : 'Workouts'} tab.`,
        'success'
    );
}
```

## Testing Strategy

### Unit Tests

- LLM prompt generation
- Plan parsing with various formats
- Error handling for malformed LLM output
- Save button state management

### Integration Tests

- End-to-end plan generation and saving
- UI button interactions
- API endpoint responses
- Database persistence

### Manual Testing Scenarios

1. Generate meal plan with specific targets
2. Modify plan through conversation
3. Save plan and verify in dashboard
4. Test with LLM unavailable
5. Test parsing with unusual LLM formats

## Performance Considerations

- **LLM Response Time**: 2-10 seconds (acceptable for conversational UX)
- **Parsing Time**: < 100ms
- **Save Operation**: < 500ms
- **Caching**: Cache parsed plans to avoid re-parsing

## Security Considerations

- Validate all LLM output before parsing
- Sanitize plan text before storage
- Rate limit plan generation requests
- Validate plan IDs before saving

## Future Enhancements

1. **Plan Comparison**: Compare LLM-generated vs structured plans
2. **Plan History**: View all generated plans in chat history
3. **Collaborative Refinement**: Multi-turn conversation to refine plans
4. **Template Learning**: Learn from saved plans to improve future generations
5. **Nutritional Database Integration**: Use real nutritional data for better estimates
