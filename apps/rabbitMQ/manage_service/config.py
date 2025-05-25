from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATA_URL: str
    BUSSINESS_URL: str
    RABBITMQ_URL: str
    RABBITMQ_HOST: str
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str
    RABBITMQ_MANAGEMENT_URL: str

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
