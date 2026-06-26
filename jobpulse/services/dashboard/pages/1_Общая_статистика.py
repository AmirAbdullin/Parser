import pandas as pd
import plotly.express as px
import streamlit as st

from api_client import EXPERIENCE_OPTIONS, ROLE_OPTIONS, api_get, check_api, format_api_datetime

st.set_page_config(page_title="Общая статистика — SkillCompass", layout="wide")
st.title("📊 Общая статистика")

ok, msg = check_api()
if not ok:
    st.error(msg)
    st.stop()

stats = api_get("/data/stats")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Вакансий", stats["total_vacancies"])
c2.metric("С зарплатой", stats["with_salary"])
c3.metric("Источников", len(stats.get("sources", {})))
c4.metric("Ролей", len(stats.get("roles", {})))

st.caption(
    f"Обновлено: {format_api_datetime(stats.get('updated_at'))} · "
    f"источник данных: {stats.get('data_source', '—')}"
)

col1, col2 = st.columns(2)
with col1:
    roles_by_source = stats.get("roles_by_source", {})
    if roles_by_source:
        rows = []
        for role, sources in roles_by_source.items():
            for source, count in sources.items():
                if count:
                    rows.append({"role": role, "source": source.upper(), "count": count})
        df_r = pd.DataFrame(rows)
        fig = px.bar(
            df_r,
            x="role",
            y="count",
            color="source",
            title="Вакансии по роли",
            labels={"role": "Роль", "count": "Кол-во вакансий", "source": "Источник"},
            barmode="stack",
        )
        fig.update_layout(xaxis_tickangle=-20)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("SuperJob включён в столбцы (оранжевый/синий сегмент), доля небольшая (~3%).")
    else:
        roles = stats.get("roles", {})
        if roles:
            df_r = pd.DataFrame({"role": list(roles.keys()), "count": list(roles.values())})
            fig = px.bar(
                df_r,
                x="role",
                y="count",
                title="Вакансии по роли",
                labels={"role": "Роль", "count": "Кол-во вакансий"},
            )
            fig.update_layout(xaxis_tickangle=-20)
            st.plotly_chart(fig, use_container_width=True)
with col2:
    src = stats.get("sources", {})
    if src:
        fig2 = px.pie(
            names=list(src.keys()),
            values=list(src.values()),
            title="Источники данных",
        )
        st.plotly_chart(fig2, use_container_width=True)

avg_by_role = stats.get("avg_salary_by_role", {})
if avg_by_role:
    df_s = pd.DataFrame(
        {"role": list(avg_by_role.keys()), "avg_salary": list(avg_by_role.values())}
    )
    fig3 = px.bar(
        df_s,
        x="role",
        y="avg_salary",
        title="Средняя зарплата по ролям (₽)",
        labels={"role": "Роль", "avg_salary": "Средняя ЗП, ₽"},
    )
    fig3.update_layout(xaxis_tickangle=-15)
    st.plotly_chart(fig3, use_container_width=True)
    st.caption("Без фильтров по опыту, городу и источнику — по всем вакансиям с указанной ЗП.")

st.divider()
st.subheader("Динамика зарплат")

filters = api_get("/data/filters")
experiences = filters.get("experiences", EXPERIENCE_OPTIONS)
role_labels = list(ROLE_OPTIONS.keys())
role_label = st.selectbox("Роль для графика", ["Все роли"] + role_labels)
experience = st.selectbox("Опыт для графика", ["Все"] + experiences)

role_param = None if role_label == "Все роли" else ROLE_OPTIONS[role_label]
exp_param = None if experience == "Все" else experience

query = "/data/salary-history"
params = []
if role_param:
    params.append(f"role={role_param}")
if exp_param:
    params.append(f"experience={exp_param}")
if params:
    query += "?" + "&".join(params)

history = api_get(query).get("items", [])
if history:
    df_h = pd.DataFrame(history)
    df_h["snapshot_at"] = pd.to_datetime(df_h["snapshot_at"], errors="coerce")
    fig_h = px.line(
        df_h,
        x="snapshot_at",
        y="median_salary",
        markers=True,
        title="Медианная зарплата во времени (₽)",
        labels={"snapshot_at": "Дата", "median_salary": "Медианная ЗП, ₽"},
    )
    st.plotly_chart(fig_h, use_container_width=True)
else:
    st.info("История появится после нескольких циклов ingest (snapshots) или при наличии published_at в данных.")
