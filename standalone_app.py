"""
standalone_app.py - Entry point for PyInstaller standalone build.

This wraps the Streamlit app to launch it properly when bundled.
"""

import sys
import os
from pathlib import Path

# Set up paths for bundled app
if getattr(sys, 'frozen', False):
    # Running as compiled
    BASE_DIR = Path(sys._MEIPASS)
    # Use user's home directory for data storage
    DATA_DIR = Path.home() / ".personal_finance"
    DATA_DIR.mkdir(exist_ok=True)
    os.environ['PERSONAL_FINANCE_DATA'] = str(DATA_DIR)
else:
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"

# Add src to path
sys.path.insert(0, str(BASE_DIR / "src"))

import subprocess
import webbrowser
import time
import socket


def find_free_port():
    """Find an available port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]


def main():
    """Launch the Streamlit app."""
    port = find_free_port()
    app_path = BASE_DIR / "src" / "app.py"
    
    # Start Streamlit server
    env = os.environ.copy()
    env['STREAMLIT_SERVER_PORT'] = str(port)
    env['STREAMLIT_SERVER_HEADLESS'] = 'true'
    env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    process = subprocess.Popen(
        [sys.executable, '-m', 'streamlit', 'run', str(app_path),
         '--server.port', str(port),
         '--server.headless', 'true',
         '--browser.gatherUsageStats', 'false'],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for server to start
    time.sleep(3)
    
    # Open browser
    url = f"http://localhost:{port}"
    webbrowser.open(url)
    
    print(f"Personal Finance running at {url}")
    print("Press Ctrl+C to stop")
    
    try:
        process.wait()
    except KeyboardInterrupt:
        process.terminate()


if __name__ == "__main__":
    main()
