import os
from typing import Optional
from langchain_openai import OpenAI
from langchain.schema import HumanMessage


class OpenRouterLLM:
    """Wrapper for OpenRouter API (compatible with OpenAI SDK)."""

    def __init__(
        self,
        model: str = "openai/gpt-4o",
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1",
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
