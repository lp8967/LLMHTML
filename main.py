from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import time
import logging
from typing import Dict, Any

from app.config import TOP_K_RESULTS
from app.database import vector_db
from app.models import QueryRequest, RAGStrategy
from app.gemini_client import gemini_client
from app.modular_rag import modular_rag
from app.memory import conversation_memory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI application
app = FastAPI(
    title="Academic Research Assistant",
    description="AI-powered research assistant using arXiv data and Gemini Pro",
    version="1.0.0"
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Render the main landing page."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    """Render the chat interface page."""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/api/query")
async def query_documents(query_request: QueryRequest, session_id: str = "default"):
    """
    Handle user query:
    - Retrieve relevant documents using the selected RAG strategy
    - Generate answer with Gemini
    - Store conversation in memory
    """
    start_time = time.time()
    
    try:
        logger.info(f"Processing question: {query_request.question}")
        
        # Ensure strategy is of type RAGStrategy
        rag_strategy = query_request.strategy
        if isinstance(rag_strategy, str):
            rag_strategy = RAGStrategy(rag_strategy.lower())
            
        # Execute RAG search
        rag_results = modular_rag.execute_rag(
            question=query_request.question,
            strategy=rag_strategy,
            top_k=query_request.top_k
        )
        
        if not rag_results['documents']:
            # Generate answer even if no documents are found
            prompt = f"""
            A user asked: "{query_request.question}"
            
            CONTEXT: No relevant research papers found.
            
            Provide a helpful answer indicating this may be outside the academic database scope.
            """
            answer = gemini_client.generate_response(prompt)
        
        context_documents = rag_results['documents']
        metadatas = rag_results.get('metadatas', [])
        
        # Safely extract metadata from nested structure
        if metadatas and isinstance(metadatas, list) and len(metadatas) > 0:
            if isinstance(metadatas[0], list):
                metadatas = metadatas[0]
        else:
            metadatas = []
        
        formatted_context = format_context(context_documents, metadatas)
        
        # Include recent conversation history if available
        conversation_history = conversation_memory.get_conversation_history(session_id, limit=3)
        if conversation_history:
            history_context = "\n\nPrevious conversation:\n" + "\n".join(
                [f"Q: {conv['question']}\nA: {conv['answer']}" for conv in reversed(conversation_history)]
            )
            formatted_context = history_context + "\n\nCurrent context:\n" + formatted_context
        
        # Generate answer using LLM
        prompt = f"""
        You are a helpful AI assistant for academic research. Answer based on the provided context.

        CONTEXT:
        {formatted_context}

        QUESTION: {query_request.question}

        ANSWER:
        """
        answer = gemini_client.generate_response(prompt)
        
        # Format sources safely
        sources = format_sources([metadatas])
        
        # Construct response
        response = {
            "answer": answer,
            "sources": sources,
            "context": context_documents,
            "strategy": rag_strategy.value,
            "processing_time": round(time.time() - start_time, 2)
        }
        
        # Store conversation in memory
        conversation_memory.store_conversation(
            session_id, query_request.question, answer, sources
        )
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/conversation/{session_id}")
async def get_conversation(session_id: str, limit: int = 10):
    """Retrieve conversation history for a session."""
    history = conversation_memory.get_conversation_history(session_id, limit)
    return {"session_id": session_id, "history": history}

@app.delete("/api/conversation/{session_id}")
async def clear_conversation(session_id: str):
    """Clear conversation history for a session."""
    conversation_memory.clear_conversation(session_id)
    return {"message": f"Conversation history for {session_id} cleared"}

@app.get("/api/strategies")
async def get_available_strategies():
    """Return all available RAG strategies."""
    return {
        "available_strategies": [strategy.value for strategy in RAGStrategy],
        "default_strategy": RAGStrategy.BASIC.value
    }

@app.get("/api/stats")
async def get_stats():
    """Return vector database and model statistics."""
    try:
        collection_stats = vector_db.collection.count()
        return {
            "total_documents": collection_stats,
            "embedding_model": "ChromaDB Default",
            "llm_model": "Gemini Pro"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Academic Research Assistant"}

def format_context(documents, metadatas):
    """Format document context for prompt generation."""
    formatted = []
    for i, (doc, meta) in enumerate(zip(documents, metadatas)):
        source_info = f"[Source {i+1}]"
        if meta and 'title' in meta:
            source_info += f" {meta['title']}"
        formatted.append(f"{source_info}\n{doc}")
    return "\n\n".join(formatted)

def format_sources(metadatas):
    """Format sources for response output."""
    sources = []
    
    if not metadatas:
        return sources
        
    # Handle possible nested structures
    actual_metas = metadatas[0] if metadatas and isinstance(metadatas[0], list) else metadatas
    
    for i, meta in enumerate(actual_metas):
        if meta and isinstance(meta, dict):
            source = f"Source {i+1}: {meta.get('title', 'Unknown title')}"
            if meta.get('authors'):
                source += f" by {meta['authors']}"
            sources.append(source)
        else:
            sources.append(f"Source {i+1}")
    
    return sources

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
