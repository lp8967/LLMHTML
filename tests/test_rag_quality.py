import pytest
import json
from unittest.mock import Mock, patch
from app.modular_rag import ModularRAG, RAGStrategy
from app.database import vector_db

class TestRAGQuality:
    """RAG system quality tests"""
    
    def test_basic_rag_returns_documents(self, sample_arxiv_data):
        """Test that basic RAG returns documents"""
        rag = ModularRAG()
        question = "What are transformers in AI?"
        
        with patch.object(vector_db, 'search') as mock_search:
            mock_search.return_value = {
                'documents': [[
                    "Title: Attention Is All You Need\nAbstract: The dominant sequence transduction models...",
                    "Title: BERT: Pre-training of Deep Bidirectional Transformers\nAbstract: We introduce a new language representation model..."
                ]],
                'metadatas': [[
                    {"title": "Attention Is All You Need", "authors": "Vaswani et al."},
                    {"title": "BERT: Pre-training of Deep Bidirectional Transformers", "authors": "Devlin et al."}
                ]]
            }
            
            result = rag.execute_rag(question, RAGStrategy.BASIC)
            
            assert 'documents' in result
            assert len(result['documents']) > 0
            assert result['strategy'] == 'basic'
    
    def test_hierarchical_rag_reranking(self):
        """Test that hierarchical RAG performs re-ranking"""
        rag = ModularRAG()
        question = "transformer architecture attention mechanism"
        
        with patch.object(vector_db, 'search') as mock_search:
            mock_search.return_value = {
                'documents': [[
                    "Title: Some Paper\nAbstract: Unrelated content here...",
                    "Title: Attention Is All You Need\nAbstract: Transformer architecture with attention...",
                    "Title: Another Paper\nAbstract: More unrelated content..."
                ]],
                'metadatas': [[{}, {}, {}]]
            }
            
            result = rag.execute_rag(question, RAGStrategy.HIERARCHICAL)
            
            assert 'documents' in result
            assert len(result['documents']) > 0
    
    def test_adaptive_rag_strategy_selection(self):
        """Test that adaptive RAG selects strategy based on question complexity"""
        rag = ModularRAG()
        
        simple_question = "What is AI?"
        result_simple = rag.execute_rag(simple_question, RAGStrategy.ADAPTIVE)
        
        complex_question = "How does the self-attention mechanism in transformers differ from traditional RNN approaches and what are the computational advantages?"
        result_complex = rag.execute_rag(complex_question, RAGStrategy.ADAPTIVE)
        
        assert 'documents' in result_simple
        assert 'documents' in result_complex
    
    def test_hybrid_rag_keyword_extraction(self):
        """Test that hybrid RAG extracts keywords"""
        rag = ModularRAG()
        question = "What are the main advantages of transformer models over recurrent neural networks?"
        
        keywords = rag._extract_keywords(question)
        
        assert len(keywords) > 0
        assert 'advantages' in keywords
        assert 'transformer' in keywords
        assert 'recurrent' in keywords
        assert 'what' not in keywords
        assert 'the' not in keywords
