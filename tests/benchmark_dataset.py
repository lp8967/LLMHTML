import json
from typing import List, Dict


class BenchmarkDataset:
    """
    Class representing a small benchmark dataset for testing RAG/document retrieval.
    Each test case contains a question, expected documents, keywords, and a category.
    """
    def __init__(self):
        self.test_cases = self._create_test_cases()

    def _create_test_cases(self) -> List[Dict]:
        """
        Create predefined test cases for the benchmark dataset.

        Returns:
            List[Dict]: List of test case dictionaries
        """
        return [
            {
                "id": "test_001",
                "question": "What is the proton elastic form factor ratio at low momentum transfer?",
                "expected_documents": ["0706.0128"],
                "expected_keywords": ["proton", "elastic", "form factor", "ratio", "momentum transfer", "GEp", "dipole"],
                "category": "nuclear_physics"
            },
            {
                "id": "test_002",
                "question": "What are the Sigma_b and Sigma_b* baryons and their measured masses?",
                "expected_documents": ["0706.3868"],
                "expected_keywords": ["Sigma_b", "baryons", "Tevatron", "CDF", "mass", "Lambda_b", "bottom"],
                "category": "particle_physics"
            },
            {
                "id": "test_003",
                "question": "Explain parity doublet Delta resonances P33 and D33",
                "expected_documents": ["0711.1138"],
                "expected_keywords": ["parity", "doublet", "Delta", "resonances", "photoproduction", "P33", "D33"],
                "category": "nuclear_physics"
            }
        ]

    def get_test_cases(self, category: str = None, difficulty: str = None) -> List[Dict]:
        """
        Retrieve test cases with optional filtering by category and difficulty.

        Args:
            category (str, optional): Filter by category name. Defaults to None.
            difficulty (str, optional): Filter by difficulty level. Defaults to None.

        Returns:
            List[Dict]: List of filtered test cases
        """
        cases = self.test_cases

        if category:
            cases = [c for c in cases if c["category"] == category]
        if difficulty:
            cases = [c for c in cases if c.get("difficulty") == difficulty]

        return cases

    def save_dataset(self, filepath: str):
        """
        Save the benchmark dataset to a JSON file.

        Args:
            filepath (str): Path to save the JSON file
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.test_cases, f, indent=2, ensure_ascii=False)
