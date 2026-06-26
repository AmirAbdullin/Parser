# SkillCompass — контекст проекта (handoff)

> **Для AI в новом чате:** прочитай этот файл целиком перед работой.  
> Код: `local-tasks/datapulse/jobpulse/`.  
> Пользователь **не пишет код** — только команды в терминале и браузер.

---

## 1. Что это

| Поле | Значение |
|------|----------|
| **Задание** | DataPulse — учебный проект (data-driven сервис, ML, Docker) |
| **Продукт** | **SkillCompass** — аналитика вакансий **IT-аналитиков** (BA/SA/PA/DA) |
| **Репозиторий** | Папка `local-tasks/datapulse/` в b2b-репо, **не связана с ERP** |

---

## 2. Текущий статус (2026-06-25)

| Компонент | Статус |
|-----------|--------|
| **Docker Desktop** | ✅ Установлен, 4 контейнера работают |
| **PostgreSQL** | ✅ Локально в Docker, БД **`datapulse`** (не `skillcompass`!) |
| **Ingestor** | ✅ HH (HTML fallback) + SuperJob → PostgreSQL, scheduler 4 ч |
| **API** | ✅ FastAPI читает **PostgreSQL** (`data_source: postgresql`) |
| **Streamlit** | ✅ 4 страницы (Gradio **не нужен** сейчас) |
| **ML** | ✅ CatBoost, `salary_spec`, beats naive |
| **Облачная БД (Yandex)** | ❌ Отложена, проблемы с доступом |

### Данные (PostgreSQL)

| Метрика | Значение |
|---------|----------|
| Всего вакансий | **~1437** |
| С указанной ЗП (от и/или до) | **~348** (~24%) |
| HH | ~1350 |
| SuperJob | ~87 |
| ML обучение | **346** samples (только вакансии с `salary_mid`) |

**Почему не все с ЗП:** HH API 403 → HTML-парсинг **списка** поиска; на карточке в списке часто нет ₽ (на полной странице может быть). Фильтр HH «Указан доход» **не используем** при сборе.

---

## 3. Ниша — 4 роли

| Ключ | Роль | Поиск RU + EN |
|------|------|---------------|
| `business_analyst` | Бизнес-аналитик | бизнес-аналитик / business analyst |
| `systems_analyst` | Системный аналитик | системный аналитик / system analyst |
| `product_analyst` | Продуктовый аналитик | продуктовый аналитик / product analyst |
| `data_analyst` | Аналитик данных | аналитик данных / data analyst |

Код: `services/ingestor/src/ingestor/roles.py`, классификация по title: `role_classifier.py`

---

## 4. Качество данных (реализовано)

| Проблема | Решение | Файл |
|----------|---------|------|
| Мусор (брокер, химик…) | Stop-list + классификатор title | `role_classifier.py`, `filters.py` |
| Аномальные ЗП (1M ₽) | Cap **30k–600k** ₽ | `salary_utils.py`, `ml/load_data.py` |
| RU/EN дубли | Отдельные запросы, dedup `(source, external_id)` | `hh_html.py`, `row_processing.py` |
| Роль «бизнес и системный» | Роль из **названия**, не из поискового запроса | `role_classifier.py` |
| HH key_skills | Догрузка до 400 вакансий/прогон | `collectors/hh_skills.py` |
| История зарплат | Таблица `salary_snapshots` после ingest | `snapshots.py` |

---

## 5. Стек

Python · requests · BeautifulSoup4 · SQLAlchemy · PostgreSQL · APScheduler · pandas · CatBoost · FastAPI · Streamlit · Docker Compose

---

## 6. Структура

```
local-tasks/datapulse/
├── PROJECT_CONTEXT.md      ← этот файл
├── CONSULTATION.md         ← сценарий консультации
├── DEMO.md                 ← сценарий защиты
├── USER_STEPS.md           ← шаги для пользователя
└── jobpulse/
    ├── .env                ← секреты (НЕ в git!)
    ├── docker-compose.yml  ← db + ingestor + api + dashboard
    ├── services/
    │   ├── ingestor/       ← сбор → PostgreSQL
    │   ├── api/            ← FastAPI, читает PostgreSQL
    │   └── dashboard/      ← Streamlit
    ├── ml/
    │   ├── training/train_salary.py
    │   ├── load_data.py
    │   └── artifacts/
    ├── data/processed/vacancies.parquet  ← экспорт из БД для ML
    └── scripts/
        ├── export_parquet_from_db.py   ← БД → parquet (localhost)
        ├── fetch_all.py                ← сбор без Docker → parquet
        ├── run_api.py / run_dashboard.py
```

---

## 7. `.env` (шаблон)

```env
DB_USER=datapulse
DB_PASSWORD=datapulse_secret
DB_NAME=datapulse
DATABASE_URL=postgresql://datapulse:datapulse_secret@db:5432/datapulse

HH_USER_AGENT=SkillCompass/1.0 (email@edu.misis.ru)
SUPERJOB_API_KEY=...

INGEST_AREA_ID=0
INGEST_MAX_PAGES=20
INGEST_SCHEDULE_HOURS=4
INGEST_SKILLS_LIMIT=400

USE_DB=true
API_URL=http://api:8000
```

**Важно:** для скриптов на Windows host БД = `localhost:5432/datapulse`.  
`export_parquet_from_db.py` сам заменяет `@db:` → `@localhost:`.

**Не коммитить `.env` и не просить ключи в чат.**

---

## 8. Команды (Windows PowerShell)

```powershell
cd c:\Users\snaki\b2b\b2b\local-tasks\datapulse\jobpulse
```

### Docker (основной режим)

```powershell
docker compose up -d --build
docker compose ps
```

- API: http://127.0.0.1:8000/docs  
- Dashboard: http://localhost:8501  

### Ручной ingest (один раз)

```powershell
docker compose run --rm ingestor python -m ingestor.main --once
```

### ML после обновления БД

```powershell
python scripts/export_parquet_from_db.py
python ml/training/train_salary.py
docker compose restart api dashboard
```

### Логи ingestor

```powershell
docker logs jobpulse-ingestor-1 --tail 30
```

---

## 9. API эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/health` | status, vacancies_loaded, data_source |
| GET | `/data/stats` | KPI, роли, источники, with_salary |
| GET | `/data/filters` | areas, experiences, sources, roles |
| GET | `/data/vacancies?role=&source=&experience=&search=` | Список |
| GET | `/data/salary-history?role=&experience=` | Снимки / fallback по published_at |
| POST | `/predict` | см. ниже |
| GET | `/model/metrics` | MAE, RMSE, beats_naive |

**POST `/predict` body:**

```json
{
  "analyst_role": "systems_analyst",
  "experience": "Опыт 1-3 года",
  "area": "Москва",
  "source": "all",
  "employment": "unknown",
  "salary_spec": "range"
}
```

`salary_spec`: `range` | `from_only` | `to_only` — как указана ЗП в похожих вакансиях.

Ответ включает `predicted_salary` и `top_skills` (HH, если есть key_skills в БД).

---

## 10. Streamlit

| Страница | Функции |
|----------|---------|
| Overview | KPI, роли, boxplot зарплат, график динамики |
| Predictions | Dropdown: роль, опыт, город, источник, **salary_spec**; метрики ML; top skills |
| Data | Фильтры: роль, **опыт**, источник, поиск |
| Monitoring | Статус API |

---

## 11. ML

| Параметр | Значение |
|----------|----------|
| Модель | CatBoost → `ml/artifacts/salary_model.joblib` |
| Цель | `salary_mid` (среднее from/to, cap 30k–600k) |
| Признаки | `analyst_role`, `experience`, `area`, `source`, `employment`, **`salary_spec`** |
| Метрики | MAE ~**50k**, RMSE ~**75k**, **beats_naive: true** |

**MAE** — средняя ошибка прогноза в ₽. **beats_naive** — лучше, чем «всем одна медиана».

---

## 12. Архитектура

```
HH.ru + SuperJob
      ↓
  Ingestor (каждые 4 ч)
      ↓
  PostgreSQL (datapulse)  ←── API (FastAPI) ←── Streamlit
      ↓
  export_parquet_from_db.py → train_salary.py → salary_model.joblib
```

---

## 13. Известные ограничения

1. **HH API 403** → HTML fallback, ЗП парсится с карточки списка (мало цифр).
2. **348/1437 с ЗП** — не баг; нужен 2-й проход (detail page) или `only_with_salary`.
3. **top_skills** часто пустой — skills грузятся для 400 HH/прогон; detail API тоже может 403.
4. **Имя БД `datapulse`**, не `skillcompass` — иначе export с Windows падает.
5. Пользователь **не программирует** — давать готовые команды.

---

## 14. Осталось / backlog

### Для защиты (~4 дня от 2026-06-24)

- [ ] README + скриншоты в `jobpulse/docs/screenshots/`
- [ ] Репетиция по `DEMO.md`
- [ ] Опционально: 2-й ingest → точки на графике истории

### Обсуждалось, не сделано

- [ ] **Догрузка ЗП** с детальной страницы HH (как skills) → больше 348 с ЗП
- [ ] HH параметр **`only_with_salary`** при сборе
- [ ] Фильтр **«Только с зарплатой»** на Data
- [ ] SuperJob skills из текста (NLP)
- [ ] **Gradio** вместо Streamlit (не приоритет)
- [ ] Облачная PostgreSQL (Yandex MDB) — отложено
- [ ] MLflow, pytest, CI (опционально на «5»)

---

## 15. Сообщение для нового чата

```
Проект SkillCompass (DataPulse).
Прочитай: local-tasks/datapulse/PROJECT_CONTEXT.md
Docker: да. БД: локальный PostgreSQL (datapulse).
Задача: [опиши]
Пользователь не пишет код — только терминал и браузер.
```

---

## 16. Связанные файлы

| Файл | Назначение |
|------|------------|
| `CONSULTATION.md` | Краткий сценарий консультации |
| `DEMO.md` | Сценарий защиты 5–7 мин |
| `USER_STEPS.md` | Пошаговая инструкция |
| `jobpulse/NO_DOCKER.md` | Запуск без Docker |
| `onboarding.md` | Правила AI в b2b-репо |

---

*Обновлено: 2026-06-25. PostgreSQL ~1437 вакансий, ~348 с ЗП, API на PostgreSQL, Docker работает.*
