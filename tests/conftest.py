import pytest
import os
import sys
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, MagicMock

# Add project root to sys.path to allow imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.database import vector_db


@pytest.fixture
def client():
    """
    Fixture for creating a FastAPI test client.
    
    Returns:
        TestClient: FastAPI test client instance
    """
    return TestClient(app)


@pytest.fixture
def real_arxiv_data():
    """
    Fixture providing sample real arXiv paper data.
    
    Returns:
        List[Dict]: List of sample arXiv paper dictionaries
    """
    return [
        {
            "id": "0706.0128",
            "title": "The Proton Elastic Form Factor Ratio at Low Momentum Transfer",
            "authors": "G. Ron, J. Glister, B. Lee, et al. (The Jefferson Lab Hall A Collaboration)",
            "abstract": (
                "High precision measurements of the proton elastic form factor ratio "
                "have been made at four-momentum transfers, Q^2, between 0.2 and 0.5 GeV^2. "
                "The new data, while consistent with previous results, clearly show a ratio less than unity "
                "and significant differences from the central values of several recent phenomenological fits. "
                "By combining the new form-factor ratio data with an existing cross-section measurement, "
                "one finds that in this Q^2 range the deviation from unity is primarily due to GEp being smaller than the dipole parameterization."
            ),
            "categories": "nucl-ex"
        },
        {
            "id": "0706.3868",
            "title": "First Observation of Heavy Baryons Sigma_b and Sigma_b*",
            "authors": "CDF Collaboration: T. Aaltonen, et al",
            "abstract": (
                "We report an observation of new bottom baryons produced in proton-antiproton collisions at the Tevatron. "
                "Using 1.1 fb^{-1} of data collected by the CDF II detector, we observe four Lambda_b^0 pi^{+-} resonances "
                "in the fully reconstructed decay mode Lambda_b^0 -> Lambda_c^+ pi^-, where Lambda_c^+ -> p K^- pi^+. "
                "We interpret these states as the Sigma_b^{(*)+-} baryons and measure the following masses: "
                "m_{Sigma_b^+} = 5807.8^{+2.0}_{-2.2}(stat.) +/- 1.7(syst.) MeV/c^2, "
                "m_{Sigma_b^-} = 5815.2 +/- 1.0(stat.) +/- 1.7(syst.) MeV/c^2, "
                "and m(Sigma_b^*) - m(Sigma_b) = 21.2^{+2.0}_{-1.9}(stat.) ^{+0.4}_{-0.3}(syst.) MeV/c^2."
            ),
            "categories": "hep-ex"
        }
    ]


@pytest.fixture
def mock_vector_db_search():
    """
    Fixture providing a mock search function for the vector database.

    Returns:
        Callable: Function that simulates vector_db.search behavior
    """
    def create_mock_results(question, papers):
        """
        Create mock search results for a list of papers.

        Args:
            question (str): The query string
            papers (List[Dict]): List of paper dictionaries

        Returns:
            Dict: Simulated vector_db.search result
        """
        documents = []
        metadatas = []

        for paper in papers:
            doc_text = (
                f"Title: {paper['title']}\n"
                f"Authors: {paper['authors']}\n"
                f"Categories: {paper['categories']}\n"
                f"Abstract: {paper['abstract']}"
            )
            documents.append(doc_text)
            metadatas.append({
                "paper_id": paper["id"],
                "title": paper["title"],
                "authors": paper["authors"],
                "categories": paper["categories"]
            })

        return {
            'documents': [documents],
            'metadatas': [metadatas],
            'distances': [[0.1, 0.2]]
        }

    return create_mock_results
