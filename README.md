# Monday BI Agent

A FastAPI backend and simple frontend that uses Gemini 3 to query and analyze data from Monday.com boards.

## Setup

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment:**
    Copy `.env.example` to `.env` and fill in your API keys and board IDs.

3.  **Run the Backend:**
    ```bash
    uvicorn app.main:app --reload
    ```

4.  **Open the Frontend:**
    Open `frontend/index.html` in your browser.

## Features
- Natural language query interpretation via Gemini 3.
- Automated data fetching from Monday.com GraphQL API.
- Data cleaning and metric computation using Pandas.
- Transparent execution trace for every query.
