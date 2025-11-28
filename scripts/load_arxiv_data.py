import json
import logging
import os
import sys
from tqdm import tqdm

# Добавляем путь для импортов в Docker
sys.path.append('/app')

from app.database import vector_db
from app.config import DATA_PATH, BATCH_SIZE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_arxiv_data():
    """Загрузка и обработка данных из arXiv JSON"""
    
    # Проверяем существует ли уже БД
    if os.path.exists('/app/chroma_db/chroma.sqlite3'):
        logger.info("Vector database already exists, skipping data loading.")
        return True
    
    if not os.path.exists(DATA_PATH):
        logger.error(f"Data file not found: {DATA_PATH}")
        return False
    
    try:
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        
        # ОГРАНИЧИВАЕМ ДО 3000 СТАТЕЙ ДЛЯ 1GB ПАМЯТИ
        papers = papers[:3000]
        logger.info(f"Loading {len(papers)} papers from arXiv dataset")
        
        # Подготавливаем документы для векторной БД
        documents = []
        metadatas = []
        ids = []
        
        for i, paper in enumerate(tqdm(papers, desc="Processing papers")):
            # Создаем текстовое представление статьи
            text_content = create_document_text(paper)
            
            documents.append(text_content)
            metadatas.append({
                "paper_id": paper.get("id", f"unknown_{i}"),
                "title": paper.get("title", ""),
                "authors": paper.get("authors", ""),
                "categories": paper.get("categories", ""),
                "year": "2020"
            })
            ids.append(f"arxiv_{paper.get('id', i)}")
            
            # Добавляем батчами для экономии памяти
            if len(documents) >= BATCH_SIZE:
                vector_db.add_documents(documents, metadatas, ids)
                documents.clear()
                metadatas.clear()
                ids.clear()
        
        # Добавляем оставшиеся документы
        if documents:
            vector_db.add_documents(documents, metadatas, ids)
        
        logger.info("Successfully loaded all papers into vector database")
        return True
        
    except Exception as e:
        logger.error(f"Error loading arXiv data: {str(e)}")
        return False

def create_document_text(paper):
    """Создает текстовое представление статьи для эмбеддингов"""
    title = paper.get("title", "").strip()
    abstract = paper.get("abstract", "").strip()
    authors = paper.get("authors", "").strip()
    categories = paper.get("categories", "").strip()
    
    # Форматируем текст для лучшего семантического поиска
    document_text = f"Title: {title}\n"
    
    if authors:
        document_text += f"Authors: {authors}\n"
    
    if categories:
        document_text += f"Categories: {categories}\n"
    
    document_text += f"Abstract: {abstract}"
    
    return document_text

if __name__ == "__main__":
    success = process_arxiv_data()
    if success:
        print("Data loading completed successfully!")
    else:
        print("Data loading failed!")
        sys.exit(1)