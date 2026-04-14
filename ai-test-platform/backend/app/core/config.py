from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "AI Test Platform"
    database_url: str = "mysql+aiomysql://user:pass@localhost:3306/aitest"
    redis_url: str = "redis://localhost:6379/0"

    # AI 配置
    ai_model: str = "doubao-seed-2.0-code"
    ai_api_key: str = ""
    ai_base_url: str = "https://ark.cn-beijing.volces.com/api/coding/v3"

    # 沙箱配置
    sandbox_image: str = "ai-test-sandbox:latest"
    sandbox_timeout: int = 3600


@lru_cache
def get_settings() -> Settings:
    return Settings()
