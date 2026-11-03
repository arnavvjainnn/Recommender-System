import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the backend project
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # App Settings
    APP_NAME: str = "RecommendAI API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_STR: str = "/api"
    
    # Security & Auth
    SECRET_KEY: str = "supersecretrecommendai-key-change-in-production-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # Database
    # Defaults to local SQLite for instant zero-config startup, overridden by POSTGRES_URL in .env
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'recommendai.db'}"
    
    # Recommendation System Hyperparameters
    WEIGHT_COLLABORATIVE: float = 0.45
    WEIGHT_CONTENT: float = 0.35
    WEIGHT_POPULARITY: float = 0.20
    MMR_DIVERSITY_LAMBDA: float = 0.75  # 1.0 = Pure relevance, 0.0 = Pure diversity
    INTERACTION_HALF_LIFE_DAYS: float = 30.0
    TOP_K_DEFAULT: int = 10
    RANDOM_SEED: int = 42
    
    # Implicit Feedback Event Weights
    EVENT_WEIGHTS: dict = {
        "VIEW": 1.0,
        "CLICK": 2.0,
        "SEARCH_CLICK": 2.5,
        "LIKE": 3.0,
        "WISHLIST": 4.0,
        "ADD_TO_CART": 5.0,
        "PURCHASE": 8.0,
        "RATING": 6.0
    }
    
    # ML Model Artifact Paths
    MODEL_DIR: Path = BASE_DIR / "ml" / "saved_models"
    TFIDF_VECTORIZER_PATH: Path = BASE_DIR / "ml" / "saved_models" / "tfidf_vectorizer.pkl"
    CONTENT_SIMILARITY_PATH: Path = BASE_DIR / "ml" / "saved_models" / "content_similarity.pkl"
    COLLABORATIVE_MODEL_PATH: Path = BASE_DIR / "ml" / "saved_models" / "collaborative_model.pkl"
    POPULARITY_MODEL_PATH: Path = BASE_DIR / "ml" / "saved_models" / "popularity_model.pkl"
    ASSOCIATION_RULES_PATH: Path = BASE_DIR / "ml" / "saved_models" / "association_rules.pkl"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ]

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure model directory exists
os.makedirs(settings.MODEL_DIR, exist_ok=True)
