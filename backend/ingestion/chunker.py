from __future__ import annotations

import re
from dataclasses import dataclass

from langchain_text_splitters import RecursiveCharacterTextSplitter

_MARKDOWN_HEADING = re.compile(r"^#{1,6}\s+(.+)$")
_NUMBERED_HEADING = re.compile(r"^(\d+(?:\.\d+)*[\.\)]?)\s+(.+)$")


@dataclass
class ChunkPart:
    text: str
    section_title: str | None = None


class TextChunker:
    def __init__(self, chunk_size: int, chunk_overlap: int) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ""],
        )

    def split_text(self, text: str) -> list[str]:
        if not text.strip():
            return []
        return [chunk.strip() for chunk in self._splitter.split_text(text) if chunk.strip()]

    def split_unit(self, text: str, *, use_sections: bool = True) -> list[ChunkPart]:
        if use_sections:
            section_chunks = self._split_by_sections(text)
            if section_chunks:
                return section_chunks
        return [ChunkPart(text=chunk) for chunk in self.split_text(text)]

    def _split_by_sections(self, text: str) -> list[ChunkPart]:
        sections = self._extract_sections(text)
        if len(sections) < 2:
            return []

        chunks: list[ChunkPart] = []
        for title, body in sections:
            if not body.strip():
                continue
            for chunk in self.split_text(body):
                chunks.append(ChunkPart(text=f"{title}\n{chunk}".strip(), section_title=title))
        return chunks

    def _extract_sections(self, text: str) -> list[tuple[str, str]]:
        lines = text.splitlines()
        sections: list[tuple[str, str]] = []
        current_title: str | None = None
        buffer: list[str] = []

        for index, raw_line in enumerate(lines):
            line = raw_line.strip()
            if not line:
                if buffer:
                    buffer.append("")
                continue

            heading = self._parse_heading(line, lines=lines, index=index)
            if heading is not None:
                if buffer:
                    sections.append((current_title or "Introduction", "\n".join(buffer).strip()))
                current_title = heading
                buffer = []
                continue
            buffer.append(line)

        if buffer:
            sections.append((current_title or "Introduction", "\n".join(buffer).strip()))
        return [(title, body) for title, body in sections if body]

    def _parse_heading(self, line: str, *, lines: list[str], index: int) -> str | None:
        markdown_match = _MARKDOWN_HEADING.match(line)
        if markdown_match:
            return markdown_match.group(1).strip()

        numbered_match = _NUMBERED_HEADING.match(line)
        if numbered_match:
            return f"{numbered_match.group(1)} {numbered_match.group(2)}".strip()

        if self._is_uppercase_heading(line, lines=lines, index=index):
            return line
        return None

    def _is_uppercase_heading(self, line: str, *, lines: list[str], index: int) -> bool:
        if len(line) > 80 or line.endswith((".", "?", "!")):
            return False

        letters = [character for character in line if character.isalpha()]
        if len(letters) < 3:
            return False

        uppercase_ratio = sum(character.isupper() for character in letters) / len(letters)
        if uppercase_ratio < 0.75:
            return False

        previous_blank = index == 0 or not lines[index - 1].strip()
        next_blank = index + 1 >= len(lines) or not lines[index + 1].strip()
        return previous_blank or next_blank
