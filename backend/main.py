"""FastAPI entrypoint configuring CORS and mounting database-related routes."""
# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes_db import router as db_router

app = FastAPI(title="NL2SQL Backend - Data Layer")

app.add_middleware(
    CORSMiddleware,
    # Allow all origins/headers/methods for ease of local/frontend integration
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount DB-related routes under /db
app.include_router(db_router, prefix="/db", tags=["database"])


@app.get("/health")
def health_check():
    """Simple liveness probe consumed by uptime checks or load balancers."""
    # Simple liveness probe endpoint
    return {"status": "ok"}
