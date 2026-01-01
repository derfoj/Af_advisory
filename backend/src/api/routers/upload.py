from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import shutil
import uuid
from typing import Dict

# Import relative to the package structure. 
# We assume this is in backend/src/api/routers/upload.py
# python path should include backend/src
from utils.file_converter import convert_to_sqlite

router = APIRouter(
    prefix="/upload",
    tags=["File Upload"],
    responses={404: {"description": "Not found"}},
)

@router.post("/")
async def upload_file(file: UploadFile = File(...)):
    """
    Uploads a CSV or Excel file and converts it to a SQLite database.
    """
    try:
        # Create a temporary file to save the upload
        # Going up from api/routers to src to backend
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        temp_dir = os.path.join(base_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_file_path = os.path.join(temp_dir, f"{uuid.uuid4()}_{file.filename}")
        
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Define output directory for databases
        db_dir = os.path.join(base_dir, 'databases')
        os.makedirs(db_dir, exist_ok=True)
        
        # Convert to SQLite
        db_path = convert_to_sqlite(temp_file_path, db_dir)
        
        # Cleanup temp file
        os.remove(temp_file_path)
        
        return {"db_path": db_path, "filename": file.filename, "message": "File converted successfully."}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
