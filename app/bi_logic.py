"""
bi_logic.py — Data cleaning, board tagging, and filtering logic.

This version supports tagging rows as 'deals' or 'work_orders' during cleaning
and provides a unified filter_data method for period/sector filtering.
"""

import pandas as pd
from datetime import datetime, timezone
from typing import Optional


class BILogic:

    # ── Data Cleaning & Tagging ──────────────────────────────────────────────

    def clean_data(self, items: list[dict]) -> pd.DataFrame:
        """
        Convert raw items to a tagged and typed DataFrame.
        """
        if not items:
            return pd.DataFrame()

        df_list = []
        for item in items:
            row = item.copy()
            # Tag board type based on unique column presence (post-mapping)
            if "deal_value" in row:
                row["board_type"] = "deals"
            elif "amount_excl_gst" in row or "amount_receivable" in row:
                row["board_type"] = "work_orders"
            else:
                row["board_type"] = "unknown"
            df_list.append(row)

        df = pd.DataFrame(df_list)

        # Numeric and Date coercion hints
        NUMERIC_HINTS = [
            "value", "amount", "deal_value", "receivable",
            "billed", "excl_gst", "unbilled", "pipeline",
        ]
        DATE_HINTS = [
            "date", "close_date", "created_at", "delivery",
            "end_date", "month", "created_date", "tentative",
        ]

        for col in df.columns:
            col_lower = col.lower()
            if any(h in col_lower for h in NUMERIC_HINTS):
                df[col] = pd.to_numeric(df[col], errors="coerce")
            elif any(h in col_lower for h in DATE_HINTS):
                df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)

        return df

    # ── Unified Filtering ───────────────────────────────────────────────────

    def filter_data(self, df: pd.DataFrame, period: str, sector: Optional[str] = None) -> pd.DataFrame:
        """
        Apply common filters (period and sector) across both board types.
        """
        if df.empty:
            return df
            
        filtered = df.copy()
        
        # 1. Period filter
        if period != "all":
            date_col = self._pick_date_column(filtered.columns)
            if date_col:
                filtered = self._filter_by_period(filtered, period, date_col=date_col)
        
        # 2. Sector filter
        if sector and "sector" in filtered.columns:
            # Case-insensitive substring match
            mask = filtered["sector"].astype(str).str.contains(sector, case=False, na=False)
            filtered = filtered[mask]
            
        return filtered

    def _pick_date_column(self, columns: list[str]) -> Optional[str]:
        """Prioritize columns for the period filter."""
        DATE_PRIORITY = [
            "close_date", "data_delivery_date", "tentative_close_date",
            "probable_end_date", "created_at",
        ]
        for col in DATE_PRIORITY:
            if col in columns:
                return col
        return None

    # ── Helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _safe_sum(df: pd.DataFrame, col: str) -> float:
        if col not in df.columns:
            return 0.0
        return float(df[col].dropna().sum())

    @staticmethod
    def _filter_by_period(df: pd.DataFrame, period: str, date_col: str) -> pd.DataFrame:
        if period == "all" or df.empty or date_col not in df.columns:
            return df

        now = datetime.now(timezone.utc)
        month, year = now.month, now.year
        quarter = (month - 1) // 3 + 1

        try:
            if period == "this_quarter":
                q_start_month = (quarter - 1) * 3 + 1
                start = pd.Timestamp(year=year, month=q_start_month, day=1, tz="UTC")
                end = start + pd.DateOffset(months=3)
            elif period == "last_quarter":
                lq = quarter - 1 or 4
                lq_year = year - (1 if quarter == 1 else 0)
                q_start = (lq - 1) * 3 + 1
                start = pd.Timestamp(year=lq_year, month=q_start, day=1, tz="UTC")
                end = start + pd.DateOffset(months=3)
            elif period == "this_month":
                start = pd.Timestamp(year=year, month=month, day=1, tz="UTC")
                end = start + pd.DateOffset(months=1)
            elif period == "last_month":
                lm = month - 1 or 12
                lm_year = year - (1 if month == 1 else 0)
                start = pd.Timestamp(year=lm_year, month=lm, day=1, tz="UTC")
                end = start + pd.DateOffset(months=1)
            else:
                return df
                
            mask = (df[date_col] >= start) & (df[date_col] < end)
            return df[mask]
        except Exception:
            return df


bi_logic = BILogic()
