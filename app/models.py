from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    message: str
    history: List[dict] = []

class TraceStep(BaseModel):
    step: str
    description: str

class QueryResponse(BaseModel):
    answer: str
    trace: List[TraceStep]

class QueryPlan(BaseModel):
    metrics: List[str]
    sectors: List[str]
    time_periods: List[str]
    boards_needed: List[str]
    clarification_needed: bool = False
    clarification_message: Optional[str] = None
