# SkillCompass — контекст проекта (handoff)

> **Для человека и для AI в новом чате:** прочитай этот файл целиком перед продолжением работы.  
> Код лежит в `local-tasks/datapulse/jobpulse/`. Пользователь **не пишет код** — делает только команды в терминале и смотрит результат в браузере.

---

## 1. Что это

| Поле | Значение |
|------|----------|
| **Задание** | DataPulse — семестровый учебный проект (data-driven сервис, ML, Docker) |
| **Наш проект** | **SkillCompass** — аналитика вакансий **IT-аналитиков** |
| **Задача продукта** | Показать рынок труда для BA/SA/PA/DA: зарплаты, роли, ML-прогноз «сколько могу получить» |
| **Репозиторий b2b** | Основной ERP-проект; SkillCompass — отдельная папка `local-tasks/datapulse/`, к прод-коду не относится |

---

## 2. Ниша (только 4 роли)

| Ключ в данных | Роль | Поисковый запрос |
|---------------|------|------------------|
| `business_analyst` | Бизнес-аналитик | бизнес-аналитик |
| `systems_analyst` | Системный аналитик | системный аналитик |
| `product_analyst` | Продуктовый аналитик | продуктовый аналитик |
| `data_analyst` | Аналитик данных | аналитик данных |

Код ролей: `jobpulse/services/ingestor/src/ingestor/roles.py`

---

## 3. Источники данных

| # | Источник | Как собираем | Статус |
|---|----------|--------------|--------|
| 1 | **HH.ru** | Официальный API → при **403 Forbidden** автоматический **HTML fallback** (`hh_html.py`) | Работает |
| 2 | **SuperJob** | REST API, заголовок `X-Api-App-Id` = Secret Key из `.env` | Работает |

Фильтр «шума» (кредитный аналитик и т.п.): `ingestor/filters.py`

---

## 4. Стек

| Слой | Технологии |
|------|------------|
| Сбор | Python, requests, BeautifulSoup4, APScheduler |
| Данные | Parquet (`data/processed/vacancies.parquet`), позже PostgreSQL в Docker |
| ML | CatBoost, scikit-learn, joblib |
| API | FastAPI, Swagger `/docs` |
| UI | Streamlit (4 страницы) |
| Контейнеры | docker-compose.yml (Docker Desktop **у пользователя пока нет**) |

---

## 5. Структура каталогов

```
local-tasks/datapulse/
├── PROJECT_CONTEXT.md          ← этот файл
├── index.md                    ← описание и roadmap
├── onboarding.md               ← для агента
└── jobpulse/                   ← весь код SkillCompass
    ├── .env                      ← секреты (НЕ в git), уже настроен у пользователя
    ├── .env.example
    ├── docker-compose.yml
    ├── NO_DOCKER.md              ← краткий запуск без Docker
    ├── data/
    │   ├── processed/vacancies.parquet   ← основной датасет (~699 записей)
    │   └── raw/hh_analysts_sample.json
    ├── ml/
    │   ├── notebooks/01_eda.ipynb
    │   ├── training/train_salary.py
    │   └── artifacts/
    │       ├── salary_model.joblib
    │       └── salary_metrics.json
    ├── services/
    │   ├── ingestor/             ← HH + SuperJob → PostgreSQL (для Docker)
    │   ├── api/                  ← FastAPI
    │   └── dashboard/            ← Streamlit
    └── scripts/
        ├── fetch_sample.py       ← быстрый тест HH
        ├── fetch_all.py          ← полный сбор HH + SuperJob → parquet
        ├── run_api.py
        └── run_dashboard.py
```

---

## 6. Конфигурация `.env`

Файл: `jobpulse/.env` (один файл, **не** `.env.example`).

| Переменная | Назначение |
|------------|------------|
| `HH_USER_AGENT=SkillCompass/1.0 (email@...)` | **Реальный email** пользователя (edu.misis.ru) |
| `SUPERJOB_API_KEY=...` | Secret Key с api.superjob.ru/register |
| `INGEST_AREA_ID=0` | 0 = вся Россия |
| `INGEST_MAX_PAGES=10` | Страниц на каждую роль при сборе |

**Не коммитить** `.env` и ключи в чат.

---

## 7. Команды запуска (Windows, PowerShell)

Все команды — из корня **`jobpulse`**:

```powershell
cd c:\Users\snaki\b2b\b2b\local-tasks\datapulse\jobpulse
```

### 7.1. Первичная настройка (один раз)

```powershell
pip install requests python-dotenv pydantic-settings beautifulsoup4 lxml
pip install pandas pyarrow catboost scikit-learn joblib
pip install -r services/api/requirements.txt
pip install -r services/dashboard/requirements.txt
pip install -r ml/requirements.txt
```

### 7.2. Обновить данные и модель

```powershell
python scripts/fetch_all.py
python ml/training/train_salary.py
```

Ожидание: `data/processed/vacancies.parquet`, `ml/artifacts/salary_model.joblib`.

### 7.3. Запуск сервиса (2 терминала)

**Терминал 1 — API:**

```powershell
cd c:\Users\snaki\b2b\b2b\local-tasks\datapulse\jobpulse
python scripts/run_api.py
```

- Swagger: http://127.0.0.1:8000/docs  
- Health: http://127.0.0.1:8000/health  

**Терминал 2 — дашборд:**

```powershell
cd c:\Users\snaki\b2b\b2b\local-tasks\datapulse\jobpulse
python scripts/run_dashboard.py
```

- UI: http://localhost:8501  

### 7.4. EDA (notebook)

```powershell
jupyter notebook ml/notebooks/01_eda.ipynb
```

### 7.5. Docker (перед сдачей, когда установят Docker Desktop)

```powershell
docker compose up --build
```

---

## 8. API эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/health` | Статус, число вакансий |
| GET | `/data/stats` | KPI: роли, источники |
| GET | `/data/vacancies?role=&source=&search=&limit=&offset=` | Список вакансий |
| POST | `/predict` | JSON: `analyst_role`, `experience`, `area`, `source`, `employment`, `has_salary_range` |
| GET | `/model/metrics` | MAE, RMSE, beats_naive |

---

## 9. Streamlit — страницы

| Файл | Назначение |
|------|------------|
| `pages/1_📊_Overview.py` | KPI, графики ролей и зарплат |
| `pages/2_🔮_Predictions.py` | Калькulator ML + метрики |
| `pages/3_📋_Data.py` | Таблица, фильтры |
| `pages/4_⚙️_Monitoring.py` | Статус API, инструкция обновления |

---

## 10. ML

| Параметр | Значение |
|----------|----------|
| Задача | Регрессия: предсказать зарплату (₽/мес) |
| Модель | CatBoost, `ml/artifacts/salary_model.joblib` |
| Признаки | `analyst_role`, `experience`, `area`, `source`, `employment`, `has_salary_range` |
| Метрики (на момент обучения) | MAE ~53k, RMSE ~84k, лучше naive baseline |

Переобучение: после каждого `fetch_all.py` запускать `train_salary.py`.

---

## 11. Что уже сделано / что осталось

### ✅ Готово

- [x] Тема SkillCompass, 4 роли аналитиков
- [x] Сбор HH (HTML fallback) + SuperJob
- [x] ~699 вакансий в parquet
- [x] EDA notebook
- [x] ML-модель зарплаты
- [x] FastAPI + Swagger
- [x] Streamlit, 4 страницы
- [x] docker-compose.yml (api + dashboard + ingestor + db)

### ⏳ Осталось для полной сдачи DataPulse

- [ ] Установить **Docker Desktop**, проверить `docker compose up --build`
- [ ] Ingestor пишет в PostgreSQL по расписанию (сейчас данные в parquet)
- [ ] README с скриншотами для защиты
- [ ] Демо-сценарий презентации (текст для пользователя)
- [ ] Опционально для «5»: MLflow, pytest, CI, Redis, Alembic

---

## 12. Известные особенности

1. **HH API 403** — нормально; включается парсинг HTML поиска hh.ru.
2. **Папка `jobpulse`** — можно переименовать в `skillcompass`, пути в доках обновить.
3. **Пользователь не программирует** — объяснять простым языком, давать готовые команды `cd ...` + `python ...`.
4. **Лимит Cursor** — работать крупными блоками, не дублировать длинную историю чата.
5. **SuperJob ключ** — только в `.env`, регистрация приложения на api.superjob.ru (не путать с аккаунтом соискателя на superjob.ru).

---

## 13. Сценарий защиты (demo)

1. Открыть дашборд → «699 вакансий IT-аналитиков, 4 роли, HH + SuperJob».
2. **Overview** — сравнить зарплаты по ролям.
3. **Predictions** — «Системный аналитик, Москва, 1–3 года» → прогноз ML.
4. **Data** — фильтр по роли.
5. **Monitoring** — источники OK.
6. Swagger → POST `/predict` (опционально).

---

## 14. Как продолжить в новом чате

Сообщение агенту:

```
Проект SkillCompass (DataPulse). Прочитай:
local-tasks/datapulse/PROJECT_CONTEXT.md
Продолжи с пункта «Осталось» / или: [задача].
Docker у пользователя: да/нет.
```

---

## 15. Связанные файлы

| Файл | Зачем |
|------|-------|
| `index.md` | Roadmap и критерии оценки |
| `jobpulse/NO_DOCKER.md` | Короткий чеклист запуска |
| `jobpulse/README.md` | Краткое описание |
| `onboarding.md` | Правила для AI в репо b2b |

---

*Обновлено: 2026-06-24. Данные: ~699 вакансий (HH 615 + SuperJob 84 после dedup).*
