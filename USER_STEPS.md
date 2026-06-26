# SkillCompass — ваши шаги

Вы **не пишете код** — только команды в терминале и браузер.  
Полный контекст: [`PROJECT_CONTEXT.md`](PROJECT_CONTEXT.md)

---

## Текущий статус (2026-06-24)

| Что | Статус |
|-----|--------|
| `.env` с HH + SuperJob | ✅ (если уже настраивали) |
| Данные ~699 вакансий | ✅ `data/processed/vacancies.parquet` |
| ML-модель | ✅ `ml/artifacts/salary_model.joblib` |
| FastAPI + Streamlit | ✅ готовы к запуску |
| Docker Desktop | ⏳ пока не установлен |

**Следующий шаг для вас:** раздел **«Шаг 5 — запуск сервиса»** ниже.

---

## Шаг 1 — `.env` (один раз)

```powershell
cd c:\Users\snaki\b2b\b2b\local-tasks\datapulse\jobpulse
copy .env.example .env
```

В `.env` обязательно:

```
HH_USER_AGENT=SkillCompass/1.0 (ваш_реальный_email@edu.misis.ru)
SUPERJOB_API_KEY=ваш_ключ_с_api.superjob.ru
```

---

## Шаг 2 — проверка сбора (опционально)

```powershell
pip install requests python-dotenv pydantic-settings beautifulsoup4 lxml
python scripts/fetch_sample.py
```

В консоли — число вакансий **по каждой из 4 ролей**.

---

## Шаг 3 — полный сбор и ML (раз в неделю или перед защитой)

```powershell
cd c:\Users\snaki\b2b\b2b\local-tasks\datapulse\jobpulse
pip install pandas pyarrow catboost scikit-learn joblib
python scripts/fetch_all.py
python ml/training/train_salary.py
```

Ожидаемо: `699+` вакансий, файл `ml/artifacts/salary_metrics.json` с MAE ~53k.

---

## Шаг 5 — запуск сервиса (2 терминала)

### Терминал 1 — API

```powershell
cd c:\Users\snaki\b2b\b2b\local-tasks\datapulse\jobpulse
pip install -r services/api/requirements.txt
python scripts/run_api.py
```

Проверка: http://127.0.0.1:8000/docs → `GET /health` → `"vacancies_loaded": 699`

### Терминал 2 — дашборд

```powershell
cd c:\Users\snaki\b2b\b2b\local-tasks\datapulse\jobpulse
pip install -r services/dashboard/requirements.txt
python scripts/run_dashboard.py
```

Браузер: http://localhost:8501

---

## Шаг 6 — репетиция защиты

Откройте [`DEMO.md`](DEMO.md) и пройдите сценарий 5–7 минут **вживую** в дашборде.

Чеклист перед защитой:

- [ ] API запущен (Monitoring → зелёный статус)
- [ ] Overview показывает 4 роли и зарплаты
- [ ] Predictions: «Системный аналитик, Москва, 1–3 года» → число в ₽
- [ ] Data: фильтр по роли работает
- [ ] Swagger: POST `/predict` (опционально)

---

## Шаг 7 — скриншоты для README

Сделайте 4–5 скриншотов (Win+Shift+S) и положите в `jobpulse/docs/screenshots/`:

| Файл | Что снять |
|------|-----------|
| `01-overview.png` | Страница Overview — KPI и графики |
| `02-predictions.png` | Predictions — калькулятор с результатом |
| `03-data.png` | Data — таблица с фильтром |
| `04-monitoring.png` | Monitoring — статус API |
| `05-swagger.png` | Swagger `/docs` (опционально) |

Напишите агенту «скриншоты готовы» — он обновит README.

---

## Шаг 8 — Docker (перед сдачей)

1. Установите [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. Перезагрузите ПК
3. В терминале:

```powershell
cd c:\Users\snaki\b2b\b2b\local-tasks\datapulse\jobpulse
docker compose up --build
```

Откроется: API `:8000`, дашборд `:8501`, PostgreSQL `:5432`, ingestor по расписанию.

---

## Если что-то не работает

| Проблема | Решение |
|----------|---------|
| Monitoring красный | Запустите `python scripts/run_api.py` в отдельном терминале |
| HH 403 в логах | Нормально — включается HTML-парсинг |
| SuperJob 0 вакансий | Проверьте `SUPERJOB_API_KEY` в `.env` |
| Нет parquet | `python scripts/fetch_all.py` |

Напишите агенту текст ошибки из терминала — разберём.
