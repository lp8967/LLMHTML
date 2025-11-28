from typing import List, Dict, Any
import redis
import json
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ConversationMemory:
    """
    Manages conversation history and embedding cache using Redis when available,
    or an in-memory fallback when Redis is not accessible.
    """

    def __init__(self, redis_url: str = None):
        """
        Initialize the conversation memory storage.
        If a Redis URL is provided, attempts to connect to Redis.
        Falls back to in-memory storage if Redis is unavailable.
        """
        self.redis_client = None

        if redis_url:
            try:
                self.redis_client = redis.Redis.from_url(redis_url)
                self.redis_client.ping()
                logger.info("Redis connected successfully")
            except Exception as e:
                logger.warning(f"Redis connection failed: {e}. Using in-memory storage.")
                self.redis_client = None
        
        self._memory_cache = {}
        self._conversation_history = {}
    
    def cache_embedding(self, key: str, embedding: List[float], ttl: int = 3600):
        """
        Store an embedding vector in cache (Redis or in-memory).
        
        Parameters:
            key (str): Unique cache key.
            embedding (List[float]): Embedding vector.
            ttl (int): Time-to-live in seconds.
        """
        try:
            if self.redis_client:
                self.redis_client.setex(
                    f"embedding:{key}",
                    timedelta(seconds=ttl),
                    json.dumps(embedding)
                )
            else:
                self._memory_cache[f"embedding:{key}"] = {
                    "data": embedding,
                    "expires": datetime.now() + timedelta(seconds=ttl)
                }
        except Exception as e:
            logger.error(f"Cache set failed: {e}")
    
    def get_cached_embedding(self, key: str) -> List[float]:
        """
        Retrieve an embedding from cache.

        Parameters:
            key (str): Cache key for the embedding.

        Returns:
            List[float] | None: Cached embedding or None if not found or expired.
        """
        try:
            if self.redis_client:
                cached = self.redis_client.get(f"embedding:{key}")
                return json.loads(cached) if cached else None
            else:
                cache_item = self._memory_cache.get(f"embedding:{key}")
                if cache_item and cache_item["expires"] > datetime.now():
                    return cache_item["data"]
                return None
        except Exception as e:
            logger.error(f"Cache get failed: {e}")
            return None
    
    def store_conversation(self, session_id: str, question: str, answer: str, sources: List[str]):
        """
        Store a QA pair in the conversation history for a given session.
        Keeps only the last 10 messages.
        """
        conversation = {
            "timestamp": datetime.now().isoformat(),
            "question": question,
            "answer": answer,
            "sources": sources
        }
        
        try:
            if self.redis_client:
                self.redis_client.lpush(f"conversation:{session_id}", json.dumps(conversation))
                self.redis_client.ltrim(f"conversation:{session_id}", 0, 9)
            else:
                if session_id not in self._conversation_history:
                    self._conversation_history[session_id] = []
                self._conversation_history[session_id].insert(0, conversation)
                self._conversation_history[session_id] = self._conversation_history[session_id][:10]
        except Exception as e:
            logger.error(f"Conversation storage failed: {e}")
    
    def get_conversation_history(self, session_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve conversation history for a session.

        Parameters:
            session_id (str): Conversation session identifier.
            limit (int): Maximum number of messages to return.

        Returns:
            List[Dict[str, Any]]: List of conversation records.
        """
        try:
            if self.redis_client:
                history = self.redis_client.lrange(f"conversation:{session_id}", 0, limit - 1)
                return [json.loads(item) for item in reversed(history)]
            else:
                return self._conversation_history.get(session_id, [])[:limit]
        except Exception as e:
            logger.error(f"Conversation retrieval failed: {e}")
            return []
    
    def clear_conversation(self, session_id: str):
        """
        Clear conversation history for a specific session.

        Parameters:
            session_id (str): Identifier of the session to clear.
        """
        try:
            if self.redis_client:
                self.redis_client.delete(f"conversation:{session_id}")
            else:
                self._conversation_history.pop(session_id, None)
        except Exception as e:
            logger.error(f"Conversation clear failed: {e}")


conversation_memory = ConversationMemory()
