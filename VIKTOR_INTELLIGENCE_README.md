# Viktor Kozlov Intelligence System with Tool Access

This enhanced intelligence system gives your kozlov-hermes Ollama model real-time access to news dashboard tools, enabling dynamic information gathering and analysis.

## 🎯 What This Does

Your Viktor Kozlov LLM can now:
- **Search news** in real-time using multiple sources (Reuters, BBC, Guardian, etc.)
- **Get weather** conditions and alerts
- **Search social media** (Bluesky, Reddit) for public discourse analysis
- **Generate AI summaries** using all gathered intelligence
- **Access historical** intelligence summaries
- **Combine multiple sources** for comprehensive strategic assessments

When you ask Viktor a question, he will automatically:
1. **Identify** what intelligence he needs
2. **Use tools** to gather current information
3. **Analyze** the gathered data
4. **Provide** strategic assessment with recommendations

## 🚀 Quick Setup

```bash
# 1. Run the setup script
./setup-viktor.sh

# 2. Start the system
./start-viktor.sh

# 3. Use Viktor with tools
python3 viktor-intelligence-agent.py --interactive
```

## 📋 Prerequisites

- **Ollama** installed with `kozlov-hermes` model
- **Node.js** for the news server
- **Python 3** with pip
- Internet connection for real-time data

## 🛠️ Components

### 1. Viktor Intelligence Agent (`viktor-intelligence-agent.py`)
**The main interface** - Recommended way to use the system.

```bash
# Interactive mode - ask anything, Viktor uses tools automatically
python3 viktor-intelligence-agent.py --interactive

# Single query mode
python3 viktor-intelligence-agent.py --query "Analyze the situation in Eastern Europe"

# Test tool connectivity
python3 viktor-intelligence-agent.py --test
```

**Example interaction:**
```
Intelligence Query> What's happening with AI regulations in Europe?

🧠 Viktor's initial assessment:
I need to search news about AI regulations in Europe to provide current analysis...

🔧 Executing 1 intelligence gathering operations...
   • search_news with parameters: {'query': 'AI regulations Europe', 'max_results': 20}

🛠️ INTELLIGENCE TOOLS DEPLOYED: search_news

📊 REAL-TIME INTELLIGENCE GATHERED:
==================================================
📰 NEWS INTELLIGENCE (15 articles):
1. EU AI Act Implementation Timeline Released
   Source: Reuters
   The European Union has published detailed implementation guidelines...

[Viktor provides comprehensive analysis based on current data]
```

### 2. Enhanced Integration Script (`kozlov-enhanced.sh`)
Traditional shell-based interface with tool integration.

```bash
# Interactive intelligence session
./kozlov-enhanced.sh interactive

# Morning briefing with tools
./kozlov-enhanced.sh morning

# Regional analysis
./kozlov-enhanced.sh region "Middle East"

# Topic-specific analysis
./kozlov-enhanced.sh topic "cryptocurrency regulation"
```

### 3. Tools API (`viktor-tools-api.py`)
Standalone tools API for testing and development.

```bash
# Test all tools
python3 viktor-tools-api.py test

# Generate intelligence brief
python3 viktor-tools-api.py brief --topic "artificial intelligence" --social

# Search news
python3 viktor-tools-api.py search --query "economic policy"

# List available tools
python3 viktor-tools-api.py tools-list
```

### 4. News Dashboard Server
Web-based dashboard for manual intelligence gathering.

```bash
cd WebScraper
node server.js

# Then open http://localhost:3000
```

## 🎮 Usage Examples

### Strategic Intelligence Analysis
```bash
python3 viktor-intelligence-agent.py --query "Provide strategic assessment of current tensions in the South China Sea, including military movements, diplomatic responses, and economic implications"
```

Viktor will:
1. Search news about South China Sea tensions
2. Check for weather conditions (relevant for naval operations)
3. Search social media for public discourse
4. Provide comprehensive strategic assessment

### Crisis Monitoring
```bash
./kozlov-enhanced.sh crisis "cyber attack infrastructure"
```

### Economic Intelligence
```bash
python3 viktor-intelligence-agent.py --query "Analyze global inflation trends and their impact on emerging markets"
```

### Social Media Sentiment Analysis
```bash
python3 viktor-intelligence-agent.py --query "What are people saying about the upcoming elections on social media?"
```

## 🔧 Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `search_news` | Search current news articles | `query`, `max_results`, `language` |
| `get_weather` | Get weather conditions and alerts | `lat`, `lon` (optional) |
| `search_bluesky` | Search Bluesky social media | `query`, `limit` |
| `search_reddit` | Search Reddit discussions | `query`, `limit` |
| `comprehensive_intelligence_brief` | Generate full intelligence report | `topic`, `include_social` |
| `get_summary_history` | Review previous analyses | None |

## 🤖 How Viktor Uses Tools

Viktor automatically detects when he needs current information:

- **"What's happening in Ukraine?"** → Searches news, social media
- **"Current weather conditions?"** → Gets weather data
- **"Public opinion on AI?"** → Searches social media
- **"Comprehensive analysis of..."** → Uses multiple tools

## 🔒 Security & Privacy

- All tools use public APIs and data sources
- No sensitive data is stored permanently
- Social media searches use public posts only
- Weather data from US National Weather Service

## 🛡️ Troubleshooting

### News Server Not Running
```bash
cd WebScraper
node server.js
# Or use: ./start-viktor.sh
```

### Tool Connectivity Issues
```bash
python3 viktor-intelligence-agent.py --test
```

### Missing Dependencies
```bash
./setup-viktor.sh  # Reinstall everything
```

### Ollama Model Issues
```bash
ollama list  # Check if kozlov-hermes exists
ollama pull hermes2  # Pull base model if needed
```

## 📈 Advanced Usage

### Custom Tool Combinations
```python
# Example: Custom intelligence brief
python3 viktor-tools-api.py brief --topic "renewable energy policy" --social
```

### Historical Analysis
```python
# Viktor can reference previous analyses
python3 viktor-intelligence-agent.py --query "Compare current Ukraine situation to your analysis from last week"
```

### Multi-Source Verification
Viktor automatically cross-references multiple sources for accuracy and bias detection.

## 🔄 System Architecture

```
User Query → Viktor LLM → Tool Detection → API Calls → Data Gathering → Analysis → Response
     ↑                                         ↓
     └── Enhanced Response ←─ Intelligence Formatting ←─┘
```

1. **Query Processing**: Viktor analyzes what intelligence is needed
2. **Tool Selection**: Automatically chooses appropriate tools
3. **Data Gathering**: Executes API calls to news/weather/social platforms
4. **Intelligence Synthesis**: Combines and analyzes gathered data
5. **Strategic Assessment**: Provides professional analysis with recommendations

## 📊 Data Sources

- **News**: Reuters, BBC, Guardian, Google News, AP, Bloomberg
- **Weather**: US National Weather Service
- **Social Media**: Bluesky, Reddit (public posts)
- **AI Summaries**: Local Gemma model integration

## 🎯 Next Steps

1. **Run Setup**: `./setup-viktor.sh`
2. **Start System**: `./start-viktor.sh`
3. **Try Interactive Mode**: `python3 viktor-intelligence-agent.py --interactive`
4. **Ask Viktor**: "What should I know about current global events?"

Viktor will gather the intelligence and provide professional strategic assessment based on real-time data!

---

**Created for enhanced LLM intelligence capabilities with real-time tool access.**
