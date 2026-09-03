from pathlib import Path
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DATABASE_URL: str = "sqlite+aiosqlite:///data/webqa.db"
    DATA_DIRECTORY: str = "data"
    
    # Playwright Settings
    PLAYWRIGHT_BROWSER: str = "chromium"
    PLAYWRIGHT_HEADLESS: bool = True
    DEFAULT_MAX_PAGES: int = 50
    DEFAULT_MAX_DEPTH: int = 3
    DEFAULT_WORKERS: int = 3
    REQUEST_TIMEOUT_MS: int = 30000
    
    # AI Optional Settings
    AI_ENABLED: bool = False
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # CI Quality Gates
    CI_FAIL_ON_CRITICAL: bool = True
    CI_MAX_HIGH_ISSUES: int = 3
    CI_MIN_QA_SCORE: int = 80

    model_config = {"env_file": ".env", "extra": "allow"}

settings = Settings()

# Ensure runtime directories exist
DATA_DIR = Path(settings.DATA_DIRECTORY)
for subdir in ["screenshots", "traces", "videos", "reports", "baselines", "auth"]:
    (DATA_DIR / subdir).mkdir(parents=True, exist_ok=True)
