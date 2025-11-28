import chromadb
from chromadb.config import Settings
import logging
from app.config import CHROMA_DB_PATH, COLLECTION_NAME

logger = logging.getLogger(__name__)

class VectorDatabase:
    def __init__(self):
        # ChromaDB САМ генерирует эмбеддинги!
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("Vector database initialized (using ChromaDB embeddings)")
    
    def add_documents(self, documents, metadatas=None, ids=None):
        try:
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            # ChromaDB САМ создаст эмбеддинги!
            self.collection.add(
                documents=documents,
                metadatas=metadatas or [{}] * len(documents),
                ids=ids
            )
            logger.info(f"Added {len(documents)} documents to database")
            
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            raise
    
    def search(self, query, top_k=3, filter_metadata=None):
        try:
            search_params = {
                "query_texts": [query],  # Chroma сам сделает эмбеддинг!
                "n_results": top_k
            }
            
            if filter_metadata:
                search_params["where"] = filter_metadata
            
            results = self.collection.query(**search_params)
            
            logger.info(f"Search found {len(results['documents'][0])} results")
            return results
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return {"documents": [], "metadatas": []}

vector_db = VectorDatabase()