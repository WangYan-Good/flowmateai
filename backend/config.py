from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 8000

    microsoft_app_id: str = ""
    microsoft_app_password: str = ""
    microsoft_app_tenant_id: str = ""

    llm_provider: str = "openai-compatible"
    llm_base_url: str = "http://localhost:8001/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-oss-120b"
    llm_timeout_seconds: float = Field(default=120.0, gt=0)
    llm_temperature: float = Field(default=0.1, ge=0, le=2)
    llm_max_tokens: int = Field(default=1200, gt=0)
    llm_verify_tls: bool = True
    llm_trust_env_proxy: bool = False
    allow_demo_fallback: bool = False

    @property
    def llm_chat_completions_url(self) -> str:
        base = self.llm_base_url.rstrip("/")
        if base.endswith("/v1"):
            return f"{base}/chat/completions"
        return f"{base}/v1/chat/completions"

    @property
    def llm_display_name(self) -> str:
        return f"{self.llm_provider}/{self.llm_model}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
