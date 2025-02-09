from pydantic_settings import BaseSettings
from typing import List, Union, Optional

class Settings(BaseSettings):
    # Required (no default)
    DATABASE_URL: str                # Must be provided
    POSTGRES_USER: str              # Must be provided
    POSTGRES_PASSWORD: str          # Must be provided
    JWT_SECRET_KEY: str            # Must be provided
    
    # Optional (with defaults)
    APP_NAME: str = "Auth Service"  # Optional, has default
    VERSION: str = "1.0.0"         # Optional, has default
    JWT_ALGORITHM: str = "HS256"   # Optional, has default
    
    # New variables from error
    DEV_MANIFEST_REPO: Optional[str] = None
    HELM_REGISTRY: Optional[str] = None
    K8S_NAMESPACE: Optional[str] = None
    
    # JWT Settings
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    POSTGRES_DB: str
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]
    
    # OpenTelemetry Settings
    OTEL_SERVICE_NAME: str = "auth-service"
    OTEL_SERVICE_VERSION: str = "1.0.0"
    OTEL_ENVIRONMENT: str = "development"
    OTEL_TEMPO_ENDPOINT: str = "http://tempo:4318/v1/traces"
    OTEL_DEBUG: bool = True

    # Development settings (with defaults)
    LOGGING_APP: Optional[str] = None
    TRACING_APP: Optional[str] = None
    API_PATH: str = "/api/v1"
    TRACES_ENDPOINT: Optional[str] = None
    LOGS_ENDPOINT: Optional[str] = None

    # Add these settings
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"
    FRONTEND_URL: str = "http://localhost:3000"  # For redirecting back to frontend

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()