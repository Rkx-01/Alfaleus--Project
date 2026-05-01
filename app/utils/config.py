from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "News Digest API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/news_db"
    
    # AI & Security
    GROQ_API_KEY: Optional[str] = None
    NEWSAPI_API_KEY: Optional[str] = None
    API_KEY: str = "supersecretapikey" # Default for demo
    
    # Scheduler
    COLLECT_INTERVAL_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)

settings = Settings()
