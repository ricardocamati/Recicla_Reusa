from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_database: str = "recicla_reusa"
    mongo_collection_usuarios: str = "usuarios"
    cors_origins: str = "http://localhost:5500,http://127.0.0.1:5500"
    secure_cookies: bool = False

    def origens_cors(self) -> list[str]:
        return [origem.strip() for origem in self.cors_origins.split(",") if origem.strip()]
