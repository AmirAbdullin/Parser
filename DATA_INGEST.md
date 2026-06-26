# SkillCompass — откуда данные в БД

Код: `jobpulse/`

---

## Кто пишет в PostgreSQL

**Только сервис `ingestor`.** API и dashboard читают БД, к HH не ходят.

```
HH.ru + SuperJob → ingestor → PostgreSQL → API → Streamlit
```

Цепочка:

```
ingestor.main → pipeline.run_ingest()
  → collect HH (поток A + B с ЗП)
  → collect SuperJob
  → merge_and_clean_rows()
  → enrich_hh_rows_with_details()   # key_skills, недостающие поля
  → upsert_vacancies()
  → save_salary_snapshots()
```

---

## Команды

| Способ | Команда |
|--------|---------|
| По расписанию (Docker) | `python -m ingestor.main` |
| Один прогон | `docker compose run --rm ingestor python -m ingestor.main --once` |
| Backfill навыков | `python scripts/backfill_hh_skills.py` |
| Без Docker (parquet) | `python scripts/fetch_all.py` |

После ingest — переобучение ML:

```powershell
python scripts/export_parquet_from_db.py
python ml/training/train_salary.py
docker compose restart api dashboard
```

---

## Демо без повторного сбора

Данные в Docker-volume `postgres_data`. Для презентации:

```powershell
docker compose up -d db api dashboard
```

Ingestor **не запускать** — в БД уже ~3075 вакансий.

---

## CI/CD

`.github/workflows/deploy.yml`: push в `main` → SSH на сервер → `git pull` → `docker compose up -d --build`.

Volume БД сохраняется между деплоями.

---

## Актуальные объёмы (2026-06-26)

| Метрика | Значение |
|---------|----------|
| Всего | 3075 |
| С ЗП | 1104 |
| С key_skills | 1870 |
| HH / SuperJob | 2988 / 87 |

На **Мониторинге** «вакансий сохранено» — число записей за последний успешный ingest.
