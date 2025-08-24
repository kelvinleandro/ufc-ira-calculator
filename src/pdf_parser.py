import re
from pathlib import Path
import pdfplumber
from typing import Dict, List


def extract_disciplines(pdf_path: Path) -> List[Dict]:
    """
    Reads a student transcript PDF file and extracts course information.

    This final version uses a multi-pass approach to ensure correct data
    extraction, handling block separation issues and correctly identifying
    which components should be ignored.

    Args:
        pdf_path: The path to the transcript PDF file.

    Returns:
        A list of dictionaries, each representing a valid discipline for calculation.
    """
    disciplines = []

    with pdfplumber.open(pdf_path) as pdf:
        # 1. Pre-processing
        full_text = "".join(
            [page.extract_text(x_tolerance=2) or "" for page in pdf.pages]
        )
        try:
            legend_pos = full_text.index("Legenda:")
            full_text = full_text[:legend_pos]
        except ValueError:
            pass

        # 2. Map the location of all period markers (like "2025.1")
        period_regex = re.compile(r"\b(\d{4}\.\d)\b")
        period_locations = {
            m.start(): m.group(1) for m in period_regex.finditer(full_text)
        }
        sorted_period_starts = sorted(period_locations.keys())

        # 3. Find all disciplines
        # data_line_regex = re.compile(
        #     r"([*e&#@§]?)\s*([A-Z]{2,3}\d{4,})\s+.*?(\d+\.00)\s+.*?\s+(\d{1,2}(?:\.\d{1,2})?)\s+(APROVADO MÉDIA|APROVADO|REPROVADO|TRANCADO|SUPRIMIDO|APROVT INTERNO)"
        # )
        data_line_regex = re.compile(
            r"""
            ([*e&#@§]?)                                 # Group 1: Optional symbol (e.g., @, \#)
            \s*                                         # Zero or more whitespace characters
            ([A-Z]{2,3}\d{4,})                          # Group 2: Course code (e.g., CB0664)
            \s+.*?                                      # Generic separator (skips text like class, frequency)
            (\d+\.00)                                   # Group 3: Credit Hours (e.g., 128.00)
            \s+.*?                                      # Another generic separator
            (\d{1,2}(?:\.\d{1,2})?)                     # Group 4: Grade (e.g., 8.7 or 10)
            \s+                                         # One or more whitespace characters
            (                                           # Group 5: Course status
                APROVADO\ MÉDIA|APROVADO|REPROVADO|
                TRANCADO|SUPRIMIDO|APROVT\ INTERNO
            )
            """,
            re.VERBOSE,
        )
        matches = list(data_line_regex.finditer(full_text))

        last_match_end = 0

        # 4. Iterate over the found disciplines to process each block
        for _, match in enumerate(matches):
            symbol, course_code, hours, grade, status = match.groups()
            symbol = symbol.strip()

            if symbol in ["@", "§"] or status in ["APROVT INTERNO", "SUPRIMIDO"]:
                continue

            current_match_start = match.start()
            search_region = full_text[last_match_end:current_match_start]

            name_candidates = re.findall(
                r"\n([A-ZÁÀÂÃÉÊÍÎÓÔÕÚÇ\s]{3,})\n", search_region
            )
            course_name = (
                name_candidates[-1].strip()
                if name_candidates
                else "NOME NÃO ENCONTRADO"
            )

            last_match_end = match.end()

            current_period = None
            for period_start_index in reversed(sorted_period_starts):
                if period_start_index < current_match_start:
                    current_period = period_locations[period_start_index]
                    break

            if not current_period:
                continue

            try:
                disciplines.append(
                    {
                        "period": current_period,
                        "code": course_code,
                        "name": course_name,
                        "status": status,
                        "grade": float(grade),
                        "credit_hours": float(hours),
                        "symbol": symbol,
                    }
                )
            except (ValueError, IndexError):
                continue

    return disciplines


def extract_credit_hour_summary(pdf_path: Path) -> Dict[str, int]:
    """
    Parses the PDF to find the summary of total and optional credit hours.

    This function looks for the lines starting with "Carga Horária Total" and
    "Carga Horária Optativa" and extracts the 'required', 'completed', and
    'pending' hours for each category.

    Args:
        pdf_path: The Path object for the PDF file.

    Returns:
        A dictionary containing the summary of credit hours. Returns a dictionary
        with default zero values if data cannot be found or an error occurs.
    """
    summary = {
        "required_hours": 0,
        "completed_hours": 0,
        "optional_required_hours": 0,
        "optional_completed_hours": 0,
        "optional_pending_hours": 0,
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "".join([page.extract_text() or "" for page in pdf.pages])

        total_pattern = re.compile(r"Carga Horária Total\s+(\d+)\s+(\d+)")
        total_match = total_pattern.search(full_text)
        if total_match:
            summary["required_hours"] = int(total_match.group(1))
            summary["completed_hours"] = int(total_match.group(2))

        optional_pattern = re.compile(
            r"Carga Horária Optativa\s+(\d+)\s+(\d+)\s+\d+\s+(\d+)"
        )
        optional_match = optional_pattern.search(full_text)
        if optional_match:
            summary["optional_required_hours"] = int(optional_match.group(1))
            summary["optional_completed_hours"] = int(optional_match.group(2))
            summary["optional_pending_hours"] = int(optional_match.group(3))

    except Exception as e:
        print(f"Could not parse credit hour summary: {e}")

    return summary


def extract_pending_courses(pdf_path: Path) -> List[Dict]:
    """
    Parses the PDF transcript to find and extract the list of pending mandatory courses.

    This function searches for the specific section and then uses regular expressions
    to parse each subsequent line, extracting the course code, name, and
    credit hours for each pending course.

    Args:
        pdf_path: The Path object for the PDF file.

    Returns:
        A list of dictionaries, where each dictionary represents a pending course
        with 'code', 'name', and 'credit_hours'. Returns an empty list if the
        section is not found or an error occurs.
    """
    pending_courses = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "".join([page.extract_text() or "" for page in pdf.pages])

        # 1. Isolate the relevant section of the text
        # Find the start of the pending courses section
        start_marker = "Componentes Curriculares Obrigatórios Pendentes"
        start_index = full_text.find(start_marker)

        if start_index == -1:
            return []

        # The relevant text is everything after the marker
        relevant_text = full_text[start_index + len(start_marker) :]
        end_marker = "Equivalências:"
        end_index = relevant_text.find(end_marker)
        if end_index != -1:
            relevant_text = relevant_text[:end_index]

        # 2. Define the regex to find each course line
        course_pattern = re.compile(r"([A-Z]{2,3}\d{4,})\s+(.*?)\s+(\d+)\s*h")

        # 3. Find all matches in the isolated text
        matches = course_pattern.findall(relevant_text)

        # 4. Process each match and create a dictionary
        for match in matches:
            pending_courses.append(
                {
                    "code": match[0].strip(),
                    "name": match[1].strip(),
                    "credit_hours": int(match[2]),
                }
            )

    except Exception as e:
        print(f"Could not parse pending courses: {e}")

    pending_courses.sort(key=lambda x: x["name"])
    return pending_courses
