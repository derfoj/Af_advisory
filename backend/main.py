import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import sys

# Adjust the python path to include the src directory
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from api.routers import upload, query, data

# --- FastAPI App ---
app = FastAPI(
    title="Text-to-SQL API",
    description="An API to convert natural language questions into SQL queries and execute them.",
    version="1.0.0",
)

# Add CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(upload.router)
app.include_router(query.router)
app.include_router(data.router)

@app.get("/", tags=["Health Check"])
def read_root():
    """Root endpoint for health checks."""
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
