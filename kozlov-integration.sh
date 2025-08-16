#!/bin/bash

# Viktor Intelligence Integration Script
# Gathers current intelligence and feeds it to Viktor for analysis

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PYTHON_SCRIPT="$SCRIPT_DIR/kozlov-intelligence.py"

echo "🌍 Viktor Kozlov Intelligence Briefing System"
echo "============================================"

# Function to gather intelligence and feed to Viktor
viktor_briefing() {
    local briefing_type="$1"
    local region="$2"
    local topic="$3"
    
    echo "📡 Gathering intelligence..."
    local intelligence=""
    local prompt=""
    local cmd_exit=0
    
    case "$briefing_type" in
        "morning")
            echo "🌅 Preparing morning intelligence briefing..."
            # Use global region + key topics, include brief markdown
            if ! intelligence=$(python3 "$PYTHON_SCRIPT" --region global --topics economics,security --brief 2>/dev/null); then
                cmd_exit=$?
            fi
            prompt="Viktor, here is the latest synthesized intelligence (global + economics + security):\n\n$intelligence\n\nProvide professional analysis and strategic assessment.";
            ;;
        "region")
            echo "🗺️  Preparing regional intelligence briefing for $region..."
            if ! intelligence=$(python3 "$PYTHON_SCRIPT" --region "$region" --brief 2>/dev/null); then
                cmd_exit=$?
            fi
            prompt="Viktor, here is current intelligence from $region region:\n\n$intelligence\n\nProvide geopolitical analysis and assessment.";
            ;;
        "topic")
            echo "🎯 Preparing topical intelligence briefing on $topic..."
            if ! intelligence=$(python3 "$PYTHON_SCRIPT" --topics "$topic" --brief 2>/dev/null); then
                cmd_exit=$?
            fi
            prompt="Viktor, here is intelligence gathered on $topic:\n\n$intelligence\n\nProvide expert analysis and strategic implications.";
            ;;
        "crisis")
            echo "🚨 Preparing crisis monitoring briefing..."
            if ! intelligence=$(python3 "$PYTHON_SCRIPT" --crisis "$topic" --brief 2>/dev/null); then
                cmd_exit=$?
            fi
            prompt="Viktor, here is real-time intelligence on the developing situation regarding $topic:\n\n$intelligence\n\nProvide urgent assessment and risk outlook.";
            ;;
        *)
            echo "❌ Unknown briefing type: $briefing_type"
            echo "Available types: morning, region, topic, crisis"
            return 1
            ;;
    esac

    if [ $cmd_exit -ne 0 ] || [ -z "$intelligence" ]; then
        echo "⚠️  Intelligence collection failed (exit code $cmd_exit). Aborting LLM analysis to avoid generic fallback."
        return 1
    fi
    
    echo "🧠 Analyzing with Viktor Kozlov..."
    echo "================================="
    echo -e "$prompt" | ollama run kozlov-hermes
}

# Function to install Python dependencies
install_dependencies() {
    echo "📦 Installing Python dependencies..."
    pip3 install requests beautifulsoup4 feedparser python-dateutil >/dev/null || {
        echo "❌ Failed to install dependencies. Run manually:"
        echo "   pip3 install requests beautifulsoup4 feedparser python-dateutil"
        return 1
    }
    echo "✅ Dependencies installed"
}

# Function to create the Python intelligence script if it doesn't exist
create_intelligence_script() {
    if [ ! -f "$PYTHON_SCRIPT" ]; then
        echo "📝 Creating legacy intelligence gathering script (deprecated path)..."
        
        cat > "$PYTHON_SCRIPT" << 'PYTHON_EOF'
#!/usr/bin/env python3
import requests
import feedparser
import json
import argparse
import sys
from datetime import datetime, timedelta

def gather_morning_briefing():
    """Gather morning intelligence briefing"""
    sources = [
        'https://feeds.reuters.com/reuters/topNews',
        'https://feeds.bbci.co.uk/news/world/rss.xml',
        'https://rss.cnn.com/rss/edition.rss'
    ]
    
    articles = []
    for source in sources:
        try:
            feed = feedparser.parse(source)
            for entry in feed.entries[:5]:
                articles.append({
                    'title': entry.title,
                    'summary': getattr(entry, 'summary', '')[:300],
                    'source': feed.feed.get('title', 'Unknown'),
                    'url': entry.link
                })
        except:
            continue
    
    briefing = "MORNING INTELLIGENCE BRIEFING\n"
    briefing += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    briefing += "=" * 50 + "\n\n"
    
    for i, article in enumerate(articles[:10], 1):
        briefing += f"{i}. {article['title']}\n"
        briefing += f"   Source: {article['source']}\n"
        briefing += f"   Summary: {article['summary']}\n"
        briefing += f"   URL: {article['url']}\n\n"
    
    return briefing

def gather_regional_intelligence(region):
    """Gather regional intelligence"""
    region_sources = {
        'europe': ['https://feeds.bbci.co.uk/news/world/europe/rss.xml'],
        'middle-east': ['https://feeds.bbci.co.uk/news/world/middle_east/rss.xml'],
        'asia': ['https://feeds.bbci.co.uk/news/world/asia/rss.xml'],
        'africa': ['https://feeds.bbci.co.uk/news/world/africa/rss.xml']
    }
    
    sources = region_sources.get(region, ['https://feeds.reuters.com/reuters/topNews'])
    articles = []
    
    for source in sources:
        try:
            feed = feedparser.parse(source)
            for entry in feed.entries[:8]:
                articles.append({
                    'title': entry.title,
                    'summary': getattr(entry, 'summary', '')[:300],
                    'source': feed.feed.get('title', 'Unknown'),
                    'url': entry.link
                })
        except:
            continue
    
    briefing = f"REGIONAL INTELLIGENCE: {region.upper()}\n"
    briefing += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    briefing += "=" * 50 + "\n\n"
    
    for i, article in enumerate(articles[:8], 1):
        briefing += f"{i}. {article['title']}\n"
        briefing += f"   Source: {article['source']}\n"
        briefing += f"   Summary: {article['summary']}\n\n"
    
    return briefing

def gather_topical_intelligence(topics):
    """Gather intelligence on specific topics"""
    sources = [
        'https://feeds.reuters.com/reuters/topNews',
        'https://feeds.bbci.co.uk/news/world/rss.xml'
    ]
    
    articles = []
    topic_keywords = topics.split(',')
    
    for source in sources:
        try:
            feed = feedparser.parse(source)
            for entry in feed.entries:
                title_lower = entry.title.lower()
                summary_lower = getattr(entry, 'summary', '').lower()
                
                if any(keyword.strip().lower() in title_lower or keyword.strip().lower() in summary_lower 
                       for keyword in topic_keywords):
                    articles.append({
                        'title': entry.title,
                        'summary': getattr(entry, 'summary', '')[:300],
                        'source': feed.feed.get('title', 'Unknown'),
                        'url': entry.link,
                        'matched_topics': [kw.strip() for kw in topic_keywords 
                                         if kw.strip().lower() in title_lower or kw.strip().lower() in summary_lower]
                    })
        except:
            continue
    
    briefing = f"TOPICAL INTELLIGENCE: {topics.upper()}\n"
    briefing += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    briefing += "=" * 50 + "\n\n"
    
    for i, article in enumerate(articles[:10], 1):
        briefing += f"{i}. {article['title']}\n"
        briefing += f"   Source: {article['source']}\n"
        briefing += f"   Matched Topics: {', '.join(article['matched_topics'])}\n"
        briefing += f"   Summary: {article['summary']}\n\n"
    
    return briefing

def main():
    parser = argparse.ArgumentParser(description='Viktor Kozlov Intelligence Gathering')
    parser.add_argument('--briefing', choices=['morning'], help='Type of briefing')
    parser.add_argument('--region', help='Regional intelligence focus')
    parser.add_argument('--topics', help='Comma-separated topics to monitor')
    parser.add_argument('--crisis', help='Crisis keywords to monitor')
    
    args = parser.parse_args()
    
    if args.briefing == 'morning':
        print(gather_morning_briefing())
    elif args.region:
        print(gather_regional_intelligence(args.region))
    elif args.topics:
        print(gather_topical_intelligence(args.topics))
    elif args.crisis:
        print(gather_topical_intelligence(args.crisis))  # Reuse topical for crisis
    else:
        print("No valid option specified")
        sys.exit(1)

if __name__ == "__main__":
    main()
PYTHON_EOF

        chmod +x "$PYTHON_SCRIPT"
        echo "✅ Intelligence gathering script created"
    fi
}

# Main menu function
show_menu() {
    echo ""
    echo "Viktor Kozlov Intelligence Options:"
    echo "1. Morning Intelligence Briefing"
    echo "2. Regional Intelligence (e.g. europe, middle_east, asia, economics, security)"
    echo "3. Topical Intelligence (comma topics)"
    echo "4. Crisis Monitoring (keywords)"
    echo "5. Install Dependencies"
    echo "6. Exit"
    echo ""
}

# Main execution
main() {
    # Check if Viktor model exists
    if ! ollama list | grep -q "kozlov-hermes"; then
        echo "❌ kozlov-hermes model not found. Ensure it is installed."
        exit 1
    fi
    
    # Do not auto-create legacy script if modern one exists

    # Interactive mode if no arguments
    if [ $# -eq 0 ]; then
        while true; do
            show_menu
            read -p "Choose an option (1-6): " choice
            
            case $choice in
                1)
                    viktor_briefing "morning"
                    ;;
                2)
                    read -p "Enter region: " region
                    viktor_briefing "region" "$region"
                    ;;
                3)
                    read -p "Enter topics (comma-separated): " topics
                    viktor_briefing "topic" "" "$topics"
                    ;;
                4)
                    read -p "Enter crisis keywords (comma-separated): " crisis
                    viktor_briefing "crisis" "" "$crisis"
                    ;;
                5)
                    install_dependencies
                    ;;
                6)
                    echo "Goodbye!"
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
            viktor_briefing "morning"
            ;;
        region)
            viktor_briefing "region" "$2"
            ;;
        topic)
            viktor_briefing "topic" "" "$2"
            ;;
        crisis)
            viktor_briefing "crisis" "" "$2"
            ;;
        install-dependencies)
            install_dependencies
            ;;
        *)
            echo "Usage: $0 [morning|region <region>|topic <topics>|crisis <keywords>|install-dependencies]"
            echo "Or run without arguments for interactive mode"
            ;;
    esac
}

main "$@"