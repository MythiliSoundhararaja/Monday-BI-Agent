# Monday.com BI Agent - Enterprise-Ready Self-Documenting AI

🎯 **Production Status: ✅ LIVE & READY**  
🎯 **Interactive Demo**: [Render App Docs](https://monday-com-bi-agent-ao23.onrender.com/docs)

---

## 🎯 Production Checklist - Enterprise Certified
| Feature | Status | Proof |
| :--- | :--- | :--- |
| **Live monday.com API** | ✅ Connected | Every query hits GraphQL v2 |
| **Zero Caching** | ✅ No preload | Fresh data every request |
| **Swagger Auto-docs** | ✅ /docs | Interactive API testing |
| **Render Auto-scale** | ✅ Production | Handles high volume requests |
| **Null Data Handling** | ✅ Graceful | ₹0.00 reporting for missing data |
| **Multi-board Fusion** | ✅ Deals+WorkOrders | Comprehensive pipeline view |
| **Business Formatting** | ✅ ₹384.7M | Founder-readable figures |
| **Action Traces** | ✅ Visible | Interpret → Fetch → Process → Insight |

---

## 🚀 Interactive Demo - 3-Minute Test Flow
Open: [https://monday-com-bi-agent-ao23.onrender.com/docs](https://monday-com-bi-agent-ao23.onrender.com/docs)  
Endpoint: **POST /query** → "Try it out"

### 1. Comprehensive Pipeline (Multi-board)
```json
{
  "message": "What's the deal pipeline this quarter?",
  "history": []
}
```
**Expected Outcome**: A detailed breakdown of "₹X.XM committed + ₹Y.YM expected + ₹Z.ZM work orders". Proves Live API connection, multi-board fetching, and business metric calculation.

### 2. Zero-Data Edge Case (Production Reality)
```json
{
  "message": "Energy sector pipeline this quarter?",
  "history": []
}
```
**Expected Outcome**: "₹0.00 across both boards | 0 items contribute". Proves honest reporting and null resilience.

### 3. Sector + Time Filtering
```json
{
  "message": "work-order Mining pipeline this month?",
  "history": []
}
```
**Expected Outcome**: "₹0.00 work orders | ₹6.1M expected deals". Proves accurate intent parsing and March 2026 period filtering.

### 4. Agent Self-Awareness (NEW)
```json
{
  "message": "who are you?",
  "history": []
}
```
**Expected Outcome**: "I'm Monday.com BI Agent. Ask about pipeline, sectors...". Proves context-awareness and prevents hallucination.

---

## 🧠 AI Agent Architecture (Founder → Insight)
```mermaid
graph TB
    CEO[👨💼 CEO: "Mining pipeline?"] 
    --> NLP[Natural Language Parser]
    NLP --> Intent[Intent: work-order + Mining + month]
    Intent --> Plan[Strategy: Fetch 2 boards]
    Plan --> LiveAPI[(monday.com<br/>GraphQL v2)]
    LiveAPI --> Deals[Deals Board ID]
    LiveAPI --> WO[Work Orders Board ID]
    Deals --> Pandas["Pandas:<br/>₹6.1M formatting"]
    WO --> Pandas
    Pandas --> Insight["₹0 work orders<br/>₹6.1M deals pipeline"]
    Insight --> JSON["{answer, trace}"]
```

### Agent Intelligence Layers
1. **INTENT**: "work-order" vs "deals" → Board strategy
2. **ENTITY**: "Mining" → Sector filter
3. **TIME**: "this month" → March 2026 filter
4. **STRATEGIC**: Always checks both boards for comprehensive view
5. **OUTPUT**: Business language + data quality transparency

---

## 📊 Complete Query Reference
| Intent | Example Query | Expected Insight |
| :--- | :--- | :--- |
| **Pipeline** | "deal pipeline this quarter?" | Unified visibility (Committed vs Expected) |
| **Sector** | "Mining work orders month?" | Sector-specific deep dive |
| **Receivables** | "total receivables Energy?" | Outstanding invoices breakdown |
| **Zero Data** | "Energy pipeline quarter?" | Truthful ₹0.00 reporting |
| **Meta** | "who are you?" | Capability overview |
| **Broad** | "pipeline?" | Smart clarification request |

---

## 🔧 Production-Grade Tech Stack
- **🌐 API**: FastAPI + Swagger UI (/docs)
- **📊 Data**: Live monday.com GraphQL v2
- **🐼 Processing**: Pandas (typed and null-safe)
- **🚀 Deploy**: Render.com (auto-scale ready)
- **🔐 Config**: Pydantic Settings
- **📈 Monitoring**: Action Tracing in every response

---

## 🧪 Local Development (5 Minutes)
```bash
# Clone the repository
git clone <your-repo>
cd monday-bi-agent

# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env  # Add your MONDAY_API_KEY and BOARD_IDs

# Run the server
uvicorn main:app --reload
```
Test the API at: `http://localhost:8000/docs`

---

## 🏢 Enterprise Monday.com BI Agent
**Live - Self-Documenting - Production-Ready - Founder-First**  
*Deployed March 2026 - Always Fresh Data - Zero Hallucination*
