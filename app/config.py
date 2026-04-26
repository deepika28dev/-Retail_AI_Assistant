from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


class Settings(BaseSettings):
    huggingface_api_key: str | None = Field(default=None, alias="HUGGINGFACE_API_KEY")
    huggingface_model: str = Field(default="openai/gpt-oss-120b:fastest", alias="HUGGINGFACE_MODEL")
    huggingface_base_url: str = Field(
        default="https://router.huggingface.co/v1",
        alias="HUGGINGFACE_BASE_URL",
    )
    products_csv_path: Path = Field(
        default=DATA_DIR / "product_inventory.csv",
        alias="PRODUCTS_CSV_PATH",
    )
    orders_csv_path: Path = Field(
        default=DATA_DIR / "orders.csv",
        alias="ORDERS_CSV_PATH",
    )
    policy_path: Path = Field(
        default=DATA_DIR / "policy.txt",
        alias="POLICY_PATH",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
