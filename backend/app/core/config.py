from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BCW_", env_file=".env", extra="ignore")

    env: str = "dev"
    log_level: str = "INFO"

    db_host: str = "mysql"
    db_port: int = 3306
    db_user: str = "bcw"
    db_password: str = "bcw_dev_password"
    db_name: str = "bill_classifier_web"

    jwt_secret: str = "change-me"
    jwt_alg: str = "HS256"
    jwt_access_ttl_min: int = 120
    jwt_refresh_ttl_days: int = 14

    fernet_key: str = "change-me"

    cors_origins: str = "http://localhost:5173"
    upload_max_bytes: int = 10 * 1024 * 1024

    @property
    def database_url(self) -> str:
        return (
            f"mysql+asyncmy://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @property
    def sync_database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}?charset=utf8mb4"
        )

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
