from pathlib import Path

from demo_paths import list_pdf_candidates, resolve_demo_file


def test_list_pdf_candidates_ignores_non_pdf(tmp_path: Path) -> None:
    samples = tmp_path / "samples"
    samples.mkdir()
    (samples / "example.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    (samples / "alpha.pdf").write_bytes(b"%PDF-1.4")
    (samples / "beta.pdf").write_bytes(b"%PDF-1.4")

    pdfs = list_pdf_candidates(samples)
    assert [p.filename for p in pdfs] == ["alpha.pdf", "beta.pdf"]


def test_resolve_demo_file_picks_first_pdf_by_default(tmp_path: Path) -> None:
    samples = tmp_path / "samples"
    samples.mkdir()
    (samples / "zzz.pdf").write_bytes(b"%PDF-1.4")
    (samples / "aaa.pdf").write_bytes(b"%PDF-1.4")

    resolved = resolve_demo_file(samples_dir=samples)
    assert resolved.filename == "aaa.pdf"


def test_resolve_demo_file_with_explicit_name(tmp_path: Path) -> None:
    samples = tmp_path / "samples"
    samples.mkdir()
    (samples / "aaa.pdf").write_bytes(b"%PDF-1.4")
    (samples / "cible.pdf").write_bytes(b"%PDF-1.4")

    resolved = resolve_demo_file("cible.pdf", samples_dir=samples)
    assert resolved.filename == "cible.pdf"
