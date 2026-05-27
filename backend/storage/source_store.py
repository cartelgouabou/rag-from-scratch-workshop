from __future__ import annotations

import shutil
from pathlib import Path


class SourceStore:
    def __init__(self, root_dir: Path) -> None:
        self.root_dir = root_dir
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def save(self, document_id: str, filename: str, content: bytes) -> str:
        target = self._target_path(document_id, filename)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return str(target.relative_to(self.root_dir))

    def read_bytes(self, relative_path: str) -> bytes:
        return self.resolve(relative_path).read_bytes()

    def exists(self, relative_path: str | None) -> bool:
        if not relative_path:
            return False
        return self.resolve(relative_path).exists()

    def delete(self, relative_path: str | None) -> None:
        if not relative_path:
            return
        target = self.resolve(relative_path)
        if not target.exists():
            return
        target.unlink()
        parent = target.parent
        while parent != self.root_dir and parent.exists():
            if any(parent.iterdir()):
                break
            parent.rmdir()
            parent = parent.parent

    def resolve(self, relative_path: str) -> Path:
        return (self.root_dir / relative_path).resolve()

    def purge_all(self) -> None:
        if self.root_dir.exists():
            shutil.rmtree(self.root_dir)
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def replace_document_dir(self, document_id: str) -> None:
        target_dir = self.root_dir / document_id
        if target_dir.exists():
            shutil.rmtree(target_dir)

    def _target_path(self, document_id: str, filename: str) -> Path:
        safe_name = Path(filename).name
        return self.root_dir / document_id / safe_name
