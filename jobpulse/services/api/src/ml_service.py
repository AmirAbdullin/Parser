from __future__ import annotations

import joblib
import pandas as pd

from config import settings
from data_service import get_top_skills
from schemas import PredictIn, PredictOut

_bundle = None

ALL_AREA = "all"
ALL_SALARY_SPEC = "all"
_SALARY_SPECS = ("range", "from_only", "to_only")


def _load_bundle():
    global _bundle
    if _bundle is None:
        path = settings.model_file
        if not path.exists():
            raise FileNotFoundError(f"Model not found: {path}. Run ml/training/train_salary.py")
        _bundle = joblib.load(path)
    return _bundle


def _resolve_areas(area: str) -> list[str]:
    if area in ("", ALL_AREA):
        return ["unknown"]
    return [area]


def _resolve_salary_specs(salary_spec: str) -> list[str]:
    if salary_spec in ("", ALL_SALARY_SPEC):
        return list(_SALARY_SPECS)
    return [salary_spec]


def _predict_batch(model, cols: list[str], rows: list[dict]) -> float:
    if not rows:
        return 0.0
    df = pd.DataFrame(rows)
    for col in cols:
        if col not in df.columns:
            df[col] = "unknown"
    preds = model.predict(df[cols])
    return float(preds.mean())


def _predict_for_source(model, cols: list[str], base: dict, source: str) -> float:
    rows = [
        {
            "analyst_role": base["analyst_role"],
            "experience": base["experience"],
            "area": area,
            "employment": base["employment"],
            "salary_spec": spec,
            "source": source,
        }
        for area in _resolve_areas(base["area"])
        for spec in _resolve_salary_specs(base["salary_spec"])
    ]
    return _predict_batch(model, cols, rows)


def predict_salary(body: PredictIn) -> PredictOut:
    bundle = _load_bundle()
    model = bundle["model"]
    cols = bundle["feature_columns"]

    base = {
        "analyst_role": body.analyst_role,
        "experience": body.experience,
        "area": body.area,
        "employment": body.employment,
        "salary_spec": body.salary_spec,
    }

    if body.source == "all":
        pred_hh = _predict_for_source(model, cols, base, "hh")
        pred_sj = _predict_for_source(model, cols, base, "superjob")
        pred = (pred_hh + pred_sj) / 2
    else:
        source_for_model = body.source if body.source not in ("all", "") else "hh"
        pred = _predict_for_source(model, cols, base, source_for_model)

    skills, vacancy_count = get_top_skills(
        analyst_role=body.analyst_role,
        experience=body.experience,
        source=body.source,
        limit=10,
    )

    return PredictOut(
        predicted_salary=round(pred, 2),
        top_skills=skills,
        skills_vacancy_count=vacancy_count,
        skills_experience=body.experience,
    )
