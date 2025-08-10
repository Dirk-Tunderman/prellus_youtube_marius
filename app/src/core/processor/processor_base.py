"""Base classes and interfaces for transcript processors."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class TranscriptProcessorInterface(ABC):
    """Base interface for all transcript processors."""
    
    @abstractmethod
    def process_text(self, text: str, system_prompt: Optional[str] = None, model: Optional[str] = None) -> str:
        """
        Process text with a model.
        
        Args:
            text: The text to process
            system_prompt: Optional system prompt for guiding processing
            model: Optional model name to override default
            
        Returns:
            The processed text
        """
        pass
        
    @abstractmethod
    def _process_with_model(self, prompt: str, max_retries: int = 3) -> str:
        """
        Process prompt with the model, including retry logic.
        
        Args:
            prompt: The prompt to send to the model
            max_retries: Maximum number of retry attempts
            
        Returns:
            The model's response text
        """
        pass 



