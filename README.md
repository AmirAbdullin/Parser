# SkillCompass

**Компас навыков и зарплат для IT-аналитиков** — учебный проект DataPulse.

Сбор вакансий с **HH.ru** и **SuperJob** по четырём ролям (BA, SA, PA, DA), хранение в **PostgreSQL**, **ML-прогноз зарплаты** (CatBoost), REST **API** (FastAPI) и **дашборд** (Streamlit). Развёртывание — **Docker Compose** + **GitHub Actions**.

## Демо

| Сервис | URL |
|--------|-----|
| Dashboard | http://46.21.244.197:8501 |
| Swagger API | http://46.21.244.197:8000/docs |

## Возможности

- KPI и графики по ролям, источникам, зарплатам
- Прогноз ЗП по профилю (роль, опыт, город, источник)
- Топ навыков HH для выбранной роли и опыта
- Таблица вакансий с фильтрами
- Мониторинг API и последнего ingest

## Данные

| Метрика | Значение |
|---------|----------|
| Вакансий в БД | ~3075 |
| С указанной зарплатой | ~1104 |
| С навыками (HH) | ~1870 |
| ML test MAE | ~44 000 ₽ |

## Быстрый старт

```powershell
git clone https://github.com/AmirAbdullin/Parser.git
cd Parser/jobpulse
copy .env.example .env
# HH_USER_AGENT=SkillCompass/1.0 (your@email.com)
# SUPERJOB_API_KEY=...

docker compose up -d --build
```

- Dashboard: http://localhost:8501  
- API: http://localhost:8000/docs  

## Структура репозитория

```
Parser/
├── README.md
├── USER_STEPS.md          # запуск и деплой
├── DEMO.md                # сценарий презентации
├── DATA_INGEST.md         # pipeline данных
├── .github/workflows/     # auto-deploy
└── jobpulse/
    ├── docker-compose.yml
    ├── services/
    │   ├── ingestor/      # сбор → PostgreSQL
    │   ├── api/           # FastAPI
    │   └── dashboard/     # Streamlit
    └── ml/                # обучение и артефакты модели
```

## Стек

Python · PostgreSQL · SQLAlchemy · pandas · CatBoost · FastAPI · Pydantic · Streamlit · Docker · GitHub Actions

## Документация

- [USER_STEPS.md](USER_STEPS.md) — настройка `.env`, Docker, деплой
- [DEMO.md](DEMO.md) — сценарий защиты (5–7 мин)
- [DATA_INGEST.md](DATA_INGEST.md) — ingest pipeline
- [jobpulse/NO_DOCKER.md](jobpulse/NO_DOCKER.md) — запуск без Docker

## Архитектура

```
HH.ru + SuperJob
       ↓
   Ingestor (merge, dedup, enrich)
       ↓
   PostgreSQL
       ↓
   CatBoost ← export/train
       ↓
   FastAPI ←→ Streamlit
```

## Команда

Учебный проект, МИСИС / DataPulse.
