#!/bin/bash
# ============================================================================
# DuoFinance Setup Script
# Creates Python virtual environment and installs dependencies
# ============================================================================

set -e  # Exit on error

echo "🚀 Setting up DuoFinance..."
echo ""

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.10+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "✓ Virtual environment created"
echo ""
echo "📥 Installing dependencies..."

source venv/bin/activate

# Upgrade pip
pip install --upgrade pip --quiet

# Install required packages
pip install pandas streamlit plotly openpyxl --quiet

echo "✓ Dependencies installed:"
pip list | grep -E "pandas|streamlit|plotly|openpyxl"

# Create necessary directories
echo ""
echo "📁 Ensuring directory structure..."
mkdir -p data/masha data/pablo config

# Initialize config if needed
if [ ! -f "config/category_mapping.json" ]; then
    echo '{"learned_mappings": {}}' > config/category_mapping.json
fi

echo "✓ Directory structure ready"

echo ""
echo "============================================"
echo "✅ Setup complete!"
echo ""
echo "To run the application:"
echo "  ./run.sh"
echo ""
echo "Or manually:"
echo "  source venv/bin/activate"
echo "  streamlit run src/app.py"
echo "============================================"
