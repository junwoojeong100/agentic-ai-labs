#!/bin/bash
set -e

echo "======================================"
echo "🚀 Setting up Python Development Environment"
echo "======================================"

# Python 버전 확인
echo ""
echo "📍 Python Version:"
python --version

# 가상환경 생성
echo ""
echo "📦 Creating Python virtual environment (.venv)..."
if [ ! -d ".venv" ]; then
    python -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "⚠️  Virtual environment already exists"
fi

# 가상환경 활성화
echo ""
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# pip 업그레이드
echo ""
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# 필수 패키지 설치
echo ""
echo "📚 Installing required packages..."
echo "   This may take a few minutes..."

# 노트북 실행에 필요한 패키지들
pip install --no-cache-dir \
    azure-identity>=1.17.0 \
    azure-ai-projects>=1.0.0b5 \
    azure-ai-inference>=1.0.0b6 \
    azure-search-documents>=11.4.0 \
    openai>=1.51.0 \
    python-dotenv>=1.0.0 \
    requests>=2.31.0 \
    fastapi>=0.110.0 \
    uvicorn>=0.30.0 \
    httpx>=0.27.0 \
    azure-monitor-opentelemetry>=1.6.0 \
    azure-monitor-opentelemetry-exporter>=1.0.0b27 \
    opentelemetry-api>=1.20.0 \
    opentelemetry-sdk>=1.20.0 \
    opentelemetry-instrumentation-fastapi>=0.45b0 \
    "agent-framework[azure-ai]>=1.0.0b251007" \
    "fastmcp>=0.2.0" \
    "mcp>=1.1.0"

echo ""
echo "✅ All packages installed successfully!"

# Jupyter 커널 등록
echo ""
echo "🎯 Registering Jupyter kernel..."
pip install ipykernel
python -m ipykernel install --user --name=agentic-ai-labs --display-name "Python 3.12 (agentic-ai-labs)"

echo ""
echo "======================================"
echo "✅ Setup completed successfully!"
echo "======================================"
echo ""
echo "📍 Virtual environment: .venv"
echo "📍 Python interpreter: .venv/bin/python"
echo "📍 Jupyter kernel: Python 3.12 (agentic-ai-labs)"
echo ""
echo "💡 The virtual environment is now activated."
echo "   You can start running the notebooks!"
echo ""
