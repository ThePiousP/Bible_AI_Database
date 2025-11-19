#!/bin/bash
# Install dependencies for Bible AI training
# This script installs all required packages for the AI training pipeline

echo "================================================================"
echo "  Bible AI Training - Dependency Installation"
echo "================================================================"
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "❌ Error: Python 3 not found"
    echo "   Please install Python 3.8 or higher"
    exit 1
fi

echo ""
echo "================================================================"
echo "  Installing AI Training Dependencies"
echo "================================================================"
echo ""

# Install core AI dependencies
echo "Installing sentence-transformers (for embeddings)..."
pip3 install sentence-transformers

echo ""
echo "Installing numpy (for numerical operations)..."
pip3 install numpy

echo ""
echo "Installing tqdm (for progress bars)..."
pip3 install tqdm

echo ""
echo "================================================================"
echo "  Optional: Install LLM APIs (for chat interface)"
echo "================================================================"
echo ""

read -p "Install OpenAI API client? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip3 install openai
fi

echo ""
read -p "Install Anthropic API client? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pip3 install anthropic
fi

echo ""
echo "================================================================"
echo "  Verification"
echo "================================================================"
echo ""

python3 -c "
import sys
try:
    import sentence_transformers
    print('✓ sentence-transformers:', sentence_transformers.__version__)
except ImportError:
    print('✗ sentence-transformers not installed')
    sys.exit(1)

try:
    import numpy as np
    print('✓ numpy:', np.__version__)
except ImportError:
    print('✗ numpy not installed')
    sys.exit(1)

try:
    import tqdm
    print('✓ tqdm:', tqdm.__version__)
except ImportError:
    print('✗ tqdm not installed')
    sys.exit(1)

try:
    import openai
    print('✓ openai:', openai.__version__)
except ImportError:
    print('ℹ openai not installed (optional)')

try:
    import anthropic
    print('✓ anthropic:', anthropic.__version__)
except ImportError:
    print('ℹ anthropic not installed (optional)')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "================================================================"
    echo "  ✅ Installation Complete!"
    echo "================================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Create embeddings:"
    echo "     python3 code/ai_training/create_embeddings.py"
    echo ""
    echo "  2. Test RAG system:"
    echo "     python3 code/ai_training/rag_system.py --demo"
    echo ""
    echo "  3. Start chatbot:"
    echo "     python3 code/ai_training/chat_interface.py --demo"
    echo ""
else
    echo ""
    echo "❌ Installation failed"
    echo "   Please check the error messages above"
    exit 1
fi
