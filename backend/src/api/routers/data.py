from fastapi import APIRouter, HTTPException
import os
import sqlite3
import pandas as pd

router = APIRouter(
    prefix="/data",
    tags=["Data"],
    responses={404: {"description": "Not found"}},
)


def get_db_dir():
    """Returns the absolute path to the databases directory."""
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    return os.path.join(base_dir, 'databases')


@router.get("/preview")
def get_data_preview(db_path: str, limit: int = 10):
    """
    Returns the first N rows of the first table in the database.
    """
    try:
        # Validate path
        db_dir = get_db_dir()
        full_path = os.path.abspath(db_path)
        if not full_path.startswith(db_dir):
            raise HTTPException(status_code=403, detail="Access forbidden")

        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Database not found")

        # Use check_same_thread=False to avoid issues with FastAPI threads
        conn = sqlite3.connect(full_path, check_same_thread=False)

        # Get the first table name
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;")
        table = cursor.fetchone()
        if not table:
            conn.close()
            return {"columns": [], "rows": [], "table_name": None}

        table_name = table[0]

        # Get data as DataFrame
        df = pd.read_sql_query(f"SELECT * FROM [{table_name}] LIMIT {limit}", conn)
        conn.close()

        return {
            "table_name": table_name,
            "columns": df.columns.tolist(),
            "rows": df.values.tolist(),
            "total_rows_shown": len(df)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
def get_data_summary(db_path: str):
    """
    Returns summary statistics for the first table in the database.
    """
    try:
        db_dir = get_db_dir()
        full_path = os.path.abspath(db_path)
        if not full_path.startswith(db_dir):
            raise HTTPException(status_code=403, detail="Access forbidden")

        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Database not found")

        conn = sqlite3.connect(full_path)

        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1;")
        table = cursor.fetchone()
        if not table:
            conn.close()
            return {"table_name": None, "row_count": 0, "columns": []}

        table_name = table[0]

        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM [{table_name}]")
        row_count = cursor.fetchone()[0]

        # Get column info
        cursor.execute(f"PRAGMA table_info([{table_name}])")
        columns_info = cursor.fetchall()

        columns = [{"name": col[1], "type": col[2]} for col in columns_info]

        conn.close()

        return {
            "table_name": table_name,
            "row_count": row_count,
            "column_count": len(columns),
            "columns": columns
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
