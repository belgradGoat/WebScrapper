#!/bin/bash

# Viktor Kozlov Direct Access Launcher
# Simple script to launch Viktor with direct tool access

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "🌍 Viktor Kozlov - Direct Tool Access"
echo "====================================="

# Quick mode - just launch if everything is ready
if [ "$1" = "--quick" ] || [ "$1" = "-q" ]; then
    echo "🚀 Quick launch mode..."
    
    # Check if tool server is running
    if ! curl -s http://localhost:8080/health > /dev/null 2>&1; then
        echo "🛠️  Starting tool server..."
        python3 ollama-tool-server.py &
        sleep 3
    fi
    
    echo "🤖 Launching Viktor Kozlov with tools..."
    echo ""
    ollama run kozlov-hermes
    exit 0
fi

# Full setup mode
echo ""
echo "This will:"
echo "• Start the news server (if needed)"
echo "• Start the tool integration server" 
echo "• Launch Viktor Kozlov with direct tool access"
echo ""
echo "Ready? [y/N]"
read -r response

if [[ ! "$response" =~ ^[Yy]$ ]]; then
    echo "Setup cancelled."
    exit 0
fi

# Run the full setup
bash setup-kozlov-direct.sh
