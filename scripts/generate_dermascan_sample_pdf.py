"""
Génère le PDF fictif DermaScan pour l'atelier RAG.

Usage:
    python scripts/generate_dermascan_sample_pdf.py

Sortie:
    data/samples/DermaScan_fiche_projet_demo.pdf
"""

from __future__ import annotations

import re
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
SOURCE_MD = ROOT / "data" / "samples" / "_sources" / "dermascan_demo_content.md"
OUTPUT_PDF = ROOT / "data" / "samples" / "DermaScan_fiche_projet_demo.pdf"

PAGE_WIDTH = 595.28  # A4
PAGE_HEIGHT = 841.89
MARGIN_LEFT = 56
MARGIN_RIGHT = 56
MARGIN_TOP = 56
MARGIN_BOTTOM = 56
CONTENT_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT

FONT_TITLE = "helv"
FONT_BODY = "helv"
FONT_MONO = "cour"

TITLE_SIZE = 16
H2_SIZE = 13
H3_SIZE = 11
BODY_SIZE = 10
SMALL_SIZE = 9


class PdfWriter:
    def __init__(self) -> None:
        self.doc = fitz.open()
        self.page: fitz.Page | None = None
        self.y = MARGIN_TOP

    def _new_page(self) -> None:
        self.page = self.doc.new_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        self.y = MARGIN_TOP

    def _ensure_space(self, needed: float) -> None:
        if self.page is None or self.y + needed > PAGE_HEIGHT - MARGIN_BOTTOM:
            self._new_page()

    def add_title_page(self, title: str, subtitle: str, disclaimer: str) -> None:
        self._new_page()
        assert self.page is not None
        self.page.insert_text(
            (MARGIN_LEFT, 120),
            title,
            fontsize=22,
            fontname=FONT_TITLE,
            color=(0.1, 0.2, 0.45),
        )
        self.page.insert_text(
            (MARGIN_LEFT, 155),
            subtitle,
            fontsize=12,
            fontname=FONT_BODY,
            color=(0.3, 0.3, 0.3),
        )
        rect = fitz.Rect(MARGIN_LEFT, 200, PAGE_WIDTH - MARGIN_RIGHT, 320)
        self.page.insert_textbox(
            rect,
            disclaimer,
            fontsize=BODY_SIZE,
            fontname=FONT_BODY,
            color=(0.5, 0.1, 0.1),
            align=fitz.TEXT_ALIGN_LEFT,
        )
        self.y = 360

    def add_heading(self, text: str, level: int = 2) -> None:
        size = TITLE_SIZE if level == 1 else H2_SIZE if level == 2 else H3_SIZE
        self._ensure_space(size + 14)
        assert self.page is not None
        self.y += 8 if self.y > MARGIN_TOP else 0
        self.page.insert_text(
            (MARGIN_LEFT, self.y),
            text,
            fontsize=size,
            fontname=FONT_TITLE,
            color=(0.1, 0.2, 0.45) if level <= 2 else (0.15, 0.15, 0.15),
        )
        self.y += size + 6

    def _content_rect(self) -> fitz.Rect:
        return fitz.Rect(
            MARGIN_LEFT,
            self.y,
            PAGE_WIDTH - MARGIN_RIGHT,
            PAGE_HEIGHT - MARGIN_BOTTOM,
        )

    def add_paragraph(self, text: str) -> None:
        if not text.strip():
            return
        height = self._insert_wrapped(text, BODY_SIZE)
        self.y += height + 6

    def add_bullet(self, text: str) -> None:
        height = self._insert_wrapped("• " + text, BODY_SIZE, indent=12)
        self.y += height + 4

    def add_table_row(self, cells: list[str], *, header: bool = False) -> None:
        col_width = CONTENT_WIDTH / len(cells)
        row_height = BODY_SIZE + 8
        self._ensure_space(row_height + 4)
        assert self.page is not None
        for index, cell in enumerate(cells):
            x = MARGIN_LEFT + index * col_width
            rect = fitz.Rect(x, self.y - 2, x + col_width - 4, self.y + row_height)
            self.page.insert_textbox(
                rect,
                cell.strip(),
                fontsize=SMALL_SIZE if not header else BODY_SIZE,
                fontname=FONT_TITLE if header else FONT_BODY,
                color=(0.1, 0.1, 0.1),
                align=fitz.TEXT_ALIGN_LEFT,
            )
        self.y += row_height + 2

    def add_hr(self) -> None:
        self._ensure_space(12)
        assert self.page is not None
        self.page.draw_line(
            fitz.Point(MARGIN_LEFT, self.y),
            fitz.Point(PAGE_WIDTH - MARGIN_RIGHT, self.y),
            color=(0.75, 0.75, 0.75),
            width=0.5,
        )
        self.y += 12

    def _insert_wrapped(self, text: str, fontsize: float, *, indent: float = 0) -> float:
        remaining = text
        total_height = 0.0
        while remaining.strip():
            self._ensure_space(fontsize + 8)
            assert self.page is not None
            rect = fitz.Rect(
                MARGIN_LEFT + indent,
                self.y,
                PAGE_WIDTH - MARGIN_RIGHT,
                PAGE_HEIGHT - MARGIN_BOTTOM,
            )
            if rect.height <= fontsize:
                self._new_page()
                continue
            result = self.page.insert_textbox(
                rect,
                remaining,
                fontsize=fontsize,
                fontname=FONT_BODY,
                color=(0.15, 0.15, 0.15),
                align=fitz.TEXT_ALIGN_LEFT,
            )
            if result >= 0:
                used = rect.y1 - self.y
                total_height += max(used, fontsize + 2)
                self.y += max(used, fontsize + 2)
                break
            consumed = len(remaining) + result
            if consumed <= 0:
                self._new_page()
                continue
            chunk = remaining[:consumed].rstrip()
            remaining = remaining[consumed:].lstrip()
            used = rect.y1 - self.y
            total_height += max(used, fontsize + 2)
            self.y += max(used, fontsize + 2)
            if remaining:
                self._new_page()
        return max(total_height, fontsize + 2)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(path)
        self.doc.close()


def parse_markdown(content: str) -> list[tuple[str, str | list[str]]]:
    """Parse minimal markdown into (type, payload) blocks."""
    blocks: list[tuple[str, str | list[str]]] = []
    lines = content.splitlines()
    index = 0

    while index < len(lines):
        line = lines[index].rstrip()

        if not line or line.strip() == "---":
            index += 1
            continue

        if line.startswith("# "):
            blocks.append(("h1", line[2:].strip()))
            index += 1
            continue

        if line.startswith("## "):
            blocks.append(("h2", line[3:].strip()))
            index += 1
            continue

        if line.startswith("### "):
            blocks.append(("h3", line[4:].strip()))
            index += 1
            continue

        if line.startswith("|") and index + 1 < len(lines) and lines[index + 1].startswith("|"):
            table_rows: list[str] = []
            while index < len(lines) and lines[index].startswith("|"):
                row_line = lines[index].strip()
                if re.match(r"^\|[-:\s|]+\|$", row_line):
                    index += 1
                    continue
                cells = [cell.strip() for cell in row_line.strip("|").split("|")]
                table_rows.append(cells)
                index += 1
            blocks.append(("table", table_rows))
            continue

        if line.startswith("- "):
            blocks.append(("bullet", line[2:].strip()))
            index += 1
            continue

        if line.startswith("**") and line.endswith("**"):
            blocks.append(("bold_line", line.strip("*")))
            index += 1
            continue

        paragraph_lines = [line]
        index += 1
        while index < len(lines):
            next_line = lines[index].rstrip()
            if (
                not next_line
                or next_line.startswith("#")
                or next_line.startswith("|")
                or next_line.startswith("- ")
                or next_line == "---"
            ):
                break
            paragraph_lines.append(next_line)
            index += 1
        blocks.append(("paragraph", " ".join(paragraph_lines)))

    return blocks


def build_pdf(source_path: Path, output_path: Path) -> None:
    content = source_path.read_text(encoding="utf-8")
    blocks = parse_markdown(content)
    writer = PdfWriter()

    disclaimer = (
        "DOCUMENT FICTIF — DÉMONSTRATION RAG\n\n"
        "Toutes les entités, chiffres et personnes décrits dans ce document sont simulés "
        "à des fins pédagogiques. Aucune donnée réelle de patient, contrat CIFRE ou "
        "information confidentielle n'est incluse."
    )
    writer.add_title_page(
        title="DermaScan",
        subtitle="Fiche projet — Atelier RAG multi-source (v1.0, janvier 2025)",
        disclaimer=disclaimer,
    )

    skip_first_h1 = True
    for block_type, payload in blocks:
        if block_type == "h1":
            if skip_first_h1:
                skip_first_h1 = False
                continue
            assert isinstance(payload, str)
            writer.add_heading(payload, level=1)
        elif block_type == "h2":
            assert isinstance(payload, str)
            writer.add_heading(payload, level=2)
        elif block_type == "h3":
            assert isinstance(payload, str)
            writer.add_heading(payload, level=3)
        elif block_type in {"paragraph", "bold_line"}:
            assert isinstance(payload, str)
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", payload)
            writer.add_paragraph(text)
        elif block_type == "bullet":
            assert isinstance(payload, str)
            writer.add_bullet(payload)
        elif block_type == "table":
            assert isinstance(payload, list)
            for row_index, row in enumerate(payload):
                if isinstance(row, list):
                    writer.add_table_row(row, header=row_index == 0)

    writer.save(output_path)
    print(f"PDF généré : {output_path} ({output_path.stat().st_size // 1024} Ko)")


def main() -> None:
    if not SOURCE_MD.exists():
        raise FileNotFoundError(f"Source introuvable : {SOURCE_MD}")
    build_pdf(SOURCE_MD, OUTPUT_PDF)


if __name__ == "__main__":
    main()
