from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # JWT
    SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_ENV_VAR"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Groq
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-70b-versatile"

    # Database
    DATABASE_URL: str = "sqlite:///./reviews.db"

    # GitHub App (for the BugLens bot)
    GITHUB_APP_ID: str = ""                 # e.g. "123456"
    GITHUB_PRIVATE_KEY: str = ""            # PEM text of your GitHub App's private key
    GITHUB_WEBHOOK_SECRET: str = ""         # The secret you set when creating the App


settings = Settings()
