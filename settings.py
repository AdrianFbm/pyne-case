from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "extra": "ignore"}

    llm_provider: str = ""
    llm_model: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    max_tokens: int = 1024
    temperature: float = 0.0

    @model_validator(mode="after")
    def _resolve_provider(self):
        if not self.llm_provider:
            if self.anthropic_api_key:
                self.llm_provider = "anthropic"
            elif self.openai_api_key:
                self.llm_provider = "openai"
            else:
                raise ValueError(
                    "No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY in .env"
                )

        if self.llm_provider not in ("anthropic", "openai"):
            raise ValueError(f"Unknown LLM_PROVIDER: {self.llm_provider!r}")

        if not self.llm_model:
            self.llm_model = {
                "anthropic": "claude-sonnet-4-20250514",
                "openai": "gpt-4o",
            }[self.llm_provider]

        return self


settings = Settings()
