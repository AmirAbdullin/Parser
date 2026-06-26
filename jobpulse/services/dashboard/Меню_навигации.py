import streamlit as st

st.set_page_config(
    page_title="SkillCompass",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🧭 SkillCompass")
st.caption("Компас навыков и зарплат для IT-аналитиков")

st.markdown(
    """
**SkillCompass** — аналитика вакансий для бизнес-, системных, продуктовых и data-аналитиков.

Используйте меню слева:
- **Общая статистика** — KPI и графики
- **Прогноз зарплаты и навыков** — ML-прогноз и топ навыков
- **Данные** — таблица вакансий
- **Мониторинг** — статус API и данных
"""
)

from api_client import check_api

ok, msg = check_api()
if ok:
    st.success(f"API: {msg}")
else:
    st.error(f"API недоступен: {msg}")
    st.info("Запустите API: `python scripts/run_api.py`")
