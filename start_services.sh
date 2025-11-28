#!/bin/bash

set -e

echo "🚀 Starting Academic Research Assistant (FastAPI + HTML)"

# Функция проверки порта
check_port() {
    echo "Checking if port $1 is ready..."
    local max_attempts=20
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if python -c "import socket; s = socket.socket(); s.settimeout(1); s.connect(('127.0.0.1', $1)); s.close()" 2>/dev/null; then
            echo "✅ Port $1 is ready!"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    echo "❌ Port $1 failed to open after $max_attempts attempts"
    return 1
}

# Функция проверки HTTP endpoint
check_http() {
    echo "Checking HTTP endpoint: $1..."
    local max_attempts=20
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$1" >/dev/null; then
            echo "✅ HTTP endpoint $1 is ready!"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    echo "❌ HTTP endpoint $1 failed after $max_attempts attempts"
    return 1
}

# Функция для запуска БЫСТРЫХ тестов (опционально)
run_quick_tests() {
    echo "=== RUNNING QUICK HEALTH TESTS ==="
    
    # Даем бэкенду время на инициализацию
    sleep 3
    
    # Только быстрые smoke-тесты
    echo "1. Testing basic API connectivity..."
    if curl -s "http://localhost:$PORT/health" >/dev/null; then
        echo "✅ API health check: PASSED"
    else
        echo "❌ API health check: FAILED"
        return 1
    fi
    
    echo "2. Testing database connection..."
    if python -c "
import sys
sys.path.append('/app')
from app.database import vector_db
try:
    count = vector_db.collection.count()
    print(f'✅ Database connection: OK ({count} documents)')
    exit(0)
except Exception as e:
    print(f'❌ Database connection: FAILED - {e}')
    exit(1)
"; then
        echo "✅ Database test: PASSED"
    else
        echo "❌ Database test: FAILED"
        return 1
    fi
    
    echo "3. Testing RAG strategies..."
    if python -c "
import sys
sys.path.append('/app')
from app.modular_rag import modular_rag
try:
    result = modular_rag.execute_rag('test', top_k=1)
    print('✅ RAG system: WORKING')
    exit(0)
except Exception as e:
    print(f'❌ RAG system: FAILED - {e}')
    exit(1)
"; then
        echo "✅ RAG test: PASSED"
    else
        echo "❌ RAG test: FAILED"
    fi
    
    echo "=== QUICK TESTS COMPLETED ==="
    return 0
}

# Функция инициализации базы данных
initialize_database() {
    echo "=== DATABASE INITIALIZATION ==="
    
    # Проверяем текущее состояние БД
    python -c "
import sys
sys.path.append('/app')
from app.database import vector_db
try:
    count = vector_db.collection.count()
    print(f'Current document count: {count}')
    exit(0)
except Exception as e:
    print(f'Error checking database: {e}')
    exit(1)
"

    if [ $? -eq 0 ]; then
        echo "✅ Database check completed"
    else
        echo "❌ Database check failed"
    fi
    
    # Загружаем данные ТОЛЬКО если скрипт существует
    if [ -f "scripts/load_arxiv_data.py" ]; then
        echo "📥 Loading data from scripts/load_arxiv_data.py..."
        if python scripts/load_arxiv_data.py; then
            echo "✅ Data loaded successfully"
        else
            echo "❌ Data loading failed"
        fi
    else
        echo "⚠️ Data loader script not found: scripts/load_arxiv_data.py"
        echo "📁 Available files:"
        ls -la scripts/ 2>/dev/null || echo "scripts directory not found"
    fi
}

# Основной процесс
main() {
    echo "Starting Academic Research Assistant..."
    
    # Получаем порт из Render
    local port=${PORT:-8000}
    echo "Using port: $port"
    
    # Инициализация БД
    initialize_database
    
    # ЗАПУСК БЫСТРЫХ ТЕСТОВ (если нужно)
    if [ "$RUN_TESTS" = "true" ]; then
        echo "=== TESTS ENABLED ==="
        # Запускаем тесты в фоне, пока стартует сервер
        run_quick_tests &
        TESTS_PID=$!
    else
        echo "=== TESTS DISABLED ==="
    fi
    
    # ЗАПУСК FASTAPI (ОСНОВНОЙ ПРОЦЕСС)
    echo "=== STARTING FASTAPI SERVER ==="
    cd /app
    
    # Для Render: запускаем напрямую, без фона
    exec python -m uvicorn main:app \
        --host 0.0.0.0 \
        --port $port \
        --workers 1 \
        --loop asyncio
    
    # Этот код выполнится только если exec не сработает
    echo "❌ FastAPI failed to start"
    exit 1
}

# Запуск основного процесса
main
