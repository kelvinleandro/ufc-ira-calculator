import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from src.database import load_courses
from src.pdf_parser import extract_disciplines, extract_credit_hour_summary
from src.calculations import (
    calculate_individual_ira,
    calculate_general_ira,
    calculate_semester_ira,
    prepare_hourly_load_data,
    prepare_grade_distribution_data,
)
from src.components import render_header

st.set_page_config(layout="wide", page_title="Calculadora de IRA - UFC", page_icon="📊")

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

    course_options = [course[0] for course in course_list_from_db] + ["Customizado"]

    selected_course_name = st.selectbox(
        "Selecione seu curso para o cálculo do IRA Geral:",
        options=course_options,
    )

    course_avg = 0.0
    course_dev = 0.0

    if selected_course_name == "Customizado":
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

with col_results:
    st.subheader("Seus Resultados")
    if uploaded_file is None:
        st.info("Aguardando o upload do histórico para exibir a análise.")
    else:
        # Salva o arquivo temporariamente para que o pdfplumber possa lê-lo
        with open("temp_historico.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        pdf_path = Path("temp_historico.pdf")

        with st.spinner("Analisando o histórico..."):
            disciplines = extract_disciplines(pdf_path)
            credit_summary = extract_credit_hour_summary(pdf_path)

        if not disciplines:
            st.error(
                "Nenhuma disciplina válida foi encontrada no histórico. Verifique o arquivo."
            )
        else:
            final_ira = calculate_individual_ira(disciplines)
            final_general_ira = calculate_general_ira(final_ira, course_avg, course_dev)
            semester_iras = calculate_semester_ira(disciplines)

            required_hours = credit_summary.get("required_hours", 0)
            completed_hours = credit_summary.get("completed_hours", 0)
            progress_percent = (
                (completed_hours / required_hours) if required_hours > 0 else 0.0
            )

            card1, card2, card3 = st.columns(3)
            card1.metric("IRA Individual", f"{final_ira:.4f}")
            card2.metric("IRA Geral", f"{final_general_ira:.3f}")
            card3.metric("Progresso do Curso", f"{progress_percent:.1%}")

            df_ira_evolution = pd.DataFrame(
                semester_iras.items(), columns=["Semestre", "IRA Individual"]
            )
            df_ira_evolution = df_ira_evolution.sort_values(by="Semestre")
            df_ira_evolution["Semestre"] = df_ira_evolution["Semestre"].astype(str)
            fig_evolution = px.line(
                df_ira_evolution,
                x="Semestre",
                y="IRA Individual",
                markers=True,
                text=df_ira_evolution["IRA Individual"].apply(lambda x: f"{x:.3f}"),
                title="Evolução do IRA Individual por Semestre",
            )
            fig_evolution.update_xaxes(type="category")
            fig_evolution.update_traces(textposition="top center")
            st.plotly_chart(fig_evolution, use_container_width=True)

            st.divider()
            st.subheader("Análises Detalhadas")
            col_graph1, col_graph2 = st.columns(2)

            with col_graph1:
                st.markdown("##### Distribuição de Notas")
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
                    )
                    st.plotly_chart(fig_grades, use_container_width=True)
                else:
                    st.info("Não há notas para exibir.")

            with col_graph2:
                st.markdown("##### Carga Horária por Semestre")
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
                        title="Carga Horária Cursada por Semestre",
                    )

                    fig_hours.update_xaxes(type="category")
                    st.plotly_chart(fig_hours, use_container_width=True)
                else:
                    st.info("Não há dados de carga horária para exibir.")
