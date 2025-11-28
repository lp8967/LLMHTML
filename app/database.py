import chromadb
from chromadb.config import Settings
import logging
from app.config import CHROMA_DB_PATH, COLLECTION_NAME

logger = logging.getLogger(__name__)

class VectorDatabase:
    """
    A wrapper class for managing a ChromaDB persistent vector database.
    Handles initialization, document insertion, and vector-based search.
    """

    def __init__(self):
        """
        Initialize the ChromaDB client and collection.
        ChromaDB automatically generates embeddings for documents.
        """
        self.client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}  # cosine distance metric for similarity search
        )
        logger.info("Vector database initialized (using ChromaDB embeddings)")
    
    def add_documents(self, documents, metadatas=None, ids=None):
        """
        Add documents to the ChromaDB collection.

        Parameters:
            documents (list[str]): List of documents to insert.
            metadatas (list[dict], optional): Metadata entries associated with documents.
            ids (list[str], optional): Unique IDs for documents. Auto-generated if omitted.
        """
        try:
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]

            # ChromaDB automatically generates embeddings for the input documents
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
        """
        Perform a similarity search in the vector database.

        Parameters:
            query (str): Input text used to compute the query embedding.
            top_k (int): Number of search results to return.
            filter_metadata (dict, optional): Optional filtering of records by metadata.

        Returns:
            dict: Search results including documents and metadata.
        """
        try:
            search_params = {
                "query_texts": [query],  # ChromaDB generates the query embedding
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
