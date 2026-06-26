# SkillCompass — onboarding

## Задача

DataPulse, проект **SkillCompass**: вакансии **IT-аналитиков** (BA, SA, PA, DA), ML-прогноз зарплаты, FastAPI, Streamlit, Docker.

Код: `local-tasks/datapulse/jobpulse/` (целевое имя папки: `skillcompass`).

## Ограничения домена

Только 4 роли — см. `services/ingestor/src/ingestor/roles.py`. Не расширять на общий IT без согласования.

## Что нужно от пользователя

1. `.env` с реальным email в `HH_USER_AGENT=SkillCompass/1.0 (...)`
2. `SUPERJOB_API_KEY`
3. `python scripts/fetch_sample.py` — проверка HH

## Не править

- `platform-source-code/`, `docs/` — read-only (репозиторий b2b).
