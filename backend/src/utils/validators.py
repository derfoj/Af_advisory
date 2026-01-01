import os
from fastapi import HTTPException


def validate_db_path(db_path: str):
    """
    Security validation for the database path to prevent directory traversal attacks.
    """
    # Get the absolute path of the 'databases' directory
    # Assuming this file is in backend/src/utils/validators.py
    # We need to go up from utils -> src -> backend -> databases
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    db_dir = os.path.join(base_dir, 'databases')

    # Get the absolute path of the user-provided path
    user_path = os.path.abspath(db_path)

    # Check if the user_path is within the db_dir
    # Also handle the case where db_path might be just a filename in the query
    if not user_path.startswith(db_dir):
        # Try resolving it relative to db_dir if it's just a filename
        base = os.path.basename(db_path)
        potential_path = os.path.abspath(os.path.join(db_dir, base))
        if potential_path.startswith(db_dir) and os.path.exists(potential_path):
            return  # Valid

        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: Access to '{db_path}' is not allowed."
        )
