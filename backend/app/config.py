from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
import os


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://pie:pie@localhost:5432/pie"
    groq_api_key: str = ""
    groq_model: str = "llama3-8b-8192"
    extraction_cache_dir: str = ".cache/extractions"
    corpus_dir: str = "app/corpus"
    embedding_model: str = "all-mpnet-base-v2"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
