from pydantic_settings import BaseSettings
from typing import Optional

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
    CORS_ORIGINS: list[str] = ["*"]
    
    # OpenTelemetry
    OTEL_SERVICE_NAME: str = "auth-service"
    OTEL_EXPORTER_OTLP_ENDPOINT: Optional[str] = "http://localhost:4317"

    # This is a special Pydantic subclass that is automatically loaded when the Settings class is instantiated. Currently its only function is to load the environment variables from the .env file. If the environment variable loaded has the same property name as the class property, it will override the default value.
    class Config: 
        case_sensitive = True
        env_file = ".env"

settings = Settings()