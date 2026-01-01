from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any

from api.schemas import QueryRequest
from utils.validators import validate_db_path
from text_to_sql.workflow_engine import WorkflowEngine

router = APIRouter(
    prefix="/query",
    tags=["Query"],
    responses={404: {"description": "Not found"}},
)

# Instantiate WorkflowEngine. 
# In a larger app, this might be a dependency injection.
workflow_engine = WorkflowEngine()

@router.post("/")
def run_query(request: QueryRequest = Body(...)):
    """
    Takes a natural language question and returns a SQL query or the result of the query.
    """
    try:
        # Validate the provided database path
        validate_db_path(request.db_path)

        # Convert Pydantic messages to LangChain messages
        chat_history_langchain = [msg.to_langchain() for msg in request.chat_history]

        result = workflow_engine.run(
            question=request.question,
            db_path=request.db_path,
            chat_history=chat_history_langchain,
        )
        
        if result.get("error"):
            if "Security Violation" in result["error"]:
                 raise HTTPException(status_code=403, detail=result["error"])
            # For other errors, return 400 Bad Request
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Internal Server Error: {e}") 
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")
