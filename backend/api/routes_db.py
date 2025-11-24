"""FastAPI routes handling DB connectivity, ingestion, schema inspection, and queries."""
# backend/api/routes_db.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List

from ..db.database_manager import DatabaseManager
from ..db.schema_extractor import get_mysql_schema, get_sqlite_schema

router = APIRouter()
db_manager = DatabaseManager()


class MySQLConfig(BaseModel):
    # Minimal MySQL connection info expected from the client payload
    host: str
    user: str
    password: str
    database: str


class SQLQuery(BaseModel):
    # Simple container for a raw SQL statement sent by the client
    query: str


@router.post("/connect-mysql")
def connect_mysql(config: MySQLConfig):
    """Connect to a MySQL instance and switch the manager into MySQL mode."""
    # Establish a MySQL engine and remember we are in MySQL mode
    try:
        db_manager.connect_mysql(
            host=config.host,
            user=config.user,
            password=config.password,
            database=config.database
        )
        return {"status": "connected", "mode": "mysql"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load-csv")
def load_csv(path: str, table_name: str):
    """Load a CSV file into the in-memory SQLite backend as a table."""
    # Ingest a CSV file into the current SQLite in-memory database
    try:
        db_manager.load_csv_as_table(path, table_name)
        return {"status": "loaded", "table": table_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/load-excel")
def load_excel(path: str, table_name: str):
    """Load an Excel sheet into the in-memory SQLite backend as a table."""
    # Ingest an Excel sheet into the current SQLite in-memory database
    try:
        db_manager.load_excel_as_table(path, table_name)
        return {"status": "loaded", "table": table_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schema")
def get_schema() -> Dict[str, Any]:
    """Return the table/column schema for whichever backend is active."""
    # Return a schema summary depending on which backend is active
    mysql_engine = db_manager.get_mysql_engine()
    sqlite_conn = db_manager.get_sqlite_connection()

    if db_manager.current_mode == "mysql" and mysql_engine:
        return get_mysql_schema(mysql_engine)

    elif db_manager.current_mode == "sqlite" and sqlite_conn:
        return get_sqlite_schema(sqlite_conn)

    else:
        raise HTTPException(status_code=400, detail="No active database connection")


@router.post("/execute-sql")
def execute_sql(query: SQLQuery) -> List[Dict[str, Any]]:
    """Execute an arbitrary SQL statement on the active backend."""
    try:
        return db_manager.execute_sql(query.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
