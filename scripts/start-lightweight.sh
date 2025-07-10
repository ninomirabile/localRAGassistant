#!/bin/bash

set -e

echo "🚀 Starting Local RAG Assistant (Lightweight Mode)..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Run './scripts/setup.sh' first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Set environment variables for lightweight mode
export RAG_CONFIG_FILE="config/lightweight.yaml"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
export OMP_NUM_THREADS=2  # Limit OpenMP threads for dual-core
export MKL_NUM_THREADS=2  # Limit MKL threads
export NUMEXPR_NUM_THREADS=2  # Limit NumExpr threads

# Create temp directory if it doesn't exist
mkdir -p temp

# Start Redis with memory limits
echo "🔴 Starting Redis with memory limits..."
redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru --daemonize yes

# Wait for Redis to start
sleep 2

# Start the application with optimized settings
echo "🌐 Starting web application..."
python -m uvicorn src.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 1 \
    --limit-concurrency 10 \
    --limit-max-requests 1000 \
    --timeout-keep-alive 30 \
    --log-level info

echo "✅ Application started at http://127.0.0.1:8000"
echo "💡 Press Ctrl+C to stop" 