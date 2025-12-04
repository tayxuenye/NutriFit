# AI Chatbot Feature - Implementation Guide

## Overview
Added an AI-powered chatbot that allows users to have natural conversations to create and modify meal plans and workouts.

## Backend Implementation

### 1. Chatbot Engine (`nutrifit/engines/chatbot_engine.py`)
- **Intent Detection**: Automatically detects what the user wants (meal plan, workout, modification, question)
- **Conversational AI**: Uses LLM (GPT-2 or templates) to generate natural responses
- **Context Awareness**: Remembers conversation history and current plans
- **Smart Suggestions**: Can modify meals/workouts based on user requests

**Key Features:**
- Natural language understanding
- Profile-aware responses
- Plan generation through conversation
- Meal/workout modifications
- Nutrition and fitness Q&A

### 2. API Routes (`nutrifit/web/routes/chatbot.py`)
- `POST /api/chatbot/chat` - Send a message and get a response
- `GET /api/chatbot/history` - Get conversation history
- `POST /api/chatbot/reset` - Reset conversation
- `GET /api/chatbot/context` - Get current context (plans, etc.)

## Frontend Implementation (To Add)

### Add to `nutrifit/templates/index.html`:

#### 1. Add Chatbot Tab Content (after line 1200, before bottom nav):

```html
<!-- Chatbot Tab -->
<div id="chatbot" class="tab-content">
    <div class="card">
        <h2 class="card-header">AI Assistant 🤖</h2>
        <p style="color: var(--text-secondary); margin-bottom: var(--spacing-lg);">
            Chat with me to create meal plans, design workouts, or ask nutrition questions!
        </p>
        
        <!-- Chat Messages -->
        <div id="chatMessages" style="
            max-height: 400px;
            overflow-y: auto;
            margin-bottom: var(--spacing-lg);
            padding: var(--spacing-md);
            background: var(--bg);
            border-radius: var(--radius);
            border: 1px solid var(--border);
        ">
            <div class="chat-message assistant">
                <div class="message-bubble">
                    👋 Hi! I'm your NutriFit AI assistant. I can help you:
                    <ul style="margin: var(--spacing-sm) 0; padding-left: var(--spacing-lg);">
                        <li>Create personalized meal plans</li>
                        <li>Design workout routines</li>
                        <li>Answer nutrition questions</li>
                        <li>Modify your plans</li>
                    </ul>
                    What would you like to do today?
                </div>
            </div>
        </div>
        
        <!-- Chat Input -->
        <form id="chatForm" style="display: flex; gap: var(--spacing-sm);">
            <input 
                type="text" 
                id="chatInput" 
                class="form-input" 
                placeholder="Type your message..." 
                style="flex: 1; margin-bottom: 0;"
                required
            >
            <button type="submit" class="btn" style="width: auto; padding: var(--spacing-md); margin-bottom: 0;">
                Send
            </button>
        </form>
        
        <!-- Quick Actions -->
        <div style="margin-top: var(--spacing-md); display: flex; flex-wrap: wrap; gap: var(--spacing-sm);">
            <button class="btn-quick" onclick="sendQuickMessage('Create a weekly meal plan for me')">
                🍽️ Meal Plan
            </button>
            <button class="btn-quick" onclick="sendQuickMessage('Generate a workout plan')">
                💪 Workout Plan
            </button>
            <button class="btn-quick" onclick="sendQuickMessage('What should I eat for breakfast?')">
                🍳 Breakfast Ideas
            </button>
            <button class="btn-quick" onclick="sendQuickMessage('How much protein do I need?')">
                ❓ Nutrition Q&A
            </button>
        </div>
    </div>
</div>
```

#### 2. Add Chatbot Styles (in the `<style>` section, around line 900):

```css
/* ===== Chatbot Styles ===== */
.chat-message {
    margin-bottom: var(--spacing-md);
    display: flex;
    flex-direction: column;
}

.chat-message.user {
    align-items: flex-end;
}

.chat-message.assistant {
    align-items: flex-start;
}

.message-bubble {
    max-width: 85%;
    padding: var(--spacing-md);
    border-radius: var(--radius);
    line-height: 1.5;
    word-wrap: break-word;
}

.chat-message.user .message-bubble {
    background: var(--primary);
    color: white;
    border-bottom-right-radius: 4px;
}

.chat-message.assistant .message-bubble {
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text-primary);
    border-bottom-left-radius: 4px;
}

.btn-quick {
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    font-size: 0.8125rem;
    cursor: pointer;
    transition: all 0.2s;
    color: var(--text-primary);
}

.btn-quick:hover {
    border-color: var(--primary);
    background: var(--primary-light);
}

.typing-indicator {
    display: flex;
    gap: 4px;
    padding: var(--spacing-md);
}

.typing-dot {
    width: 8px;
    height: 8px;
    background: var(--text-secondary);
    border-radius: 50%;
    animation: typing 1.4s infinite;
}

.typing-dot:nth-child(2) {
    animation-delay: 0.2s;
}

.typing-dot:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes typing {
    0%, 60%, 100% {
        transform: translateY(0);
    }
    30% {
        transform: translateY(-10px);
    }
}
```

#### 3. Add Chatbot Navigation Item (around line 1245, in the bottom nav):

```html
<a href="#" class="nav-item" onclick="showTab('chatbot'); return false;">
    <div class="nav-item-icon">💬 Chat</div>
</a>
```

#### 4. Add JavaScript Functions (in the `<script>` section, around line 2600):

```javascript
// Chatbot Functions
async function sendChatMessage(message) {
    const chatMessages = document.getElementById('chatMessages');
    
    // Add user message
    const userMsg = document.createElement('div');
    userMsg.className = 'chat-message user';
    userMsg.innerHTML = `<div class="message-bubble">${escapeHtml(message)}</div>`;
    chatMessages.appendChild(userMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Show typing indicator
    const typingMsg = document.createElement('div');
    typingMsg.className = 'chat-message assistant';
    typingMsg.id = 'typing-indicator';
    typingMsg.innerHTML = `
        <div class="message-bubble">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    chatMessages.appendChild(typingMsg);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    try {
        const res = await fetch(`${API_BASE}/api/chatbot/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, user_id: 'default' })
        });
        const result = await res.json();
        
        // Remove typing indicator
        document.getElementById('typing-indicator').remove();
        
        // Add assistant response
        const assistantMsg = document.createElement('div');
        assistantMsg.className = 'chat-message assistant';
        assistantMsg.innerHTML = `<div class="message-bubble">${formatMessage(result.response)}</div>`;
        chatMessages.appendChild(assistantMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
    } catch (error) {
        document.getElementById('typing-indicator').remove();
        const errorMsg = document.createElement('div');
        errorMsg.className = 'chat-message assistant';
        errorMsg.innerHTML = `<div class="message-bubble" style="border-color: var(--error);">
            Sorry, I encountered an error: ${error.message}
        </div>`;
        chatMessages.appendChild(errorMsg);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
}

function sendQuickMessage(message) {
    document.getElementById('chatInput').value = message;
    document.getElementById('chatForm').dispatchEvent(new Event('submit'));
}

function formatMessage(text) {
    // Convert markdown-style formatting to HTML
    text = escapeHtml(text);
    text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\n/g, '<br>');
    return text;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Chat form handler
document.getElementById('chatForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (message) {
        input.value = '';
        await sendChatMessage(message);
    }
});
```

## Usage Examples

### User: "Create a weekly meal plan for me"
**Bot Response:**
- Checks user profile
- Generates personalized meal plan
- Shows preview of Day 1
- Offers to show full plan or make changes

### User: "Change my breakfast to something high-protein"
**Bot Response:**
- Detects modification intent
- Suggests high-protein breakfast alternatives
- Offers to update the plan

### User: "How much protein do I need?"
**Bot Response:**
- Provides personalized protein recommendations
- Based on user's weight and fitness goals
- Includes food sources

### User: "Generate a 4-day workout plan"
**Bot Response:**
- Creates workout plan with 4 training days
- Shows weekly schedule
- Includes rest days
- Offers to show details or modify

## Testing

### Test the API:
```bash
curl -X POST http://localhost:8000/api/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a meal plan for me", "user_id": "default"}'
```

### Test in Browser:
1. Start the app: `python -m nutrifit.web`
2. Go to http://localhost:8000
3. Click the "💬 Chat" tab
4. Try messages like:
   - "Hello"
   - "Create a weekly meal plan"
   - "I'm vegan and want to gain muscle"
   - "What's a good breakfast?"

## Benefits

1. **Natural Interaction**: Users can describe what they want in plain English
2. **Personalized**: Responses based on user profile and goals
3. **Flexible**: Can handle various requests and questions
4. **Educational**: Answers nutrition and fitness questions
5. **Iterative**: Users can refine plans through conversation

## Next Steps

1. Add the HTML/CSS/JS code to `index.html`
2. Test the chatbot functionality
3. Optionally: Add voice input support
4. Optionally: Add chat history persistence
5. Optionally: Add image support for meal/workout photos
