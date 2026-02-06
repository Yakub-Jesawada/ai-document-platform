from pydantic_settings import BaseSettings
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    # Database settings
    DATABASE_URL: str    
    BASE_FILE_PATH: str
    KAFKA_BROKER_URL: str
    OCR_WORKER_TOPIC: str
    CHUNK_WORKER_TOPIC: str
    KAFKA_FASTAPI_PRODUCER_CLIENT_ID: str


    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Application settings
    DEBUG: bool = True
    ALLOWED_HOSTS: str = "*"
    
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # This is important - it allows extra fields
        extra = "allow"

        # Add field validation for boolean strings
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name in ["DEBUG"]:
                return raw_val.upper() == "TRUE"
            return raw_val

settings = Settings()