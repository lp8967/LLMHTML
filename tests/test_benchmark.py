import pytest
import time
from app.modular_rag import ModularRAG, RAGStrategy

class TestRAGBenchmark:
    """Performance tests for the RAG system."""

    @pytest.fixture
    def benchmark_questions(self):
        """
        Fixture providing a list of benchmark questions for RAG performance testing.
        """
        return [
            "What is machine learning?",
            "Explain transformer architecture",
            "What are the differences between CNN and RNN?",
            "How does attention mechanism work?",
            "What is reinforcement learning?"
        ]

    def test_response_time_basic_rag(self, benchmark_questions):
        """
        Test response time for basic RAG strategy.
        """
        rag = ModularRAG()

        for question in benchmark_questions[:2]:
            start_time = time.time()
            result = rag.execute_rag(question, RAGStrategy.BASIC, top_k=3)
            end_time = time.time()

            response_time = end_time - start_time
            print(f"Basic RAG - Question: '{question}' - Time: {response_time:.2f}s")

            assert response_time < 10.0  # Ensure response time is under 10 seconds
            assert 'documents' in result  # Ensure the result contains documents

    def test_compare_strategies_performance(self, benchmark_questions):
        """
        Compare performance of different RAG strategies for the same question.
        """
        rag = ModularRAG()
        question = benchmark_questions[0]

        strategies = [RAGStrategy.BASIC, RAGStrategy.HYBRID, RAGStrategy.ADAPTIVE]
        performance_data = {}

        for strategy in strategies:
            start_time = time.time()
            result = rag.execute_rag(question, strategy, top_k=3)
            end_time = time.time()

            performance_data[strategy.value] = {
                'time': end_time - start_time,
                'documents_found': len(result.get('documents', [])),
                'strategy_used': result.get('strategy', 'unknown')
            }

        # Print performance summary
        print("Performance Comparison:")
        for strategy, data in performance_data.items():
            print(f"{strategy}: {data['time']:.2f}s, docs: {data['documents_found']}")

        # Assert all strategies respond within reasonable time
        for strategy, data in performance_data.items():
            assert data['time'] < 15.0
