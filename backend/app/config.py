import os
from pathlib import Path
from typing import List, Union
from pydantic import BaseSettings, validator

BASE_DIR = Path(__file__).resolve().parent.parent
CANONICAL_DB_PATH = (BASE_DIR / "payguard.db").as_posix()

class Settings(BaseSettings):
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: Union[str, List[str]] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    JWT_SECRET: str = "demo-secret-key-payguard-360-replace-in-production-long-secure"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30
    DATABASE_URL: str = f"sqlite:///{CANONICAL_DB_PATH}"
    DEMO_MODE: bool = True
    RULES_CONFIG_PATH: str = "app/risk_rules.json"

    class Config:
        env_file = (".env", "../.env")
        env_file_encoding = "utf-8"
        extra = "ignore"

    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @validator("JWT_SECRET")
    def validate_jwt_secret(cls, v: str) -> str:
        if not v or len(v) < 16:
            raise ValueError("JWT_SECRET must be at least 16 characters long.")
        return v

    @validator("DATABASE_URL", pre=True)
    def normalize_database_url(cls, v: str) -> str:
        if v.startswith("sqlite:///") and (v.startswith("sqlite:///./") or not os.path.isabs(v[10:])):
            rel_path = v[len("sqlite:///"):].lstrip("./")
            return f"sqlite:///{(BASE_DIR / rel_path).as_posix()}"
        return v

settings = Settings()
