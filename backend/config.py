from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = ""
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    CATALOG_PATH: Path = Path(__file__).parent / "catalog" / "iphone_catalog.json"
    REVIEW_SCORES_PATH: Path = Path(__file__).parents[1] / "pipeline" / "data" / "derived" / "review_aspect_scores.json"

    class Config:
        env_file = Path(__file__).parents[1] / ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
