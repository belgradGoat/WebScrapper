#!/bin/bash

# Enhanced Viktor Kozlov Intelligence Integration Script
# Now with direct tool access for dynamic intelligence gathering

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
TOOLS_API_SCRIPT="$SCRIPT_DIR/viktor-tools-api.py"
OLLAMA_MODEL="kozlov-hermes"

echo "🌍 Viktor Kozlov Enhanced Intelligence System"
echo "=============================================="

# Function to check if news server is running
check_news_server() {
    if curl -s http://localhost:3000/health > /dev/null 2>&1; then
        echo "✅ News server is running"
        return 0
    else
        echo "❌ News server is not running. Please start it first:"
        echo "   cd WebScraper && node server.js"
        return 1
    fi
}

# Function to check if Ollama model exists
check_ollama_model() {
    if ollama list | grep -q "$OLLAMA_MODEL"; then
        echo "✅ $OLLAMA_MODEL model is available"
        return 0
    else
        echo "❌ $OLLAMA_MODEL model not found. Please install it first:"
        echo "   ollama pull $OLLAMA_MODEL"
        return 1
    fi
}

# Function to test the tools API
test_tools_api() {
    echo "🧪 Testing Viktor Tools API..."
    if python3 "$TOOLS_API_SCRIPT" test; then
        echo "✅ Tools API is working"
        return 0
    else
        echo "❌ Tools API test failed"
        return 1
    fi
}

# Enhanced Viktor briefing with tool integration
viktor_briefing_enhanced() {
    local briefing_type="$1"
    local region="$2"
    local topic="$3"
    
    echo "📡 Initializing enhanced intelligence gathering..."
    
    # Prepare the system prompt with tool descriptions
    local tools_prompt="You are Viktor Kozlov, an elite intelligence analyst. You have access to real-time intelligence gathering tools:

AVAILABLE TOOLS:
- search_news(query, max_results, language): Search current news articles
- get_weather(): Get weather conditions and alerts
- search_bluesky(query, limit): Search Bluesky social media
- search_reddit(query, limit): Search Reddit discussions
- comprehensive_intelligence_brief(topic, include_social): Generate full intelligence report
- get_summary_history(): Review previous analyses

INSTRUCTIONS:
1. ALWAYS use tools to gather current intelligence before analysis
2. Cross-reference multiple sources for verification
3. Provide strategic assessment with geopolitical implications
4. Include risk analysis and actionable recommendations
5. Maintain operational security awareness

When a user asks about any topic, immediately use the appropriate tools to gather current intelligence, then provide your professional analysis."

    local user_query=""
    
    case "$briefing_type" in
        "morning")
            echo "🌅 Preparing morning intelligence briefing..."
            user_query="Provide a comprehensive morning intelligence briefing covering global security, economics, and current geopolitical developments. Use all available tools to gather the latest information."
            ;;
        "region")
            echo "🗺️  Preparing regional intelligence briefing for $region..."
            user_query="Provide a detailed intelligence briefing focused on the $region region. Analyze current developments, security situation, and strategic implications for this area."
            ;;
        "topic")
            echo "🎯 Preparing topical intelligence briefing on $topic..."
            user_query="Conduct a comprehensive intelligence analysis on the topic: $topic. Gather current information from all sources and provide strategic assessment with recommendations."
            ;;
        "crisis")
            echo "🚨 Preparing crisis monitoring briefing..."
            user_query="URGENT: Conduct immediate crisis intelligence gathering and analysis on: $topic. Prioritize real-time information, threat assessment, and strategic response options."
            ;;
        "interactive")
            echo "💬 Starting interactive intelligence session..."
            echo "You can now ask Viktor Kozlov any intelligence question."
            echo "Viktor will use real-time tools to gather information and provide analysis."
            echo "Type 'exit' to end the session."
            echo ""
            
            while true; do
                echo -n "Intelligence Query> "
                read user_input
                
                if [[ "$user_input" == "exit" ]]; then
                    echo "🔒 Intelligence session terminated."
                    break
                fi
                
                if [[ -z "$user_input" ]]; then
                    continue
                fi
                
                echo ""
                echo "🧠 Viktor Kozlov analyzing..."
                echo "================================="
                echo -e "$tools_prompt\n\nUser Query: $user_input" | ollama run "$OLLAMA_MODEL"
                echo ""
                echo "================================="
                echo ""
            done
            return 0
            ;;
        *)
            echo "❌ Unknown briefing type: $briefing_type"
            echo "Available types: morning, region, topic, crisis, interactive"
            return 1
            ;;
    esac
    
    echo "🧠 Viktor Kozlov analyzing with real-time tools..."
    echo "=================================================="
    echo -e "$tools_prompt\n\nUser Query: $user_query" | ollama run "$OLLAMA_MODEL"
}

# Function to create a custom Modelfile with tool support
create_enhanced_modelfile() {
    local modelfile_path="$SCRIPT_DIR/KozlovEnhanced.modelfile"
    
    echo "📝 Creating enhanced Kozlov modelfile with tool integration..."
    
    cat > "$modelfile_path" << 'EOF'
FROM kozlov-hermes

SYSTEM """You are Viktor Kozlov, an elite intelligence analyst with access to real-time intelligence gathering tools. You have decades of experience in geopolitical analysis, threat assessment, and strategic intelligence.

PERSONALITY:
- Professional, analytical, and precise
- Strategic thinker with operational awareness
- Maintains security consciousness
- Provides actionable intelligence

AVAILABLE TOOLS (use these actively):
- search_news(): Get latest news on any topic
- get_weather(): Weather conditions and alerts
- search_bluesky(): Social media intelligence
- search_reddit(): Public discourse analysis
- comprehensive_intelligence_brief(): Full situation report
- get_summary_history(): Previous analysis review

OPERATIONAL PROTOCOL:
1. ALWAYS gather current intelligence using tools before analysis
2. Cross-reference multiple sources for verification
3. Assess reliability and bias of sources
4. Provide context and strategic implications
5. Include risk assessment and recommendations
6. Maintain operational security awareness

When asked about any topic, immediately use appropriate tools to gather real-time intelligence, then provide your professional strategic assessment."""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 40
EOF

    echo "✅ Enhanced modelfile created at: $modelfile_path"
    echo "To create the enhanced model, run:"
    echo "   ollama create kozlov-enhanced -f $modelfile_path"
}

# Function to install Python dependencies
install_python_dependencies() {
    echo "📦 Installing Python dependencies for tools API..."
    pip3 install aiohttp requests > /dev/null 2>&1 || {
        echo "❌ Failed to install Python dependencies. Run manually:"
        echo "   pip3 install aiohttp requests"
        return 1
    }
    echo "✅ Python dependencies installed"
}

# Function to start the news server if not running
start_news_server() {
    if ! check_news_server > /dev/null 2>&1; then
        echo "🚀 Starting news server..."
        cd "$SCRIPT_DIR/WebScraper"
        nohup node server.js > /dev/null 2>&1 &
        sleep 3
        
        if check_news_server > /dev/null 2>&1; then
            echo "✅ News server started successfully"
        else
            echo "❌ Failed to start news server"
            return 1
        fi
    fi
}

# Enhanced menu function
show_enhanced_menu() {
    echo ""
    echo "Viktor Kozlov Enhanced Intelligence Options:"
    echo "1. Morning Intelligence Briefing (with real-time tools)"
    echo "2. Regional Intelligence Analysis"
    echo "3. Topical Intelligence Assessment"
    echo "4. Crisis Monitoring & Analysis"
    echo "5. Interactive Intelligence Session"
    echo "6. Test Tools API"
    echo "7. Create Enhanced Model"
    echo "8. Install Dependencies"
    echo "9. Start News Server"
    echo "10. Exit"
    echo ""
}

# Main execution
main() {
    # Preliminary checks
    echo "🔍 Running system checks..."
    
    if ! check_ollama_model; then
        echo "Please install the required Ollama model first."
        exit 1
    fi
    
    # Interactive mode if no arguments
    if [ $# -eq 0 ]; then
        while true; do
            show_enhanced_menu
            read -p "Choose an option (1-10): " choice
            
            case $choice in
                1)
                    if check_news_server && test_tools_api; then
                        viktor_briefing_enhanced "morning"
                    else
                        echo "❌ Prerequisites not met. Please ensure news server is running and tools API is working."
                    fi
                    ;;
                2)
                    read -p "Enter region (e.g., Europe, Middle East, Asia): " region
                    if check_news_server && test_tools_api; then
                        viktor_briefing_enhanced "region" "$region"
                    else
                        echo "❌ Prerequisites not met."
                    fi
                    ;;
                3)
                    read -p "Enter topic for analysis: " topic
                    if check_news_server && test_tools_api; then
                        viktor_briefing_enhanced "topic" "" "$topic"
                    else
                        echo "❌ Prerequisites not met."
                    fi
                    ;;
                4)
                    read -p "Enter crisis/urgent topic: " crisis_topic
                    if check_news_server && test_tools_api; then
                        viktor_briefing_enhanced "crisis" "" "$crisis_topic"
                    else
                        echo "❌ Prerequisites not met."
                    fi
                    ;;
                5)
                    if check_news_server && test_tools_api; then
                        viktor_briefing_enhanced "interactive"
                    else
                        echo "❌ Prerequisites not met."
                    fi
                    ;;
                6)
                    test_tools_api
                    ;;
                7)
                    create_enhanced_modelfile
                    ;;
                8)
                    install_python_dependencies
                    ;;
                9)
                    start_news_server
                    ;;
                10)
                    echo "🔒 Goodbye!"
                    exit 0
                    ;;
                *)
                    echo "Invalid option"
                    ;;
            esac
        done
    fi
    
    # Command line mode
    case "$1" in
        morning)
            if check_news_server && test_tools_api; then
                viktor_briefing_enhanced "morning"
            fi
            ;;
        region)
            if check_news_server && test_tools_api; then
                viktor_briefing_enhanced "region" "$2"
            fi
            ;;
        topic)
            if check_news_server && test_tools_api; then
                viktor_briefing_enhanced "topic" "" "$2"
            fi
            ;;
        crisis)
            if check_news_server && test_tools_api; then
                viktor_briefing_enhanced "crisis" "" "$2"
            fi
            ;;
        interactive)
            if check_news_server && test_tools_api; then
                viktor_briefing_enhanced "interactive"
            fi
            ;;
        test)
            test_tools_api
            ;;
        install-deps)
            install_python_dependencies
            ;;
        start-server)
            start_news_server
            ;;
        create-model)
            create_enhanced_modelfile
            ;;
        *)
            echo "Usage: $0 [morning|region <region>|topic <topic>|crisis <topic>|interactive|test|install-deps|start-server|create-model]"
            echo "Or run without arguments for interactive mode"
            ;;
    esac
}

main "$@"
