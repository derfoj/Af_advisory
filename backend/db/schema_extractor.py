"""Helpers to introspect table/column schemas for MySQL (SQLAlchemy) and SQLite."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from sqlalchemy import inspect
from sqlalchemy.engine import Engine

SCHEMA_OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "schema_snapshot.json"


def _normalize_type(type_str: str) -> str:
    """Collapse varied backend type strings into a simple set for downstream use."""
    t = type_str.lower()
    if any(key in t for key in ["int", "serial", "tinyint", "smallint", "mediumint", "bigint"]):
        return "integer"
    if any(key in t for key in ["char", "text", "clob", "string", "varchar", "binary"]):
        return "string"
    if any(key in t for key in ["float", "double", "real", "decimal", "numeric"]):
        return "float"
    if any(key in t for key in ["bool", "bit"]):
        return "boolean"
    if any(key in t for key in ["date", "time", "timestamp"]):
        return "datetime"
    return "unknown"


def _build_schema_payload(source: str, tables_schema: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Standardize schema payload with metadata for downstream consumers."""
    return {
        "source": source,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "tables": tables_schema,
    }


def _persist_schema(schema: Dict[str, Any], output_path: Path | str | None = None) -> Path:
    """Write the schema payload to disk as JSON and return the location."""
    target_path = Path(output_path) if output_path else SCHEMA_OUTPUT_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with target_path.open("w", encoding="utf-8") as fp:
        json.dump(schema, fp, indent=2)
    return target_path


def persist_schema(schema: Dict[str, Any], output_path: Path | str | None = None) -> Path:
    """Public helper to persist schema payloads from API routes or workers."""
    return _persist_schema(schema, output_path)


def get_mysql_schema(
    engine: Engine,
    *,
    persist: bool = True,
    output_path: Path | str | None = None,
) -> Dict[str, Any]:
    """Return a standardized schema payload for a MySQL database."""
    inspector = inspect(engine)
    tables_schema: List[Dict[str, Any]] = []

    for table_name in inspector.get_table_names():
        columns_info = inspector.get_columns(table_name)
        columns = []
        for col in columns_info:
            raw_type = str(col["type"])
            columns.append({
                "name": col["name"],
                "type": raw_type,
                "normalized_type": _normalize_type(raw_type)
            })
        tables_schema.append({
            "name": table_name,
            "columns": columns
        })

    schema_payload = _build_schema_payload("mysql", tables_schema)
    if persist:
        _persist_schema(schema_payload, output_path)
    return schema_payload


def get_sqlite_schema(
    conn: sqlite3.Connection,
    *,
    persist: bool = True,
    output_path: Path | str | None = None,
) -> Dict[str, Any]:
    """Return a standardized schema payload for SQLite databases."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    tables_schema: List[Dict[str, Any]] = []

    for table_name in tables:
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns_info = cursor.fetchall()

        columns = []
        for col in columns_info:
            raw_type = col[2]
            columns.append({
                "name": col[1],
                "type": raw_type,
                "normalized_type": _normalize_type(raw_type)
            })

        tables_schema.append({
            "name": table_name,
            "columns": columns
        })

    schema_payload = _build_schema_payload("sqlite", tables_schema)
    if persist:
        _persist_schema(schema_payload, output_path)
    return schema_payload
