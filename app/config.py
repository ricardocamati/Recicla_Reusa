from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    mongo_uri: str = (
        "mongodb://root:Mongo@localhost:27018/recicla_reusa?authSource=admin"
    )
    mongo_database: str = "recicla_reusa"


@lru_cache
def obter_configuracoes() -> Settings:
    return Settings()
