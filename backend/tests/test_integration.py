import pytest
from fastapi.testclient import TestClient
import os
import sys
from unittest.mock import MagicMock

# Add backend directory to path to import main
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Set dummy API keys to avoid error during main import
os.environ["OPENAI_API_KEY"] = "sk-dummy"
os.environ["GOOGLE_API_KEY"] = "dummy"

from main import app
# Import workflow_engine from the router where it is instantiated
from api.routers.query import workflow_engine

# Mock the workflow engine run method to avoid actual LLM calls
workflow_engine.run = MagicMock(return_value={"result": "Mocked SQL Result", "sql": "SELECT * FROM table"})

client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_upload_csv():
    # Create a dummy CSV file
    content = b"name,age,city\nAlice,30,New York\nBob,25,Los Angeles"
    files = {"file": ("test_data.csv", content, "text/csv")}
    
    response = client.post("/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert "db_path" in data
    assert data["filename"] == "test_data.csv"
    assert os.path.exists(data["db_path"])
    
    # Cleanup
    if os.path.exists(data["db_path"]):
        os.remove(data["db_path"])

def test_upload_invalid_file_type():
    content = b"some text"
    files = {"file": ("test.txt", content, "text/plain")}
    
    response = client.post("/upload", files=files)
    
    # Expecting 400 because only csv/xls/xlsx are handled in try block or 500 if implicit
    # Based on my implementation it might raise 400 or 500 depending on how file_converter handles it.
    # checking file_converter.py: it raises ValueError "Unsupported file format"
    # main.py catches ValueError and returns 400.
    assert response.status_code == 400

# Skip LLM query test if no API key is present to avoid failure in CI/Validation environment
# But we can test the Validation Logic
def test_query_invalid_db_path():
    response = client.post("/query", json={
        "question": "Hello",
        "chat_history": [],
        "db_path": "/etc/passwd" # malicious path
    })
    assert response.status_code == 403
