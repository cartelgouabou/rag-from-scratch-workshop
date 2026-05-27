from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import tempfile
from typing import Any, Literal

import fitz
import pandas as pd
import pdfplumber

SupportedFileType = Literal["pdf", "csv", "xlsx", "xls", "png", "jpg", "jpeg", "webp"]

SUPPORTED_EXTENSIONS: dict[str, SupportedFileType] = {
    ".pdf": "pdf",
    ".csv": "csv",
    ".xlsx": "xlsx",
    ".xls": "xls",
    ".png": "png",
    ".jpg": "jpg",
    ".jpeg": "jpeg",
    ".webp": "webp",
}

_DOCTR_PREDICTOR: Any | None = None


@dataclass
class TextUnit:
    text: str
    metadata: dict[str, str | int | bool]


@dataclass
class ExtractedDocument:
    units: list[TextUnit]
    extraction_source: str
    ocr_used: bool


def detect_file_type(filename: str) -> SupportedFileType:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension or 'unknown'}")
    return SUPPORTED_EXTENSIONS[extension]


def extract_pdf_document(file_bytes: bytes, dpi: int = 200) -> ExtractedDocument:
    native_units = _extract_pdf_text_units(file_bytes)
    if native_units:
        return ExtractedDocument(
            units=native_units,
            extraction_source="pdfplumber",
            ocr_used=False,
        )

    ocr_units = _extract_pdf_with_doctr(file_bytes, dpi=dpi)
    return ExtractedDocument(
        units=ocr_units,
        extraction_source="doctr_ocr" if ocr_units else "none",
        ocr_used=bool(ocr_units),
    )


def extract_image_document(file_bytes: bytes, extension: str) -> ExtractedDocument:
    units = _extract_images_with_doctr([(file_bytes, extension)], source_modality="image")
    return ExtractedDocument(
        units=units,
        extraction_source="doctr_ocr" if units else "none",
        ocr_used=bool(units),
    )


def load_csv(file_bytes: bytes) -> pd.DataFrame:
    return pd.read_csv(BytesIO(file_bytes)).fillna("")


def load_excel(file_bytes: bytes) -> pd.DataFrame:
    sheets = pd.read_excel(BytesIO(file_bytes), sheet_name=None).values()
    frames: list[pd.DataFrame] = []
    for index, sheet in enumerate(sheets, start=1):
        frame = sheet.fillna("").copy()
        frame.insert(0, "sheet_name", f"sheet_{index}")
        frames.append(frame)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def dataframe_to_text_rows(dataframe: pd.DataFrame, filename: str) -> list[TextUnit]:
    records = dataframe.fillna("").to_dict(orient="records")
    rows: list[TextUnit] = []
    for position, record in enumerate(records, start=1):
        parts = [f"{key}: {value}" for key, value in record.items()]
        metadata: dict[str, str | int | bool] = {
            "source_modality": "table",
            "row_number": position,
            "ocr_used": False,
            "extraction_source": "tabular",
        }
        sheet_name = record.get("sheet_name")
        if isinstance(sheet_name, str) and sheet_name:
            metadata["sheet_name"] = sheet_name
        rows.append(
            TextUnit(
                text=f"Document: {filename}\nRow: {position}\n" + "\n".join(parts),
                metadata=metadata,
            )
        )
    return rows


def _extract_pdf_text_units(file_bytes: bytes) -> list[TextUnit]:
    units: list[TextUnit] = []
    with pdfplumber.open(BytesIO(file_bytes)) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if not page_text:
                continue
            units.append(
                TextUnit(
                    text=page_text,
                    metadata={
                        "source_modality": "pdf",
                        "page_number": page_number,
                        "ocr_used": False,
                        "extraction_source": "pdfplumber",
                    },
                )
            )
    return units


def _extract_pdf_with_doctr(file_bytes: bytes, dpi: int) -> list[TextUnit]:
    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    images: list[tuple[bytes, str]] = []

    document = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        for page in document:
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            images.append((_pixmap_to_png_bytes(pix), ".png"))
    finally:
        document.close()

    return _extract_images_with_doctr(images, source_modality="pdf")


def _extract_images_with_doctr(
    images: list[tuple[bytes, str]],
    *,
    source_modality: str,
) -> list[TextUnit]:
    if not images:
        return []

    from doctr.io import DocumentFile

    predictor = _get_doctr_predictor()
    with tempfile.TemporaryDirectory(prefix="rag_doctr_") as tmpdir:
        image_paths: list[str] = []
        for index, (image_bytes, suffix) in enumerate(images, start=1):
            image_path = Path(tmpdir) / f"page_{index:04d}{suffix}"
            image_path.write_bytes(image_bytes)
            image_paths.append(str(image_path))

        document = DocumentFile.from_images(image_paths)
        result = predictor(document)

    units: list[TextUnit] = []
    for page_number, page in enumerate(result.pages, start=1):
        lines: list[str] = []
        for block in page.blocks:
            for line in block.lines:
                words = [word.value.strip() for word in line.words if word.value.strip()]
                if words:
                    lines.append(" ".join(words))
        page_text = "\n".join(lines).strip()
        if not page_text:
            continue
        units.append(
            TextUnit(
                text=page_text,
                metadata={
                    "source_modality": source_modality,
                    "page_number": page_number,
                    "ocr_used": True,
                    "extraction_source": "doctr_ocr",
                },
            )
        )
    return units


def _get_doctr_predictor() -> Any:
    global _DOCTR_PREDICTOR

    if _DOCTR_PREDICTOR is None:
        import torch
        from doctr.models import ocr_predictor

        predictor = ocr_predictor(pretrained=True, assume_straight_pages=True)
        if torch.cuda.is_available():
            predictor = predictor.cuda()
        _DOCTR_PREDICTOR = predictor

    return _DOCTR_PREDICTOR


def _pixmap_to_png_bytes(pixmap: fitz.Pixmap) -> bytes:
    mode = "RGB" if pixmap.n >= 3 else "L"
    from PIL import Image

    image = Image.frombytes(mode, (pixmap.width, pixmap.height), pixmap.samples)
    if image.mode != "RGB":
        image = image.convert("RGB")

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()
