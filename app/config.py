import os
from functools import lru_cache


class Settings:
    API_KEY: str = os.getenv("API_KEY", "your-secret-api-key")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "/tmp/uploads")
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))


@lru_cache()
def get_settings() -> Settings:
    return Settings()
