import streamlit as st
from src.database import save_course_suggestion
import time


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
                .custom-logo {
                    color: #fff !important;
                    transition: color 0.3s ease;
                }

                .custom-logo-link:hover .custom-logo {
                    color: #26c2ed !important;
                }
            </style>
            <a href="/" target="_self" class="custom-logo-link" style="text-decoration: none;">
                <h2 class="custom-logo">Calculadora de IRA</h2>
            </a>
            """,
            unsafe_allow_html=True,
        )

    with col_about:
        st.page_link("pages/1_About.py", label="Sobre o IRA", icon="❓")

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
