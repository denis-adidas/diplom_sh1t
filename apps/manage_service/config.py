from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    URL: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
