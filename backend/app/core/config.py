import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # App Settings
    PROJECT_NAME: str = "Shamba AI"
    API_V1_STR: str = "/api/v1"
    
    # Database Configuration (PostgreSQL, TiDB Cloud, SQLite fallback)
    # Default is a local SQLite database for easy development
    DATABASE_URL: str = "sqlite:///./shamba_ai.db"
    
    # JWT Authentication
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_ENV"  # Override in .env for production!
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Firebase Configuration
    FIREBASE_PROJECT_ID: Optional[str] = None
    FIREBASE_CREDENTIALS_JSON: Optional[str] = None  # Path to service account JSON or inline JSON
    FIREBASE_API_KEY: Optional[str] = None            # Client-side Firebase API key
    FIREBASE_AUTH_DOMAIN: Optional[str] = None
    FIREBASE_STORAGE_BUCKET: Optional[str] = None
    FIREBASE_MESSAGING_SENDER_ID: Optional[str] = None
    FIREBASE_APP_ID: Optional[str] = None
    FIREBASE_MEASUREMENT_ID: Optional[str] = None
    
    # AI Services — Gemini (Google)
    GEMINI_API_KEY_1: Optional[str] = None   # Primary Gemini key
    GEMINI_API_KEY_2: Optional[str] = None   # Secondary/failover Gemini key
    
    # AI Services — OpenAI
    OPENAI_API_KEY_1: Optional[str] = None   # Primary OpenAI key (NLP tasks, voice transcription)
    OPENAI_API_KEY_2: Optional[str] = None   # Secondary/failover OpenAI key
    
    # Plant Disease Detection — Plant.id
    PLANT_ID_API_KEY: Optional[str] = None   # Plant.id API key for crop disease identification
    
    # Weather Services Configuration
    WEATHER_API_KEY: Optional[str] = None    # OpenWeatherMap API key
    
    # Satellite Data Provider Toggle
    # Options: 'sentinel' (default, active) or 'gee' (pending credentials)
    SATELLITE_PROVIDER: str = "sentinel"
    
    # Sentinel Hub — Active satellite data provider
    SENTINEL_API_KEY: Optional[str] = None
    SENTINEL_USER_ID: Optional[str] = None
    
    # Google Earth Engine (GEE) — INACTIVE / Pending credentials
    # Kept for future use. Set SATELLITE_PROVIDER=gee to activate once configured.
    GEE_SERVICE_ACCOUNT_EMAIL: Optional[str] = None
    GEE_PRIVATE_KEY_FILE: Optional[str] = None
    
    @property
    def GEMINI_API_KEY(self) -> Optional[str]:
        """Returns the first available Gemini API key for backward compatibility."""
        return self.GEMINI_API_KEY_1 or self.GEMINI_API_KEY_2
    
    @property
    def OPENAI_API_KEY(self) -> Optional[str]:
        """Returns the first available OpenAI API key."""
        return self.OPENAI_API_KEY_1 or self.OPENAI_API_KEY_2
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

settings = Settings()
