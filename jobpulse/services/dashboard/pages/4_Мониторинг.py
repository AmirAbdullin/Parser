import streamlit as st

from api_client import API_URL, api_get, check_api, format_api_datetime

st.set_page_config(page_title="Мониторинг — SkillCompass", layout="wide")
st.title("⚙️ Мониторинг")

st.write(f"**API URL:** `{API_URL}`")

ok, msg = check_api()
if ok:
    st.success(msg)
    health = api_get("/health")
    st.json(health)

    stats = api_get("/data/stats")
    st.subheader("Сбор данных")
    last_ingest = stats.get("last_ingest_at")
    if last_ingest:
        records = stats.get("last_ingest_records", "—")
        st.metric("Последний успешный ingest", format_api_datetime(last_ingest))
        st.caption(
            f"Вакансий сохранено в БД: **{records}** "
            "(уникальные записи HH + SuperJob после очистки и dedup)."
        )
    else:
        st.warning("Нет записей об успешном ingest в БД (таблица ingest_runs).")

    st.caption(f"Данные в API обновлены: {format_api_datetime(stats.get('updated_at'))}")

    st.subheader("Источники")
    for name, count in stats.get("sources", {}).items():
        st.write(f"- **{name}**: {count} вакансий ✅")
else:
    st.error(msg)

st.subheader("Как обновить данные")
st.code(
    "docker compose run --rm ingestor python -m ingestor.main --once\n"
    "python scripts/export_parquet_from_db.py\n"
    "python ml/training/train_salary.py\n"
    "docker compose restart api dashboard",
    language="powershell",
)
