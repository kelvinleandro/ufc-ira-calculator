from pathlib import Path
from src.pdf_parser import extract_disciplines
from src.calculations import calculate_individual_ira, calculate_general_ira


def main():
    MEDIA_CURSO = 7.2652
    DESVIO_CURSO = 1.8389

    pdf_path = Path("data/historico.pdf")
    disciplinas = extract_disciplines(pdf_path)
    ira_i = calculate_individual_ira(disciplinas)
    ira_g = calculate_general_ira(ira_i, MEDIA_CURSO, DESVIO_CURSO)
    print(f"IRA-I: {ira_i:.3f}, IRA-G: {ira_g:.3f}")


if __name__ == "__main__":
    main()
