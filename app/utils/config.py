#config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    cubejs_api_url: str
    cubejs_api_token: str
    openai_api_key: str

    class Config:
        env_file = ".env"

settings = Settings()
