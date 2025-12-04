# backend/semantic_router.py

from __future__ import annotations

from typing import Any, Callable, Dict, List, Set, Tuple

import numpy as np

from backend.preprocessing import PromptCleaner
from backend.embeddings_manager import EmbeddingsManager


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-10
    return float(a @ b / denom)


Schema = Dict[str, Any]
SchemaProvider = Callable[[], Schema]


class SemanticRouter:
    """
    Given:
      - a natural language prompt
      - a database schema (via a schema_provider)

    It returns:
      - cleaned_prompt
      - selected_tables: list[str]
      - selected_columns: dict[table -> list[column]]
    """

    def __init__(self, schema_provider: SchemaProvider) -> None:
        if schema_provider is None:
            raise ValueError("schema_provider must not be None")
        self.schema_provider = schema_provider
        self.cleaner = PromptCleaner()
        self.embedder = EmbeddingsManager()

    # ---------- internal helpers ----------

    def _build_items_from_schema(self, schema: Schema) -> List[Tuple[str, str, str]]:
        """
        Turn schema into a list of (kind, id, description) items.

        kind is either "table" or "column".
        id is "orders" or "orders.total_amount".
        """
        items: List[Tuple[str, str, str]] = []

        for table in schema.get("tables", []):
            table_name = table["name"]
            col_names = [c["name"] for c in table.get("columns", [])]

            # table-level description
            table_desc = f"table {table_name} with columns {', '.join(col_names)}"
            items.append(("table", table_name, table_desc))

            # column-level descriptions
            for col in table.get("columns", []):
                col_name = col["name"]
                col_type = col.get("type", "unknown")
                col_desc = f"column {col_name} in table {table_name}, type {col_type}"
                items.append(("column", f"{table_name}.{col_name}", col_desc))

        return items

    # ---------- public API ----------

    def route(self, raw_prompt: str, top_k: int = 10) -> Dict[str, Any]:
        """
        Main entry point.

        Returns a dict with:
          - cleaned_prompt
          - selected_tables: list[str]
          - selected_columns: dict[table -> list[column]]
        """
        cleaned = self.cleaner.clean(raw_prompt)

        schema = self.schema_provider()
        items = self._build_items_from_schema(schema)
        if not items:
            return {
                "cleaned_prompt": cleaned,
                "selected_tables": [],
                "selected_columns": {},
            }

        kinds = [item[0] for item in items]  # "table" or "column"
        ids = [item[1] for item in items]    # "orders" or "orders.total_amount"
        texts = [item[2] for item in items]  # descriptions

        prompt_vec = self.embedder.embed([cleaned])[0]
        item_vecs = self.embedder.embed(texts)

        scores: List[float] = [
            cosine_similarity(prompt_vec, vec) for vec in item_vecs
        ]

        # sort by similarity
        ranked = sorted(
            zip(kinds, ids, scores),
            key=lambda x: x[2],
            reverse=True,
        )
        top_items = ranked[: top_k]

        selected_tables: Set[str] = set()
        selected_columns: Dict[str, Set[str]] = {}

        for kind, identifier, score in top_items:
            if kind == "table":
                table_name = identifier
                selected_tables.add(table_name)
            elif kind == "column":
                table_name, col_name = identifier.split(".", 1)
                selected_tables.add(table_name)
                selected_columns.setdefault(table_name, set()).add(col_name)

        # normalize sets → sorted lists
        selected_columns_norm: Dict[str, List[str]] = {
            t: sorted(cols) for t, cols in selected_columns.items()
        }

        return {
            "cleaned_prompt": cleaned,
            "selected_tables": sorted(selected_tables),
            "selected_columns": selected_columns_norm,
        }
