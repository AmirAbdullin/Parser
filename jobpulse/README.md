# SkillCompass

**Компас навыков и зарплат для IT-аналитиков** — бизнес-, системный, продуктовый и data-аналитик.

HH.ru + SuperJob → PostgreSQL → CatBoost → FastAPI → Streamlit.

## Быстрый старт

```powershell
cd jobpulse
copy .env.example .env
# заполните HH_USER_AGENT и SUPERJOB_API_KEY

docker compose up -d --build
```

- Dashboard: http://localhost:8501  
- API docs: http://localhost:8000/docs  

**Демо без ingest:** `docker compose up -d db api dashboard`

## Ниша

| Роль | Код |
|------|-----|
| Бизнес-аналитик | `business_analyst` |
| Системный аналитик | `systems_analyst` |
| Продуктовый аналитик | `product_analyst` |
| Аналитик данных | `data_analyst` |

## Дашборд

| Страница | Описание |
|----------|----------|
| Общая статистика | KPI, графики |
| Прогноз зарплаты и навыков | ML + топ навыков |
| Данные | Таблица вакансий |
| Мониторинг | Статус сервисов |

Документация в корне репозитория: `USER_STEPS.md`, `DEMO.md`, `DATA_INGEST.md`.

Без Docker: `NO_DOCKER.md`.

## Данные

~3075 вакансий · MAE модели ~44k ₽ (test) · beats naive baseline.
