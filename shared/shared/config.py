from pydantic_settings import BaseSettings, SettingsConfigDict


class ServiceConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    SERVICE_NAME: str = "unknown"
    DATABASE_URL: str = "postgresql+asyncpg://realestate:realestate@postgres:5432/db_default"
    KAFKA_BOOTSTRAP: str = "kafka:29092"
    REDIS_URL: str = "redis://redis:6379"

    # Inter-service URLs
    PROPERTY_SERVICE_URL: str = "http://property-listing:8000"
    CRM_SERVICE_URL: str = "http://crm-contact:8000"
    MARKET_SERVICE_URL: str = "http://market-data:8000"

    # LiteLLM
    LITELLM_URL: str = "http://litellm:4000/v1"
    LLM_MODEL: str = "ollama/qwen2.5:14b"
