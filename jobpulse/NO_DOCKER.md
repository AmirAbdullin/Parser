# SkillCompass — без Docker

```powershell
cd jobpulse
pip install -r services/api/requirements.txt
pip install -r services/dashboard/requirements.txt
```

## API (терминал 1)

```powershell
python scripts/run_api.py
```

http://127.0.0.1:8000/docs

## Дашборд (терминал 2)

```powershell
python scripts/run_dashboard.py
```

http://localhost:8501

## Страницы

| Страница | Содержание |
|----------|------------|
| Общая статистика | KPI, графики |
| Прогноз зарплаты и навыков | ML-калькулятор |
| Данные | Таблица |
| Мониторинг | Статус API |

## Данные и ML (без PostgreSQL)

```powershell
python scripts/fetch_all.py
python ml/training/train_salary.py
```

Для production-режима используйте `docker compose up`.
