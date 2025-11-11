"""Abstract LLM interface for multi-model support."""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from config.llm_config import LLMConfig


class BaseLLM(ABC):
    """Abstract base class for LLM implementations."""

    def __init__(self, config: LLMConfig):
        """
        Initialize LLM.

        Args:
            config: LLM configuration
        """
        self.config = config
        self.client = None
        self._initialize()

    @abstractmethod
    def _initialize(self):
        """Initialize the LLM client."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text from a prompt.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Temperature override (optional)
            max_tokens: Max tokens override (optional)

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate text with conversation history.

        Args:
            messages: List of messages with 'role' and 'content'
            temperature: Temperature override (optional)
            max_tokens: Max tokens override (optional)

        Returns:
            Generated text
        """
        pass

    def _get_temperature(self, override: Optional[float] = None) -> float:
        """Get temperature value."""
        return override if override is not None else self.config.temperature

    def _get_max_tokens(self, override: Optional[int] = None) -> int:
        """Get max tokens value."""
        return override if override is not None else self.config.max_tokens

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test the LLM connection.

        Returns:
            True if connection is successful
        """
        pass
