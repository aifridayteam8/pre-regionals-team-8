from openai import OpenAI
from typing import Dict, List, Optional
import logging
from .base_client import BaseAIClient

logger = logging.getLogger(__name__)


class OpenAIClient(BaseAIClient):
    """Client for interacting with OpenAI API."""
    
    def __init__(self, api_key: str, model: str = 'gpt-4'):
        self.api_key = api_key
        self.model = model
        self.client = OpenAI(api_key=api_key)
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate text using OpenAI."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            kwargs = {"temperature": temperature if temperature is not None else 0.7}
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI generation error: {e}")
            raise
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Generate text using chat interface."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI chat error: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if OpenAI API is available."""
        try:
            self.client.models.list()
            return True
        except Exception:
            return False
