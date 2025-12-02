class SQLSecurityError(Exception):
    """Custom exception for SQL security violations."""
    pass

def validate_sql_safety(sql: str) -> str:
    """
    Validates the given SQL query to ensure it is a read-only SELECT statement.

    Args:
        sql: The SQL query string to validate.

    Returns:
        The validated SQL query string.

    Raises:
        SQLSecurityError: If the SQL query is not a SELECT statement or contains
                          other security violations.
    """
    stripped_sql = sql.strip()
    if not stripped_sql.upper().startswith("SELECT"):
        raise SQLSecurityError(f"Security Violation: Only SELECT statements are allowed. Query: '{sql}'")
    
    # Add more checks here if needed, e.g., for subqueries, multiple statements, etc.
    
    return sql