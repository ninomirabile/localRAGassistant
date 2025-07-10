#!/bin/bash

set -e

cd "$(dirname "$0")/.."

echo "🚀 Starting Local RAG Assistant..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Blocca ogni tentativo di uso OpenAI
export OPENAI_API_KEY=dummy

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements/base.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data index cache logs

# Start the application
echo "🌟 Starting FastAPI server..."
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

echo "✅ Local RAG Assistant is running at http://localhost:8000" 