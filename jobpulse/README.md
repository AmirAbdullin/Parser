# SkillCompass

**Компас навыков и зарплат для IT-аналитиков** — бизнес-, системный, продуктовый и аналитик данных.

Полный контекст и команды: [`../PROJECT_CONTEXT.md`](../PROJECT_CONTEXT.md)

DataPulse · HH.ru + SuperJob → PostgreSQL → ML → FastAPI → Streamlit.

## Ниша

| Роль | Код |
|------|-----|
| Бизнес-аналитик | `business_analyst` |
| Системный аналитик | `systems_analyst` |
| Продуктовый аналитик | `product_analyst` |
| Аналитик данных | `data_analyst` |

## Быстрый старт

```powershell
cd local-tasks\datapulse\jobpulse
copy .env.example .env
# HH_USER_AGENT=SkillCompass/1.0 (ваш_email@mail.ru)
# SUPERJOB_API_KEY=...

pip install requests python-dotenv pydantic-settings beautifulsoup4 lxml
python scripts/fetch_sample.py
```

Ожидаемо: `data/raw/hh_analysts_sample.json` с разбивкой по 4 ролям.

## Docker

```powershell
docker compose up --build
```

## Скриншоты (для защиты)

Положите PNG в `docs/screenshots/` (см. `../USER_STEPS.md`, шаг 7):

| Файл | Страница |
|------|----------|
| `01-overview.png` | Overview — KPI и графики |
| `02-predictions.png` | Predictions — калькулятор |
| `03-data.png` | Data — таблица |
| `04-monitoring.png` | Monitoring — статус API |

## Demo на защите

Полный сценарий речи (5–7 мин): [`../DEMO.md`](../DEMO.md)

Кратко:

1. «SkillCompass — 4 роли IT-аналитиков, HH + SuperJob, ~699 вакансий»
2. Overview — сравнение зарплат по ролям
3. Predictions — системный аналитик, Москва, 1–3 года → ML-прогноз
4. Data — фильтр по роли
5. Monitoring + Swagger `/predict`

План: `../index.md` · ваши шаги: `../USER_STEPS.md`
