from enum import Enum
from typing import List, Dict, Any
import logging
from app.database import vector_db
from app.config import TOP_K_RESULTS

logger = logging.getLogger(__name__)


class RAGStrategy(Enum):
    """
    Enumeration of Retrieval-Augmented Generation strategies.
    """
    BASIC = "basic"
    HIERARCHICAL = "hierarchical"
    HYBRID = "hybrid"
    ADAPTIVE = "adaptive"


class ModularRAG:
    """
    Modular implementation of multiple RAG strategies.
    Allows switching between different retrieval workflows.
    """

    def __init__(self):
        """
        Initialize strategy mapping for dynamic dispatch.
        """
        self.strategies = {
            RAGStrategy.BASIC: self._basic_rag,
            RAGStrategy.HIERARCHICAL: self._hierarchical_rag,
            RAGStrategy.HYBRID: self._hybrid_rag,
            RAGStrategy.ADAPTIVE: self._adaptive_rag
        }
    
    def execute_rag(self, question: str, strategy: RAGStrategy = RAGStrategy.BASIC, **kwargs):
        """
        Execute a selected RAG strategy.

        Args:
            question (str): User query.
            strategy (RAGStrategy): Selected retrieval strategy.
            kwargs: Additional parameters for specific strategies.

        Returns:
            Dict[str, Any]: Retrieved documents and metadata.

        Raises:
            ValueError: If an unknown strategy is provided.
        """
        if isinstance(strategy, str):
            strategy = RAGStrategy(strategy.lower())
        
        if strategy not in self.strategies:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        logger.info(f"Executing {strategy.value} RAG for: {question}")
        
        # Special handling for hierarchical RAG parameters
        if strategy == RAGStrategy.HIERARCHICAL:
            return self._hierarchical_rag(
                question,
                broad_top_k=10,
                final_top_k=kwargs.get('top_k', 3)
            )
        
        return self.strategies[strategy](question, **kwargs)
    
    def _basic_rag(self, question: str, top_k: int = TOP_K_RESULTS) -> Dict[str, Any]:
        """
        Perform standard semantic vector search.
        """
        results = vector_db.search(question, top_k=top_k)
        return {
            "documents": results['documents'][0] if results['documents'] else [],
            "metadatas": results['metadatas'][0] if results['metadatas'] else [],
            "strategy": "basic",
            "search_type": "semantic"
        }
    
    def _hierarchical_rag(self, question: str, broad_top_k: int = 10, final_top_k: int = 3) -> Dict[str, Any]:
        """
        Two-stage hierarchical RAG:
        1. Broad retrieval
        2. Reranking and narrowing results
        """
        broad_results = vector_db.search(question, top_k=broad_top_k)
        
        if not broad_results['documents']:
            return {
                "documents": [],
                "metadatas": [],
                "strategy": "hierarchical",
                "search_type": "two_stage"
            }
        
        reranked_docs = self._rerank_documents(question, broad_results['documents'][0])
        
        final_docs = reranked_docs[:final_top_k]
        final_metadatas = broad_results['metadatas'][0][:final_top_k] if broad_results['metadatas'] else []
        
        return {
            "documents": final_docs,
            "metadatas": final_metadatas,
            "strategy": "hierarchical",
            "search_type": "two_stage"
        }
    
    def _hybrid_rag(self, question: str, top_k: int = TOP_K_RESULTS, alpha: float = 0.5) -> Dict[str, Any]:
        """
        Hybrid RAG combining semantic and keyword-based search.
        """
        semantic_results = vector_db.search(question, top_k=top_k)
        keywords = self._extract_keywords(question)
        
        if keywords:
            keyword_results = self._keyword_search(keywords, top_k=top_k)
            combined_results = self._merge_results(semantic_results, keyword_results, alpha)
            return {
                **combined_results,
                "strategy": "hybrid",
                "search_type": "semantic_keyword"
            }
        
        return {
            **semantic_results,
            "strategy": "hybrid",
            "search_type": "semantic_only"
        }
    
    def _adaptive_rag(self, question: str, top_k: int = TOP_K_RESULTS) -> Dict[str, Any]:
        """
        Adaptive RAG that selects a strategy based on question complexity.
        """
        question_complexity = self._assess_question_complexity(question)
        
        if question_complexity == "simple":
            return self._basic_rag(question, top_k)
        elif question_complexity == "medium":
            return self._hybrid_rag(question, top_k)
        else:
            return self._hierarchical_rag(question, broad_top_k=15, final_top_k=top_k)
    
    def _rerank_documents(self, question: str, documents: List[str]) -> List[str]:
        """
        Simple keyword-overlap reranker.
        """
        scored_docs = []
        for doc in documents:
            score = sum(1 for word in question.lower().split() if word in doc.lower())
            scored_docs.append((score, doc))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs]
    
    def _extract_keywords(self, question: str) -> List[str]:
        """
        Extract keywords from the user query by filtering stop words.
        """
        stop_words = {"what", "is", "the", "a", "an", "in", "on", "at", "to", "for", "of", "with", "by"}
        words = question.lower().split()
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        return keywords[:5]
    
    def _keyword_search(self, keywords: List[str], top_k: int) -> Dict[str, Any]:
        """
        Perform keyword-based metadata search.
        """
        try:
            filter_conditions = {
                "$or": [
                    {"title": {"$in": keywords}} for keyword in keywords
                ] + [
                    {"abstract": {"$in": keywords}} for keyword in keywords
                ]
            }
            
            dummy_query = " ".join(keywords)
            results = vector_db.search(dummy_query, top_k=top_k, filter_metadata=filter_conditions)
            return results
            
        except Exception as e:
            logger.warning(f"Keyword search failed: {e}")
            return {"documents": [], "metadatas": []}
    
    def _merge_results(self, results1: Dict, results2: Dict, alpha: float) -> Dict[str, Any]:
        """
        Merge semantic and keyword-based search results, removing duplicates.
        """
        docs1 = results1.get('documents', [[]])[0]
        docs2 = results2.get('documents', [[]])[0]
        metas1 = results1.get('metadatas', [[]])[0]
        metas2 = results2.get('metadatas', [[]])[0]
        
        seen_docs = set()
        merged_docs = []
        merged_metas = []
        
        for doc, meta in zip(docs1, metas1):
            if doc not in seen_docs:
                seen_docs.add(doc)
                merged_docs.append(doc)
                merged_metas.append(meta)
        
        for doc, meta in zip(docs2, metas2):
            if doc not in seen_docs and len(merged_docs) < len(docs1) + len(docs2):
                seen_docs.add(doc)
                merged_docs.append(doc)
                merged_metas.append(meta)
        
        return {
            "documents": [merged_docs],
            "metadatas": [merged_metas]
        }
    
    def _assess_question_complexity(self, question: str) -> str:
        """
        Determine question complexity based on linguistic indicators.
        """
        question_lower = question.lower()
        
        simple_indicators = {"what", "who", "when", "where"}
        complex_indicators = {"how", "why", "compare", "difference", "advantages", "disadvantages"}
        
        if any(indicator in question_lower for indicator in complex_indicators):
            return "complex"
        elif any(indicator in question_lower for indicator in simple_indicators):
            return "medium"
        return "simple"


modular_rag = ModularRAG()
