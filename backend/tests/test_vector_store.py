from storage.vector_store import VectorStore, _sanitize_metadata


class DummyCollection:
    def __init__(self) -> None:
        self.query_kwargs = {}

    def query(self, **kwargs):
        self.query_kwargs = kwargs
        return {
            "documents": [["chunk-a"]],
            "metadatas": [[{"document_id": "doc-1", "filename": "arthur_CV.pdf"}]],
            "distances": [[0.42]],
        }

    def get(self, **kwargs):
        return {
            "metadatas": [
                {"document_id": "doc-1"},
                {"document_id": "doc-1"},
                {"document_id": "doc-2"},
            ]
        }


def test_sanitize_metadata_drops_none_values() -> None:
    sanitized = _sanitize_metadata(
        {
            "document_kind": "text",
            "section_title": None,
            "page_number": 1,
            "ocr_used": False,
        }
    )

    assert "section_title" not in sanitized
    assert sanitized["document_kind"] == "text"
    assert sanitized["page_number"] == 1
    assert sanitized["ocr_used"] is False


def test_query_forwards_where_filters() -> None:
    store = object.__new__(VectorStore)
    store.collection = DummyCollection()

    results = store.query(
        [0.1, 0.2],
        10,
        where={"filename": "arthur_CV.pdf"},
        where_document={"$contains": "arthur"},
    )

    assert len(results) == 1
    assert store.collection.query_kwargs["where"] == {"filename": "arthur_CV.pdf"}
    assert store.collection.query_kwargs["where_document"] == {"$contains": "arthur"}


def test_get_document_chunk_counts_aggregates_by_document() -> None:
    store = object.__new__(VectorStore)
    store.collection = DummyCollection()

    counts = store.get_document_chunk_counts()

    assert counts == {"doc-1": 2, "doc-2": 1}
