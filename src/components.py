import time
from typing import List, Dict
import streamlit as st
import pandas as pd
from src.database import save_course_suggestion
from src.calculations import calculate_individual_ira, calculate_general_ira


@st.dialog("Sugerir Novo Curso")
def show_form():
    with st.form("form_novo_curso"):
        st.markdown(
            """
            <style>
            input[type="text"] {
                text-transform: uppercase;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        st.write(
            "Ajude-nos a adicionar mais cursos à lista. Envie os dados e um comprovante (print do SIGAA mostrando os valores, por exemplo)."
        )

        course_name_sug = st.text_input("Nome do Curso").upper()
        avg_col, dev_col = st.columns(2)
        with avg_col:
            average_sug = st.number_input(
                "Média do Curso (IRAm)", format="%.4f", min_value=0.0, max_value=10.0
            )
        with dev_col:
            deviation_sug = st.number_input(
                "Desvio Padrão (IRAdp)", format="%.4f", min_value=0.0, max_value=10.0
            )

        proof_file_sug = st.file_uploader(
            "Anexar comprovante (imagem)", type=["png", "jpg", "jpeg"]
        )

        if st.form_submit_button("Enviar Sugestão"):
            if save_course_suggestion(
                course_name_sug, average_sug, deviation_sug, proof_file_sug
            ):
                st.success("Obrigado! Sua sugestão foi enviada para análise.")
                time.sleep(2)
                st.rerun()
            else:
                st.error("Não foi possível enviar a sugestão. Verifique os campos.")


def render_header():
    """
    Renders the reusable page header, including the title, navigation links,
    and the modal logic for suggesting a new course.
    """

    col_logo, _, col_about, col_modal = st.columns(
        [3, 3, 1.5, 2.5], vertical_alignment="center"
    )

    with col_logo:
        st.markdown(
            """
            <style>
                div.st-key-logo_button button[kind="tertiary"] p {
                    font-size: 2.25rem;
                    font-weight: bold;
                    padding:0;
                    margin:0;
                    transition: color 0.3s ease;
                }

                div.st-key-logo_button button[kind="tertiary"] p:hover {
                    color: #26c2ed;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Calculadora de IRA", type="tertiary", key="logo_button"):
            st.switch_page("app.py")

    with col_about:
        if st.button("Sobre o IRA", icon="❓", type="secondary", key="about_button"):
            st.switch_page("pages/1_About.py")
        # st.page_link("pages/1_About.py", label="Sobre o IRA", icon="❓")

    with col_modal:
        if st.button("Meu curso não está na lista"):
            show_form()


def apply_global_styles():
    st.markdown(
        """
        <style>
        [data-testid="stSidebar"] {
            display: none
        }

        [data-testid="stExpandSidebarButton"] {
            display: none
        }

        [data-testid="collapsedControl"] {
            display: none
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.dialog("Simular IRA", width="large")
def show_ira_simulator_dialog(
    current_disciplines: List[Dict], course_avg: float, course_dev: float
):
    st.info(
        "Adicione as disciplinas futuras, o período em que pretende cursá-las e as notas que espera obter."
    )

    last_period = max(d["period"] for d in current_disciplines)
    year, semester = map(int, last_period.split("."))
    default_next_period = f"{year}.2" if semester == 1 else f"{year + 1}.1"

    simulated_courses_df = pd.DataFrame(
        [
            {
                "Componente": "",
                "Período": default_next_period,
                "CH": 64,
                "Nota": 0.0,
            }
        ]
    )

    edited_df = st.data_editor(
        simulated_courses_df,
        num_rows="dynamic",
        column_config={
            "Componente": st.column_config.TextColumn(
                "Componente Curricular", required=True
            ),
            "Período": st.column_config.TextColumn(
                "Período (ex: 2025.2)", required=True
            ),
            "CH": st.column_config.NumberColumn(
                "Carga Horária (h)", min_value=0, required=True
            ),
            "Nota": st.column_config.NumberColumn(
                "Nota Esperada",
                min_value=0.0,
                max_value=10.0,
                format="%.2f",
                required=True,
            ),
        },
        key="simulator_editor",
    )

    if st.button("Simular Novo IRA", type="primary"):
        valid_simulated_courses = edited_df[edited_df["Componente"] != ""].copy()

        if valid_simulated_courses.empty:
            st.warning("Por favor, adicione pelo menos uma disciplina para simular.")
        else:
            future_disciplines = []
            error_found = False
            completed_periods = set(d["period"] for d in current_disciplines)

            for index, row in valid_simulated_courses.iterrows():
                period = row["Período"]
                grade = float(row["Nota"])

                if period in completed_periods:
                    st.error(
                        f"Erro: O período '{period}' na linha {index + 1} já foi cursado. Por favor, insira um período novo."
                    )
                    error_found = True
                    break

                future_disciplines.append(
                    {
                        "period": period,
                        "status": "APROVADO" if grade >= 5.0 else "REPROVADO",
                        "grade": grade,
                        "credit_hours": float(row["CH"]),
                    }
                )

            if not error_found:
                combined_disciplines = current_disciplines + future_disciplines

                current_ira = calculate_individual_ira(current_disciplines)
                simulated_ira = calculate_individual_ira(combined_disciplines)

                current_general_ira = calculate_general_ira(
                    current_ira, course_avg, course_dev
                )
                simulated_general_ira = calculate_general_ira(
                    simulated_ira, course_avg, course_dev
                )

                st.subheader("Resultados da Simulação")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "IRA Individual Simulado",
                        f"{simulated_ira:.4f}",
                        delta=f"{simulated_ira - current_ira:.4f}",
                    )
                with col2:
                    st.metric(
                        "IRA Geral Simulado",
                        f"{simulated_general_ira:.3f}",
                        delta=f"{simulated_general_ira - current_general_ira:.3f}",
                    )


def render_ira_simulator(
    current_disciplines: List[Dict], course_avg: float, course_dev: float
):
    """
    Renders an interactive IRA simulator.

    Allows the user to input future courses, expected grades, and the specific
    period for each course.

    Args:
        current_disciplines (list): The list of discipline dictionaries already extracted from the PDF.
        course_avg (float): The average IRA of the selected course.
        course_dev (float): The standard deviation of the selected course.
    """
    if st.button("Simular IRA", icon="🔮", type="secondary"):
        show_ira_simulator_dialog(current_disciplines, course_avg, course_dev)
