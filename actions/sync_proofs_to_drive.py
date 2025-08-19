import os
import base64
import logging
import psycopg2
import io
import json
from dotenv import load_dotenv

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaIoBaseUpload

from utils import get_connection

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()

GDRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]


def get_gdrive_service() -> Resource:
    """
    Authenticates with the Google Drive API using OAuth 2.0 user credentials.
    """
    try:
        # base64_creds = os.environ["GDRIVE_OAUTH_CREDENTIALS"]
        base64_token = os.environ["GDRIVE_OAUTH_TOKEN"]

        # json_creds_bytes = base64.b64decode(base64_creds)
        json_token_bytes = base64.b64decode(base64_token)

        # creds_info = json.loads(json_creds_bytes)
        token_info = json.loads(json_token_bytes)

        creds = Credentials.from_authorized_user_info(info=token_info)
        service = build("drive", "v3", credentials=creds)
        logging.info("Autenticação com a API do Google Drive bem-sucedida.")
        return service
    except Exception as e:
        logging.error(f"Não foi possível autenticar no Google Drive.")
        raise


def list_existing_file_ids(service: Resource, folder_id: str) -> set:
    """Lists the file names (without extension) in a folder on Google Drive."""
    existing_ids = set()
    page_token = None
    try:
        while True:
            response = (
                service.files()
                .list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    spaces="drive",
                    fields="nextPageToken, files(name)",
                    pageToken=page_token,
                )
                .execute()
            )
            for file in response.get("files", []):
                file_id = os.path.splitext(file.get("name"))[0]
                existing_ids.add(file_id)
            page_token = response.get("nextPageToken", None)
            if page_token is None:
                break
        logging.info(
            f"Encontrados {len(existing_ids)} arquivos existentes no Google Drive."
        )
        return existing_ids
    except Exception as e:
        logging.error(f"Erro ao listar arquivos no Google Drive.")
        return existing_ids


def get_unresolved_forms(conn: psycopg2.extensions.connection) -> list:
    """Searches the 'forms' table for rows that have not been resolved yet."""
    forms_to_process = []
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, print_base64 FROM forms WHERE resolvido = false;")
            forms_to_process = cur.fetchall()
        logging.info(
            f"Encontrados {len(forms_to_process)} formulários não resolvidos na base de dados."
        )
        return forms_to_process
    except psycopg2.Error as e:
        logging.error(f"Erro ao buscar formulários no banco de dados.")
        return []


def upload_image_to_drive(
    service: Resource, folder_id: str, form_id: str, base64_data: str
) -> bool:
    """Uploads a decoded image to Google Drive."""
    try:
        image_bytes = base64.b64decode(base64_data)
        file_metadata = {"name": f"{form_id}.png", "parents": [folder_id]}

        fh = io.BytesIO(image_bytes)
        media = MediaIoBaseUpload(fh, mimetype="image/png", resumable=True)

        service.files().create(
            body=file_metadata, media_body=media, fields="id"
        ).execute()
        logging.info(
            f"Upload do comprovante '{form_id[:6]}...' para o Google Drive concluído."
        )
        return True
    except Exception as e:
        logging.error(f"Falha no upload do comprovante '{form_id[:6]}...'.")
        return False


def main():
    """
    Main function that orchestrates the process of synchronizing
    proof documents from the database to Google Drive.
    """
    logging.info("Iniciando o workflow de sincronização de comprovantes.")

    gdrive_folder_id = os.environ.get("GDRIVE_FOLDER_ID")
    if not gdrive_folder_id:
        logging.error("A variável de ambiente GDRIVE_FOLDER_ID não está definida.")
        return

    try:
        db_conn = get_connection()
        gdrive_service = get_gdrive_service()

        existing_drive_ids = list_existing_file_ids(gdrive_service, gdrive_folder_id)
        pending_forms = get_unresolved_forms(db_conn)

        new_forms_to_upload = [
            form for form in pending_forms if str(form[0]) not in existing_drive_ids
        ]

        if not new_forms_to_upload:
            logging.info(
                "Nenhum novo comprovante para sincronizar. Workflow concluído."
            )
            return

        logging.info(
            f"Sincronizando {len(new_forms_to_upload)} novo(s) comprovante(s)..."
        )

        success_count = 0
        for form in new_forms_to_upload:
            form_id_uuid = form[0]
            form_id_str = str(form_id_uuid)
            base64_image = form[1]

            if upload_image_to_drive(
                gdrive_service, gdrive_folder_id, form_id_str, base64_image
            ):
                success_count += 1

        logging.info(
            f"Sincronização concluída. {success_count} de {len(new_forms_to_upload)} comprovantes enviados com sucesso."
        )

    except Exception as e:
        logging.error(f"Ocorreu um erro fatal no workflow.")
    finally:
        if "db_conn" in locals() and db_conn:
            db_conn.close()
            logging.info("Conexão com o PostgreSQL fechada.")


if __name__ == "__main__":
    main()
