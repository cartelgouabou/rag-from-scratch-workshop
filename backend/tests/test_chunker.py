from ingestion.chunker import TextChunker
from ingestion.pipeline import _document_kind


def test_split_unit_preserves_markdown_sections() -> None:
    chunker = TextChunker(chunk_size=120, chunk_overlap=0)

    chunks = chunker.split_unit(
        """
        # Ordre du jour
        Point 1: Budget

        ## Décisions
        Validation du planning Q2.
        """,
        use_sections=True,
    )

    assert len(chunks) >= 2
    assert any(chunk.section_title == "Ordre du jour" for chunk in chunks)
    assert any(chunk.section_title == "Décisions" for chunk in chunks)
    assert any("planning Q2" in chunk.text for chunk in chunks)


def test_split_unit_preserves_numbered_sections() -> None:
    chunker = TextChunker(chunk_size=120, chunk_overlap=0)

    chunks = chunker.split_unit(
        """
        1. Contexte
        Le projet démarre en janvier.

        2.1 Décisions
        Le comité valide le budget.
        """,
        use_sections=True,
    )

    assert len(chunks) >= 2
    assert any(chunk.section_title and "Contexte" in chunk.section_title for chunk in chunks)
    assert any("budget" in chunk.text for chunk in chunks)


def test_split_unit_preserves_uppercase_sections() -> None:
    chunker = TextChunker(chunk_size=120, chunk_overlap=0)

    chunks = chunker.split_unit(
        """
        SYNTHESE

        Le patient est stable.

        TRAITEMENT

        Antibiotiques pendant 7 jours.
        """,
        use_sections=True,
    )

    assert len(chunks) >= 2
    assert any(chunk.section_title == "SYNTHESE" for chunk in chunks)
    assert any("Antibiotiques" in chunk.text for chunk in chunks)


def test_split_unit_falls_back_without_sections() -> None:
    chunker = TextChunker(chunk_size=40, chunk_overlap=0)

    chunks = chunker.split_unit(
        "Un paragraphe continu sans titre ni structure explicite pour guider le découpage.",
        use_sections=True,
    )

    assert len(chunks) >= 1
    assert all(chunk.section_title is None for chunk in chunks)


def test_split_unit_skips_sections_for_tabular_units() -> None:
    chunker = TextChunker(chunk_size=120, chunk_overlap=0)

    chunks = chunker.split_unit(
        """
        # Ne doit pas devenir un titre
        colonne: valeur
        """,
        use_sections=False,
    )

    assert len(chunks) == 1
    assert chunks[0].section_title is None


def test_document_kind_mapping() -> None:
    assert _document_kind("pdf") == "text"
    assert _document_kind("png") == "text"
    assert _document_kind("csv") == "table"
    assert _document_kind("xlsx") == "table"
