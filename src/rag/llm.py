import os
from typing import Optional
from openai import OpenAI
from pathlib import Path
from dotenv import load_dotenv

# Cargar .env desde el directorio del proyecto
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)


class OpenRouterLLM:
    """Wrapper for Groq API."""

    def __init__(
        self,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ):
        self.api_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError(
                "GROQ_API_KEY or OPENROUTER_API_KEY not found in environment"
            )

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    def invoke(self, prompt: str) -> str:
        """Generate a response from the model."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content

    def __call__(self, prompt: str) -> str:
        """Allow calling as a function."""
        return self.invoke(prompt)
