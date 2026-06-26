# SkillCompass

**Компас навыков и зарплат для IT-аналитиков** — data-driven сервис в рамках учебного проекта **DataPulse** (МИСИС).

---

## Что это простым языком

**SkillCompass** помогает понять рынок труда для людей, которые работают или хотят работать **IT-аналитиками**: бизнес-, системными, продуктовыми и data-аналитиками.

Сервис собирает реальные вакансии с **HH.ru** и **SuperJob**, убирает «мусор» (кредитные аналитики, брокеры и т.п.), показывает статистику по зарплатам и навыкам и даёт **прогноз зарплаты** для вашего профиля — роль, опыт, город — на основе **машинного обучения**, а не простой средней по всем объявлениям.

### Для кого

| Аудитория | Польза |
|-----------|--------|
| **Соискатели IT-аналитики** | Ориентир по ЗП и востребованным навыкам (SQL, BPMN, Jira…) |
| **Студенты и junior-специалисты** | Карта рынка: какие роли востребованы, чем отличаются медианы |
| **Карьерные консультанты / HR** | Агрегированная аналитика по нише без ручного мониторинга сотен объявлений |
| **Команды обучения** | Демонстрация data pipeline + ML + API + дашборд в одном продукте |

### Чем полезен

- **Прозрачность:** каждую цифру можно проверить в таблице вакансий и через API.
- **Узкая ниша:** только 4 роли IT-аналитиков — данные чище, чем «все аналитики».
- **Два источника:** HH + SuperJob, с дедупликацией и слиянием потоков.
- **ML-прогноз:** CatBoost учитывает роль, опыт, город, источник; на тесте точнее, чем «одна медиана для всех».
- **Навыки:** топ key_skills с HH для выбранной роли и опыта.

---

## Демо

| Сервис | URL |
|--------|-----|
| **Dashboard** | http://46.21.244.197:8501 |
| **Swagger API** | http://46.21.244.197:8000/docs |

### Возможности дашборда

| Страница | Что внутри |
|----------|------------|
| Меню навигации | Старт, статус API |
| Общая статистика | KPI, графики по ролям и источникам |
| Прогноз зарплаты и навыков | Калькулятор ML + топ навыков |
| Данные | Таблица вакансий с фильтрами |
| Мониторинг | Health API, последний ingest |

### Данные (июнь 2026)

| Метрика | Значение |
|---------|----------|
| Вакансий в БД | ~3075 |
| С указанной зарплатой | ~1104 |
| С навыками (HH) | ~1870 |
| ML test MAE | ~44 000 ₽ |

---

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

**Демо без повторного сбора с HH:** `docker compose up -d db api dashboard`

---

## Структура репозитория

```
Parser/
├── README.md              ← вы здесь
├── TECHNICAL.md           ← архитектура, VPS, CI/CD
├── USER_STEPS.md          ← запуск и деплoy
├── DEMO.md                ← сценарий защиты
├── DATA_INGEST.md         ← откуда данные в БД
├── .github/workflows/     ← auto-deploy
└── jobpulse/              ← исходный код
```

---

## Стек

Python · PostgreSQL · SQLAlchemy · pandas · CatBoost · FastAPI · Pydantic · Streamlit · Docker Compose · GitHub Actions

Подробная архитектура: **[TECHNICAL.md](TECHNICAL.md)**

---

## Масштабирование

### Качественное (новые возможности)

| Направление | Что добавить | Референс реализации |
|-------------|--------------|---------------------|
| Новые источники | Telegram-каналы, Habr Career, LinkedIn | Новый `collectors/telegram.py` + строка в `pipeline.py` |
| Новые роли / регионы | Расширить `roles.py`, фильтры area | Конфиг + отдельные search queries |
| NLP по описанию | Извлечение навыков из текста | TF-IDF / embeddings в `ml/training/` |
| Персональные отчёты | PDF/Excel по профилю | Celery task + шаблон отчёта |
| OAuth и личный кабинет | Сохранение профиля соискателя | FastAPI Users + PostgreSQL users |
| Алерты «ЗП выросла» | Подписка на изменения | `salary_snapshots` + cron + email/Telegram bot |

### Количественное (нагрузка и объём данных)

| Узкое место | Стратегия | Референс |
|-------------|-----------|----------|
| Ingest (долгий HH enrich) | Очередь задач (**Celery** + **Redis**), worker'ы по ролям | Ingestor → broker → N workers |
| API под нагрузкой | N реплик `api` за **nginx** / **Traefik** | `docker compose scale api=3` |
| БД | Read-replica PostgreSQL, индексы по `analyst_role`, `area` | Streaming replication |
| ML inference | Кэш прогнозов (**Redis**) по hash признаков | `@lru_cache` → Redis TTL 1h |
| Дашборд | Отдельный хост или **Streamlit Cloud** / static frontend на React | Decouple UI от API |
| Хранение истории | Партиционирование `vacancies` по `collected_at`, **S3** для архива | TimescaleDB / cold storage |
| Деплой | **Kubernetes** (Yandex Managed K8s) вместо одного VPS | Helm chart из Compose |

---

## Монетизация (варианты и теоретическая реализация)

| Модель | Суть | Как могло бы работать (референс) |
|--------|------|----------------------------------|
| **Freemium API** | Бесплатно: `/stats`, `/health`; платно: `/predict`, bulk export | API-ключи в PostgreSQL, rate limit (**Redis**), тарифы в Stripe |
| **Подписка B2C** | 299–990 ₽/мес — прогнозы, алерты, сравнение с рынком | Stripe Checkout + JWT; Streamlit gated pages |
| **B2B для HR / edtech** | Доступ к агрегированной аналитике по нише | White-label dashboard, отдельный tenant в БД, договор SLA |
| **Отчёты и дайджесты** | Еженедельный PDF «рынок SA в Москве» | Celery + WeasyPrint, рассылка SendGrid |
| **Партнёрские ссылки** | Рефералы на курсы (SQL, BA) по gap навыков | UTM в UI «востребованные навыки» → affiliate |
| **Реклама в дашборде** | Баннеры школ и рекрутеров | Sponsored block в Streamlit sidebar (осторожно с UX) |
| **Продажа дataset** | Анонимизированный parquet для исследователей | Export pipeline + лицензия, без PII работодателей |

На учебном этапе монетизация **не реализована** — перечислено как roadmap для обсуждения на защите.

---

## Документация

- [TECHNICAL.md](TECHNICAL.md) — техническое описание, VPS, CI/CD
- [USER_STEPS.md](USER_STEPS.md) — настройка и деплой
- [DEMO.md](DEMO.md) — сценарий презентации (5–7 мин)
- [DATA_INGEST.md](DATA_INGEST.md) — pipeline данных
- [jobpulse/NO_DOCKER.md](jobpulse/NO_DOCKER.md) — запуск без Docker

---

## Архитектура (кратко)

```
HH.ru + SuperJob → Ingestor → PostgreSQL → CatBoost → FastAPI ↔ Streamlit
                              ↑
                    GitHub Actions → VPS (Yandex Cloud)
```

---

## Команда

Учебный проект **DataPulse**, НИТУ «МИСИС».

Репозиторий: [github.com/AmirAbdullin/Parser](https://github.com/AmirAbdullin/Parser)
