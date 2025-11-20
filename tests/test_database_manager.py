"""Pytest coverage for the lightweight data layer connectors and schema export."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.db.database_manager import DatabaseManager
from backend.db.schema_extractor import get_sqlite_schema

DATA_DIR = Path("backend/data")


@pytest.fixture()
def fresh_manager() -> DatabaseManager:
    """Ensure each test works with a clean in-memory SQLite database."""
    manager = DatabaseManager()
    manager.init_sqlite()
    yield manager
    conn = manager.get_sqlite_connection()
    if conn:
        conn.close()


def _table_schema(schema_payload, table_name):
    """Return the schema dictionary for a specific table name."""
    for table in schema_payload["tables"]:
        if table["name"] == table_name:
            return table
    raise AssertionError(f"Table {table_name} not found in schema payload: {schema_payload}")


def test_load_csv_creates_sqlite_table_and_schema(fresh_manager: DatabaseManager):
    sample_csv = DATA_DIR / "sample.csv"
    fresh_manager.load_csv_as_table(str(sample_csv), "customers_csv")

    conn = fresh_manager.get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM customers_csv;")
    row_count = cursor.fetchone()[0]

    assert row_count == 4

    schema = get_sqlite_schema(conn, persist=False)
    table_schema = _table_schema(schema, "customers_csv")
    column_names = [c["name"] for c in table_schema["columns"]]
    assert column_names == ["id", "name", "category", "amount", "created_at"]


def test_load_excel_creates_sqlite_table(fresh_manager: DatabaseManager):
    sample_excel = DATA_DIR / "sample.xlsx"
    fresh_manager.load_excel_as_table(str(sample_excel), "customers_xlsx")

    conn = fresh_manager.get_sqlite_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='customers_xlsx';")
    assert cursor.fetchone()[0] == "customers_xlsx"


def test_schema_persistence_writes_json_snapshot(tmp_path, fresh_manager: DatabaseManager):
    sample_csv = DATA_DIR / "sample.csv"
    fresh_manager.load_csv_as_table(str(sample_csv), "snapshot_demo")

    conn = fresh_manager.get_sqlite_connection()
    schema_path = tmp_path / "schema_snapshot.json"

    schema_payload = get_sqlite_schema(conn, output_path=schema_path)

    assert schema_path.exists()
    with schema_path.open("r", encoding="utf-8") as fp:
        saved_payload = json.load(fp)

    assert saved_payload["source"] == "sqlite"
    assert saved_payload["tables"]
    assert schema_payload == saved_payload

