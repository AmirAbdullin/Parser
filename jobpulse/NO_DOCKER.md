# SkillCompass — без Docker

## 1. Данные и модель (если ещё не делали)

```powershell
cd c:\Users\snaki\b2b\b2b\local-tasks\datapulse\jobpulse
python scripts/fetch_all.py
python ml/training/train_salary.py
```

## 2. API (терминал 1)

```powershell
pip install -r services/api/requirements.txt
python scripts/run_api.py
```

Swagger: http://127.0.0.1:8000/docs

## 3. Дашборд (терминал 2)

```powershell
pip install -r services/dashboard/requirements.txt
python scripts/run_dashboard.py
```

Браузер: http://localhost:8501

## Страницы дашборда

| Страница | Что показывает |
|----------|----------------|
| Overview | KPI, роли, зарплаты |
| Predictions | ML-калькулятор зарплаты |
| Data | Таблица вакансий |
| Monitoring | Статус API |

## Перед защитой

Установите Docker Desktop → `docker compose up --build`
