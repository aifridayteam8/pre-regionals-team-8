from abc import ABC, abstractmethod
from typing import List, Optional


class BaseAIClient(ABC):
    """Base interface for AI clients."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text from a prompt."""
        pass
    
    @abstractmethod
    def chat(self, messages: List[dict]) -> str:
        """Generate text from chat messages."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the AI service is available."""
        pass
    
    @abstractmethod
    def list_models(self) -> List[str]:
        """List available models."""
        pass
