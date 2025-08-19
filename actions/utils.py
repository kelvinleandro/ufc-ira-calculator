import os
import logging
import psycopg2
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()


def get_connection():
    try:
        conn = psycopg2.connect(
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=os.getenv("POSTGRES_PORT", "5432"),
            database=os.getenv("POSTGRES_DB", "postgres"),
        )
        logging.info("Conexão com o PostgreSQL estabelecida com sucesso.")
        return conn
    except:
        logging.error("Não foi possível conectar ao PostgreSQL.")
        raise
