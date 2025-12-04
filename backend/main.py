# backend/main.py
"""FastAPI entrypoint configuring CORS and mounting API routes."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ✅ imports for routers
from backend.api.routes_db import router as db_router
from backend.api.routes_semantic import router as semantic_router


app = FastAPI(title="NL2SQL Backend - Data Layer")

# CORS so React / other clients can call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # you can restrict this later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Register routers
# Database routes under /db
app.include_router(db_router, prefix="/db", tags=["database"])

# Semantic routing routes under /semantic
app.include_router(semantic_router, prefix="/semantic", tags=["semantic-routing"])


@app.get("/health")
def health_check():
    """Simple liveness probe endpoint."""
    return {"status": "ok"}
