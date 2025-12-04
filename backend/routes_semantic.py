# backend/api/routes_semantic.py

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from backend.semantic_router import SemanticRouter

router = APIRouter(
    tags=["semantic-routing"],
)


class SemanticRouteRequest(BaseModel):
    prompt: str


# Temporary schema provider (same as tests); later replace with real DB schema
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


semantic_engine = SemanticRouter(schema_provider=_fake_schema)


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
    return semantic_engine.route(body.prompt)
