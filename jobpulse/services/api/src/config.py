from __future__ import annotations

import os
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_app_root() -> Path:
    if env_root := os.getenv("APP_ROOT"):
        return Path(env_root)
    here = Path(__file__).resolve()
    if len(here.parents) > 3:
        return here.parents[3]
    return here.parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_root: Path = Field(default_factory=_default_app_root)
    database_url: str = Field(
        default="postgresql://datapulse:datapulse_secret@localhost:5432/skillcompass"
    )
    data_parquet: str = ""
    model_path: str = ""
    metrics_path: str = ""
    use_db: bool = True

    @property
    def parquet_file(self) -> Path:
        if self.data_parquet:
            return Path(self.data_parquet)
        return self.app_root / "data" / "processed" / "vacancies.parquet"

    @property
    def model_file(self) -> Path:
        if self.model_path:
            return Path(self.model_path)
        return self.app_root / "ml" / "artifacts" / "salary_model.joblib"

    @property
    def metrics_file(self) -> Path:
        if self.metrics_path:
            return Path(self.metrics_path)
        return self.app_root / "ml" / "artifacts" / "salary_metrics.json"


settings = Settings()
