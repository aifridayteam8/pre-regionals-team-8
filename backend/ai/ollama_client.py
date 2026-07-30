import ollama
from typing import Dict, List, Optional
import logging
from .base_client import BaseAIClient

logger = logging.getLogger(__name__)


class OllamaClient(BaseAIClient):
    """Client for interacting with Ollama local LLM."""
    
    def __init__(self, base_url: str = 'http://localhost:11434', model: str = 'llama3.2'):
        self.base_url = base_url
        self.model = model
        self.client = ollama.Client(host=base_url)
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate text using Ollama."""
        options = {}
        if max_tokens is not None:
            options['num_predict'] = max_tokens
        if temperature is not None:
            options['temperature'] = temperature

        try:
            response = self.client.generate(
                model=self.model,
                prompt=prompt,
                system=system_prompt,
                stream=False,
                options=options or None
            )
            return response['response']
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    def chat(self, messages: List[Dict[str, str]]) -> str:
        """Generate text using chat interface."""
        try:
            response = self.client.chat(
                model=self.model,
                messages=messages,
                stream=False
            )
            return response['message']['content']
        except Exception as e:
            logger.error(f"Ollama chat error: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Ollama service is available."""
        try:
            self.client.list()
            return True
        except Exception:
            return False
    
    def list_models(self) -> List[str]:
        """List available models."""
        try:
            models = self.client.list()
            return [model['name'] for model in models.get('models', [])]
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            return []
