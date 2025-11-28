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
    
    logger.info("=== STARTING DATA LOADING ===")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"DATA_PATH: {DATA_PATH}")
    
    # 🔴 ИСПРАВЛЯЕМ ПРОБЛЕМУ: всегда проверяем КОЛИЧЕСТВО документов
    try:
        count = vector_db.collection.count()
        logger.info(f"📊 Current document count: {count}")
        
        if count > 100:  # Если уже есть достаточное количество документов
            logger.info(f"✅ Database already has {count} documents, skipping loading.")
            return True
        elif count > 0:
            logger.warning(f"⚠️ Database has only {count} documents, but proceeding with loading...")
        else:
            logger.info("🔄 Database is EMPTY - loading data...")
    except Exception as e:
        logger.warning(f"Could not check collection count: {e}")
        logger.info("Proceeding with data loading...")
    
    # Проверяем существование файла данных
    if not os.path.exists(DATA_PATH):
        logger.error(f"❌ Data file not found: {DATA_PATH}")
        logger.info(f"Files in current directory: {os.listdir('.')}")
        if os.path.exists('data'):
            logger.info(f"Files in data directory: {os.listdir('data')}")
        return False
    
    try:
        logger.info(f"📖 Reading data from {DATA_PATH}")
        with open(DATA_PATH, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        
        logger.info(f"📊 Loaded {len(papers)} papers from dataset")
        
        # ОГРАНИЧИВАЕМ ДО 1000 СТАТЕЙ ДЛЯ БЫСТРОЙ ЗАГРУЗКИ
        papers = papers[:101]
        logger.info(f"📦 Processing {len(papers)} papers")
        
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
                logger.info(f"📤 Adding batch of {len(documents)} documents...")
                vector_db.add_documents(documents, metadatas, ids)
                documents.clear()
                metadatas.clear()
                ids.clear()
        
        # Добавляем оставшиеся документы
        if documents:
            logger.info(f"📤 Adding final batch of {len(documents)} documents...")
            vector_db.add_documents(documents, metadatas, ids)
        
        # Проверяем результат
        final_count = vector_db.collection.count()
        logger.info(f"✅ Successfully loaded {final_count} papers into vector database")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading arXiv data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
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

