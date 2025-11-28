#!/bin/bash

set -e  # Останавливаться при любой ошибке

# Функция для запуска тестов (опционально для продакшена)
run_tests() {
    echo "=== RUNNING QUICK HEALTH TESTS ==="
    
    # Только быстрые smoke-тесты для продакшена
    echo "1. Running quick API health check..."
    if python -c "
import sys
sys.path.append('/app')
from app.database import vector_db
print('✅ Database connection OK')
"; then
        echo "Database test passed"
    else
        echo "Database test issues, but continuing..."
    fi
    
    echo "=== QUICK TESTS COMPLETED ==="
}

# Функция для ожидания готовности сервиса
wait_for_service() {
    echo "Waiting for $1 to be ready..."
    local max_attempts=15  # Уменьшено для Render
    local attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -s $2 >/dev/null 2>&1; then
            echo "✅ $1 is ready!"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 2
    done
    
    echo "❌ $1 failed to start after $max_attempts attempts"
    return 1
}

# Функция инициализации базы данных
initialize_database() {
    echo "=== DATABASE INITIALIZATION ==="
    
    # Проверяем, нужно ли инициализировать БД
    if python -c "
import sys
sys.path.append('/app')
from app.database import vector_db
try:
    count = vector_db.collection.count()
    print(f'Database already has {count} documents')
    exit(0 if count > 0 else 1)
except Exception as e:
    print('Database empty or error:', str(e))
    exit(1)
"; then
        echo "✅ Database already initialized"
        return 0
    else
        echo "Initializing vector database..."
        if python scripts/load_arxiv_data.py; then
            echo "✅ Database initialized successfully"
            return 0
        else
            echo "❌ Database initialization failed"
            # Продолжаем работу даже если данные не загрузились
            echo "⚠️ Continuing with empty database..."
            return 0
        fi
    fi
}

# Функция проверки здоровья системы
health_check() {
    echo "=== SYSTEM HEALTH CHECK ==="
    
    # Проверка переменных окружения
    if [ -z "$GEMINI_API_KEY" ]; then
        echo "❌ GEMINI_API_KEY is not set"
        return 1
    else
        echo "✅ GEMINI_API_KEY is set"
    fi
    
    # Проверка Python окружения
    if python -c "import google.generativeai, chromadb" 2>/dev/null; then
        echo "✅ Python dependencies OK"
    else
        echo "❌ Python dependencies missing"
        return 1
    fi
    
    echo "✅ All health checks passed"
    return 0
}

# Функция запуска только FastAPI (для продакшена)
start_fastapi_only() {
    echo "=== STARTING FASTAPI BACKEND ==="
    
    # Получаем порт из переменной окружения Render
    local port=${PORT:-8000}
    
    echo "Starting FastAPI on port $port..."
    
    cd /app
    exec python -m uvicorn main:app \
        --host 0.0.0.0 \
        --port $port \
        --workers 1 \
        --loop asyncio
}

# Функция запуска обоих сервисов (для разработки)
start_both_services() {
    echo "=== STARTING BOTH SERVICES ==="
    
    # Запуск бэкенда в фоне
    echo "Starting FastAPI backend..."
    cd /app
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1 &
    BACKEND_PID=$!
    
    # Ждем готовности бэкенда
    wait_for_service "Backend" "http://localhost:8000/health" || {
        echo "Backend failed to start, killing process..."
        kill $BACKEND_PID 2>/dev/null || true
        exit 1
    }
    
    # Быстрые тесты (опционально)
    run_tests || echo "Tests had issues, but continuing..."
    
    # Запуск Streamlit фронтенда (основной процесс)
    echo "Starting Streamlit frontend..."
    cd /app
    streamlit run streamlit_app.py \
        --server.port=8501 \
        --server.address=0.0.0.0 \
        --server.headless=true \
        --server.enableCORS=true \
        --browser.serverAddress="0.0.0.0" \
        --browser.gatherUsageStats=false
    
    # Если Streamlit падает, останавливаем бэкенд
    echo "Frontend stopped. Shutting down backend..."
    kill $BACKEND_PID 2>/dev/null || true
    wait $BACKEND_PID 2>/dev/null || true
}

# Основной процесс запуска
main() {
    echo "🚀 Starting Academic Research Assistant..."
    echo "Environment: $NODE_ENV"
    
    # Шаг 1: Проверка здоровья системы
    health_check || {
        echo "❌ Health check failed. Exiting."
        exit 1
    }
    
    # Шаг 2: Инициализация базы данных
    initialize_database || {
        echo "⚠️ Database initialization had issues, but continuing..."
    }
    
    # Определяем режим запуска
    if [ "$RUN_MODE" = "fastapi-only" ] || [ "$RENDER" = "true" ]; then
        # Режим только FastAPI (для Render продакшена)
        echo "🔧 Starting in FastAPI-only mode (production)"
        start_fastapi_only
    else
        # Режим обоих сервисов (для разработки)
        echo "🔧 Starting in full mode (both services)"
        start_both_services
    fi
}

# Обработка сигналов для graceful shutdown
cleanup() {
    echo "🛑 Received shutdown signal..."
    # Дополнительная логика очистки при необходимости
    exit 0
}

trap cleanup SIGTERM SIGINT

# Запуск основного процесса
main "$@"