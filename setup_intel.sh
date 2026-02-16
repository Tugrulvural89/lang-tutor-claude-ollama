#!/bin/bash
# Language Tutor - Intel Mac Quick Setup
set -e

echo "🌍 Language Tutor - Intel Mac Setup"
echo "===================================="
echo ""

# Check macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only"
    exit 1
fi

# Check architecture
ARCH=$(uname -m)
if [[ "$ARCH" != "x86_64" ]]; then
    echo "⚠️  Warning: This is optimized for Intel Macs"
    echo "   Your architecture: $ARCH"
    read -p "   Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📦 Step 1/4: Installing system dependencies..."
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Install from: https://brew.sh"
    exit 1
fi

# PortAudio for PyAudio
if ! brew list portaudio &> /dev/null; then
    echo "   Installing PortAudio..."
    brew install portaudio
else
    echo "   ✓ PortAudio already installed"
fi

echo ""
echo "📦 Step 2/4: Installing Python packages..."
pip3 install pyaudio faster-whisper numpy pynput edge-tts requests --break-system-packages

echo ""
echo "📦 Step 3/4: Installing Claude Desktop CLI..."
if command -v claude &> /dev/null; then
    echo "   ✓ Claude CLI already installed: $(which claude)"
else
    if ! command -v npm &> /dev/null; then
        echo "❌ npm not found. Install Node.js from: https://nodejs.org"
        exit 1
    fi
    npm install -g @anthropic-ai/claude-cli
    echo "   ✓ Claude CLI installed"
fi

echo ""
echo "📦 Step 4/4: Claude authentication..."
if ! claude whoami &> /dev/null 2>&1; then
    echo "   Please login to Claude:"
    claude login
else
    echo "   ✓ Already logged in: $(claude whoami)"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Quick Start:"
echo "   python3 lang_intel.py --lang en --level B1"
echo ""
echo "📖 Full documentation:"
echo "   cat README_INTEL.md"
echo ""
echo "⌨️  Controls:"
echo "   Cmd+Shift (hold) - Speak"
echo "   Cmd+Q - Quit"
echo ""