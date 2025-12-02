import uvicorn
from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Adjust the python path to include the src directory
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from text_to_sql.workflow_engine import WorkflowEngine

# --- Pydantic Models ---
class Message(BaseModel):
    role: str
    content: str

    def to_langchain(self) -> BaseMessage:
        if self.role == "user":
            return HumanMessage(content=self.content)
        elif self.role == "assistant":
            return AIMessage(content=self.content)
        else:
            # Fallback for other roles if necessary
            return HumanMessage(content=self.content)

class QueryRequest(BaseModel):
    question: str
    db_path: str
    chat_history: Optional[List[Message]] = []

# --- FastAPI App ---
app = FastAPI(
    title="Text-to-SQL API",
    description="An API to convert natural language questions into SQL queries and execute them.",
    version="1.0.0",
)

workflow_engine = WorkflowEngine()

def validate_db_path(db_path: str):
    """
    Security validation for the database path to prevent directory traversal attacks.
    """
    # Get the absolute path of the 'databases' directory
    db_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'databases'))
    
    # Get the absolute path of the user-provided path
    user_path = os.path.abspath(db_path)
    
    # Check if the user_path is within the db_dir
    if not user_path.startswith(db_dir):
        raise HTTPException(status_code=403, detail=f"Forbidden: Access to '{db_path}' is not allowed.")

@app.get("/", tags=["Health Check"])
def read_root():
    """Root endpoint for health checks."""
    return {"status": "ok"}

@app.post("/query", tags=["Query"])
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
        
        # Check for errors in the result and return appropriate HTTP status
        if result.get("error"):
            # If the error is a security violation, return 403 Forbidden
            if "Security Violation" in result["error"]:
                 raise HTTPException(status_code=403, detail=result["error"])
            # For other errors, return 400 Bad Request
            raise HTTPException(status_code=400, detail=result["error"])

        return result

    except HTTPException as e:
        # Re-raise HTTPException to let FastAPI handle it
        raise e
    except Exception as e:
        # For any other unexpected errors, return 500 Internal Server Error
        raise HTTPException(status_code=500, detail=f"An internal server error occurred: {str(e)}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
