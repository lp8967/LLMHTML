FROM python:3.9-slim

WORKDIR /app

# Устанавливаем зависимости для ChromaDB
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Создаем директории
RUN mkdir -p chroma_db data

# Делаем скрипты исполняемыми
RUN chmod +x start_services.sh

# Используем порт Render
EXPOSE 8000

# Запускаем через shell-скрипт
CMD ["./start_services.sh"]