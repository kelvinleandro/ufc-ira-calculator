import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from src.database import load_courses
from src.pdf_parser import (
    extract_disciplines,
    extract_credit_hour_summary,
    extract_pending_courses,
)
from src.calculations import (
    calculate_individual_ira,
    calculate_general_ira,
    calculate_semester_ira,
    calculate_mean_grade_per_semester,
    prepare_hourly_load_data,
    prepare_grade_distribution_data,
)
from src.components import render_header, render_ira_simulator
from src.config import page_config


@st.cache_data
def convert_to_csv(disciplines_df: pd.DataFrame):
    """Convert a DataFrame to a CSV file and return its bytes representation."""
    return disciplines_df.to_csv(index=False).encode("utf-8")


page_config(
    layout="wide",
    page_title="Calculadora de IRA - UFC",
    initial_sidebar_state="collapsed",
)

render_header()

st.divider()

col_controls, col_results = st.columns([1, 2], gap="large")

with col_controls:
    st.subheader("Controles")
    uploaded_file = st.file_uploader("Selecione o seu histórico em PDF:", type="pdf")

    course_list_from_db = load_courses()

    # course_list_from_db = [
    #     ("Engenharia de Computação", 7.0248, 1.9467),
    #     ("Ciência da Computação", 7.2123, 1.8543),
    # ]

    course_options = [course[0] for course in course_list_from_db] + ["CUSTOMIZADO"]

    selected_course_name = st.selectbox(
        "Selecione seu curso para o cálculo do IRA Geral:",
        options=course_options,
    )

    course_avg = 0.0
    course_dev = 0.0

    if selected_course_name == "CUSTOMIZADO":
        st.write("Insira os valores para o cálculo:")
        course_avg = st.number_input(
            "Média do Curso (IRAm)", min_value=0.0, max_value=10.0, format="%.4f"
        )
        course_dev = st.number_input(
            "Desvio Padrão (IRAdp)", min_value=0.0, format="%.4f"
        )
    else:
        for course in course_list_from_db:
            if course[0] == selected_course_name:
                course_avg, course_dev = course[1], course[2]
                break

disciplines = []
if uploaded_file is not None:
    # Salva o arquivo temporariamente para que o pdfplumber possa lê-lo
    with open("temp_historico.pdf", "wb") as f:
        f.write(uploaded_file.getbuffer())
    pdf_path = Path("temp_historico.pdf")
    disciplines = extract_disciplines(pdf_path)

with col_controls:
    df_disciplines = pd.DataFrame(disciplines)
    df_disciplines.rename(
        columns={
            "period": "Periodo",
            "code": "Codigo",
            "name": "Disciplina",
            "status": "Status",
            "grade": "Nota",
            "credit_hours": "CH",
            "symbol": "Simbolo",
        },
        inplace=True,
    )
    csv_data = convert_to_csv(df_disciplines)

    st.download_button(
        label=":violet[:material/download:] Exportar Dados para CSV",
        data=csv_data,
        file_name="dados_historico_academico.csv",
        mime="text/csv",
        use_container_width=True,
        disabled=not disciplines,
        on_click="ignore",
    )

with col_results:
    col_header, col_simulator = st.columns([3, 1], gap="large")
    col_header.subheader("Seus Resultados")

    if uploaded_file is None:
        st.info("Aguardando o upload do histórico para exibir a análise.")
    else:
        with st.spinner("Analisando o histórico..."):
            # disciplines = extract_disciplines(pdf_path)
            credit_summary = extract_credit_hour_summary(pdf_path)
            pending_courses = extract_pending_courses(pdf_path)

        if not disciplines:
            st.error(
                "Nenhuma disciplina válida foi encontrada no histórico. Verifique o arquivo."
            )
        else:
            with col_simulator:
                render_ira_simulator(disciplines, course_avg, course_dev)

            final_ira = calculate_individual_ira(disciplines)
            final_general_ira = calculate_general_ira(final_ira, course_avg, course_dev)
            semester_iras = calculate_semester_ira(disciplines)
            semester_mean = calculate_mean_grade_per_semester(disciplines)

            required_hours = credit_summary.get("required_hours", 0)
            completed_hours = credit_summary.get("completed_hours", 0)
            progress_percent = (
                (completed_hours / required_hours) if required_hours > 0 else 0.0
            )
            optional_pending_hours = credit_summary.get("optional_pending_hours", 0)

            card1, card2, card3, card4 = st.columns(4)
            card1.metric("IRA Individual", f"{final_ira:.4f}")
            card2.metric("IRA Geral", f"{final_general_ira:.3f}")
            card3.metric("Progresso do Curso", f"{progress_percent:.1%}")
            card4.metric("Optativas Restantes", f"{optional_pending_hours:.0f} h")

            tab_plot, tab_sheet = st.tabs(
                [
                    ":blue[:material/bar_chart_4_bars:] Análise",
                    ":green[:material/table:] Pendências",
                ]
            )

            with tab_plot:
                df_ira_evolution = pd.DataFrame(
                    semester_iras.items(), columns=["Semestre", "IRA Individual"]
                )
                df_ira_evolution = df_ira_evolution.sort_values(by="Semestre")
                df_ira_evolution["Semestre"] = df_ira_evolution["Semestre"].astype(str)

                fig_combined = go.Figure()

                fig_combined.add_trace(
                    go.Scatter(
                        x=df_ira_evolution["Semestre"],
                        y=df_ira_evolution["IRA Individual"],
                        mode="lines+markers+text",
                        name="IRA Individual",
                        text=[f"{x:.3f}" for x in df_ira_evolution["IRA Individual"]],
                        textposition="top center",
                    )
                )

                fig_combined.add_trace(
                    go.Scatter(
                        x=semester_mean.index.astype(str),
                        y=semester_mean.values,
                        mode="lines+markers+text",
                        name="Média do Semestre",
                        text=[f"{x:.3f}" for x in semester_mean.values],
                        textposition="top center",
                    )
                )

                fig_combined.update_layout(
                    xaxis=dict(type="category", title="Semestre"),
                    yaxis=dict(title="Nota"),
                    title="Evolução Semestral do Estudante",
                    legend_title="Legenda",
                )

                st.plotly_chart(fig_combined, use_container_width=True)

                st.divider()
                st.subheader("Análises Detalhadas")
                col_graph1, col_graph2 = st.columns(2)

                with col_graph1:
                    grade_data = prepare_grade_distribution_data(disciplines)
                    if not grade_data.empty:
                        fig_grades = px.bar(
                            grade_data,
                            x=grade_data.index,
                            y=grade_data.values,
                            labels={
                                "y": "Quantidade de Disciplinas",
                                "Grade Range": "Faixa de Nota",
                            },
                            text_auto=True,
                            title="Distribuição de Notas",
                        )
                        st.plotly_chart(fig_grades, use_container_width=True)
                    else:
                        st.info("Não há notas para exibir.")

                with col_graph2:
                    hourly_data = prepare_hourly_load_data(disciplines)
                    if not hourly_data.empty:
                        hourly_data = hourly_data.sort_index()
                        hourly_data.index = hourly_data.index.astype(str)

                        fig_hours = px.bar(
                            hourly_data,
                            x=hourly_data.index,
                            y=hourly_data.values,
                            labels={
                                "y": "Carga Horária Total (h)",
                                "period": "Semestre",
                            },
                            text_auto=True,
                            title="Carga Horária por Semestre",
                        )

                        fig_hours.update_xaxes(type="category")
                        st.plotly_chart(fig_hours, use_container_width=True)
                    else:
                        st.info("Não há dados de carga horária para exibir.")

            with tab_sheet:
                st.subheader("Disciplinas Obrigatórias Pendentes")
                if pending_courses:
                    df_pending = pd.DataFrame(pending_courses)
                    df_pending.columns = [
                        "Código",
                        "Componente Curricular",
                        "Carga Horária (h)",
                    ]

                    st.dataframe(data=df_pending, hide_index=True)
                else:
                    st.success(
                        "Parabéns! Nenhuma disciplina obrigatória pendente foi encontrada."
                    )
