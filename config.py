import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# LLM Providers Configuration
DEFAULT_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # gemini, openrouter, deepseek, anthropic, openai_compatible
DEFAULT_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash")
API_KEY = os.getenv("LLM_API_KEY", "") or os.getenv("GEMINI_API_KEY", "")
BASE_URL = os.getenv("LLM_BASE_URL", "")

# Specific API Keys (if provided separately)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Server & Network Settings
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "7432"))
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "35.0"))
