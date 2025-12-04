"""Ollama engine for local modern LLMs."""

import json
from typing import Optional

import requests


class OllamaEngine:
    """
    Ollama engine for running modern LLMs locally.
    
    Requires:
    1. Install Ollama: https://ollama.ai
    2. Pull a model: ollama pull llama3.2
    
    Supported models:
    - llama3.2 (3B, 1B) - Meta's latest, very good
    - mistral (7B) - Fast and capable
    - phi3 (3.8B) - Microsoft's efficient model
    - gemma2 (2B, 9B) - Google's model
    """

    def __init__(
        self,
        model: str = "llama3.2",
        base_url: str = "http://localhost:11434",
    ):
        """Initialize Ollama engine.
        
        Args:
            model: Model name (e.g., "llama3.2", "mistral", "phi3")
            base_url: Ollama API base URL
        """
        self.model = model
        self.base_url = base_url
        self._available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Ollama is running and model is available."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(m["name"].startswith(self.model) for m in models)
            return False
        except Exception:
            return False
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        return self._available
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 256,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate a response using Ollama.
        
        Args:
            prompt: User prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-2)
            system_prompt: Optional system prompt
            
        Returns:
            Generated response
        """
        if not self._available:
            raise RuntimeError(
                f"Ollama not available. Install from https://ollama.ai and run: ollama pull {self.model}"
            )
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=300,  # 5 minutes timeout for long meal/workout plans
            )
            response.raise_for_status()
            return response.json()["response"].strip()
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"Ollama timed out after 5 minutes. The model might be loading for the first time. "
                f"Try again in a moment or use a smaller model."
            )
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")
    
    def chat(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 256,
        temperature: float = 0.7,
    ) -> str:
        """Chat with conversation history.
        
        Args:
            messages: List of {"role": "user/assistant/system", "content": "..."}
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            
        Returns:
            Generated response
        """
        if not self._available:
            raise RuntimeError(
                f"Ollama not available. Install from https://ollama.ai and run: ollama pull {self.model}"
            )
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=300,  # 5 minutes timeout for long meal/workout plans
            )
            response.raise_for_status()
            return response.json()["message"]["content"].strip()
        except requests.exceptions.Timeout:
            raise RuntimeError(
                f"Ollama timed out after 5 minutes. The model might be loading for the first time. "
                f"Try again in a moment or use a smaller model."
            )
        except Exception as e:
            raise RuntimeError(f"Ollama API error: {e}")
    
    @staticmethod
    def list_available_models() -> list[str]:
        """List all available Ollama models."""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m["name"] for m in models]
            return []
        except Exception:
            return []
