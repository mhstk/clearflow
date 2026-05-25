from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    PROJECT_NAME: str = "Personal Finance Intelligence API"
    API_V1_PREFIX: str = "/api/v1"

    # Environment: "development" or "production"
    ENV: str = "development"

    # Database - SQLite for dev, PostgreSQL for production
    DATABASE_URL: str = "sqlite:///./finance.db"

    # AI Provider selection: "openrouter" (default) or "groq"
    AI_PROVIDER: str = "openrouter"

    # AI Settings - OpenRouter
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "amazon/nova-2-lite-v1:free"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # AI Settings - Groq (OpenAI-compatible API)
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # JWT Settings
    JWT_SECRET_KEY: str = "change-this-secret-key-in-production"  # Generate with: openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Google OAuth Settings
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:5173/auth/google/callback"

    # CORS - comma-separated origins for production
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Demo user ID (existing data)
    DEMO_USER_ID: int = 1

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string into list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.ENV.lower() == "production"

    @property
    def ai_provider(self) -> str:
        """Normalized active AI provider name ("openrouter" or "groq")."""
        return self.AI_PROVIDER.lower()

    @property
    def ai_api_key(self) -> Optional[str]:
        """API key for the active AI provider."""
        if self.ai_provider == "groq":
            return self.GROQ_API_KEY
        return self.OPENROUTER_API_KEY

    @property
    def ai_model(self) -> str:
        """Model name for the active AI provider."""
        if self.ai_provider == "groq":
            return self.GROQ_MODEL
        return self.OPENROUTER_MODEL

    @property
    def ai_base_url(self) -> str:
        """Base URL for the active AI provider (OpenAI-compatible /chat/completions)."""
        if self.ai_provider == "groq":
            return self.GROQ_BASE_URL
        return self.OPENROUTER_BASE_URL

    @property
    def ai_extra_body(self) -> dict:
        """Provider-specific extra request body.

        OpenRouter supports a `reasoning` field; Groq rejects unknown properties,
        so it must be omitted there.
        """
        if self.ai_provider == "groq":
            return {}
        return {"reasoning": {"enabled": True}}

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
