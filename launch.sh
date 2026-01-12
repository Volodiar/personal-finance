#!/bin/bash
# Personal Finance App Launcher
# This script launches the Streamlit app and opens it in the browser

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the project directory
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Kill any existing Streamlit processes on port 8501
lsof -ti:8501 | xargs kill -9 2>/dev/null

# Start Streamlit in the background
streamlit run src/app.py --server.port=8501 &

# Wait a moment for the server to start
sleep 2

# Open in default browser
open http://localhost:8501

echo "Personal Finance app is running at http://localhost:8501"
echo "Press Ctrl+C to stop the server"

# Wait for the Streamlit process
wait
