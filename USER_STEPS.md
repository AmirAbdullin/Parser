# SkillCompass — запуск и деплой

## Требования

- Docker Desktop (рекомендуется) или Python 3.12+
- Ключ [SuperJob API](https://api.superjob.ru/register/)
- User-Agent для HH: `SkillCompass/1.0 (your@email.com)`

## 1. Настройка окружения

```powershell
cd jobpulse
copy .env.example .env
```

Заполните в `.env`:

```env
HH_USER_AGENT=SkillCompass/1.0 (your@email.com)
SUPERJOB_API_KEY=your_key
DB_NAME=datapulse
```

## 2. Запуск (Docker)

```powershell
docker compose up -d --build
docker compose ps
```

| Сервис | Порт | Назначение |
|--------|------|------------|
| dashboard | 8501 | Streamlit UI |
| api | 8000 | FastAPI + Swagger |
| db | 5432 | PostgreSQL |
| ingestor | — | сбор данных по расписанию |

**Демо без повторного сбора с HH:**

```powershell
docker compose up -d db api dashboard
```

## 3. Переобучение ML

После обновления данных в БД:

```powershell
python scripts/export_parquet_from_db.py
python ml/training/train_salary.py
docker compose restart api dashboard
```

На Windows `export_parquet_from_db.py` подключается к `localhost:5432`.

## 4. Ручной ingest

```powershell
docker compose run --rm ingestor python -m ingestor.main --once
```

## 5. Деплой на сервер

Push в ветку `main` запускает GitHub Actions (`.github/workflows/deploy.yml`):

1. SSH на сервер
2. `git pull` в `~/Parser/jobpulse`
3. `docker compose up -d --build --force-recreate`

Volume PostgreSQL сохраняется между деплоями.

## 6. Проверка перед презентацией

- [ ] http://localhost:8501 — **Мониторинг** показывает зелёный статус
- [ ] **Общая статистика** — ~3000+ вакансий, 4 роли
- [ ] **Прогноз зарплаты и навыков** — расчёт для SA, Москва, 1–3 года
- [ ] **Данные** — фильтр по роли работает
- [ ] http://localhost:8000/docs — POST `/predict`

Сценарий речи: [DEMO.md](DEMO.md)

## Устранение неполадок

| Симптом | Решение |
|---------|---------|
| Predictions → 503 | Проверьте `ml/artifacts/salary_model.joblib`, переобучите модель |
| API недоступен | `docker compose up -d api db` |
| HH 403 в логах | Ожидаемо — используется HTML fallback |
| SuperJob 0 | Проверьте `SUPERJOB_API_KEY` |

## Без Docker

См. [jobpulse/NO_DOCKER.md](jobpulse/NO_DOCKER.md).
