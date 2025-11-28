import pytest
import time
import statistics
from fastapi.testclient import TestClient

class TestPerformanceBenchmark:
    """Тесты производительности системы"""
    
    @pytest.fixture
    def performance_test_cases(self):
        """Тестовые случаи для бенчмарка производительности"""
        return [
            {"question": "proton", "category": "simple", "expected_max_time": 5.0},
            {"question": "baryon discoveries at Tevatron", "category": "medium", "expected_max_time": 8.0},
            {"question": "evidence for parity doublet delta resonances in photoproduction", "category": "complex", "expected_max_time": 12.0}
        ]
    
    def test_response_time_benchmark(self, client, performance_test_cases):
        """Бенчмарк времени ответа для разных типов вопросов"""
        results = {}
        
        for test_case in performance_test_cases:
            question = test_case["question"]
            category = test_case["category"]
            
            times = []
            for i in range(2):
                start_time = time.time()
                response = client.post("/query", json={
                    "question": question,
                    "top_k": 3,
                    "strategy": "basic"
                })
                end_time = time.time()
                
                assert response.status_code == 200
                times.append(end_time - start_time)
            
            avg_time = statistics.mean(times)
            max_time = max(times)
            
            results[category] = {
                "average_time": avg_time,
                "max_time": max_time,
                "min_time": min(times),
                "question": question
            }
            
            print(f"{category.upper()} Question: '{question}'")
            print(f"Average time: {avg_time:.2f}s, Max: {max_time:.2f}s")
            
            assert max_time < test_case["expected_max_time"]
        
        print("PERFORMANCE SUMMARY:")
        for category, data in results.items():
            print(f"{category}: {data['average_time']:.2f}s avg, {data['max_time']:.2f}s max")