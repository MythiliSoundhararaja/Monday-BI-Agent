import asyncio
import json
from app.llm_agent import llm_agent
from app.bi_logic import bi_logic
from app.monday_client import monday_client
from app.config import get_settings

async def test_scenarios():
    settings = get_settings()
    queries = [
        "What's the deal pipeline this quarter?",
        "What are work order receivables for Mining this month?",
        "Show me pipeline for Energy this quarter."
    ]

    for query in queries:
        print(f"\n>>> QUERY: {query}")
        
        # 1. Plan
        plan = await llm_agent.generate_plan(query, [])
        print(f"PLAN: metric={plan['metric']}, period={plan['period']}, sector={plan['sector']}, boards={plan['boards_needed']}")
        
        if plan.get('clarification_needed'):
            print(f"CLARIFICATION: {plan['clarification_question']}")
            continue

        # 2. Fetch (Always both for comprehensive view)
        raw_data = {}
        raw_data["deals"] = await monday_client.fetch_deals(settings.DEALS_BOARD_ID)
        raw_data["work_orders"] = await monday_client.fetch_work_orders(settings.WORK_ORDERS_BOARD_ID)

        # 3. Process (Matching main.py logic)
        all_items = []
        for board_items in raw_data.values():
            if isinstance(board_items, list):
                all_items.extend(board_items)
        df = bi_logic.clean_data(all_items)

        # Apply filters
        period = plan.get("period", "this_quarter")
        sector = plan.get("sector")
        
        # DEALS
        deals_df = df[df.get("board_type") == "deals"]
        if sector:
            deals_df = deals_df[deals_df["sector"].astype(str).str.contains(sector, case=False, na=False)]
        
        committed_df = bi_logic._filter_by_period(deals_df, period, "close_date")
        expected_df = bi_logic._filter_by_period(deals_df, period, "tentative_close_date")
        
        metrics_deals = {
            "total_records": len(deals_df),
            "filtered_records": len(committed_df),
            "pipeline_close_date": bi_logic._safe_sum(committed_df, "deal_value"),
            "pipeline_tentative_close": bi_logic._safe_sum(expected_df, "deal_value"),
            "data_quality": {
                "deal_value_non_null": int(committed_df["deal_value"].notna().sum())
            }
        }

        # WORK ORDERS
        wo_df = df[df.get("board_type") == "work_orders"]
        if sector:
            wo_df = wo_df[wo_df["sector"].astype(str).str.contains(sector, case=False, na=False)]
            
        execution_df = bi_logic._filter_by_period(wo_df, period, "data_delivery_date")

        metrics_wo = {
            "total_records": len(wo_df),
            "filtered_records": len(execution_df),
            "total_value": bi_logic._safe_sum(execution_df, "amount_excl_gst"),
            "receivables": bi_logic._safe_sum(execution_df, "amount_receivable"),
            "unbilled": bi_logic._safe_sum(execution_df, "amount_to_be_billed_excl_gst"),
            "data_quality": {
                "amount_non_null": int(execution_df["amount_excl_gst"].notna().sum())
            }
        }

        total_filtered = int(metrics_deals["filtered_records"]) + int(metrics_wo["filtered_records"])
        metrics = {
            "deals": metrics_deals,
            "work_orders": metrics_wo,
            "period": period,
            "sector": sector or "all sectors",
            "note": f"Comprehensive analysis from 2 boards. {total_filtered} items contribute to pipeline visibility."
        }
        
        # 4. Answer
        context = {
            "plan": plan,
            "summary": metrics,
            "data_quality": {"boards_processed": len(raw_data)}
        }
        
        answer = await llm_agent.generate_final_answer(context)
        print(f"\nFINAL ANSWER:\n{answer}")
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(test_scenarios())
