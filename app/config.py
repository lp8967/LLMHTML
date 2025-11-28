import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API configuration: loads the API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ChromaDB configuration: database path and collection name for storing embeddings
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = "arxiv_papers_2020"

# Model configuration: name of the LLM model used for RAG operations
LLM_MODEL = "gemini-2.5-flash"

# RAG-related settings: number of results retrieved and maximum context size
TOP_K_RESULTS = 3
MAX_CONTEXT_LENGTH = 2000

# Data configuration: path to dataset and batch size for processing
DATA_PATH = os.getenv("DATA_PATH", "./data/filtered_arxiv_2020.json")
BATCH_SIZE = 100

# Gemini safety settings: defines allowed content categories and moderation thresholds
GEMINI_SAFETY_SETTINGS = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH", 
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
]
