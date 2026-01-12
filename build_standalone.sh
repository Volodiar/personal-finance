#!/bin/bash
# Build standalone Personal Finance app for macOS
# This creates a fully self-contained .app bundle

set -e

echo "🚀 Building Personal Finance standalone app..."
echo ""

# Check if PyInstaller is installed
if ! pip show pyinstaller > /dev/null 2>&1; then
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/ dist/

# Build the app
echo "🔨 Building standalone executable..."
echo "   This may take several minutes..."
echo ""

pyinstaller personal_finance.spec --clean --noconfirm

# Check result
if [ -d "dist/Personal Finance.app" ]; then
    echo ""
    echo "✅ Build successful!"
    echo ""
    echo "📁 App location: dist/Personal Finance.app"
    echo ""
    echo "To install:"
    echo "  1. Copy 'dist/Personal Finance.app' to /Applications/"
    echo "  2. Double-click to run"
    echo ""
    echo "Note: On first run, you may need to:"
    echo "  - Right-click → Open to bypass Gatekeeper"
    echo "  - Or go to System Preferences → Security → Open Anyway"
    
    # Optionally copy to Applications
    read -p "Copy to /Applications now? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "/Applications/Personal Finance.app"
        cp -R "dist/Personal Finance.app" /Applications/
        echo "✅ Installed to /Applications/Personal Finance.app"
    fi
else
    echo "❌ Build failed. Check the output above for errors."
    exit 1
fi
