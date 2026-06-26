from __future__ import annotations

from pydantic import BaseModel, Field


class HealthOut(BaseModel):
    status: str
    service: str = "SkillCompass API"
    vacancies_loaded: int
    data_source: str = "postgresql"


class SkillOut(BaseModel):
    name: str
    count: int


class PredictIn(BaseModel):
    analyst_role: str = Field(..., examples=["systems_analyst"])
    experience: str = Field(default="Опыт 1-3 года", examples=["Опыт 1-3 года"])
    area: str = Field(default="all", examples=["Москва", "all"])
    source: str = Field(default="all", examples=["all"])
    employment: str = Field(default="unknown")
    # range | from_only | to_only | all
    salary_spec: str = Field(default="range", examples=["range", "all"])


class PredictOut(BaseModel):
    predicted_salary: float
    currency: str = "RUR"
    model_version: str = "salary_model.joblib"
    top_skills: list[SkillOut] = Field(default_factory=list)
    skills_vacancy_count: int = 0
    skills_experience: str = ""


class VacancyOut(BaseModel):
    source: str
    external_id: str
    title: str
    analyst_role: str | None = None
    role_label: str | None = None
    employer: str | None = None
    area: str | None = None
    experience: str | None = None
    salary_from: float | None = None
    salary_to: float | None = None
    url: str | None = None

    @classmethod
    def from_row(cls, row) -> VacancyOut:
        return cls(
            source=str(row.get("source", "")),
            external_id=str(row.get("external_id", "")),
            title=str(row.get("title", "")),
            analyst_role=row.get("analyst_role"),
            role_label=row.get("role_label"),
            employer=row.get("employer"),
            area=row.get("area"),
            experience=row.get("experience"),
            salary_from=row.get("salary_from") if pd_notna(row.get("salary_from")) else None,
            salary_to=row.get("salary_to") if pd_notna(row.get("salary_to")) else None,
            url=row.get("url"),
        )


def pd_notna(v) -> bool:
    try:
        import pandas as pd

        return pd.notna(v)
    except Exception:
        return v is not None
