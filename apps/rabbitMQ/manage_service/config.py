from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATA_URL: str
    BUSSINESS_URL: str
    RABBITMQ_URL: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
