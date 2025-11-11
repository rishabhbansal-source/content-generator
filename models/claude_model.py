"""Anthropic Claude LLM implementation."""

from typing import Optional, List, Dict
import logging
from anthropic import Anthropic
from models.llm_interface import BaseLLM
from config.llm_config import LLMConfig

logger = logging.getLogger(__name__)


class ClaudeModel(BaseLLM):
    """Anthropic Claude model implementation."""

    def _initialize(self):
        """Initialize Anthropic client."""
        try:
            self.client = Anthropic(api_key=self.config.api_key)
            logger.info(f"Claude client initialized with model: {self.config.get_default_model()}")
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {e}")
            raise

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text from a prompt."""
        try:
            kwargs = {
                "model": self.config.get_default_model(),
                "messages": [{"role": "user", "content": prompt}],
                "temperature": self._get_temperature(temperature),
                "max_tokens": self._get_max_tokens(max_tokens)
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            response = self.client.messages.create(**kwargs)

            return response.content[0].text

        except Exception as e:
            logger.error(f"Error generating with Claude: {e}")
            raise

    def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text with conversation history."""
        try:
            # Extract system message if present
            system_prompt = None
            user_messages = []

            for msg in messages:
                if msg["role"] == "system":
                    system_prompt = msg["content"]
                else:
                    # Claude expects 'user' and 'assistant' roles
                    role = "assistant" if msg["role"] == "assistant" else "user"
                    user_messages.append({"role": role, "content": msg["content"]})

            kwargs = {
                "model": self.config.get_default_model(),
                "messages": user_messages,
                "temperature": self._get_temperature(temperature),
                "max_tokens": self._get_max_tokens(max_tokens)
            }

            if system_prompt:
                kwargs["system"] = system_prompt

            response = self.client.messages.create(**kwargs)

            return response.content[0].text

        except Exception as e:
            logger.error(f"Error generating with Claude: {e}")
            raise

    def test_connection(self) -> bool:
        """Test Claude connection."""
        try:
            response = self.client.messages.create(
                model=self.config.get_default_model(),
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return bool(response.content[0].text)
        except Exception as e:
            logger.error(f"Claude connection test failed: {e}")
            return False
