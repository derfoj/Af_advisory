"""Lightweight database layer that flips between MySQL (SQLAlchemy) and SQLite."""

from typing import List, Dict, Any, Optional
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


class DatabaseManager:
    def __init__(self):
        """Initialize empty handles for MySQL engine and SQLite connection."""
        self.mysql_engine: Optional[Engine] = None
        self.sqlite_conn: Optional[sqlite3.Connection] = None
        self.current_mode: Optional[str] = None

    def connect_mysql(self, host: str, user: str, password: str, database: str):
        """Create a MySQL SQLAlchemy engine, test connectivity, and set active mode."""
        # Build a SQLAlchemy engine and switch mode to MySQL
        url = f"mysql+pymysql://{user}:{password}@{host}/{database}"
        engine = create_engine(url)
        # Lightweight connectivity check (SELECT 1)
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
        except SQLAlchemyError as exc:
            raise RuntimeError(f"Failed to connect to MySQL: {exc}")

        self.mysql_engine = engine
        self.current_mode = "mysql"

    def init_sqlite(self, db_path: str = ":memory:"):
        """Create or reuse a SQLite connection (default in-memory) and set mode."""
        # Create or reuse a lightweight SQLite database (default in-memory)
        self.sqlite_conn = sqlite3.connect(db_path)
        self.current_mode = "sqlite"

    def get_mysql_engine(self) -> Optional[Engine]:
        """Expose the current MySQL engine if available."""
        return self.mysql_engine

    def get_sqlite_connection(self) -> Optional[sqlite3.Connection]:
        """Expose the current SQLite connection if available."""
        return self.sqlite_conn

    def load_csv_as_table(self, csv_path: str, table_name: str):
        """Import a CSV file into SQLite as the given table name."""
        # Read a CSV into a new/replaced SQLite table
        if self.sqlite_conn is None:
            self.init_sqlite()
        df = pd.read_csv(csv_path)
        df.to_sql(table_name, self.sqlite_conn, index=False, if_exists="replace")
        self.current_mode = "sqlite"

    def load_excel_as_table(self, excel_path: str, table_name: str, sheet_name: int | str = 0):
        """Import an Excel sheet into SQLite as the given table name."""
        # Read an Excel sheet into a new/replaced SQLite table
        if self.sqlite_conn is None:
            self.init_sqlite()
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        df.to_sql(table_name, self.sqlite_conn, index=False, if_exists="replace")
        self.current_mode = "sqlite"

    def execute_sql(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL on the active backend and return rows as dicts."""
        # Run the provided SQL against the active backend and return rows as dicts
        if self.current_mode == "mysql" and self.mysql_engine is not None:
            with self.mysql_engine.connect() as conn:
                trans = conn.begin()
                result = conn.execute(text(sql))
                rows = [dict(row._mapping) for row in result] if result.returns_rows else []
                trans.commit()
                return rows

        elif self.current_mode == "sqlite" and self.sqlite_conn is not None:
            cursor = self.sqlite_conn.cursor()
            cursor.execute(sql)
            col_names = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            self.sqlite_conn.commit()
            return [dict(zip(col_names, row)) for row in rows]

        else:
            raise RuntimeError("No active database connection")
