from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import time
from typing import Dict, Any

from app.config import TOP_K_RESULTS
from app.database import vector_db
from app.models import QueryRequest, QueryResponse, RAGStrategyRequest
from app.prompts import SYSTEM_PROMPT_TEMPLATE
from app.gemini_client import gemini_client
from app.modular_rag import modular_rag, RAGStrategy
from app.memory import conversation_memory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate Limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="Academic Research Assistant - Gemini",
    description="AI-powered research assistant using arXiv data and Gemini Pro",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Метрики производительности
class PerformanceMetrics:
    def __init__(self):
        self.request_times = []
        self.error_count = 0
        self.success_count = 0
    
    def record_request(self, duration: float, success: bool = True):
        self.request_times.append(duration)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        
        if len(self.request_times) > 100:
            self.request_times.pop(0)
    
    def get_metrics(self) -> Dict[str, Any]:
        if not self.request_times:
            return {"average_response_time": 0, "success_rate": 1.0}
        
        avg_time = sum(self.request_times) / len(self.request_times)
        total_requests = self.success_count + self.error_count
        success_rate = self.success_count / total_requests if total_requests > 0 else 1.0
        
        return {
            "average_response_time": round(avg_time, 2),
            "success_rate": round(success_rate, 2),
            "total_requests": total_requests,
            "error_count": self.error_count
        }

metrics = PerformanceMetrics()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    metrics.record_request(process_time, success=response.status_code < 400)
    
    return response

@app.get("/")
async def root():
    return {
        "message": "Academic Research Assistant API",
        "version": "1.0.0", 
        "llm": "Gemini Pro",
        "data_source": "arXiv 2020",
        "features": ["modular_rag", "conversation_memory", "rate_limiting"]
    }

@app.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute")
async def query_documents(
    request: Request,
    query_request: QueryRequest,
    session_id: str = "default"
):
    start_time = time.time()
    
    try:
        logger.info(f"Processing question: {query_request.question}")
        
        rag_strategy = query_request.strategy

        if isinstance(rag_strategy, str):
            rag_strategy = RAGStrategy(rag_strategy.lower())
            
        rag_results = modular_rag.execute_rag(
            question=query_request.question,
            strategy=rag_strategy,
            top_k=query_request.top_k
        )
        
        if not rag_results['documents']:
            response = QueryResponse(
                answer="I couldn't find any relevant research papers in my database to answer your question. Please try rephrasing or asking about a different topic.",
                sources=[],
                context=[],
                strategy=rag_strategy.value
            )
            
            conversation_memory.store_conversation(
                session_id, query_request.question, 
                response.answer, response.sources
            )
            return response
        
        context_documents = rag_results['documents']
        metadatas = rag_results.get('metadatas', [])
        
        formatted_context = format_context(context_documents, metadatas)
        
        conversation_history = conversation_memory.get_conversation_history(session_id, limit=3)
        if conversation_history:
            history_context = "\n\nPrevious conversation:\n" + "\n".join(
                [f"Q: {conv['question']}\nA: {conv['answer']}" for conv in reversed(conversation_history)]
            )
            formatted_context = history_context + "\n\nCurrent context:\n" + formatted_context
        
        prompt = SYSTEM_PROMPT_TEMPLATE.format(
            context=formatted_context,
            question=query_request.question
        )
        
        answer = gemini_client.generate_response(prompt)
        
        sources = format_sources(metadatas)
        
        response = QueryResponse(
            answer=answer,
            sources=sources,
            context=context_documents,
            strategy=rag_strategy.value,
            processing_time=round(time.time() - start_time, 2)
        )
        
        conversation_memory.store_conversation(
            session_id, query_request.question, answer, sources
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        metrics.record_request(time.time() - start_time, success=False)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/query/strategy", response_model=QueryResponse)
@limiter.limit("10/minute")
async def query_with_strategy(
    request: Request,
    strategy_request: RAGStrategyRequest
):
    query_request = QueryRequest(
        question=strategy_request.question,
        top_k=strategy_request.top_k
    )
    return await query_documents(
        request, query_request, strategy_request.session_id
    )

@app.get("/conversation/{session_id}")
async def get_conversation(session_id: str, limit: int = 10):
    history = conversation_memory.get_conversation_history(session_id, limit)
    return {"session_id": session_id, "history": history}

@app.delete("/conversation/{session_id}")
async def clear_conversation(session_id: str):
    conversation_memory.clear_conversation(session_id)
    return {"message": f"Conversation history for {session_id} cleared"}

@app.get("/metrics")
async def get_metrics():
    return metrics.get_metrics()

@app.get("/strategies")
async def get_available_strategies():
    return {
        "available_strategies": [strategy.value for strategy in RAGStrategy],
        "default_strategy": RAGStrategy.BASIC.value
    }

@app.get("/stats")
async def get_stats():
    try:
        collection_stats = vector_db.collection.count()
        return {
            "total_documents": collection_stats,
            "embedding_model": "all-MiniLM-L6-v2",
            "llm_model": "Gemini Pro"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Academic Research Assistant"}

def format_context(documents, metadatas):
    formatted = []
    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        source_info = f"[Source {i+1}]"
        if meta and 'title' in meta:
            source_info += f" {meta['title']}"
        formatted.append(f"{source_info}\n{doc}")
    return "\n\n".join(formatted)

def format_sources(metadatas):
    sources = []
    for i, meta in enumerate(metadatas):
        if meta:
            source = f"Source {i+1}: {meta.get('title', 'Unknown title')}"
            if meta.get('authors'):
                source += f" by {meta['authors']}"
            sources.append(source)
        else:
            sources.append(f"Source {i+1}")
    return sources