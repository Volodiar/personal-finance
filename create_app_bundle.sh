#!/bin/bash
# Create a macOS .app bundle for Personal Finance

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
APP_NAME="Personal Finance"
APP_BUNDLE="${SCRIPT_DIR}/${APP_NAME}.app"

echo "Creating ${APP_NAME}.app bundle..."

# Create .app bundle structure
mkdir -p "${APP_BUNDLE}/Contents/MacOS"
mkdir -p "${APP_BUNDLE}/Contents/Resources"

# Create the launcher script inside the .app
cat > "${APP_BUNDLE}/Contents/MacOS/launcher" << 'EOF'
#!/bin/bash
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"

cd "$PROJECT_DIR"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Kill any existing Streamlit processes on port 8501
lsof -ti:8501 | xargs kill -9 2>/dev/null

# Start Streamlit
streamlit run src/app.py --server.port=8501 &

# Wait for server to start
sleep 2

# Open in browser
open http://localhost:8501
EOF

chmod +x "${APP_BUNDLE}/Contents/MacOS/launcher"

# Copy icon if it exists
if [ -f "${SCRIPT_DIR}/assets/icon.png" ]; then
    cp "${SCRIPT_DIR}/assets/icon.png" "${APP_BUNDLE}/Contents/Resources/icon.png"
fi

# Create Info.plist
cat > "${APP_BUNDLE}/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIconFile</key>
    <string>icon.png</string>
    <key>CFBundleIdentifier</key>
    <string>com.personalfinance.app</string>
    <key>CFBundleName</key>
    <string>${APP_NAME}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>
EOF

echo "✅ ${APP_NAME}.app created successfully!"
echo ""
echo "To install:"
echo "  1. Drag '${APP_NAME}.app' to your Applications folder"
echo "  2. Or double-click to run directly from here"
echo ""
echo "Note: On first run, you may need to right-click > Open to bypass Gatekeeper"
