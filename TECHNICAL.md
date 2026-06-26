# SkillCompass — техническое описание

Учебный проект **DataPulse**: data-driven сервис с сбором данных, ML-моделью, REST API, веб-дашбордом, контейнеризацией и автоматическим развёртыванием.

**Репозиторий:** [github.com/AmirAbdullin/Parser](https://github.com/AmirAbdullin/Parser) · **Код:** `jobpulse/`

---

## 1. Назначение системы

**SkillCompass** — сервис аналитики рынка труда для **IT-аналитиков** (бизнес-, системных, продуктовых, data-аналитиков). Система:

1. собирает вакансии из внешних источников;
2. нормализует и сохраняет их в реляционную БД;
3. обучает модель регрессии зарплаты;
4. отдаёт агрегаты и прогнозы через API и Streamlit-дашборд.

---

## 2. Архитектура (логическая)

```
┌─────────────────────────────────────────────────────────────────┐
│                      Источники данных                           │
│   HH.ru (API + HTML fallback)    SuperJob (REST API)            │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Ingestor (сервис сбора)                                        │
│  collectors → merge/dedup → enrich → upsert                     │
│  APScheduler: периодический запуск (interval, 4 ч)              │
└────────────────────────────┬────────────────────────────────────┘
                             │ SQLAlchemy ORM
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PostgreSQL 16 (хранилище)                                      │
│  vacancies · ingest_runs · salary_snapshots                     │
└──────────────┬──────────────────────────────┬───────────────────┘
               │                              │
               │ read                         │ export → parquet
               ▼                              ▼
┌──────────────────────────┐    ┌──────────────────────────────┐
│  API (FastAPI)           │    │  ML pipeline                 │
│  Pydantic · SQLAlchemy   │◄───│  CatBoostRegressor · joblib  │
└──────────────┬───────────┘    └──────────────────────────────┘
               │ HTTP (REST)
               ▼
┌─────────────────────────────────────────────────────────────────┐
│  Dashboard (Streamlit) — 5 страниц, русский UI                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Выбор технологий и обоснование

| Компонент | Решение | Почему |
|-----------|---------|--------|
| Язык | **Python 3.12** | Единый стек для ETL, ML, API и UI; богатая экосистема для data science |
| Сбор данных | **requests** + **BeautifulSoup4** | HH API нестабилен (403/400 с VPS); HTML fallback даёт устойчивость |
| Планировщик | **APScheduler** | Лёгкий in-process cron без отдельного Celery для учебного масштаба |
| БД | **PostgreSQL 16** | Требование курса; ACID, upsert по `(source, external_id)`, JSON-поля навыков |
| ORM | **SQLAlchemy 2** | Декларативные модели, миграции через `create_all` + точечные `ALTER` |
| ML | **CatBoostRegressor** | Категориальные признаки (роль, город, опыт) без one-hot; устойчив к шуму |
| API | **FastAPI** + **Pydantic v2** | Авто-Swagger, валидация входа, асинхронная готовность |
| UI | **Streamlit** | Быстрый интерактивный дашборд без отдельного фронтенда |
| Контейнеры | **Docker Compose** | 4 сервиса (db, ingestor, api, dashboard) — воспроизводимое окружение |
| CI/CD | **GitHub Actions** | Push в `main` → SSH-deploy на VPS без ручного копирования |

---

## 4. Конвейер данных (ingest)

**Точка входа:** `services/ingestor/src/ingestor/main.py` → `pipeline.run_ingest()`.

| Этап | Модуль | Действие |
|------|--------|----------|
| 1 | `collectors/hh.py` | Поток A: все вакансии; поток B: `only_with_salary` |
| 2 | `collectors/superjob.py` | REST по 4 ролям |
| 3 | `row_processing.py` | Dedup `(source, external_id)`, merge полей, классификация роли по title |
| 4 | `role_classifier.py`, `salary_utils.py` | Stop-list, cap ЗП 30k–600k ₽ |
| 5 | `collectors/hh_detail.py` | Detail enrich: key_skills, недостающие поля (HTML при 403 API) |
| 6 | `storage.py` | Upsert в `vacancies` |
| 7 | `snapshots.py` | Снимки медиан в `salary_snapshots` |

**Запись в БД** выполняет **только ingestor**. API и dashboard — **read-only** к PostgreSQL.

---

## 5. ML-подсистема

| Параметр | Значение |
|----------|----------|
| Задача | Регрессия: `salary_mid` (₽/мес) |
| Алгоритм | CatBoost, 300 итераций, depth=6 |
| Признаки | `analyst_role`, `experience`, `area`, `source`, `employment`, `salary_spec` |
| Обучение | `ml/training/train_salary.py` |
| Split | 80% train / 20% test, `random_state=42` |
| Baseline | Медиана train → сравнение MAE (naive) |
| Артефакты | `ml/artifacts/salary_model.joblib`, `salary_metrics.json` |
| Инференс | `services/api/src/ml_service.py` — загрузка joblib, batch predict |

**Метрики (актуальные):** ~1103 samples, test MAE ≈ 43.6k ₽, RMSE ≈ 56k ₽, beats naive ✅.

---

## 6. API (контракт)

| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/health` | Статус, число вакансий |
| GET | `/data/stats` | KPI, роли, источники |
| GET | `/data/filters` | Справочники для UI |
| GET | `/data/vacancies` | Список с фильтрами и пагинацией |
| GET | `/data/salary-history` | Динамика ЗП |
| POST | `/predict` | Прогноз ЗП + top skills |
| GET | `/model/metrics` | MAE, RMSE, beats_naive |

Документация: Swagger UI (`/docs`).

---

## 7. Развёртывание на VPS

**Провайдер:** Yandex Cloud (виртуальная машина, публичный IP).

| Параметр | Значение |
|----------|----------|
| IP | `46.21.244.197` |
| Dashboard | `:8501` |
| API | `:8000` |
| Путь на сервере | `~/Parser/jobpulse` |
| Оркестрация | Docker Compose v2 |

**Сервисы на VPS:**

```
jobpulse-db-1          PostgreSQL 16, volume postgres_data
jobpulse-api-1         FastAPI, порт 8000
jobpulse-dashboard-1   Streamlit, порт 8501
jobpulse-ingestor-1    фоновый сбор (опционально stop для демо)
```

**Секреты:** `.env` на сервере (не в Git): `HH_USER_AGENT`, `SUPERJOB_API_KEY`, `DB_*`.

**Данные на демо:** загружены в volume PostgreSQL (дамп с локального ingest); ingest с IP VPS может получать 400 от HH API — для защиты достаточно `db + api + dashboard`.

---

## 8. CI/CD (GitHub Actions)

**Файл:** `.github/workflows/deploy.yml`

**Триггер:** push в ветку `main` (или `master`).

**Pipeline:**

```
push → GitHub Actions runner (ubuntu-latest)
     → checkout репозитория
     → ssh-agent + SSH_PRIVATE_KEY (secret)
     → SSH на VPS:
          cd ~/Parser/jobpulse
          git pull origin main
          docker compose up -d --build --force-recreate
```

**Secrets в GitHub:** `SSH_PRIVATE_KEY`, `SERVER_USER`, `SERVER_IP`.

**Особенности:** volume `postgres_data` **не удаляется** при redeploy — данные сохраняются между выкатами. Образы пересобираются при изменении кода.

---

## 9. Структура репозитория

```
Parser/
├── README.md                 # описание продукта (простым языком)
├── TECHNICAL.md              # этот документ
├── USER_STEPS.md               # запуск и деплой
├── DEMO.md                     # сценарий защиты
├── DATA_INGEST.md              # pipeline данных
├── .github/workflows/deploy.yml
└── jobpulse/
    ├── docker-compose.yml
    ├── services/ingestor|api|dashboard/
    ├── ml/training/ · ml/artifacts/ · ml/notebooks/
    └── scripts/
```

---

## 10. Нефункциональные свойства

| Аспект | Реализация |
|--------|------------|
| Валидация входа API | Pydantic-схемы |
| Качество данных | Stop-list, cap ЗП, dedup, роль из title |
| Наблюдаемость | `/health`, Monitoring UI, таблица `ingest_runs` |
| Повторяемость | Docker, фиксированный `random_state` в ML |
| Безопасность | Секреты в `.env`; API без записи в БД |

---

## 11. Ограничения (честно для защиты)

- HH API с IP дата-центра часто недоступен → HTML fallback только при 403, не при 400.
- Не все вакансии содержат ЗП (~36% с salary_mid).
- ML — ориентир по рынку, не персональный оффер; MAE ~44k ₽.
- Автотесты и Alembic не используются (учебный scope).

---

*SkillCompass · DataPulse · МИСИС · 2026*
