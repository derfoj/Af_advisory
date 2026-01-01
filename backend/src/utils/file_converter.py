import pandas as pd
import sqlite3
import os
import uuid

def convert_to_sqlite(file_path: str, output_dir: str) -> str:
    """
    Converts a CSV or Excel file to a SQLite database.
    
    Args:
        file_path (str): Path to the input file (csv, xls, xlsx).
        output_dir (str): Directory to save the resulting .db file.
        
    Returns:
        str: Absolute path to the generated SQLite database.
    """
    filename = os.path.basename(file_path)
    name, ext = os.path.splitext(filename)
    ext = ext.lower()
    
    # Generate a unique database name to avoid conflicts
    db_name = f"{name}_{uuid.uuid4().hex[:8]}.db"
    db_path = os.path.join(output_dir, db_name)
    
    # Create connection
    conn = sqlite3.connect(db_path)
    
    try:
        if ext == '.csv':
            df = pd.read_csv(file_path)
            # Sanitize table name (simple version)
            table_name = "".join([c if c.isalnum() else "_" for c in name])
            df.to_sql(table_name, conn, if_exists='replace', index=False)
            
        elif ext in ['.xls', '.xlsx']:
            xls = pd.ExcelFile(file_path)
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                # Sanitize sheet name for table name
                table_name = "".join([c if c.isalnum() else "_" for c in sheet_name])
                df.to_sql(table_name, conn, if_exists='replace', index=False)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
            
    except Exception as e:
        # Clean up if failed
        conn.close()
        if os.path.exists(db_path):
            os.remove(db_path)
        raise e
    finally:
        conn.close()
        
    return os.path.abspath(db_path)
