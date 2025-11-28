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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Academic Research Assistant",
    description="AI-powered research assistant using arXiv data and Gemini Pro",
    version="1.0.0"
)

# Статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/chat", response_class=HTMLResponse)
async def chat_interface(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/api/query")
async def query_documents(query_request: QueryRequest, session_id: str = "default"):
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
            # Все равно генерируем ответ, но честно говорим об ограничениях
            prompt = f"""
            A user asked: "{query_request.question}"
            
            CONTEXT: I couldn't find any relevant research papers in my database.
            
            Please provide a helpful but honest response explaining that 
            this might be outside my specialized academic database scope.
            """
            answer = gemini_client.generate_response(prompt)
        
        context_documents = rag_results['documents']
        metadatas = rag_results.get('metadatas', [])
        
        # 🟢 ДОБАВЬ ЭТУ ПРОВЕРКУ ДЛЯ БЕЗОПАСНОСТИ:
        # Безопасное извлечение метаданных из вложенной структуры
        if metadatas and isinstance(metadatas, list) and len(metadatas) > 0:
            if isinstance(metadatas[0], list):
                metadatas = metadatas[0]  # Извлекаем внутренний список
        else:
            metadatas = []
        
        formatted_context = format_context(context_documents, metadatas)
        
        conversation_history = conversation_memory.get_conversation_history(session_id, limit=3)
        if conversation_history:
            history_context = "\n\nPrevious conversation:\n" + "\n".join(
                [f"Q: {conv['question']}\nA: {conv['answer']}" for conv in reversed(conversation_history)]
            )
            formatted_context = history_context + "\n\nCurrent context:\n" + formatted_context
        
        prompt = f"""
        You are a helpful AI assistant for academic research. Answer based on the provided context.

        CONTEXT:
        {formatted_context}

        QUESTION: {query_request.question}

        ANSWER:
        """
        
        answer = gemini_client.generate_response(prompt)
        
        # 🟢 ИСПРАВЬ ЭТУ СТРОКУ:
        sources = format_sources([metadatas])  # Передаем как вложенный список
        
        response = {
            "answer": answer,
            "sources": sources,
            "context": context_documents,
            "strategy": rag_strategy.value,
            "processing_time": round(time.time() - start_time, 2)
        }
        
        conversation_memory.store_conversation(
            session_id, query_request.question, answer, sources
        )
        
        return JSONResponse(content=response)
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/conversation/{session_id}")
async def get_conversation(session_id: str, limit: int = 10):
    history = conversation_memory.get_conversation_history(session_id, limit)
    return {"session_id": session_id, "history": history}

@app.delete("/api/conversation/{session_id}")
async def clear_conversation(session_id: str):
    conversation_memory.clear_conversation(session_id)
    return {"message": f"Conversation history for {session_id} cleared"}

@app.get("/api/strategies")
async def get_available_strategies():
    return {
        "available_strategies": [strategy.value for strategy in RAGStrategy],
        "default_strategy": RAGStrategy.BASIC.value
    }

@app.get("/api/stats")
async def get_stats():
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
    
    # 🟢 БЕЗОПАСНАЯ ОБРАБОТКА: проверяем структуру данных
    if not metadatas:
        return sources
        
    # metadatas может быть: [[]] или [[meta1, meta2, meta3]] или [meta1, meta2]
    actual_metas = metadatas[0] if metadatas and isinstance(metadatas[0], list) else metadatas
    
    for i, meta in enumerate(actual_metas):
        if meta and isinstance(meta, dict):  # 🟢 Проверяем что это словарь
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

