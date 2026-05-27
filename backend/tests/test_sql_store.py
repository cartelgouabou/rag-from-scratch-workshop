from pathlib import Path

import pandas as pd

from storage.sql_store import SQLStore


def test_sql_store_tracks_documents_and_stats(tmp_path: Path) -> None:
    sqlite_file = tmp_path / "knowledge.db"
    store = SQLStore(sqlite_file)

    dataframe = pd.DataFrame(
        [
            {"mois": "mars", "chiffre_affaires": 142300, "commandes": 156},
            {"mois": "avril", "chiffre_affaires": 131200, "commandes": 148},
        ]
    )

    table_name = store.create_tabular_table("doc-123", dataframe)
    store.upsert_document(
        document_id="doc-123",
        filename="example.csv",
        file_type="csv",
        nb_chunks=2,
        nb_records=2,
        sql_table_name=table_name,
        source_path="doc-123/example.csv",
    )

    documents = store.list_documents()
    stats = store.get_stats()
    result = store.execute_query(f'SELECT SUM(chiffre_affaires) AS total FROM "{table_name}"')

    assert len(documents) == 1
    assert documents[0]["source_path"] == "doc-123/example.csv"
    assert stats["total_documents"] == 1
    assert stats["total_chunks"] == 2
    assert stats["total_records"] == 2
    assert result[0]["total"] == 273500

    deleted = store.delete_document("doc-123")

    assert deleted is not None
    assert store.list_documents() == []


def test_sql_store_purge_all(tmp_path: Path) -> None:
    sqlite_file = tmp_path / "knowledge.db"
    store = SQLStore(sqlite_file)

    dataframe = pd.DataFrame([{"value": 1}, {"value": 2}])
    table_name = store.create_tabular_table("doc-a", dataframe)
    store.upsert_document(
        document_id="doc-a",
        filename="a.csv",
        file_type="csv",
        nb_chunks=1,
        nb_records=2,
        sql_table_name=table_name,
    )
    store.upsert_document(
        document_id="doc-b",
        filename="b.pdf",
        file_type="pdf",
        nb_chunks=3,
        nb_records=0,
    )

    deleted_count = store.purge_all()

    assert deleted_count == 2
    assert store.list_documents() == []
    assert store.get_stats()["total_documents"] == 0
