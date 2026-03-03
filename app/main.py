from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.models import QueryRequest, QueryResponse, TraceStep
from app.config import get_settings
from app.llm_agent import llm_agent
from app.monday_client import monday_client
from app.bi_logic import bi_logic
import pandas as pd

app = FastAPI(title="Monday BI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(request: QueryRequest):
    settings = get_settings()
    trace = []
    
    # 0. Block greetings/non-business queries
    greetings = ["hi", "hello", "hey", "how are you", "good morning", "thanks"]
    meta_queries = ["who are you", "what are you", "help", "features"]
    
    message_lower = request.message.lower().strip()
    if any(g in message_lower for g in greetings + meta_queries):
        return QueryResponse(
            answer="👋 Hi! I'm your Monday.com BI Agent. Ask me about:\n\n💰 **Pipeline**: 'deal pipeline this quarter?'\n📊 **Sectors**: 'Mining work orders?'\n📈 **Receivables**: 'total receivables?'\n\nTry: 'What's our pipeline looking like?'",
            trace=[TraceStep(step="Greeting", description="Handled casual greeting with capabilities overview.")]
        )

    try:
        # 1. Interpret Question
        trace.append(TraceStep(step="Interpret Question", description="Agent is planning data retrieval strategy."))
        plan = await llm_agent.generate_plan(request.message, request.history)

        if plan.get("clarification_needed"):
            return QueryResponse(answer=plan.get("clarification_question"), trace=trace)

        # 2. ALWAYS fetch BOTH boards for pipeline questions (comprehensive view)
        trace.append(TraceStep(step="Fetch Data", description="Fetching ALL relevant boards for comprehensive pipeline analysis."))
        raw_data = {}
        raw_data["deals"] = await monday_client.fetch_deals(settings.DEALS_BOARD_ID)
        raw_data["work_orders"] = await monday_client.fetch_work_orders(settings.WORK_ORDERS_BOARD_ID)
        
        # 3. Clean and compute comprehensive metrics
        trace.append(TraceStep(step="Process Data", description="Cleaning data and computing multi-perspective metrics."))
        all_items = []
        for board_items in raw_data.values():
            if isinstance(board_items, list):
                all_items.extend(board_items)
        df = bi_logic.clean_data(all_items)

        # Apply filters from plan
        period = plan.get("period", "this_quarter")
        sector = plan.get("sector")
        
        # ── DEALS AGGREGATION ────────────────────────────────────────────────
        deals_df = df[df.get("board_type") == "deals"]
        if sector:
            deals_df = deals_df[deals_df["sector"].astype(str).str.contains(sector, case=False, na=False)]
            
        # Filter for Committed (Close Date)
        committed_df = bi_logic._filter_by_period(deals_df, period, "close_date")
        # Filter for Expected (Tentative Close Date)
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

        # ── WORK ORDERS AGGREGATION ─────────────────────────────────────────
        wo_df = df[df.get("board_type") == "work_orders"]
        if sector:
            wo_df = wo_df[wo_df["sector"].astype(str).str.contains(sector, case=False, na=False)]
            
        # Execution filter usually uses data_delivery_date
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

        # ── COMBINED SUMMARY ────────────────────────────────────────────────
        f_deals = metrics_deals.get("filtered_records", 0)
        f_wo = metrics_wo.get("filtered_records", 0)
        total_filtered = int(f_deals) + int(f_wo)
        
        metrics = {
            "deals": metrics_deals,
            "work_orders": metrics_wo,
            "period": period,
            "sector": sector or "all sectors",
            "note": f"Comprehensive analysis from 2 boards. {total_filtered} items contribute to pipeline visibility."
        }

        # 4. Generate comprehensive founder-friendly answer
        trace.append(TraceStep(step="Generate Insight", description="Synthesizing comprehensive business analysis."))
        context = {
            "plan": plan,
            "summary": metrics,
            "data_quality": {"boards_processed": len(raw_data)}
        }

        answer = await llm_agent.generate_final_answer(context)
        return QueryResponse(answer=answer, trace=trace)

    except HTTPException:
        raise  # Re-raise clean HTTP errors (e.g. from monday_client)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
