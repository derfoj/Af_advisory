
import sqlite3
import os

def execute_query_and_format(sql: str, db_path: str) -> dict:
    """
    Executes a SQL query on a given database and returns the result in a 
    JSON-serializable format. It enforces security best practices.
    """
    # MOCK BEHAVIOR FOR TESTING
    if os.environ.get("USE_MOCK_DB") == "True":
        if "SELECT" in sql.upper():
            return {
                "columns": ["id", "name", "email"],
                "data": [
                    {"id": 1, "name": "Alice", "email": "alice@example.com"},
                    {"id": 2, "name": "Bob", "email": "bob@example.com"}
                ]
            }
        return {"message": "Mock query executed."}

    if not db_path or not os.path.exists(db_path):
        return {"error": f"Database file not found at {db_path}"}

    try:
        db_uri = f"file:{db_path}?mode=ro"
        with sqlite3.connect(db_uri, uri=True, timeout=5) as conn:
            cursor = conn.cursor()
            
            # This is a hack to handle empty queries from the LLM
            if not sql.strip():
                return {"columns": [], "data": []}

            cursor.execute(sql)
            
            if cursor.description:
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                
                data = []
                for row in rows:
                    data.append(dict(zip(columns, row)))
                    
                return {"columns": columns, "data": data}
            else:
                return {"message": "Query executed successfully (no data returned)."}
                
    except sqlite3.OperationalError as e:
        if "attempt to write a readonly database" in str(e):
             return {"error": "Security Violation: Database is in Read-Only mode. Write operations are forbidden."}
        return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}
