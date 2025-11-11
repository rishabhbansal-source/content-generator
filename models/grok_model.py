"""xAI Grok LLM implementation."""

from typing import Optional, List, Dict
import logging
from openai import OpenAI
from models.llm_interface import BaseLLM
from config.llm_config import LLMConfig

logger = logging.getLogger(__name__)


class GrokModel(BaseLLM):
    """xAI Grok model implementation (OpenAI-compatible API)."""

    def _initialize(self):
        """Initialize Grok client."""
        try:
            # Grok uses OpenAI-compatible API
            self.client = OpenAI(
                api_key=self.config.api_key,
                base_url="https://api.x.ai/v1"
            )
            logger.info(f"Grok client initialized with model: {self.config.get_default_model()}")
        except Exception as e:
            logger.error(f"Failed to initialize Grok client: {e}")
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
            logger.error(f"Error generating with Grok: {e}")
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
            logger.error(f"Error generating with Grok: {e}")
            raise

    def test_connection(self) -> bool:
        """Test Grok connection."""
        try:
            response = self.client.chat.completions.create(
                model=self.config.get_default_model(),
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            return bool(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Grok connection test failed: {e}")
            return False
