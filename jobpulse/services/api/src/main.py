from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from data_service import (
    get_filter_options,
    get_salary_history,
    get_stats,
    get_top_skills,
    load_dataframe,
    load_metrics,
    query_vacancies,
)
from ml_service import predict_salary
from schemas import HealthOut, PredictIn, PredictOut

app = FastAPI(
    title="SkillCompass API",
    description="IT-аналитики: вакансии и прогноз зарплаты",
    version="1.1.0",
)


@app.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    try:
        n = len(load_dataframe())
        src = get_stats().get("data_source", "postgresql")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return HealthOut(status="ok", vacancies_loaded=n, data_source=src)


@app.get("/data/stats")
def data_stats():
    try:
        return get_stats()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/data/filters")
def data_filters():
    try:
        return get_filter_options()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/data/salary-history")
def salary_history(
    role: str | None = None,
    experience: str | None = None,
):
    try:
        return {"items": get_salary_history(role=role, experience=experience)}
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/data/skills")
def data_skills(
    role: str,
    experience: str | None = None,
    source: str | None = "hh",
    limit: int = Query(default=10, ge=1, le=30),
):
    try:
        items, vacancy_count = get_top_skills(
            analyst_role=role,
            experience=experience,
            source=source,
            limit=limit,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {
        "role": role,
        "experience": experience,
        "vacancy_count": vacancy_count,
        "items": items,
    }


@app.get("/data/vacancies")
def data_vacancies(
    role: str | None = None,
    source: str | None = None,
    experience: str | None = None,
    search: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    try:
        items, total = query_vacancies(
            role=role,
            source=source,
            experience=experience,
            search=search,
            limit=limit,
            offset=offset,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"total": total, "limit": limit, "offset": offset, "items": items}


@app.post("/predict", response_model=PredictOut)
def predict(body: PredictIn) -> PredictOut:
    try:
        return predict_salary(body)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/model/metrics")
def model_metrics():
    return load_metrics()
