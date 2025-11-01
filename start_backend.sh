#!/bin/bash

# Start GenSec Backend API Server

export PATH="$PWD/.venv/bin:$PATH"
export GITHUB_TOKEN="${GITHUB_TOKEN:-}"
export GROQ_API_KEY="${GROQ_API_KEY:-}"

echo "🚀 Starting GenSec Backend API Server..."
echo "📡 Server will be available at: http://localhost:8000"
echo "📖 API Documentation: http://localhost:8000/docs"
echo ""

.venv/bin/python api_server.py
