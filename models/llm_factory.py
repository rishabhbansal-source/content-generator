"""Factory for creating LLM instances."""

from typing import Optional
from config.llm_config import LLMConfig, LLMProvider
from models.llm_interface import BaseLLM
from models.openai_model import OpenAIModel
from models.gemini_model import GeminiModel
from models.claude_model import ClaudeModel
from models.grok_model import GrokModel


class LLMFactory:
    """Factory for creating LLM instances."""

    @staticmethod
    def create(config: LLMConfig) -> BaseLLM:
        """
        Create an LLM instance based on configuration.

        Args:
            config: LLM configuration

        Returns:
            LLM instance

        Raises:
            ValueError: If provider is not supported
        """
        models = {
            LLMProvider.OPENAI: OpenAIModel,
            LLMProvider.GEMINI: GeminiModel,
            LLMProvider.CLAUDE: ClaudeModel,
            LLMProvider.GROK: GrokModel
        }

        model_class = models.get(config.provider)
        if not model_class:
            raise ValueError(f"Unsupported LLM provider: {config.provider}")

        return model_class(config)

    @staticmethod
    def create_from_params(
        provider: str,
        api_key: str,
        model_name: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> BaseLLM:
        """
        Create an LLM instance from individual parameters.

        Args:
            provider: Provider name (openai, gemini, claude, grok)
            api_key: API key
            model_name: Model name (optional, uses default if not provided)
            temperature: Temperature setting
            max_tokens: Maximum tokens

        Returns:
            LLM instance
        """
        # Convert string to LLMProvider enum
        provider_map = {
            "openai": LLMProvider.OPENAI,
            "gemini": LLMProvider.GEMINI,
            "google": LLMProvider.GEMINI,
            "claude": LLMProvider.CLAUDE,
            "anthropic": LLMProvider.CLAUDE,
            "grok": LLMProvider.GROK,
            "xai": LLMProvider.GROK
        }

        provider_enum = provider_map.get(provider.lower())
        if not provider_enum:
            raise ValueError(f"Unknown provider: {provider}")

        config = LLMConfig(
            provider=provider_enum,
            api_key=api_key,
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )

        return LLMFactory.create(config)
