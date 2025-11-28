# Academic Research Assistant

An AI-powered research assistant that helps you search and get answers from academic papers using RAG architecture and Google Gemini AI.

## Quick Start

### 1. Clone and install dependencies
```bash
git clone <your-repo-url>
cd research-assistant
pip install -r requirements.txt
```
### 2. Set up environment variables
Create .env file with your Gemini API key:
```bash
env
GEMINI_API_KEY=your_google_gemini_api_key_here
```
### 3. Run the application
```bash
python main.py
```
The application will be available at http://localhost:8000

### Deployment Railway
1. Connect your GitHub repository to Railway

2. Add GEMINI_API_KEY to environment variables

3. Deployment happens automatically

### Docker
```bash
docker build -t research-assistant .
docker run -p 8000:8000 -e GEMINI_API_KEY=your_key research-assistant
```

### Project Structure
```text
main.py                 # FastAPI application
app/                    # Core application logic
  config.py            # Configuration settings
  database.py          # ChromaDB vector database
  gemini_client.py     # Google Gemini AI client
  modular_rag.py       # RAG strategies implementation
  memory.py            # Conversation memory
  models.py            # Pydantic models
scripts/               # Data loading scripts
templates/             # HTML frontend
static/                # CSS and JavaScript assets
requirements.txt       # Python dependencies
```
### Features
1. Semantic search through academic papers

2. Multiple RAG strategies (basic, hybrid, hierarchical, adaptive)

3. Conversation memory with session support

4. Web interface and REST API

5. Automatic embeddings with ChromaDB

6. Support for arXiv papers dataset

### API Usage
Example request:
```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Explain transformer architecture",
    "strategy": "basic",
    "top_k": 3
  }'
```
### Available RAG strategies:
1. basic: Direct semantic search

2. hybrid: Combines semantic and keyword search

3. hierarchical: Two-stage search with reranking

4. adaptive: Automatically selects the best strategy
