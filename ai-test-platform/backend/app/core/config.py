from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "AI Test Platform"
    database_url: str = "mysql+aiomysql://user:pass@localhost:3306/aitest"
    redis_url: str = "redis://localhost:6379/0"

    # AI 配置
    ai_provider: str = "doubao"  # 可选: doubao, minimax, ollama
    ai_model: str = "doubao-seed-2.0-code"
    ai_api_key: str = ""
    ai_base_url: str = "https://ark.cn-beijing.volces.com/api/coding/v3"

    # Minimax 配置
    minimax_api_key: str = ""
    minimax_base_url: str = "https://api.minimaxi.com/v1"
    minimax_model: str = "MiniMax-M2.7"

    # Ollama 本地配置
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.2"

    # 沙箱配置
    sandbox_image: str = "ai-test-sandbox:latest"
    sandbox_timeout: int = 3600
    registry_url: str = ""

    # Appium 配置
    appium_host: str = "localhost"
    appium_port: str = "4723"
    android_sdk_path: str = ""
    ios_sdk_path: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
