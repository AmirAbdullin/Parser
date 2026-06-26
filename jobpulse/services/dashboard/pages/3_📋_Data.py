import pandas as pd
import streamlit as st
from urllib.parse import quote

from api_client import EXPERIENCE_OPTIONS, ROLE_OPTIONS, api_get, check_api

st.set_page_config(page_title="Data — SkillCompass", layout="wide")
st.title("📋 Вакансии")

ok, msg = check_api()
if not ok:
    st.error(msg)
    st.stop()

filters = api_get("/data/filters")
experiences = filters.get("experiences", EXPERIENCE_OPTIONS)

role_label = st.selectbox("Роль", ["Все"] + list(ROLE_OPTIONS.keys()))
experience = st.selectbox("Опыт", ["Все"] + experiences)
source = st.selectbox("Источник", ["Все", "hh", "superjob"])
search = st.text_input("Поиск в названии")

params = "limit=100&offset=0"
if role_label != "Все":
    params += f"&role={ROLE_OPTIONS[role_label]}"
if experience != "Все":
    params += f"&experience={quote(experience)}"
if source != "Все":
    params += f"&source={source}"
if search.strip():
    params += f"&search={search.strip()}"

data = api_get(f"/data/vacancies?{params}")
st.caption(f"Показано {len(data['items'])} из {data['total']}")

df = pd.DataFrame(data["items"])
if not df.empty:
    show = [
        c
        for c in [
            "role_label",
            "title",
            "employer",
            "area",
            "salary_from",
            "salary_to",
            "experience",
            "source",
            "url",
        ]
        if c in df.columns
    ]
    st.dataframe(df[show], use_container_width=True, hide_index=True)
else:
    st.info("Ничего не найдено")
