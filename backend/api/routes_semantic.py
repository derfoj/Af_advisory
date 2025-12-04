# backend/api/routes_semantic.py

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from backend.semantic_router import SemanticRouter


router = APIRouter(
    prefix="/semantic",
    tags=["semantic-routing"],
)


class SemanticRouteRequest(BaseModel):
    prompt: str


# --- TEMP schema provider for Phase 2 demo ---
# This uses the same fake schema as in tests.
# Later you can replace this with a real provider that
# reads from your SQLite/MySQL DB via DatabaseManager + get_sqlite_schema.
def _fake_schema() -> Dict[str, Any]:
    return {
        "tables": [
            {
                "name": "orders",
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "customer_id", "type": "INTEGER"},
                    {"name": "total_amount", "type": "FLOAT"},
                    {"name": "date", "type": "DATE"},
                ],
            },
            {
                "name": "customers",
                "columns": [
                    {"name": "id", "type": "INTEGER"},
                    {"name": "name", "type": "TEXT"},
                    {"name": "address", "type": "TEXT"},
                ],
            },
        ]
    }


semantic_router = SemanticRouter(schema_provider=_fake_schema)


@router.post("/route")
def semantic_route(body: SemanticRouteRequest):
    """
    Semantic routing endpoint for Phase 2.

    Input:
      {
        "prompt": "What is the total sales per month in 2023?"
      }

    Output:
      {
        "cleaned_prompt": "...",
        "selected_tables": [...],
        "selected_columns": {...}
      }
    """
    result = semantic_router.route(body.prompt)
    return result
