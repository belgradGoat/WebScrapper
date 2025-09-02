# Eagle Watchtower MCP Server

## Overview
This MCP (Model Context Protocol) server provides LLM access to the Eagle Watchtower news aggregation platform, enabling AI agents to search news, monitor social media, generate summaries, and access weather data.

## Features

### 🔍 News & Media Search
- **Multi-source news aggregation** from GNews API, web scraping, Google News RSS, and Guardian API
- **Social media monitoring** via Reddit and Bluesky APIs
- **Combined search** across all sources simultaneously

### 🤖 AI Analysis
- **Gemma-powered summarization** with weighted source analysis (70% news, 30% social)
- **Historical summary retrieval** from MongoDB
- **Custom prompt support** for tailored analysis

### 🌦️ Additional Services
- **Weather information** from US National Weather Service
- **Location-based forecasts** and current conditions

## Installation

### Prerequisites
1. Node.js 18+ installed
2. Eagle Watchtower running on port 3000
3. LM Studio or Claude Desktop for MCP client

### Setup Steps

1. **Install Eagle Watchtower dependencies** (if not already done):
```bash
cd /Users/sebastianszewczyk/Documents/GitHub/WebScrapper/WebScraper
npm install
```

2. **Install MCP server dependencies**:
```bash
npm install --save @modelcontextprotocol/sdk node-fetch
# OR use the package-mcp.json:
npm install --prefix . --package-lock-only --package=package-mcp.json
```

3. **Start Eagle Watchtower**:
```bash
node server.js
# Dashboard will be available at http://localhost:3000
```

4. **Test the MCP server**:
```bash
node eagle-watchtower-mcp.js
# Should show: "[MCP] Eagle Watchtower MCP Server is running"
```

## Configuration

### For Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "eagle-watchtower": {
      "command": "node",
      "args": [
        "/Users/sebastianszewczyk/Documents/GitHub/WebScrapper/WebScraper/eagle-watchtower-mcp.js"
      ],
      "env": {
        "EAGLE_API_URL": "http://localhost:3000"
      }
    }
  }
}
```

### For LM Studio

LM Studio doesn't natively support MCP, but you can use it through:

1. **Option A: OpenAI-compatible API mode**
   - Configure LM Studio to expose an OpenAI-compatible endpoint
   - Use a bridge script to connect MCP tools to function calls

2. **Option B: Custom integration script**
   ```python
   # lm_studio_mcp_bridge.py
   import subprocess
   import json
   
   def call_mcp_tool(tool_name, args):
       # Communicate with MCP server via stdio
       process = subprocess.Popen(
           ['node', 'eagle-watchtower-mcp.js'],
           stdin=subprocess.PIPE,
           stdout=subprocess.PIPE,
           stderr=subprocess.PIPE
       )
       
       # Send tool call request
       request = {
           "jsonrpc": "2.0",
           "method": "tools/call",
           "params": {
               "name": tool_name,
               "arguments": args
           },
           "id": 1
       }
       
       stdout, stderr = process.communicate(json.dumps(request).encode())
       return json.loads(stdout)
   ```

3. **Option C: HTTP wrapper for LM Studio**
   Create an HTTP server that LM Studio can call:
   ```javascript
   // lm-studio-bridge.js
   const express = require('express');
   const { exec } = require('child_process');
   const app = express();
   app.use(express.json());
   
   app.post('/mcp/:tool', async (req, res) => {
     // Forward to MCP server
     // Return results to LM Studio
   });
   
   app.listen(3001);
   ```

## Available Tools

### 1. `search_news`
Search across multiple news sources.

**Parameters:**
- `query` (required): Search keyword
- `max_results`: Maximum results (default: 20)
- `language`: Language code (default: "en")
- `country`: Country code (default: "us")

**Example:**
```json
{
  "tool": "search_news",
  "arguments": {
    "query": "artificial intelligence",
    "max_results": 10
  }
}
```

### 2. `search_bluesky`
Search Bluesky social media posts.

**Parameters:**
- `query` (required): Search term
- `limit`: Max posts (default: 50, max: 100)

### 3. `search_reddit`
Search Reddit posts and discussions.

**Parameters:**
- `query` (required): Search term
- `limit`: Max posts (default: 50, max: 100)

### 4. `search_all_sources`
Combined search across news and social media.

**Parameters:**
- `query` (required): Search term
- `max_results_per_source`: Results per source (default: 20)

### 5. `generate_ai_summary`
Create AI-powered analysis using Gemma.

**Parameters:**
- `query` (required): Topic to analyze
- `custom_prompt`: Optional custom instruction
- `include_social`: Include social media (default: true)

### 6. `get_weather`
Fetch weather information.

**Parameters:**
- `latitude`: Optional latitude
- `longitude`: Optional longitude

### 7. `get_summary_history`
Retrieve past AI summaries.

**Parameters:**
- `limit`: Number of summaries (default: 10)

## Usage Examples

### With Claude Desktop
Once configured, you can ask Claude:
- "Search for news about climate change"
- "What are people saying about AI on Reddit and Bluesky?"
- "Generate a comprehensive analysis of today's tech news"
- "What's the weather forecast?"

### With LM Studio
Configure your system prompt:
```
You have access to Eagle Watchtower through these functions:
- search_news(query, max_results, language, country)
- search_bluesky(query, limit)
- search_reddit(query, limit)
- search_all_sources(query, max_results_per_source)
- generate_ai_summary(query, custom_prompt, include_social)
- get_weather(latitude, longitude)
- get_summary_history(limit)

When users ask about current events, use these tools to provide accurate, up-to-date information.
```

## Troubleshooting

### MCP server won't start
- Ensure Node.js 18+ is installed: `node --version`
- Check dependencies: `npm list @modelcontextprotocol/sdk`
- Verify Eagle Watchtower is running: `curl http://localhost:3000/health`

### No results returned
- Check Eagle Watchtower logs for errors
- Verify API endpoints: `curl http://localhost:3000/api/news?q=test`
- Ensure all Python dependencies are installed for scrapers

### Connection errors
- Confirm Eagle Watchtower is on port 3000
- Check firewall settings
- Try setting custom URL: `EAGLE_API_URL=http://localhost:3000 node eagle-watchtower-mcp.js`

## Architecture

```
┌─────────────┐     MCP Protocol    ┌──────────────────┐
│  LM Studio  │◄───────────────────►│  MCP Server      │
│  or Claude  │                     │  (eagle-watch-   │
└─────────────┘                     │   tower-mcp.js)  │
                                    └────────┬─────────┘
                                             │ HTTP
                                    ┌────────▼─────────┐
                                    │ Eagle Watchtower │
                                    │  (server.js)     │
                                    └────────┬─────────┘
                                             │
                    ┌────────────────────────┼────────────────────────┐
                    │                        │                        │
            ┌───────▼────────┐    ┌─────────▼────────┐    ┌──────────▼────────┐
            │   News APIs    │    │  Social Media    │    │  Weather API      │
            │  - GNews       │    │  - Reddit        │    │  - NWS            │
            │  - Guardian    │    │  - Bluesky       │    └───────────────────┘
            │  - Google RSS  │    └──────────────────┘
            └────────────────┘
```

## Performance Considerations

- **Caching**: Eagle Watchtower implements 5-minute cache for API responses
- **Rate Limiting**: Be mindful of API rate limits for external services
- **Parallel Requests**: The MCP server uses parallel fetching for multi-source searches
- **MongoDB Storage**: Historical summaries are stored for quick retrieval

## Security Notes

- Never expose the Eagle Watchtower server to public internet
- Keep API keys secure in environment variables
- Use localhost connections when possible
- Monitor logs for suspicious activity

## Contributing

To add new tools or modify existing ones:
1. Edit `eagle-watchtower-mcp.js`
2. Update tool definitions in `tools/list` handler
3. Add implementation in `tools/call` handler
4. Test with: `node eagle-watchtower-mcp.js --test`

## License

MIT License - See Eagle Watchtower main repository for details.

## Support

For issues or questions:
1. Check Eagle Watchtower logs: `webscraper.log`
2. Check MCP server console output
3. Verify all services are running
4. Review this documentation

---

*Built for Eagle Watchtower News Aggregation Platform*