# Requirements Document

## Introduction

The LLM-Based Conversational Plan Generation feature enables users to have natural conversations with the AI chatbot to explore and generate meal plans and workout routines. Instead of immediately committing to auto-generated structured plans, users can iteratively refine their requirements through conversation, and only save plans to their dashboard when satisfied.

## Glossary

- **LLM (Large Language Model)**: The AI model (Llama via Ollama) that generates natural language responses
- **Conversational Plan**: A meal or workout plan described in natural language by the LLM
- **Structured Plan**: A plan with formal data structure (recipes, exercises, nutritional info) that can be saved and tracked
- **Plan Extraction**: The process of parsing LLM-generated text into structured data
- **Save Action**: User-initiated action to commit a conversational plan to their dashboard
- **Chat Context**: The conversation history and generated plans available in the current chat session
- **Plan Preview**: A formatted display of the LLM-generated plan in the chat interface

## Requirements

### Requirement 1

**User Story:** As a user, I want the chatbot to generate meal plans using natural language, so that I can have a more conversational and exploratory planning experience.

#### Acceptance Criteria

1. WHEN a user requests a meal plan through chat, THE NutriFit System SHALL use the LLM to generate a natural language meal plan description
2. WHEN generating a meal plan, THE NutriFit System SHALL include the user's dietary preferences, calorie targets, and macro targets in the LLM prompt
3. WHEN the LLM generates a meal plan, THE NutriFit System SHALL format the response to include daily meal suggestions with approximate nutritional information
4. WHEN displaying the meal plan, THE NutriFit System SHALL present it in a readable, conversational format within the chat interface

### Requirement 2

**User Story:** As a user, I want the chatbot to generate workout plans using natural language, so that I can explore different workout options conversationally.

#### Acceptance Criteria

1. WHEN a user requests a workout plan through chat, THE NutriFit System SHALL use the LLM to generate a natural language workout plan description
2. WHEN generating a workout plan, THE NutriFit System SHALL include the user's fitness goals, available equipment, and fitness level in the LLM prompt
3. WHEN the LLM generates a workout plan, THE NutriFit System SHALL format the response to include daily workout suggestions with exercises and durations
4. WHEN displaying the workout plan, THE NutriFit System SHALL present it in a readable, conversational format within the chat interface

### Requirement 3

**User Story:** As a user, I want to see a "Save to My Plans" button after the chatbot generates a plan, so that I can choose whether to commit the plan to my dashboard.

#### Acceptance Criteria

1. WHEN the chatbot generates a meal plan, THE NutriFit System SHALL display a "Save to Meal Plans" button below the plan in the chat interface
2. WHEN the chatbot generates a workout plan, THE NutriFit System SHALL display a "Save to Workout Plans" button below the plan in the chat interface
3. WHEN a save button is displayed, THE NutriFit System SHALL make it visually distinct and easily clickable
4. WHEN a user has not yet saved a generated plan, THE NutriFit System SHALL keep the save button visible and enabled

### Requirement 4

**User Story:** As a user, I want to click the "Save to My Plans" button to add the chatbot-generated plan to my dashboard, so that I can track and follow the plan.

#### Acceptance Criteria

1. WHEN a user clicks "Save to Meal Plans", THE NutriFit System SHALL parse the LLM-generated meal plan into structured data
2. WHEN a user clicks "Save to Workout Plans", THE NutriFit System SHALL parse the LLM-generated workout plan into structured data
3. WHEN parsing is successful, THE NutriFit System SHALL save the structured plan to the user's meal or workout plan list
4. WHEN a plan is saved successfully, THE NutriFit System SHALL display a confirmation message in the chat
5. WHEN a plan is saved successfully, THE NutriFit System SHALL disable or hide the save button to prevent duplicate saves

### Requirement 5

**User Story:** As a user, I want the system to extract structured data from LLM-generated plans, so that I can track nutritional information and progress.

#### Acceptance Criteria

1. WHEN parsing an LLM-generated meal plan, THE NutriFit System SHALL extract meal names, ingredients, and approximate nutritional values for each day
2. WHEN parsing an LLM-generated workout plan, THE NutriFit System SHALL extract exercise names, sets, reps, duration, and rest periods for each day
3. WHEN extraction fails or data is incomplete, THE NutriFit System SHALL use reasonable defaults and notify the user
4. WHEN creating structured data, THE NutriFit System SHALL validate that required fields are present before saving

### Requirement 6

**User Story:** As a user, I want to refine my plan requirements through conversation, so that I can iteratively improve the plan before saving it.

#### Acceptance Criteria

1. WHEN a user requests modifications to a generated plan, THE NutriFit System SHALL use the LLM to generate an updated plan
2. WHEN generating an updated plan, THE NutriFit System SHALL include the previous plan and modification request in the LLM context
3. WHEN displaying an updated plan, THE NutriFit System SHALL show a new save button for the updated version
4. WHEN a user saves an updated plan, THE NutriFit System SHALL save only the latest version

### Requirement 7

**User Story:** As a user, I want the LLM to generate plans that respect my specific targets, so that the plans align with my goals.

#### Acceptance Criteria

1. WHEN a user specifies calorie targets in their message, THE NutriFit System SHALL include those targets in the LLM prompt
2. WHEN a user specifies macro targets (protein, carbs, fat), THE NutriFit System SHALL include those targets in the LLM prompt
3. WHEN a user specifies workout frequency or duration, THE NutriFit System SHALL include those constraints in the LLM prompt
4. WHEN the LLM generates a plan, THE NutriFit System SHALL instruct the LLM to approximately match the specified targets

### Requirement 8

**User Story:** As a user, I want saved plans to appear in my Meal Plans or Workout Plans panels, so that I can access them alongside other plans.

#### Acceptance Criteria

1. WHEN a meal plan is saved from chat, THE NutriFit System SHALL add it to the user's meal plan list with a unique identifier
2. WHEN a workout plan is saved from chat, THE NutriFit System SHALL add it to the user's workout plan list with a unique identifier
3. WHEN viewing the Meal Plans panel, THE NutriFit System SHALL display chat-generated plans alongside manually created plans
4. WHEN viewing the Workout Plans panel, THE NutriFit System SHALL display chat-generated plans alongside manually created plans
5. WHEN displaying a chat-generated plan, THE NutriFit System SHALL indicate its source (e.g., "Generated by AI Chat")

### Requirement 9

**User Story:** As a user, I want the system to handle LLM failures gracefully, so that I can still use the chatbot even if plan generation fails.

#### Acceptance Criteria

1. WHEN the LLM fails to generate a plan, THE NutriFit System SHALL display an error message in the chat
2. WHEN the LLM is unavailable, THE NutriFit System SHALL offer to use the structured plan generator as a fallback
3. WHEN plan parsing fails, THE NutriFit System SHALL notify the user and offer to regenerate the plan
4. WHEN an error occurs, THE NutriFit System SHALL log the error details for debugging

### Requirement 10

**User Story:** As a user, I want the chatbot to provide helpful prompts and examples, so that I know how to request plans effectively.

#### Acceptance Criteria

1. WHEN a user asks for help with meal planning, THE NutriFit System SHALL provide example requests with specific targets
2. WHEN a user asks for help with workout planning, THE NutriFit System SHALL provide example requests with specific parameters
3. WHEN a user's request is ambiguous, THE NutriFit System SHALL ask clarifying questions before generating a plan
4. WHEN displaying a generated plan, THE NutriFit System SHALL include a note about how to modify or regenerate it
