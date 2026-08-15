from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from pydantic import model_validator
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://pie:pie@localhost:5432/pie"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"

    # Provider-agnostic settings
    llm_provider: str = "groq"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    llm_api_key: str = ""
    llm_model: str = "llama-3.1-8b-instant"

    extraction_cache_dir: str = ".cache/extractions"
    corpus_dir: str = "app/corpus"
    embedding_model: str = "all-mpnet-base-v2"
    embed_corpus: bool = True
    log_level: str = "INFO"

    @model_validator(mode="after")
    def fallback_settings(self) -> "Settings":
        # Dynamic defaults depending on provider
        if self.llm_provider == "qwen":
            if self.llm_base_url == "https://api.groq.com/openai/v1":
                self.llm_base_url = "https://ws-h28trj7vdat6f6dv.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1"
            if self.llm_model == "llama-3.1-8b-instant":
                self.llm_model = "qwen-plus"

        # Fallback to GROQ settings if LLM_API_KEY is not set but GROQ_API_KEY is
        if not self.llm_api_key and self.groq_api_key:
            self.llm_api_key = self.groq_api_key
        if self.llm_provider == "groq":
            if self.llm_model == "llama-3.1-8b-instant" and self.groq_model != "llama-3.1-8b-instant":
                self.llm_model = self.groq_model
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()

