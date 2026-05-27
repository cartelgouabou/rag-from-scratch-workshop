from api.routes_chat import _diversify_results, _extract_filename_filter


def test_extract_filename_filter_matches_stem() -> None:
    documents = [
        {"id": "doc-1", "filename": "arthur_CV.pdf", "type": "pdf"},
        {"id": "doc-2", "filename": "example.csv", "type": "csv"},
    ]

    result = _extract_filename_filter("Que dit arthur cv sur les postes occupes ?", documents)

    assert result == "arthur_CV.pdf"


def test_diversify_results_limits_chunks_per_document() -> None:
    results = [
        {"metadata": {"document_id": "doc-1"}, "score": 0.9},
        {"metadata": {"document_id": "doc-1"}, "score": 0.85},
        {"metadata": {"document_id": "doc-1"}, "score": 0.8},
        {"metadata": {"document_id": "doc-2"}, "score": 0.79},
    ]

    diversified = _diversify_results(results, top_k=3, max_per_document=2)

    assert len(diversified) == 3
    assert sum(item["metadata"]["document_id"] == "doc-1" for item in diversified) == 2
