import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ChromaDB Settings
CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
COLLECTION_NAME = "arxiv_papers_2020"

# 🟢 Указываем правильное имя модели
LLM_MODEL = "gemini-2.5-flash"

# RAG Settings
TOP_K_RESULTS = 3
MAX_CONTEXT_LENGTH = 2000

# Data Settings
DATA_PATH = os.getenv("DATA_PATH", "./data/filtered_arxiv_2020.json")
BATCH_SIZE = 100

# Gemini Safety Settings
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
