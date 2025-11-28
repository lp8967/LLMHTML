from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class RAGStrategy(str, Enum):
    BASIC = "basic"
    HIERARCHICAL = "hierarchical"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"

class QueryRequest(BaseModel):
    question: str = Field(..., min_length=1, description="Research question")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of results (1-10)")
    strategy: RAGStrategy = Field(default=RAGStrategy.BASIC, description="RAG strategy to use")

class RAGStrategyRequest(BaseModel):
    question: str
    top_k: int = 3
    strategy: RAGStrategy = RAGStrategy.BASIC
    session_id: str = "default"

class QueryResponse(BaseModel):
    answer: str
    sources: List[str]
    context: List[str]
    strategy: str = "basic"
    processing_time: Optional[float] = None

class ConversationHistory(BaseModel):
    session_id: str
    history: List[dict]

class MetricsResponse(BaseModel):
    average_response_time: float
    success_rate: float
    total_requests: int
    error_count: int