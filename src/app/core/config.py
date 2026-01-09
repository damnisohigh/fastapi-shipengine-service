from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "src/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "local"
    database_url: str
    redis_url: str
    sql_echo: bool = False


settings = Settings()