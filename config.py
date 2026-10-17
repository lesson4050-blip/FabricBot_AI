import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "mock_bot_token")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    
    # 1C Integration
    erp_1c_base_url: str = os.getenv("ERP_1C_BASE_URL", "http://localhost:8080/hs/stock")
    erp_1c_username: str = os.getenv("ERP_1C_USERNAME", "admin")
    erp_1c_password: str = os.getenv("ERP_1C_PASSWORD", "admin")
    erp_1c_timeout_sec: float = float(os.getenv("ERP_1C_TIMEOUT_SEC", "5.0"))
    
    # Model configuration
    claude_model: str = "claude-3-5-sonnet-20241022"
    
settings = Settings()
