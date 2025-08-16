#!/bin/bash

# Viktor Kozlov Direct Ollama Integration Setup
# Complete system for direct tool access through Ollama conversation

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "🌍 Viktor Kozlov Direct Ollama Integration"
echo "=========================================="
echo ""

# Function to check if a process is running on a port
check_port() {
    local port=$1
    if lsof -i :$port > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to start news server if not running
start_news_server() {
    if check_port 3000; then
        echo "✅ News server already running on port 3000"
        return 0
    fi
    
    echo "🚀 Starting news server..."
    if [ -f "server.js" ]; then
        node server.js &
        local news_pid=$!
        sleep 3
        
        if check_port 3000; then
            echo "✅ News server started (PID: $news_pid)"
            return 0
        else
            echo "❌ Failed to start news server"
            return 1
        fi
    else
        echo "❌ server.js not found. Please make sure the news server is available."
        return 1
    fi
}

# Function to start tool server
start_tool_server() {
    echo "🛠️  Starting Ollama tool integration server..."
    python3 ollama-tool-server.py --port 8080 --ollama-url http://localhost:11434 &
    local tool_pid=$!
    sleep 3
    
    if check_port 8080; then
        echo "✅ Tool server started (PID: $tool_pid)"
        return 0
    else
        echo "❌ Failed to start tool server"
        return 1
    fi
}

# Function to create enhanced model
create_enhanced_model() {
    echo "🤖 Creating enhanced kozlov-hermes model with tool access..."
    
    if ollama list | grep -q "kozlov-tools"; then
        echo "ℹ️  Enhanced model already exists"
        return 0
    fi
    
    if [ -f "Modelfile.kozlov-tools" ]; then
        ollama create kozlov-tools -f Modelfile.kozlov-tools
        if [ $? -eq 0 ]; then
            echo "✅ Enhanced model 'kozlov-tools' created"
            return 0
        else
            echo "❌ Failed to create enhanced model"
            return 1
        fi
    else
        echo "❌ Modelfile.kozlov-tools not found"
        return 1
    fi
}

# Function to test the integration
test_integration() {
    echo "🧪 Testing integration..."
    
    # Test tool server health
    if curl -s http://localhost:8080/health > /dev/null; then
        echo "✅ Tool server health check passed"
    else
        echo "❌ Tool server health check failed"
        return 1
    fi
    
    # Test news server health  
    if curl -s http://localhost:3000/health > /dev/null; then
        echo "✅ News server health check passed"
    else
        echo "❌ News server health check failed"
        return 1
    fi
    
    echo "✅ All systems operational"
    return 0
}

# Function to show usage instructions
show_usage() {
    echo ""
    echo "🎯 INTEGRATION COMPLETE!"
    echo "======================"
    echo ""
    echo "Your Viktor Kozlov model now has direct access to intelligence tools!"
    echo ""
    echo "💡 USAGE OPTIONS:"
    echo ""
    echo "1. DIRECT OLLAMA ACCESS (Recommended):"
    echo "   ollama run kozlov-tools"
    echo "   Then ask: 'What's the latest on artificial intelligence?'"
    echo "   Or: 'Give me an intelligence brief on the Middle East'"
    echo ""
    echo "2. API ACCESS:"
    echo "   curl -X POST http://localhost:8080/v1/chat/completions \\"
    echo "     -H 'Content-Type: application/json' \\"
    echo "     -d '{\"model\":\"kozlov-hermes\",\"messages\":[{\"role\":\"user\",\"content\":\"What is happening in Ukraine?\"}]}'"
    echo ""
    echo "3. PYTHON INTEGRATION:"
    echo "   python3 viktor-intelligence-agent.py --query 'Tell me about current events'"
    echo ""
    echo "🛠️  AVAILABLE TOOLS:"
    echo "   • Real-time news monitoring"
    echo "   • Weather intelligence"
    echo "   • Social media analysis (Bluesky, Reddit)"
    echo "   • Comprehensive intelligence briefings"
    echo ""
    echo "🔧 RUNNING SERVICES:"
    echo "   • News Server: http://localhost:3000"
    echo "   • Tool Server: http://localhost:8080"
    echo "   • Enhanced Model: kozlov-tools"
    echo ""
    echo "To stop services: kill the background processes or use Ctrl+C"
    echo ""
}

# Main execution
echo "📋 Pre-flight checks..."

# Check if Ollama is installed and running
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed. Please install Ollama first."
    exit 1
fi

# Check if kozlov-hermes model exists
if ! ollama list | grep -q "kozlov-hermes"; then
    echo "❌ kozlov-hermes model not found. Please install it first:"
    echo "   ollama pull kozlov-hermes"
    exit 1
fi

# Check Python dependencies
if ! python3 -c "import aiohttp, requests" 2>/dev/null; then
    echo "📦 Installing Python dependencies..."
    pip3 install aiohttp requests
fi

echo "✅ Pre-flight checks complete"
echo ""

# Start services
start_news_server
start_tool_server
create_enhanced_model

echo ""
echo "🧪 Testing integration..."
sleep 2
test_integration

echo ""
show_usage

# Interactive prompt
echo "🚀 Ready to start? Press Enter to launch kozlov-tools or Ctrl+C to exit"
read -r

echo "🤖 Launching Viktor Kozlov with tool access..."
echo "============================================="
echo ""
echo "You can now ask Viktor about current events, news, weather, or request intelligence analysis!"
echo "Type 'exit' to quit the conversation."
echo ""

# Launch the enhanced model
ollama run kozlov-tools
