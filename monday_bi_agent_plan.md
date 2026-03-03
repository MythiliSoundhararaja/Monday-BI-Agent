# Monday BI Agent Implementation Plan

## Project overview
Monday BI Agent is a business intelligence application designed to bridge the gap between human questions and structured data from monday.com. The app consists of a FastAPI backend that uses the Gemini 3 LLM to interpret natural language queries, fetch relevant data from the "Work Orders" and "Deals" boards via GraphQL, and provide data-driven answers. Gemini 3 acts as the orchestrator, both planning the data retrieval strategy and synthesizing final insights, while the frontend provides a user-friendly interface for querying this agent.

## File structure
```text
monday_bi_agent/
├── app/
│   ├── main.py              # FastAPI application entry point and endpoint definitions.
│   ├── config.py            # Configuration management and environment variable loading.
│   ├── monday_client.py     # Client for interacting with the monday.com GraphQL API.
│   ├── llm_agent.py         # Interface for communicating with Gemini 3 for planning and synthesis.
│   ├── bi_logic.py          # Core logic for data cleaning, normalization, and metric computation.
│   ├── models.py            # Pydantic models for request/response validation and internal data structures.
├── frontend/
│   ├── index.html           # Main frontend interface for user interaction.
├── requirements.txt         # List of Python dependencies (FastAPI, httpx, google-generativeai, etc.).
├── README.md                # Project documentation and setup instructions.
├── .env                     # Local environment variables (not for version control).
└── monday_bi_agent_plan.md  # Detailed implementation planning document.
```

## Responsibilities of each module

### main.py
*   **Inputs:** HTTP requests from the frontend, specifically on the `/query` endpoint.
*   **Outputs:** JSON responses containing the LLM-generated answer and a trace of the execution steps.
*   **Internal Functions:** `query_endpoint()` (handles the POST request), `setup_middleware()` (CORS configuration).

### config.py
*   **Inputs:** System environment variables and optional `.env` file.
*   **Outputs:** A configuration object used by other modules to access API keys and board IDs.
*   **Internal Functions:** `get_settings()` (dependency to provide cached settings).

### monday_client.py
*   **Inputs:** Board IDs, column mappings, and GraphQL query strings.
*   **Outputs:** Raw JSON data returned from the monday.com API.
*   **Internal Functions:** `fetch_board_data()`, `execute_query()`, `get_board_schema()`.

### llm_agent.py
*   **Inputs:** User questions, conversation history, and raw data from `bi_logic.py`.
*   **Outputs:** Structured "plans" (JSON) and final natural language answers.
*   **Internal Functions:** `generate_plan()`, `generate_final_answer()`.

### bi_logic.py
*   **Inputs:** Raw JSON data from `monday_client.py`.
*   **Outputs:** Cleaned DataFrames or lists of normalized records and computed metrics.
*   **Internal Functions:** `clean_data()`, `compute_pipeline_metrics()`, `calculate_revenue()`.

### models.py
*   **Inputs:** Raw JSON or dictionary data during instantiation.
*   **Outputs:** Validated Pydantic objects.
*   **Internal Functions:** Definition of `QueryRequest`, `QueryResponse`, `QueryPlan`, and `TraceStep`.

## /query endpoint flow
1.  **Receive Request:** The server receives a JSON payload containing the user's message and the conversation history.
2.  **Interpret Question:** `llm_agent.py` calls Gemini 3 with the question and history to generate a structured "plan" (identifying metrics, sectors, time periods, and boards needed).
3.  **Check Clarification:** If Gemini 3 determines the question is ambiguous, it sets a `clarification_needed` flag, and the API responds immediately asking for missing details.
4.  **Fetch Data:** Based on the plan, `monday_client.py` retrieves records from the "Work Orders" and/or "Deals" boards using GraphQL.
5.  **Clean and Normalize:** `bi_logic.py` processes the raw data, converting date strings to datetime objects, normalizing numbers, handling missing values, and mapping sector names consistently.
6.  **Compute Metrics:** The clean data is used to calculate specific business metrics identified in the plan (e.g., total pipeline value, conversion rates, or record counts).
7.  **Generate Insight:** `llm_agent.py` calls Gemini 3 again, providing it with the computed metrics and data-quality notes to generate a founder-friendly, natural-language answer.
8.  **Return Response:** The endpoint returns a JSON response containing the `answer` and a `trace` array that chronicles each of the above steps for transparency.

## Configuration and environment variables
*   `MONDAY_API_KEY`: Personal API token for authorizing GraphQL requests.
*   `WORK_ORDERS_BOARD_ID`: The unique identifier for the "Work Orders" board on monday.com.
*   `DEALS_BOARD_ID`: The unique identifier for the "Deals" board on monday.com.
*   `GEMINI_API_KEY`: API key for accessing Google Gemini 3 models.
*   `ENV`: Execution environment (e.g., `development`, `production`).
*   `PORT`: The port on which the FastAPI server will run (default: 8000).

## Data and error-handling strategy
*   **Missing or null values:** Null values in numeric columns will be treated as zero when appropriate (e.g., deal values) or removed from average calculations to avoid skewing results.
*   **Inconsistent formats:** All dates will be coerced into ISO 8601 format, and numbers will be stripped of currency symbols or commas before conversion to floats.
*   **Empty result sets:** If no data is found for a specific sector or time period, the agent will explicitly state that no data exists for that filter rather than providing a zero value that might be misleading.
*   **monday.com API errors:** Implement retries for transient HTTP errors (5xx) and raise specific exceptions for rate limits (429) or authentication failures (401/403).
*   **Gemini 3 errors:** If the LLM returns an invalid JSON plan, the system will attempt one retry with an updated prompt or fallback to a "clarification needed" response.
*   **Schema Evolution:** If board column names change, the `config.py` column mappings will be the single point of truth to be updated, preventing breaks in `bi_logic.py`.
