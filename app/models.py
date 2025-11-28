from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class RAGStrategy(str, Enum):
    """
    Enumeration of available RAG (Retrieval-Augmented Generation) strategies.
    Defines different retrieval and reasoning modes.
    """
    BASIC = "basic"
    HIERARCHICAL = "hierarchical"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"


class QueryRequest(BaseModel):
    """
    Request model for sending a research question to the RAG system.

    Attributes:
        question (str): The user's research question.
        top_k (int): Number of retrieved documents.
        strategy (RAGStrategy): RAG retrieval strategy to use.
    """
    question: str = Field(..., min_length=1, description="Research question")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of results (1-10)")
    strategy: RAGStrategy = Field(default=RAGStrategy.BASIC, description="RAG strategy to use")


class RAGStrategyRequest(BaseModel):
    """
    Request model for explicitly specifying a RAG strategy for a query.

    Attributes:
        question (str): Research question.
        top_k (int): Number of documents to retrieve.
        strategy (RAGStrategy): RAG strategy to use.
        session_id (str): Conversation session identifier.
    """
    question: str
    top_k: int = 3
    strategy: RAGStrategy = RAGStrategy.BASIC
    session_id: str = "default"


class QueryResponse(BaseModel):
    """
    Response model returned after processing a RAG query.

    Attributes:
        answer (str): LLM-generated answer.
        sources (List[str]): List of sources used for reasoning.
        context (List[str]): Retrieved context documents.
        strategy (str): Applied RAG strategy.
        processing_time (Optional[float]): Execution time in seconds.
    """
    answer: str
    sources: List[str]
    context: List[str]
    strategy: str = "basic"
    processing_time: Optional[float] = None


class ConversationHistory(BaseModel):
    """
    Response model containing a conversation history for a given session.
    """
    session_id: str
    history: List[dict]


class MetricsResponse(BaseModel):
    """
    Response model for API performance metrics.

    Attributes:
        average_response_time (float): Average processing time.
        success_rate (float): Successful request ratio.
        total_requests (int): Total number of processed requests.
        error_count (int): Number of failed requests.
    """
    average_response_time: float
    success_rate: float
    total_requests: int
    error_count: int
