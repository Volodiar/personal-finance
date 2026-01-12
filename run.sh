#!/bin/bash
# ============================================================================
# DuoFinance Run Script
# Activates virtual environment and launches the Streamlit application
# ============================================================================

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found."
    echo "Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "🚀 Starting DuoFinance..."
echo ""

# Run Streamlit
streamlit run src/app.py --server.headless=false
