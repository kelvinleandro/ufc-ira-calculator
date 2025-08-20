import streamlit as st


def page_config(**kwargs):
    st.set_page_config(page_icon="assets/brasao_ufc.png", **kwargs)


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
