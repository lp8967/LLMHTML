FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for ChromaDB
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create required directories
RUN mkdir -p chroma_db data

# Make shell scripts executable
RUN chmod +x start_services.sh

# Expose port (for Render or other hosting platforms)
EXPOSE 8000

# Start the application via shell script
CMD ["./start_services.sh"]
