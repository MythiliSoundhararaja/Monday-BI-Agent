"""
llm_agent.py — Pure Python rule-based BI Agent.

No external LLM dependencies.
1. generate_plan: Simple keyword parsing for metric, period, sector.
2. generate_final_answer: Template-based synthesis using the rich nested summary.
"""

import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class Plan:
    metric: str
    period: str
    sector: Optional[str]
    boards_needed: list[str]
    clarification_needed: bool = False
    clarification_question: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "metric": self.metric,
            "period": self.period,
            "sector": self.sector,
            "boards_needed": self.boards_needed,
            "clarification_needed": self.clarification_needed,
            "clarification_question": self.clarification_question,
        }


class LLMAgent:
    def __init__(self):
        pass

    # ── Planner ──────────────────────────────────────────────────────────────

    async def generate_plan(self, message: str, history: list) -> dict:
        """
        Extract intent from user query using keyword matching.
        """
        text = (message or "").lower()

        # Self-awareness check
        if any(kw in text for kw in ["who are you", "what can you do", "introduce yourself"]):
            return {
                "metric": "meta",
                "period": "all",
                "sector": None,
                "boards_needed": [],
                "clarification_needed": False,
            }

        metric, boards = self._infer_metric_and_boards(text)
        period = self._infer_period(text)
        sector = self._infer_sector(text)

        # Clarification logic
        clarification_needed = False
        clarification_question = None
        if "pipeline" in text and not any(kw in text for kw in ["deal", "work order", "wo"]):
            clarification_needed = True
            clarification_question = "Do you want deal pipeline, work-order pipeline, or both?"

        plan = Plan(
            metric=metric,
            period=period,
            sector=sector,
            boards_needed=boards,
            clarification_needed=clarification_needed,
            clarification_question=clarification_question,
        )
        return plan.to_dict()

    def _infer_metric_and_boards(self, text: str) -> tuple[str, list[str]]:
        metric = "pipeline_value"
        boards = ["deals", "work_orders"]

        if any(kw in text for kw in ["work order", "wo ", "wo-"]):
            metric = "work_order_value"
            boards = ["work_orders"]
        elif any(kw in text for kw in ["receivable", "outstanding"]):
            metric = "receivable_value"
            boards = ["work_orders"]
        elif any(kw in text for kw in ["deal", "funnel", "sales pipeline"]):
            metric = "pipeline_value"
            boards = ["deals"]

        return metric, boards

    def _infer_period(self, text: str) -> str:
        if "last quarter" in text: return "last_quarter"
        if "this quarter" in text or "current quarter" in text: return "this_quarter"
        if "last month" in text or "previous month" in text: return "last_month"
        if "this month" in text or "current month" in text: return "this_month"
        if "all time" in text or "overall" in text: return "all"
        return "this_quarter"

    def _infer_sector(self, text: str) -> Optional[str]:
        if "mining" in text: return "Mining"
        if "powerline" in text: return "Powerline"
        if "energy" in text: return "Energy"
        return None

    # ── Synthesis ─────────────────────────────────────────────────────────────

    def format_rupees(self, value: float) -> str:
        """Format rupees as ₹X.XXM, ₹X.XXK, or ₹X,XXX"""
        if value == 0:
            return "₹0.00"
        
        abs_val = abs(value)
        if abs_val >= 1_000_000:  # Millions
            return f"₹{value / 1_000_000:.1f}M"
        elif abs_val >= 1_000:    # Thousands
            return f"₹{value / 1_000:.0f}K"
        else:                        # Raw number
            return f"₹{value:,.0f}"

    async def generate_final_answer(self, context: dict) -> str:
        """Generate comprehensive founder-friendly answer with proper formatting."""
        plan = context.get("plan", {})
        summary = context.get("summary", {})
        data_quality = context.get("data_quality", {})
        
        # Meta/Self-awareness response
        if plan.get("metric") == "meta":
            return (
                "I am the Monday.com BI Agent. I help you track your business pipeline by fetching live "
                "data from your Deals and Work Orders boards. You can ask me about:\n\n"
                "• **Sales Pipeline**: Committed (close date) vs. Expected (tentative).\n"
                "• **Execution Pipeline**: Work order totals, unbilled values, and receivables.\n"
                "• **Sector Analysis**: Filtering by Mining, Energy, Powerline, etc.\n"
                "• **Time Periods**: Comparisons for this month, last quarter, etc."
            )

        # Period formatting: remove 'this_' or 'last_' for cleaner headers
        period_raw = summary.get("period", "unknown")
        period = period_raw.replace("this_", "").replace("last_", "")
        sector = summary.get("sector") or "all sectors"
        
        lines = []
        lines.append(f"Analysis for {period} ({sector}):")
        lines.append("")
        
        # 1. DEALS Section
        deals = summary.get("deals", {})
        if deals:
            lines.append("DEALS (Sales Pipeline):")
            committed = float(deals.get("pipeline_close_date", 0) or 0)
            expected = float(deals.get("pipeline_tentative_close", 0) or 0)
            
            lines.append(f"• Committed Pipeline (Close Date): {self.format_rupees(committed)}")
            lines.append(f"• Expected Pipeline (Tentative): {self.format_rupees(expected)}")
            lines.append("")
        
        # 2. WORK ORDERS Section  
        work_orders = summary.get("work_orders", {})
        if work_orders:
            lines.append("WORK ORDERS (Execution Pipeline):")
            total_val = float(work_orders.get("total_value", 0) or 0)
            receivables = float(work_orders.get("receivables", 0) or 0)
            unbilled = float(work_orders.get("unbilled", 0) or 0)
            
            lines.append(f"• Total Value: {self.format_rupees(total_val)}")
            if receivables > 0:
                lines.append(f"• Receivables: {self.format_rupees(receivables)}")
            if unbilled > 0:
                lines.append(f"• Unbilled: {self.format_rupees(unbilled)}")
            lines.append("")
        
        # 3. Overall
        total_items = int(deals.get("filtered_records", 0) or 0) + int(work_orders.get("filtered_records", 0) or 0)
        boards_count = data_quality.get("boards_processed", 2)
        lines.append(f"Overall: Comprehensive analysis from {boards_count} boards. {total_items} items contribute to pipeline visibility.")
        
        return "\n".join(lines)


llm_agent = LLMAgent()
