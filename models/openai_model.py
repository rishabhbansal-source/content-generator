"""OpenAI LLM implementation."""

from typing import Optional, List, Dict
import logging
from openai import OpenAI
from models.llm_interface import BaseLLM
from config.llm_config import LLMConfig

logger = logging.getLogger(__name__)


class OpenAIModel(BaseLLM):
    """OpenAI GPT model implementation."""

    def _initialize(self):
        """Initialize OpenAI client."""
        try:
            self.client = OpenAI(api_key=self.config.api_key)
            logger.info(f"OpenAI client initialized with model: {self.config.get_default_model()}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
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
            messages = []

            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.config.get_default_model(),
                messages=messages,
                temperature=self._get_temperature(temperature),
                max_tokens=self._get_max_tokens(max_tokens)
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating with OpenAI: {e}")
            raise

    def generate_with_history(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate text with conversation history."""
        try:
            response = self.client.chat.completions.create(
                model=self.config.get_default_model(),
                messages=messages,
                temperature=self._get_temperature(temperature),
                max_tokens=self._get_max_tokens(max_tokens)
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error generating with OpenAI: {e}")
            raise

    def test_connection(self) -> bool:
        """Test OpenAI connection."""
        try:
            response = self.client.chat.completions.create(
                model=self.config.get_default_model(),
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return bool(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"OpenAI connection test failed: {e}")
            return False
