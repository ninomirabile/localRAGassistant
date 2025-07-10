#!/bin/bash

echo "🛑 Stopping Local RAG Assistant..."

# Find and kill the uvicorn or python process
PIDS=$(pgrep -f "uvicorn src.main:app|python src/main.py")
if [ ! -z "$PIDS" ]; then
    for PID in $PIDS; do
        echo "🔴 Killing process $PID..."
        kill -TERM $PID
        sleep 2
        if kill -0 $PID 2>/dev/null; then
            echo "⚡ Force killing process $PID..."
            kill -KILL $PID
        fi
    done
    echo "✅ Application stopped successfully"
else
    echo "ℹ️  No running application found"
fi

# Optional: deactivate virtual environment if active
if [ ! -z "$VIRTUAL_ENV" ]; then
    echo "🔧 Deactivating virtual environment..."
    deactivate
fi 