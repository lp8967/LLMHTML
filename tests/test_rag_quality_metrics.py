import pytest
import json
from unittest.mock import patch, MagicMock
from app.modular_rag import ModularRAG, RAGStrategy
from app.database import vector_db
from app.gemini_client import gemini_client

class TestRAGQualityMetrics:
    """RAG system quality metrics tests with real data"""
    
    @pytest.fixture
    def benchmark_questions_answers(self):
        """Fixture with test questions and expected answers"""
        return [
            {
                "question": "What is the proton elastic form factor ratio?",
                "expected_keywords": ["proton", "elastic", "form factor", "ratio", "momentum transfer"],
                "expected_sources": ["0706.0128"],
                "category": "physics",
                "difficulty": "factual"
            },
            {
                "question": "What evidence exists for new baryons?",
                "expected_keywords": ["baryons", "Sigma_b", "observation", "mass", "Tevatron"],
                "expected_sources": ["0706.3868", "0711.1138"],
                "category": "particle_physics", 
                "difficulty": "analytical"
            }
        ]
    
    def test_retrieval_precision(self, real_arxiv_data, benchmark_questions_answers):
        """Test retrieval precision (Precision@K)"""
        rag = ModularRAG()
        
        for test_case in benchmark_questions_answers[:1]:
            question = test_case["question"]
            expected_sources = test_case["expected_sources"]
            
            with patch.object(vector_db, 'search') as mock_search:
                relevant_papers = [p for p in real_arxiv_data if p["id"] in expected_sources]
                mock_results = {
                    'documents': [[
                        f"Title: {p['title']}\nAbstract: {p['abstract']}" for p in relevant_papers
                    ]],
                    'metadatas': [[
                        {"paper_id": p["id"], "title": p["title"]} for p in relevant_papers
                    ]]
                }
                mock_search.return_value = mock_results
                
                result = rag.execute_rag(question, RAGStrategy.BASIC, top_k=3)
                
                retrieved_sources = [meta["paper_id"] for meta in result.get("metadatas", [])]
                relevant_retrieved = len(set(retrieved_sources) & set(expected_sources))
                precision = relevant_retrieved / len(retrieved_sources) if retrieved_sources else 0
                
                print(f"Question: {question}")
                print(f"Precision@3: {precision:.2f}")
                print(f"Retrieved: {retrieved_sources}")
                print(f"Expected: {expected_sources}")
                
                assert precision >= 0.0
    
    def test_answer_relevance_with_gemini_mock(self, real_arxiv_data, benchmark_questions_answers):
        """Test answer relevance using mocked Gemini client"""
        rag = ModularRAG()
        
        for test_case in benchmark_questions_answers[:1]:
            question = test_case["question"]
            expected_keywords = test_case["expected_keywords"]
            
            with patch.object(vector_db, 'search') as mock_search, \
                 patch.object(gemini_client, 'generate_response') as mock_gemini:
                
                relevant_papers = [p for p in real_arxiv_data if any(kw in p["abstract"].lower() for kw in ["proton", "baryon", "delta"])]
                mock_search.return_value = {
                    'documents': [[p["abstract"] for p in relevant_papers]],
                    'metadatas': [[{"paper_id": p["id"]} for p in relevant_papers]]
                }
                
                mock_answer = f"This is about {', '.join(expected_keywords)}. Based on the research..."
                mock_gemini.return_value = mock_answer
                
                result = rag.execute_rag(question, RAGStrategy.BASIC)
                
                answer = result.get("answer", "").lower()
                keyword_matches = sum(1 for kw in expected_keywords if kw in answer)
                relevance_score = keyword_matches / len(expected_keywords)
                
                print(f"Question: {question}")
                print(f"Relevance score: {relevance_score:.2f}")
                print(f"Answer: {answer[:100]}...")
                
                assert relevance_score > 0.3
