"""Sélection du fichier démo dans data/samples/ (PDF par défaut)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ingestion.loader import detect_file_type

IGNORED_NAMES = {".gitkeep", "README.md", ".DS_Store"}
SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"


@dataclass
class DemoFile:
    path: Path
    filename: str
    file_type: str

    @property
    def document_kind(self) -> str:
        return "table" if self.file_type in {"csv", "xlsx", "xls"} else "text"


def list_pdf_candidates(samples_dir: Path | None = None) -> list[DemoFile]:
    root = samples_dir or SAMPLES_DIR
    if not root.exists():
        return []

    pdfs: list[DemoFile] = []
    for path in sorted(root.iterdir()):
        if not path.is_file():
            continue
        if path.name in IGNORED_NAMES or path.name.startswith("."):
            continue
        if path.suffix.lower() != ".pdf":
            continue
        pdfs.append(
            DemoFile(
                path=path,
                filename=path.name,
                file_type="pdf",
            )
        )
    return pdfs


def resolve_demo_file(
    filename: str | None = None,
    *,
    samples_dir: Path | None = None,
) -> DemoFile:
    root = samples_dir or SAMPLES_DIR

    if filename:
        path = root / filename
        if not path.is_file():
            available = ", ".join(item.filename for item in list_pdf_candidates(samples_dir)) or "(aucun PDF)"
            raise FileNotFoundError(
                f"Fichier '{filename}' introuvable dans {root}. PDF disponibles: {available}"
            )
        return DemoFile(
            path=path,
            filename=path.name,
            file_type=detect_file_type(path.name),
        )

    pdfs = list_pdf_candidates(samples_dir)
    if not pdfs:
        raise FileNotFoundError(
            f"Aucun PDF dans {root}. Déposez un fichier .pdf ou définissez DEMO_FILENAME."
        )
    return pdfs[0]


def load_demo_bytes(
    filename: str | None = None,
    *,
    samples_dir: Path | None = None,
) -> tuple[DemoFile, bytes]:
    demo_file = resolve_demo_file(filename, samples_dir=samples_dir)
    return demo_file, demo_file.path.read_bytes()
