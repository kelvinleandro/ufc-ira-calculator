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

        # 3. Find all disciplines and their symbols
        # Group 1: Optional symbol (@, #, e, etc.), Group 2: Discipline Code
        discipline_regex = re.compile(r"([*e&#@§]?)\s*([A-Z]{2,3}\d{4,})")
        matches = list(discipline_regex.finditer(full_text))

        # 4. Iterate over the found disciplines to process each block
        for i, match in enumerate(matches):
            # Define the text block for the current discipline
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
            course_block = full_text[start_pos:end_pos]

            # Get the symbol (if any) to decide whether to ignore the block
            symbol = match.group(1).strip()

            # Ignore Mandatory Activities (@) and Optional Activities (§)
            if symbol in ["@", "§"]:
                continue

            # Find the correct period for the current discipline
            current_period = None
            for period_start_index in reversed(sorted_period_starts):
                if period_start_index < start_pos:
                    current_period = period_locations[period_start_index]
                    break

            if not current_period:
                continue

            # Extract data from the discipline block
            status_match = re.search(
                r"(APROVADO MÉDIA|APROVADO|REPROVADO|TRANCADO|SUPRIMIDO|APROVT INTERNO)",
                course_block,
            )
            if not status_match:
                continue

            status = status_match.group(0)
            if status in ["APROVT INTERNO", "SUPRIMIDO"]:
                continue

            grade_match = re.search(
                r"(\d{1,2}(?:\.\d{1,2})?)\s+" + re.escape(status), course_block
            )
            hours_match = re.search(r"(\d+\.00)", course_block)

            if grade_match and hours_match:
                try:
                    disciplines.append(
                        {
                            "period": current_period,
                            "status": status,
                            "grade": float(grade_match.group(1)),
                            "credit_hours": float(hours_match.group(1)),
                        }
                    )
                except (ValueError, IndexError):
                    continue

    return disciplines


def extract_credit_hour_summary(pdf_path: Path) -> Dict[str, int]:
    """
    Parses the PDF to find the summary of total credit hours.

    This function looks for the line starting with "Carga Horária Total"
    which typically appears after the "Legenda:" section in the transcript,
    and extracts the 'required' and 'completed' hours.

    Args:
        pdf_path: The Path object for the PDF file.

    Returns:
        A dictionary with 'required_hours' and 'completed_hours'.
        Returns a dictionary with 0s if the data cannot be found or an error occurs.
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "".join([page.extract_text() or "" for page in pdf.pages])

        # Regex to find the "Carga Horária Total" line and capture the first two numbers
        pattern = re.compile(r"Carga Horária Total\s+(\d+)\s+(\d+)")
        match = pattern.search(full_text)

        if match:
            required = int(match.group(1))
            completed = int(match.group(2))

            return {"required_hours": required, "completed_hours": completed}

    except Exception as e:
        print(f"Could not parse credit hour summary: {e}")

    return {"required_hours": 0, "completed_hours": 0}
