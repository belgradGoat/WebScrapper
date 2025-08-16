#!/bin/bash

# Viktor Kozlov Intelligence Setup Script
# Sets up the enhanced intelligence system with tool access

echo "🌍 Viktor Kozlov Intelligence System Setup"
echo "=========================================="

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# Function to check requirements
check_requirements() {
    echo "🔍 Checking system requirements..."
    
    # Check if Ollama is installed
    if ! command -v ollama &> /dev/null; then
        echo "❌ Ollama is not installed. Please install it first:"
        echo "   https://ollama.ai"
        return 1
    else
        echo "✅ Ollama is installed"
    fi
    
    # Check if kozlov-hermes model exists
    if ! ollama list | grep -q "kozlov-hermes"; then
        echo "❌ kozlov-hermes model not found"
        echo "Please install the model first or create it:"
        echo "   ollama pull hermes2  # or your preferred base model"
        echo "   # Then create kozlov-hermes from your Modelfile"
        return 1
    else
        echo "✅ kozlov-hermes model is available"
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo "❌ Python 3 is not installed"
        return 1
    else
        echo "✅ Python 3 is installed"
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js is not installed. Needed for news server."
        return 1
    else
        echo "✅ Node.js is installed"
    fi
    
    return 0
}

# Function to install Python dependencies
install_python_deps() {
    echo "📦 Installing Python dependencies..."
    pip3 install aiohttp requests > /dev/null 2>&1 || {
        echo "❌ Failed to install Python dependencies"
        echo "Please run manually: pip3 install aiohttp requests"
        return 1
    }
    echo "✅ Python dependencies installed"
}

# Function to install Node.js dependencies for news server
install_node_deps() {
    echo "📦 Installing Node.js dependencies for news server..."
    cd "$SCRIPT_DIR/WebScraper"
    if npm install > /dev/null 2>&1; then
        echo "✅ Node.js dependencies installed"
        cd "$SCRIPT_DIR"
        return 0
    else
        echo "❌ Failed to install Node.js dependencies"
        echo "Please run manually: cd WebScraper && npm install"
        cd "$SCRIPT_DIR"
        return 1
    fi
}

# Function to test the news server
test_news_server() {
    echo "🧪 Testing news server..."
    
    cd "$SCRIPT_DIR/WebScraper"
    
    # Start server in background
    nohup node server.js > /dev/null 2>&1 &
    SERVER_PID=$!
    
    # Wait a moment for server to start
    sleep 3
    
    # Test if server is responding
    if curl -s http://localhost:3000/health > /dev/null 2>&1; then
        echo "✅ News server is working"
        kill $SERVER_PID > /dev/null 2>&1
        cd "$SCRIPT_DIR"
        return 0
    else
        echo "❌ News server test failed"
        kill $SERVER_PID > /dev/null 2>&1
        cd "$SCRIPT_DIR"
        return 1
    fi
}

# Function to test the intelligence agent
test_intelligence_agent() {
    echo "🧪 Testing Viktor Intelligence Agent..."
    
    cd "$SCRIPT_DIR/WebScraper"
    nohup node server.js > /dev/null 2>&1 &
    SERVER_PID=$!
    sleep 3
    
    cd "$SCRIPT_DIR"
    
    if python3 viktor-intelligence-agent.py --test; then
        echo "✅ Intelligence Agent is working"
        kill $SERVER_PID > /dev/null 2>&1
        return 0
    else
        echo "❌ Intelligence Agent test failed"
        kill $SERVER_PID > /dev/null 2>&1
        return 1
    fi
}

# Function to create a quick-start script
create_quickstart() {
    echo "📝 Creating quick-start script..."
    
    cat > "$SCRIPT_DIR/start-viktor.sh" << 'EOF'
#!/bin/bash

# Viktor Kozlov Quick Start Script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "🌍 Starting Viktor Kozlov Intelligence System"
echo "============================================"

# Start news server
echo "🚀 Starting news server..."
cd "$SCRIPT_DIR/WebScraper"
nohup node server.js > /dev/null 2>&1 &
NEWS_SERVER_PID=$!

# Wait for server to start
sleep 3

# Check if server is running
if curl -s http://localhost:3000/health > /dev/null 2>&1; then
    echo "✅ News server is running (PID: $NEWS_SERVER_PID)"
else
    echo "❌ Failed to start news server"
    exit 1
fi

cd "$SCRIPT_DIR"

echo ""
echo "🧠 Viktor Kozlov Intelligence Agent Ready"
echo "========================================"
echo "Available modes:"
echo "1. Interactive Intelligence Terminal:"
echo "   python3 viktor-intelligence-agent.py --interactive"
echo ""
echo "2. Single Query Mode:"
echo "   python3 viktor-intelligence-agent.py --query 'What is happening in Ukraine?'"
echo ""
echo "3. Enhanced Integration Script:"
echo "   ./kozlov-enhanced.sh interactive"
echo ""
echo "4. Classic Integration Script:"
echo "   ./kozlov-integration.sh"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep script running and handle cleanup
cleanup() {
    echo ""
    echo "🔒 Shutting down Viktor Intelligence System..."
    kill $NEWS_SERVER_PID > /dev/null 2>&1
    echo "✅ News server stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep running
while true; do
    sleep 1
done
EOF

    chmod +x "$SCRIPT_DIR/start-viktor.sh"
    echo "✅ Quick-start script created: start-viktor.sh"
}

# Function to show usage examples
show_usage() {
    echo ""
    echo "🎯 Viktor Kozlov Intelligence System Ready!"
    echo "=========================================="
    echo ""
    echo "Quick Start:"
    echo "  ./start-viktor.sh                    # Start all services"
    echo ""
    echo "Intelligence Agent (Recommended):"
    echo "  python3 viktor-intelligence-agent.py --interactive"
    echo "  python3 viktor-intelligence-agent.py --query 'Analyze current geopolitical situation'"
    echo ""
    echo "Enhanced Integration:"
    echo "  ./kozlov-enhanced.sh interactive     # Interactive mode with tools"
    echo "  ./kozlov-enhanced.sh morning         # Morning briefing"
    echo "  ./kozlov-enhanced.sh topic 'Ukraine' # Topic analysis"
    echo ""
    echo "Classic Mode:"
    echo "  ./kozlov-integration.sh              # Original integration"
    echo ""
    echo "Tools Testing:"
    echo "  python3 viktor-intelligence-agent.py --test"
    echo "  python3 viktor-tools-api.py test"
    echo ""
    echo "News Dashboard:"
    echo "  Open http://localhost:3000 in your browser"
    echo ""
}

# Main setup process
main() {
    echo "Starting setup process..."
    echo ""
    
    # Check requirements
    if ! check_requirements; then
        echo "❌ Setup failed - missing requirements"
        exit 1
    fi
    
    echo ""
    
    # Install dependencies
    if ! install_python_deps; then
        echo "❌ Setup failed - Python dependencies"
        exit 1
    fi
    
    if ! install_node_deps; then
        echo "❌ Setup failed - Node.js dependencies"
        exit 1
    fi
    
    echo ""
    
    # Test components
    if ! test_news_server; then
        echo "❌ Setup failed - news server test"
        exit 1
    fi
    
    if ! test_intelligence_agent; then
        echo "❌ Setup failed - intelligence agent test"
        exit 1
    fi
    
    echo ""
    
    # Create quick-start script
    create_quickstart
    
    echo ""
    echo "✅ Setup completed successfully!"
    
    # Show usage
    show_usage
}

# Run setup
main "$@"
