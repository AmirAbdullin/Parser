# SkillCompass — к консультации (80–90%)

## Что показать (5 мин)

1. **Docker** — `docker compose ps` (db + ingestor + api + dashboard)
2. **Overview** — KPI, роли, boxplot зарплат, график динамики
3. **Predictions** — dropdown опыт/город, прогноз + **топ навыков HH**
4. **Data** — фильтр по роли
5. **Swagger** — `GET /data/stats`, `POST /predict`

## Что сказать про данные

- 4 роли IT-аналитиков, RU + EN запросы
- Фильтр шума (брокер, химик, кредитный аналитик…)
- Дедуп по `(source, id)`, роль из **названия** вакансии
- Cap зарплат 30k–600k ₽
- HH + SuperJob, ingest каждые **4 часа**
- PostgreSQL — единый источник для API

## Команды перед консультацией

```powershell
cd c:\Users\snaki\b2b\b2b\local-tasks\datapulse\jobpulse
docker compose up -d --build
docker compose run --rm ingestor python -m ingestor.main --once
docker compose exec api python -c "print('ok')"
```

После ingest (может занять 10–20 мин из‑за навыков HH):

```powershell
python scripts/export_parquet_from_db.py
python ml/training/train_salary.py
docker compose restart api dashboard
```

## Если спросят «что дальше»

- Gradio (опционально)
- SuperJob skills из текста (NLP)
- Облачная БД вместо локальной Postgres в Docker
