import pytest
import json
import os
from fastapi.testclient import TestClient

class TestIntegrationWithRealData:
    """Интеграционные тесты с реальными данными"""
    
    def test_query_with_physics_questions(self, client):
        """Тест запросов по физике"""
        physics_questions = [
            "proton form factor measurements",
            "new baryon discoveries"
        ]
        
        for question in physics_questions[:1]:
            response = client.post("/query", json={
                "question": question,
                "top_k": 3,
                "strategy": "hybrid"
            })
            
            assert response.status_code == 200
            data = response.json()
            
            print(f"Question: {question}")
            print(f"Answer length: {len(data['answer'])}")
            print(f"Sources found: {len(data['sources'])}")
            print(f"Strategy used: {data.get('strategy', 'unknown')}")
            
            assert "answer" in data
            assert "sources" in data
            assert "context" in data
            assert len(data["sources"]) <= 3
    
    def test_different_rag_strategies_integration(self, client):
        """Интеграционное тестирование разных стратегий RAG"""
        question = "particle physics discoveries"
        
        strategies = ["basic", "hybrid", "adaptive"]
        
        for strategy in strategies:
            response = client.post("/query", json={
                "question": question,
                "top_k": 2,
                "strategy": strategy
            })
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["strategy"] == strategy
            assert len(data["answer"]) > 0