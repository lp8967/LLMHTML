import requests
import time
from benchmark_dataset import BenchmarkDataset

def run_benchmark():
    """Запуск бенчмарка RAG системы"""
    dataset = BenchmarkDataset()
    test_cases = dataset.get_test_cases()
    
    results = []
    
    for test in test_cases:
        print(f"Testing: {test['question'][:50]}...")
        
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/query",
            json={"question": test["question"], "top_k": 3, "strategy": "basic"}
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            retrieved_ids = [meta.get("paper_id", "") for meta in data.get("metadatas", [])]
            expected_ids = test["expected_documents"]
            correct = len(set(retrieved_ids) & set(expected_ids))
            precision = correct / len(retrieved_ids) if retrieved_ids else 0
            
            results.append({
                "test_id": test["id"],
                "question": test["question"],
                "precision": precision,
                "response_time": response_time,
                "found_documents": retrieved_ids,
                "expected_documents": expected_ids,
                "answer_length": len(data.get("answer", ""))
            })
    
    avg_precision = sum(r["precision"] for r in results) / len(results) if results else 0
    avg_time = sum(r["response_time"] for r in results) / len(results) if results else 0
    
    print("BENCHMARK RESULTS")
    print(f"Average Precision@3: {avg_precision:.2f}")
    print(f"Average Response Time: {avg_time:.2f}s")
    print(f"Tests Passed: {len([r for r in results if r['precision'] > 0])}/{len(results)}")
    
    return results

if __name__ == "__main__":
    run_benchmark()