# 🚀 Upgrade Your Chatbot to a Better LLM

Your chatbot is currently using **GPT-2 (2019)** which is pretty basic. Here's how to upgrade to much better, modern LLMs!

## 🎯 Quick Comparison

| Option | Quality | Speed | Cost | Offline | Setup Difficulty |
|--------|---------|-------|------|---------|------------------|
| **Ollama (Llama 3.2)** | ⭐⭐⭐⭐⭐ | ⚡⚡⚡⚡ | FREE | ✅ Yes | Easy |
| **OpenAI GPT-4** | ⭐⭐⭐⭐⭐ | ⚡⚡⚡⚡⚡ | $$ | ❌ No | Very Easy |
| **OpenAI GPT-3.5** | ⭐⭐⭐⭐ | ⚡⚡⚡⚡⚡ | $ | ❌ No | Very Easy |
| **Current (GPT-2)** | ⭐⭐ | ⚡⚡⚡ | FREE | ✅ Yes | Already done |

## 🏆 **Recommended: Ollama with Llama 3.2** (Best Balance)

Ollama lets you run modern LLMs locally for FREE!

### Step 1: Install Ollama

**Mac:**
```bash
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from https://ollama.ai

### Step 2: Start Ollama

```bash
ollama serve
```

### Step 3: Pull a Model

Choose one:

```bash
# Llama 3.2 (3B) - RECOMMENDED - Fast and smart
ollama pull llama3.2

# Mistral (7B) - Very capable
ollama pull mistral

# Phi-3 (3.8B) - Microsoft's efficient model
ollama pull phi3

# Gemma 2 (2B) - Google's lightweight model
ollama pull gemma2:2b
```

### Step 4: Install Python Package

```bash
pip install requests
```

### Step 5: Restart Your Server

```bash
python -m nutrifit.web
```

**That's it!** The chatbot will automatically detect and use Ollama! 🎉

---

## 💰 **Option 2: OpenAI API** (Best Quality, Requires Internet)

### Step 1: Get API Key

1. Go to https://platform.openai.com/api-keys
2. Create an account
3. Generate an API key

### Step 2: Install OpenAI Package

```bash
pip install openai
```

### Step 3: Set API Key

**Mac/Linux:**
```bash
export OPENAI_API_KEY="sk-your-key-here"
```

**Windows:**
```cmd
set OPENAI_API_KEY=sk-your-key-here
```

Or add to your `.env` file:
```
OPENAI_API_KEY=sk-your-key-here
```

### Step 4: Enable OpenAI in Chatbot

Edit `nutrifit/web/routes/chatbot.py`:

```python
_chatbot_engine = ChatbotEngine(
    llm_engine=llm_engine,
    meal_planner=meal_planner,
    workout_planner=workout_planner,
    use_openai=True,  # Enable OpenAI
    use_ollama=False,  # Disable Ollama
)
```

### Step 5: Restart Server

```bash
python -m nutrifit.web
```

---

## 🔧 **How It Works Now**

The chatbot now auto-detects the best available LLM in this order:

1. **Ollama** (if running) - Modern, free, offline
2. **OpenAI** (if API key set) - Best quality, requires internet
3. **GPT-2** (fallback) - Basic, always works

You'll see a message when the server starts:
- ✅ `Using Ollama with llama3.2` - You're using Ollama!
- ✅ `Using OpenAI API with gpt-3.5-turbo` - You're using OpenAI!
- ⚠️ `Using LocalLLMEngine (GPT-2 or templates)` - Still using old model

---

## 📊 **Model Recommendations**

### For Best Quality (Offline):
```bash
ollama pull llama3.2  # 3B parameters, very good
```

### For Speed (Offline):
```bash
ollama pull gemma2:2b  # 2B parameters, fast
```

### For Best Overall (Online):
```bash
# Use OpenAI GPT-4 or GPT-3.5-turbo
export OPENAI_API_KEY="your-key"
```

---

## 🎯 **Test the Upgrade**

After upgrading, test with:

```
You: "Explain the benefits of high-protein diets"
```

**With GPT-2 (old):**
> "Protein is essential for muscle building..."

**With Llama 3.2 (new):**
> "High-protein diets offer several key benefits:
> 1. Enhanced muscle growth and repair
> 2. Increased satiety and reduced hunger
> 3. Higher thermic effect (burns more calories)
> 4. Better blood sugar control
> 5. Preservation of lean mass during weight loss
> 
> For muscle gain, aim for 1.6-2.2g per kg body weight..."

Much better! 🎉

---

## 🐛 **Troubleshooting**

### Ollama not detected?

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve

# Check available models
ollama list
```

### OpenAI not working?

```bash
# Check API key is set
echo $OPENAI_API_KEY

# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Still using GPT-2?

Check the server logs when starting:
```bash
python -m nutrifit.web
```

Look for:
- ✅ `Using Ollama with llama3.2`
- ⚠️ `Ollama not available: ...`

---

## 💡 **Pro Tips**

1. **Ollama is recommended** - Free, fast, modern, offline
2. **Start with llama3.2** - Best balance of quality and speed
3. **OpenAI for production** - If you need the absolute best quality
4. **Keep GPT-2 as fallback** - Always works, no setup needed

---

## 📈 **Performance Comparison**

**Response Quality Test: "Create a high-protein breakfast"**

**GPT-2:**
> "Try a protein-rich scramble or smoothie using eggs..."

**Llama 3.2:**
> "Here's a delicious high-protein breakfast:
> 
> **Protein Power Bowl**
> - 3 scrambled eggs (18g protein)
> - 1/2 cup Greek yogurt (12g protein)
> - 1/4 cup granola (4g protein)
> - Handful of berries
> - 1 tbsp almond butter (3.5g protein)
> 
> Total: ~37g protein, 450 calories
> 
> This provides sustained energy and supports muscle recovery!"

**Winner:** Llama 3.2 by far! 🏆

---

## 🚀 **Ready to Upgrade?**

**Easiest:** Install Ollama (5 minutes)
```bash
# Mac
brew install ollama
ollama serve
ollama pull llama3.2

# Restart server
python -m nutrifit.web
```

**Done!** Your chatbot is now 10x better! 🎉
