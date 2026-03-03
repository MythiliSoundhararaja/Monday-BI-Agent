"""
monday_client.py — Async GraphQL client for monday.com v2 API.

Provides two high-level fetchers:
  - fetch_work_orders(board_id) → list of flat item dicts
  - fetch_deals(board_id)       → list of flat item dicts

Each uses inline fragments on column types so we get the right
typed fields (text, number, date) rather than the generic `value` blob.
"""

import httpx
from fastapi import HTTPException
from app.config import get_settings

# ──────────────────────────────────────────────────────────────────────────────
# Shared GraphQL query template
# ──────────────────────────────────────────────────────────────────────────────

_BOARD_QUERY = """
query FetchBoardItems($boardId: [ID!]!) {
  boards(ids: $boardId) {
    items_page(limit: 500) {
      items {
        id
        name
        created_at
        column_values {
          id
          ... on StatusValue {
            text
            index
          }
          ... on NumbersValue {
            number
            text
          }
          ... on DateValue {
            date
            text
          }
          ... on MirrorValue {
            display_value
          }
          ... on BoardRelationValue {
            display_value
          }
          ... on TextValue {
            text
          }
          ... on LongTextValue {
            text
          }
          ... on FormulaValue {
            text
          }
          ... on ItemIdValue {
            item_id
          }
          ... on DropdownValue {
            text
          }
        }
      }
    }
  }
}
"""

# ──────────────────────────────────────────────────────────────────────────────
# Column-ID → flat key mappings (adjust IDs to match your actual board columns)
# ──────────────────────────────────────────────────────────────────────────────

# Work-orders board:  status | value (numbers) | date4 | sector (label/dropdown)
WORK_ORDER_COLUMN_MAP: dict[str, str] = {
    "numeric_mm11805b": "amount_excl_gst",
    "numeric_mm11hjk5": "amount_to_be_billed_excl_gst",
    "numeric_mm11k5zb": "amount_receivable",
    "date_mm11th5h":    "data_delivery_date",
    "date_mm11d93k":    "probable_end_date",
    "color_mm11kw47":     "actual_billing_month",
    "text_mm11bvbk":    "actual_collection_month",

}

# Deals board:  status | deal_value (numbers) | close_date | sector (label/dropdown)
DEALS_COLUMN_MAP: dict[str, str] = {
    "color_mm117d83":      "deal_status",
    "text_mm11g5zw":         "owner_code",
    "text_mm117g9b":        "client_code",
    "color_mm11x67t":  "closure_probability",
    "numeric_mm11xtnb":  "deal_value",
    "date_mm11zzt7":         "close_date",
    "date_mm117crw": "tentative_close_date",
    "color_mm11twe6":  "deal_stage",
    "color_mm11v4vw":       "product_deal",
    "color_mm111rzt":      "sector",
    "date_mm11ywfg":       "created_date",
}


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _extract_column_text(col: dict) -> str | None:
    """
    Return the most meaningful text value from a typed column_values entry.
    Priority order: date → number → display_value → text → item_id → None
    """
    if "date" in col and col["date"] is not None:
        return col["date"]
    if "number" in col and col["number"] is not None:
        return str(col["number"])
    if "display_value" in col and col["display_value"] is not None:
        return col["display_value"]
    if "item_id" in col and col["item_id"] is not None:
        return str(col["item_id"])
    return col.get("text")  # covers StatusValue, TextValue, LongTextValue, etc.


def _map_items(raw_items: list[dict], column_map: dict[str, str]) -> list[dict]:
    """
    Convert raw items_page items into flat dicts keyed by column_map values.

    Any column whose id is NOT in column_map is still stored under its raw id
    so that no data is silently dropped.
    """
    result: list[dict] = []
    for item in raw_items:
        record: dict = {
            "id":         item.get("id"),
            "name":       item.get("name"),
            "created_at": item.get("created_at"),
        }
        for col in item.get("column_values", []):
            col_id = col.get("id", "")
            key    = column_map.get(col_id, col_id)  # fall back to raw id
            record[key] = _extract_column_text(col)
        result.append(record)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# Client
# ──────────────────────────────────────────────────────────────────────────────

class MondayClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._url = "https://api.monday.com/v2"
        self._headers = {
            "Authorization": settings.MONDAY_API_KEY,
            "Content-Type":  "application/json",
            "API-Version":   "2023-10",
        }

    # ── low-level ──────────────────────────────────────────────────────────

    async def _execute(self, query: str, variables: dict) -> dict:
        """POST a GraphQL query; raise HTTPException on any transport/API error."""
        payload = {"query": query, "variables": variables}
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self._url,
                    json=payload,
                    headers=self._headers,
                )
                response.raise_for_status()
                data = response.json()

        except httpx.HTTPStatusError as exc:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Failed to fetch board data: HTTP {exc.response.status_code} "
                    f"from monday.com — check MONDAY_API_KEY in .env"
                ),
            ) from exc
        except httpx.TimeoutException as exc:
            raise HTTPException(
                status_code=400,
                detail="Failed to fetch board data: request to monday.com timed out.",
            ) from exc
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch board data: {exc}",
            ) from exc

        # Surface GraphQL-level errors (they come back as HTTP 200 with an errors key)
        if "errors" in data:
            messages = "; ".join(e.get("message", str(e)) for e in data["errors"])
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch board data: GraphQL error — {messages}",
            )

        return data

    # ── internal board fetcher ─────────────────────────────────────────────

    async def _fetch_items(self, board_id: int) -> list[dict]:
        """Return the raw items list for a given board id."""
        variables = {"boardId": [str(board_id)]}
        data = await self._execute(_BOARD_QUERY, variables)
        boards: list[dict] = (
            data.get("data", {}).get("boards", [])
        )
        if not boards:
            return []
        return boards[0].get("items_page", {}).get("items", [])

    # ── public API ─────────────────────────────────────────────────────────

    async def fetch_work_orders(self, board_id: int) -> list[dict]:
        """
        Fetch all items from the Work-Orders board and return flat dicts with:
          id, name, created_at, status, value, date4, sector
        """
        raw_items = await self._fetch_items(board_id)
        return _map_items(raw_items, WORK_ORDER_COLUMN_MAP)

    async def fetch_deals(self, board_id: int) -> list[dict]:
        """
        Fetch all items from the Deals board and return flat dicts with:
          id, name, created_at, status, deal_value, close_date, sector
        """
        raw_items = await self._fetch_items(board_id)
        return _map_items(raw_items, DEALS_COLUMN_MAP)


# Module-level singleton (import and use directly)
monday_client = MondayClient()
