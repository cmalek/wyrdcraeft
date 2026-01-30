from __future__ import annotations

from dataclasses import dataclass

from wyrdcraeft.exc import ConfigurationError


@dataclass(frozen=True)
class AnyLLMConfig:
    """Configuration for Python any-llm."""

    #: The provider to use for any-llm.
    provider: str = "ollama"
    #: The model ID to use for any-llm.
    model_id: str = "qwen2.5:14b-instruct"
    #: The temperature to use for any-llm.
    temperature: float = 0.0
    #: The maximum number of tokens to use for any-llm.
    max_tokens: int = 4096
    #: The timeout in seconds for any-llm.
    timeout_s: int = 120

    @property
    def api_key(self) -> str | None:
        """
        Get the API key for the LLM provider.
        """
        # Avoid circular import
        from wyrdcraeft.settings import Settings  # noqa: PLC0415

        if self.provider == "openai":
            if Settings().openai_api_key is None:
                msg = "You chose an openai model bu OpenAI API key is not set"
                raise ConfigurationError(msg)
            return Settings().openai_api_key
        if self.provider == "gemini":
            if Settings().gemini_api_key is None:
                msg = "You chose a gemini model but no Gemini API key is set"
                raise ConfigurationError(msg)
            return Settings().gemini_api_key
        return None

    @property
    def model(self) -> str:
        """
        Get the model ID.

        Raises:
            ValueError: If we can't determine the model.

        Returns:
            The model ID.

        """
        if self.model_id.startswith("qwen"):
            return "qwen"
        if self.model_id.startswith("gemini"):
            return "gemini"
        if self.model_id.startswith(("gpt-", "o1", "o3")):
            return "openai"
        msg = f"Unknown model ID: {self.model_id}"
        raise ValueError(msg)
