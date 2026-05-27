from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from sqlalchemy import DateTime, Integer, String, create_engine, delete, func, inspect, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class DocumentRecord(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    file_type: Mapped[str] = mapped_column(String, nullable=False)
    nb_chunks: Mapped[int] = mapped_column(Integer, default=0)
    nb_records: Mapped[int] = mapped_column(Integer, default=0)
    indexed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sql_table_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_path: Mapped[Optional[str]] = mapped_column(String, nullable=True)


class SQLStore:
    def __init__(self, sqlite_file: Path) -> None:
        self.sqlite_file = sqlite_file
        self.engine = create_engine(f"sqlite:///{sqlite_file}", future=True)
        self.session_factory = sessionmaker(self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)
        self._ensure_document_columns()

    def upsert_document(
        self,
        document_id: str,
        filename: str,
        file_type: str,
        nb_chunks: int,
        nb_records: int,
        sql_table_name: str | None = None,
        source_path: str | None = None,
    ) -> None:
        with self.session_factory() as session:
            existing = session.get(DocumentRecord, document_id)
            if existing is None:
                existing = DocumentRecord(
                    id=document_id,
                    filename=filename,
                    file_type=file_type,
                    nb_chunks=nb_chunks,
                    nb_records=nb_records,
                    indexed_at=datetime.now(timezone.utc),
                    sql_table_name=sql_table_name,
                    source_path=source_path,
                )
                session.add(existing)
            else:
                existing.filename = filename
                existing.file_type = file_type
                existing.nb_chunks = nb_chunks
                existing.nb_records = nb_records
                existing.indexed_at = datetime.now(timezone.utc)
                existing.sql_table_name = sql_table_name
                existing.source_path = source_path
            session.commit()

    def create_tabular_table(self, document_id: str, dataframe: pd.DataFrame) -> str:
        table_name = f"doc_{document_id.replace('-', '_')}"
        prepared = self._prepare_dataframe(dataframe)
        prepared.to_sql(table_name, self.engine, if_exists="replace", index=False)
        return table_name

    def list_documents(self) -> list[dict[str, Any]]:
        with self.session_factory() as session:
            rows = session.scalars(select(DocumentRecord).order_by(DocumentRecord.indexed_at.desc())).all()
        return [
            {
                "id": row.id,
                "filename": row.filename,
                "type": row.file_type,
                "nb_chunks": row.nb_chunks,
                "nb_records": row.nb_records,
                "indexed_at": row.indexed_at,
                "sql_table_name": row.sql_table_name,
                "source_path": row.source_path,
            }
            for row in rows
        ]

    def get_document(self, document_id: str) -> dict[str, Any] | None:
        with self.session_factory() as session:
            row = session.get(DocumentRecord, document_id)
            if row is None:
                return None
            return {
                "id": row.id,
                "filename": row.filename,
                "type": row.file_type,
                "nb_chunks": row.nb_chunks,
                "nb_records": row.nb_records,
                "indexed_at": row.indexed_at,
                "sql_table_name": row.sql_table_name,
                "source_path": row.source_path,
            }

    def delete_document(self, document_id: str) -> dict[str, Any] | None:
        with self.session_factory() as session:
            row = session.get(DocumentRecord, document_id)
            if row is None:
                return None
            payload = {
                "id": row.id,
                "filename": row.filename,
                "type": row.file_type,
                "nb_chunks": row.nb_chunks,
                "nb_records": row.nb_records,
                "indexed_at": row.indexed_at,
                "sql_table_name": row.sql_table_name,
                "source_path": row.source_path,
            }
            if row.sql_table_name:
                self._drop_table(row.sql_table_name)
            session.delete(row)
            session.commit()
            return payload

    def get_stats(self) -> dict[str, int]:
        with self.session_factory() as session:
            total_documents = session.scalar(select(func.count()).select_from(DocumentRecord)) or 0
            total_chunks = session.scalar(select(func.coalesce(func.sum(DocumentRecord.nb_chunks), 0))) or 0
            total_records = session.scalar(select(func.coalesce(func.sum(DocumentRecord.nb_records), 0))) or 0
        return {
            "total_documents": int(total_documents),
            "total_chunks": int(total_chunks),
            "total_records": int(total_records),
        }

    def build_schema_context(self, preview_rows: int = 3) -> str:
        documents = [doc for doc in self.list_documents() if doc["sql_table_name"]]
        if not documents:
            return "No SQL tables are currently available."

        inspector = inspect(self.engine)
        sections: list[str] = []
        with self.engine.connect() as connection:
            for document in documents:
                table_name = document["sql_table_name"]
                columns = inspector.get_columns(table_name)
                column_lines = [f"- {column['name']} ({column['type']})" for column in columns]
                preview = connection.execute(
                    text(f'SELECT * FROM "{table_name}" LIMIT {preview_rows}')
                ).mappings().all()
                sections.append(
                    "\n".join(
                        [
                            f"Document: {document['filename']}",
                            f"Table: {table_name}",
                            "Columns:",
                            *column_lines,
                            f"Preview: {preview}",
                        ]
                    )
                )
        return "\n\n".join(sections)

    def execute_query(self, query: str) -> list[dict[str, Any]]:
        normalized = query.strip().rstrip(";")
        lowered = f" {normalized.lower()} "
        forbidden = [" insert ", " update ", " delete ", " drop ", " alter ", " pragma ", " attach ", " create "]
        if not (normalized.lower().startswith("select") or normalized.lower().startswith("with")):
            raise ValueError("Only SELECT queries are allowed.")
        if any(keyword in lowered for keyword in forbidden) or ";" in normalized:
            raise ValueError("Unsafe SQL query rejected.")

        with self.engine.connect() as connection:
            rows = connection.execute(text(normalized)).mappings().all()
        return [dict(row) for row in rows]

    def purge_all(self) -> int:
        documents = self.list_documents()
        for document in documents:
            self.drop_table_if_exists(document.get("sql_table_name"))
        with self.session_factory() as session:
            result = session.execute(delete(DocumentRecord))
            session.commit()
        return int(result.rowcount or 0)

    def drop_table_if_exists(self, table_name: str | None) -> None:
        if table_name:
            self._drop_table(table_name)

    def _drop_table(self, table_name: str) -> None:
        safe_table_name = re.sub(r"[^a-zA-Z0-9_]", "", table_name)
        with self.engine.connect() as connection:
            connection.execute(text(f'DROP TABLE IF EXISTS "{safe_table_name}"'))
            connection.commit()

    def _prepare_dataframe(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        prepared = dataframe.copy()
        prepared.columns = self._normalize_columns(prepared.columns.tolist())
        for column in prepared.columns:
            if pd.api.types.is_datetime64_any_dtype(prepared[column]):
                prepared[column] = prepared[column].dt.strftime("%Y-%m-%d")
            elif prepared[column].dtype == object:
                prepared[column] = prepared[column].fillna("").astype(str).str.strip()
        return prepared

    def _normalize_columns(self, columns: list[str]) -> list[str]:
        seen: dict[str, int] = {}
        normalized: list[str] = []
        for raw_name in columns:
            base = re.sub(r"[^a-zA-Z0-9_]+", "_", str(raw_name).strip().lower()).strip("_") or "column"
            count = seen.get(base, 0)
            seen[base] = count + 1
            normalized.append(base if count == 0 else f"{base}_{count + 1}")
        return normalized

    def _ensure_document_columns(self) -> None:
        inspector = inspect(self.engine)
        columns = {column["name"] for column in inspector.get_columns("documents")}
        if "source_path" not in columns:
            with self.engine.connect() as connection:
                connection.execute(text('ALTER TABLE documents ADD COLUMN source_path VARCHAR'))
                connection.commit()
