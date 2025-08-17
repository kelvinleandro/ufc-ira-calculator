from typing import List, Dict
import pandas as pd


def calculate_individual_ira(disciplines: List[Dict]) -> float:
    """
    Calculates the Individual Academic Performance Index (IRA).

    Args:
        disciplines: A list of dictionaries, where each dictionary represents a course
                     with keys 'period', 'status', 'grade', and 'credit_hours'.

    Returns:
        The calculated Individual IRA as a float.
    """
    if not disciplines:
        return 0.0

    # Find the student's starting period for relative semester calculation
    first_period = min(d["period"] for d in disciplines)
    start_year, start_semester = map(int, first_period.split("."))

    # T = Sum of credit hours for dropped courses ('TRANCADO')
    dropped_hours_sum = sum(
        d["credit_hours"] for d in disciplines if d["status"] == "TRANCADO"
    )
    # C = Sum of credit hours for all attempted courses
    total_hours_sum = sum(d["credit_hours"] for d in disciplines)

    numerator = 0.0
    denominator = 0.0

    filtered_disciplines = [
        d
        for d in disciplines
        if d["status"] in ["APROVADO", "APROVADO MÉDIA", "REPROVADO"]
    ]

    for discipline in filtered_disciplines:
        credit_hours = discipline["credit_hours"]
        grade = discipline["grade"]
        year, semester = map(int, discipline["period"].split("."))

        # Calculate the relative semester number
        semester_number = (year - start_year) * 2 + (semester - start_semester) + 1
        period_weight = min(6, semester_number)

        numerator += period_weight * credit_hours * grade
        denominator += period_weight * credit_hours

    if total_hours_sum == 0:
        return 0.0
    penalty_factor = 1.0 - (0.5 * dropped_hours_sum) / total_hours_sum

    if denominator == 0:
        return 0.0
    weighted_average = numerator / denominator

    individual_ira = penalty_factor * weighted_average
    return individual_ira


def calculate_general_ira(
    individual_ira: float, course_average: float, course_deviation: float
) -> float:
    """
    Calculates the General Academic Performance Index (IRA).
    This normalizes the individual IRA against the student's course cohort.

    Args:
        individual_ira: The student's individual IRA.
        course_average: The average IRA for the course.
        course_deviation: The standard deviation of the IRA for the course.

    Returns:
        The General IRA, capped between 0 and 10, rounded to 3 decimal places.
    """
    if course_deviation == 0:
        general_ira = 6.0
    else:
        general_ira = 6 + 2 * ((individual_ira - course_average) / course_deviation)

    capped_ira = max(0.0, min(10.0, general_ira))
    return round(capped_ira, 3)


def calculate_semester_ira(disciplines: List[Dict]) -> Dict[str, float]:
    """
    Calculates the cumulative Individual IRA at the end of each completed semester.

    Args:
        disciplines: The full list of all disciplines from the transcript.

    Returns:
        A dictionary where the key is the period (e.g., "2022.1") and the value is
        the Individual IRA calculated with all disciplines up to that point.
    """
    if not disciplines:
        return {}

    semester_iras = {}
    completed_periods = sorted(list(set(d["period"] for d in disciplines)))

    for period in completed_periods:
        disciplines_until_period = [d for d in disciplines if d["period"] <= period]

        ira_for_period = calculate_individual_ira(disciplines_until_period)
        semester_iras[period] = ira_for_period

    return semester_iras


def calculate_mean_grade_per_semester(disciplines: List[Dict]) -> pd.Series:
    """
    Calculates the mean grade for each semester.

    Args:
        disciplines (List[Dict]): A list of course dictionaries. Each dictionary
            must contain at least a 'period' (e.g., '2022.1') and a 'grade' key.

    Returns:
        pd.Series: A Pandas Series where the index contains the sorted semester
            periods (str) and the values are the corresponding mean grades (float).
            Returns an empty Series if the input list is empty.
    """
    if not disciplines:
        return pd.Series(dtype=float)

    df = pd.DataFrame(disciplines)
    mean_grades_per_semester = df.groupby("period")["grade"].mean().sort_index()
    return mean_grades_per_semester


def prepare_hourly_load_data(disciplines: List[Dict]) -> pd.Series:
    """
    Groups disciplines by period and sums their credit hours for plotting.

    Args:
        disciplines: The full list of extracted disciplines.

    Returns:
        A Pandas Series with the period as the index and the sum of credit hours
        as the value.
    """
    if not disciplines:
        return pd.Series(dtype=float)

    df = pd.DataFrame(disciplines)
    hourly_load_per_semester = df.groupby("period")["credit_hours"].sum()
    return hourly_load_per_semester


def prepare_grade_distribution_data(disciplines: List[Dict]) -> pd.Series:
    """
    Calculates the distribution of grades by grouping them into bins.

    Args:
        disciplines: The full list of extracted disciplines.

    Returns:
        A Pandas Series with grade ranges as the index and the count of
        disciplines in each range as the value.
    """
    if not disciplines:
        return pd.Series(dtype=int)

    df = pd.DataFrame(disciplines)

    df_valid_grades = df[
        df["status"].str.contains("APROVADO|REPROVADO", case=False, na=False)
    ].copy()

    if df_valid_grades.empty:
        return pd.Series(dtype=int)

    bins = [0, 5, 7, 8, 9, 10.1]
    labels = [
        "Ruim (<5)",
        "Regular (5-7)",
        "Bom (7-8)",
        "Otimo (8-9)",
        "Excelente (9-10)",
    ]

    df_valid_grades["Grade Range"] = pd.cut(
        df_valid_grades["grade"],
        bins=bins,
        labels=labels,
        right=False,
        include_lowest=True,
    )

    grade_counts = df_valid_grades["Grade Range"].value_counts().sort_index()
    return grade_counts
