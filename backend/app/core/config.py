from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name: str = "ProcuraX API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    frontend_origin: str = "http://localhost:5173"
    log_level: str = "INFO"
    demo_mode: bool = True
    data_seed: int = 42
    data_as_of: str = "2026-09-30"
    approval_threshold_inr: int = 10_000_000
    llm_provider: str = "rule_based"
    llm_model: str = ""
    groq_api_key: str = ""
    openrouter_api_key: str = ""
    marketaux_api_token: str = ""
    alpha_vantage_api_key: str = ""
    newsdata_api_key: str = ""
    sec_user_agent: str = "ProcuraXResearch contact@example.com"
    enable_live_signals: bool = False
    database_url: str = ""

    model_config = SettingsConfigDict(env_file=REPOSITORY_ROOT / ".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
