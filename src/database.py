import base64
from typing import List, Tuple
import psycopg2
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile


def get_db_connection():
    """Stabilish and return a connection with the PostgreSQL database using the Streamlit secrets."""
    try:
        conn = psycopg2.connect(**st.secrets["postgres"])
        return conn
    except Exception as e:
        # st.error(f"Error connecting to the database: {e}")
        st.error(
            f"Erro ao conectar com o banco de dados. Tente novamente ou use a opção customizada."
        )
        return None


def load_courses() -> List[Tuple]:
    """
    Fetches and returns the list of courses (name, average, deviation) from the 'ira' table.

    Returns:
        A list of tuples, where each tuple contains (course_name, average, deviation).
        Returns an empty list in case of an error.
    """
    courses = []
    conn = get_db_connection()
    if conn is None:
        return courses

    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute("SELECT curso, media, desvio FROM ira ORDER BY curso;")
                courses = cur.fetchall()
    except psycopg2.Error as e:
        # st.error(f"Error fetching courses: {e}")
        st.error("Erro ao buscar cursos. Tente novamente.")
    finally:
        if conn:
            conn.close()

    return courses


def save_course_suggestion(
    course_name: str, average: float, deviation: float, proof_file: UploadedFile
) -> bool:
    """
    Saves the course suggestion form data, including a proof image (screenshot)
    encoded in Base64, to the 'forms' table.

    Args:
        course_name: The suggested course name.
        average: The course average (IRAm).
        deviation: The course standard deviation (IRAdp).
        proof_file: The file object uploaded via st.file_uploader.

    Returns:
        True if the operation was successful, False otherwise.
    """
    if not all([course_name, average, deviation, proof_file]):
        st.warning("Preencha todos os campos.")
        return False

    conn = get_db_connection()
    if conn is None:
        return False

    success = False
    try:
        # Encode to Base64
        image_bytes = proof_file.getvalue()
        base64_bytes = base64.b64encode(image_bytes)
        base64_string = base64_bytes.decode("utf-8")

        with conn:
            with conn.cursor() as cur:
                query = """
                    INSERT INTO forms (nome_curso, media, desvio, print_base64)
                    VALUES (%s, %s, %s, %s);
                """
                cur.execute(query, (course_name, average, deviation, base64_string))

        success = True
    except psycopg2.Error as e:
        # st.error(f"Error saving suggestion: {e}")
        st.error("Erro ao tentar salvar sugestão.")
        conn.rollback()
    finally:
        if conn:
            conn.close()

    return success
