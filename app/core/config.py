from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Auth Service"
    VERSION: str = "1.0.0"
    
    # JWT Settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # OpenTelemetry Settings
    OTEL_SERVICE_NAME: str = "auth-service"
    OTEL_SERVICE_VERSION: str = "1.0.0"
    OTEL_ENVIRONMENT: str = "development"
    OTEL_TEMPO_ENDPOINT: str = "http://tempo:4318/v1/traces"
    OTEL_DEBUG: bool = True

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()