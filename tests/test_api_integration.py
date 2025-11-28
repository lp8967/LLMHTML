import pytest
from fastapi.testclient import TestClient

class TestAPIIntegration:
    """Integration tests for the FastAPI endpoints of the Academic Research Assistant API."""

    def test_root_endpoint(self, client: TestClient):
        """
        Test the root endpoint '/' to ensure the API is reachable.
        """
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Academic Research Assistant API" in data["message"]

    def test_health_check(self, client: TestClient):
        """
        Test the health check endpoint '/health'.
        """
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_query_endpoint_basic(self, client: TestClient):
        """
        Test the main query endpoint '/query' with a basic question.
        """
        test_data = {
            "question": "What is machine learning?",
            "top_k": 2
        }

        response = client.post("/query", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "context" in data

    def test_query_with_different_strategies(self, client: TestClient):
        """
        Test the '/query' endpoint with all available RAG strategies.
        """
        strategies = ["basic", "hierarchical", "hybrid", "adaptive"]

        for strategy in strategies:
            test_data = {
                "question": "Explain transformer models",
                "top_k": 3,
                "strategy": strategy
            }

            response = client.post("/query", json=test_data)
            assert response.status_code == 200
            data = response.json()
            assert data["strategy"] == strategy

    def test_conversation_endpoints(self, client: TestClient):
        """
        Test conversation history management endpoints.
        """
        session_id = "test_session_123"

        # Clear conversation history
        response = client.delete(f"/conversation/{session_id}")
        assert response.status_code == 200

        # Retrieve empty conversation history
        response = client.get(f"/conversation/{session_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert len(data["history"]) == 0

    def test_metrics_endpoint(self, client: TestClient):
        """
        Test the '/metrics' endpoint to ensure performance metrics are returned.
        """
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.json()
        assert "average_response_time" in data
        assert "success_rate" in data
        assert "total_requests" in data

    def test_strategies_endpoint(self, client: TestClient):
        """
        Test the '/strategies' endpoint to check available RAG strategies.
        """
        response = client.get("/strategies")
        assert response.status_code == 200
        data = response.json()
        assert "available_strategies" in data
        assert "default_strategy" in data
        assert len(data["available_strategies"]) == 4
