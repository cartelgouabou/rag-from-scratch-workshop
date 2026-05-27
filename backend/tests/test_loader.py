import pandas as pd

from ingestion.loader import dataframe_to_text_rows, detect_file_type


def test_detect_file_type_supports_expected_extensions() -> None:
    assert detect_file_type("report.pdf") == "pdf"
    assert detect_file_type("sales.csv") == "csv"
    assert detect_file_type("planning.xlsx") == "xlsx"


def test_dataframe_to_text_rows_serializes_tabular_content() -> None:
    dataframe = pd.DataFrame(
        [
            {"mois": "mars", "chiffre_affaires": 142300},
            {"mois": "avril", "chiffre_affaires": 131200},
        ]
    )

    rows = dataframe_to_text_rows(dataframe, "example.csv")

    assert len(rows) == 2
    assert "Document: example.csv" in rows[0].text
    assert "mois: mars" in rows[0].text
