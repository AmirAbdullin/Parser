from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://datapulse:datapulse_secret@localhost:5432/datapulse"
    hh_user_agent: str = "SkillCompass/1.0 (datapulse@example.com)"
    superjob_api_key: str = ""
    ingest_area_id: int = 0  # 0 = вся Россия; 1 = Москва
    ingest_max_pages: int = 20
    ingest_max_pages_salary: int = 40  # поток only_with_salary; 0 = до конца выдачи
    ingest_schedule_hours: int = 4
    ingest_collect_salary_stream: bool = True
    ingest_detail_enrich: bool = True
    ingest_detail_limit: int = 0  # 0 = все HH без salary/skills
    ingest_detail_sleep_sec: float = 0.12
    ingest_skills_limit: int = 400  # legacy, для fetch_all fallback


settings = Settings()
