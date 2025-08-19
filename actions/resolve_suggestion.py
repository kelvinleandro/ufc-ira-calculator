import logging
from utils import get_connection

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    import sys

    try:
        form_id = sys.argv[1]
    except IndexError:
        form_id = input("Digite o ID do formulário: ")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT nome_curso, media, desvio, print_base64 FROM forms WHERE id = %s AND resolvido = false",
                (form_id,),
            )
            form = cur.fetchone()
            if form:
                nome_curso, media, desvio, print_base64 = form

                cur.execute(
                    "UPDATE forms SET resolvido = true WHERE id = %s", (form_id,)
                )

                cur.execute(
                    "INSERT INTO ira (curso, media, desvio) VALUES (%s, %s, %s)",
                    (nome_curso, media, desvio),
                )

                conn.commit()
                logging.info(f"Formulário '{form_id[:6]}...' resolvido com sucesso.")
            else:
                logging.info(
                    f"Formulario '{form_id[:6]}...' não encontrado ou já resolvido."
                )
    except Exception as e:
        logging.error(e)
        conn.rollback()
    finally:
        conn.close()
