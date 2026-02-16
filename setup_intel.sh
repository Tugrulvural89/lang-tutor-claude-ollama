#!/bin/bash
# Language Tutor - M1 Mac Quick Setup
set -e

echo "🌍 Language Tutor - M1 Mac Setup"
echo "================================"
echo ""

# Check macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only"
    exit 1
fi

# Check architecture
ARCH=$(uname -m)
if [[ "$ARCH" != "arm64" ]]; then
    echo "❌ This script is for Apple Silicon (M1/M2/M3) Macs"
    echo "   Your architecture: $ARCH"
    echo "   For Intel Macs, use setup_intel.sh instead"
    exit 1
fi

echo "✓ Detected Apple Silicon ($ARCH)"
echo ""

# Check RAM
RAM_GB=$(sysctl hw.memsize | awk '{print int($2/1024/1024/1024)}')
echo "✓ Detected ${RAM_GB}GB RAM"
if [ "$RAM_GB" -lt 8 ]; then
    echo "⚠️  Warning: Less than 8GB RAM detected"
    echo "   The app may run slowly. Consider using Claude Desktop (default) instead of Ollama."
fi
echo ""

echo "📦 Step 1/4: Checking Homebrew..."
if ! command -v brew &> /dev/null; then
    echo "❌ Homebrew not found. Install from: https://brew.sh"
    exit 1
else
    echo "   ✓ Homebrew installed: $(brew --version | head -1)"
fi

echo ""
echo "📦 Step 2/4: Installing Python packages..."
pip3 install pyaudio mlx-whisper numpy pynput edge-tts requests --break-system-packages

echo ""
echo "📦 Step 3/4: Installing Claude Desktop CLI..."
if command -v claude &> /dev/null; then
    echo "   ✓ Claude CLI already installed: $(which claude)"
else
    if ! command -v npm &> /dev/null; then
        echo "❌ npm not found. Install Node.js from: https://nodejs.org"
        echo "   Or run: brew install node"
        exit 1
    fi
    npm install -g @anthropic-ai/claude-cli
    echo "   ✓ Claude CLI installed"
fi

echo ""
echo "📦 Step 4/4: Claude authentication..."
if claude whoami &> /dev/null 2>&1; then
    echo "   ✓ Already logged in: $(claude whoami)"
else
    echo "   Please login to Claude:"
    claude login
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 Quick Start:"
echo "   python3 lang_m1.py --lang en --level B1"
echo ""
echo "💡 M1 Optimizations:"
echo "   - MLX Whisper for Apple Silicon (fast!)"
echo "   - Claude Desktop default (RAM efficient)"
echo "   - Use --ollama for fully local (more RAM)"
echo ""
echo "📖 Full documentation:"
echo "   cat README_M1.md"
echo ""
echo "⌨️  Controls:"
echo "   Cmd+Shift (hold) - Speak"
echo "   Cmd+Q - Quit"
echo ""