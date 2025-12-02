import sqlite3
import os

def get_db_schema(db_path: str) -> str:
    """
    Inspects an SQLite database and returns a string representation of its schema.
    """
    if not db_path or not os.path.exists(db_path):
        return f"Error: Database file not found at {db_path}"

    try:
        # Connect in read-only mode for safety
        db_uri = f"file:{db_path}?mode=ro"
        with sqlite3.connect(db_uri, uri=True) as conn:
            cursor = conn.cursor()
            
            # Get list of tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [table[0] for table in cursor.fetchall()]
            
            schema_str = ""
            for table_name in tables:
                # Get schema for each table
                cursor.execute(f"PRAGMA table_info('{table_name}');")
                columns = cursor.fetchall()
                
                schema_str += f"Table '{table_name}':\n"
                for col in columns:
                    col_name = col[1]
                    col_type = col[2]
                    is_pk = " (PRIMARY KEY)" if col[5] else ""
                    schema_str += f"  - {col_name}: {col_type}{is_pk}\n"
                schema_str += "\n"
                
            return schema_str if schema_str else "Database is empty (no tables found)."

    except sqlite3.OperationalError as e:
        return f"Error inspecting schema: {str(e)}"
    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"
