import pytest
import json
import os
from fastapi.testclient import TestClient

class TestIntegrationWithRealData:
    """Integration tests using real dataset queries."""

    def test_query_with_physics_questions(self, client):
        """
        Test queries related to physics topics and verify responses.
        """
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

            # Validate response structure
            assert "answer" in
