import pandas as pd

import plotly.express as px

import streamlit as st



from api_client import (

    ALL_CITIES_LABEL,

    EXPERIENCE_OPTIONS,

    ROLE_OPTIONS,

    SALARY_SPEC_OPTIONS,

    SOURCE_OPTIONS,

    api_get,

    api_post,

    check_api,

)



st.set_page_config(page_title="Прогноз зарплаты и навыков — SkillCompass", layout="wide")

st.title("🔮 Прогноз зарплаты и навыков")



ok, msg = check_api()

if not ok:

    st.error(msg)

    st.stop()



metrics = api_get("/model/metrics")

st.subheader("Метрики модели")

st.caption(

    "MAE — средняя ошибка прогноза в ₽. RMSE — штрафует крупные промахи сильнее. "

    "«Лучше naive» — модель точнее, чем просто медиана зарплат по обучающей выборке."

)

m1, m2, m3 = st.columns(3)

m1.metric("MAE (тест)", f"{metrics.get('test_mae', 0):,.0f} ₽")

m2.metric("RMSE (тест)", f"{metrics.get('test_rmse', 0):,.0f} ₽")

m3.metric("Лучше naive", "✅" if metrics.get("beats_naive") else "❌")



filters = api_get("/data/filters")

experiences = filters.get("experiences", EXPERIENCE_OPTIONS)

cities = filters.get("cities", filters.get("areas", ["Москва"]))

city_options = [ALL_CITIES_LABEL] + cities



st.divider()

st.subheader("Калькулятор")



role_label = st.selectbox("Роль", list(ROLE_OPTIONS.keys()))

experience = st.selectbox(

    "Опыт",

    experiences,

    index=experiences.index("Опыт 1-3 года") if "Опыт 1-3 года" in experiences else 0,

)

city_label = st.selectbox(

    "Город",

    city_options,

    index=city_options.index("Москва") if "Москва" in city_options else 0,

)

source_label = st.selectbox("Источник", list(SOURCE_OPTIONS.keys()))

salary_spec_label = st.selectbox(

    "Формат диапазона данных",

    list(SALARY_SPEC_OPTIONS.keys()),

    help="Как указана зарплата в похожих вакансиях. «Все» — среднее по всем форматам.",

)



if st.button("Рассчитать", type="primary"):

    area_value = "all" if city_label == ALL_CITIES_LABEL else city_label

    payload = {

        "analyst_role": ROLE_OPTIONS[role_label],

        "experience": experience,

        "area": area_value,

        "source": SOURCE_OPTIONS[source_label],

        "employment": "unknown",

        "salary_spec": SALARY_SPEC_OPTIONS[salary_spec_label],

    }

    result = api_post("/predict", payload)

    st.success(f"Прогноз зарплаты: **{result['predicted_salary']:,.0f} ₽** / мес")



    skills = result.get("top_skills") or []

    n_vac = result.get("skills_vacancy_count", 0)

    st.subheader("Востребованные навыки (HH)")

    st.caption(

        f"Топ навыков для **{role_label}** · **{experience}** "

        f"(по {n_vac} вакансиям с key_skills на HH). "

        "На прогноз ЗП навыки не влияют."

    )

    if skills:

        df_sk = pd.DataFrame(skills)

        fig = px.bar(

            df_sk,

            x="count",

            y="name",

            orientation="h",

            title="Самые популярные навыки в вакансиях",

            labels={"count": "Вакансий", "name": "Навык"},

        )

        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=400)

        st.plotly_chart(fig, use_container_width=True)

    else:

        st.info(

            "Нет навыков HH для выбранной роли и опыта. "

            "Попробуйте другую роль или опыт."

        )


