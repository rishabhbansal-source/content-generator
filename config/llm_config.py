"""LLM configuration settings."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class LLMProvider(Enum):
    """Available LLM providers."""
    OPENAI = "openai"
    GEMINI = "gemini"
    CLAUDE = "claude"
    GROK = "grok"


@dataclass
class LLMConfig:
    """LLM configuration."""
    provider: LLMProvider
    api_key: str
    model_name: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000

    def get_default_model(self) -> str:
        """Get default model name for the provider."""
        defaults = {
            LLMProvider.OPENAI: "gpt-4-turbo-preview",
            LLMProvider.GEMINI: "gemini-1.5-flash",  # Most reliable and fast
            LLMProvider.CLAUDE: "claude-3-sonnet-20240229",
            LLMProvider.GROK: "grok-1"
        }
        return self.model_name or defaults.get(self.provider, "")


# Model options for UI
MODEL_OPTIONS = {
    "OpenAI": {
        "GPT-4 Turbo": "gpt-4-turbo-preview",
        "GPT-4": "gpt-4",
        "GPT-3.5 Turbo": "gpt-3.5-turbo"
    },
    "Google Gemini": {
        "Gemini 2.0 Flash Exp": "gemini-2.0-flash-exp",
        "Gemini 2.5 Flash": "gemini-2.5-flash"
    },
    "Anthropic Claude": {
        "Claude 3.5 Sonnet": "claude-3.5-sonnet-20241022",
        "Claude 3.5 Haiku": "claude-3.5-haiku-20241022",
        "Claude 4 Sonnet": "claude-4-sonnet-20250219"
    },
    "xAI Grok": {
        "Grok 2": "grok-2"
    }
}
