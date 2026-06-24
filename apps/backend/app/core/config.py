from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_JWT_SECRET = "change-me-in-production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/startup_engine"
    GIGACHAT_CLIENT_ID: str = ""
    GIGACHAT_CLIENT_SECRET: str = ""
    JWT_SECRET: str = _INSECURE_JWT_SECRET
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    DEMO_MODE: bool = False
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    APP_VERSION: str = "2.0.0"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in {"production", "prod"}

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        if self.is_production and self.JWT_SECRET == _INSECURE_JWT_SECRET:
            raise ValueError(
                "JWT_SECRET must be set to a strong, unique value in production "
                "(the default placeholder is not allowed)."
            )
        return self


settings = Settings()
