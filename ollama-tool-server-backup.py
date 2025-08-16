#!/usr/bin/env python3
"""
Ollama Tool Integration Server
Enables kozlov-hermes to access Eagle Watchtower tools through function calling
Creates an OpenAI-compatible API that intercepts Ollama requests and adds tool functionality
"""

import json
import asyncio
import aiohttp
from aiohttp import web
import sys
import os
import re
import subprocess
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

# Import our existing tools
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from viktor_intelligence_agent import NewsToolsAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaToolServer:
    """
    Server that provides tools to Ollama via function calling API
    """
    
    def __init__(self, port: int = 8080, ollama_url: str = "http://localhost:11434"):
        self.port = port
        self.ollama_url = ollama_url
        self.tools_api = NewsToolsAPI()
        self.app = web.Application()
        self.setup_routes()
        self.setup_cors()
    
    def setup_routes(self):
        """Setup HTTP routes for tool access"""
        self.app.router.add_post('/v1/chat/completions', self.handle_chat_completion)
        self.app.router.add_get('/v1/models', self.handle_models)
        self.app.router.add_options('/v1/chat/completions', self.handle_options)
        self.app.router.add_get('/health', self.handle_health)
    
    def setup_cors(self):
        """Setup CORS headers"""
        async def cors_handler(request, handler):
            response = await handler(request)
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        self.app.middlewares.append(cors_handler)
    
    async def handle_options(self, request):
        """Handle OPTIONS requests for CORS"""
        return web.Response()
    
    async def handle_health(self, request):
        """Health check endpoint"""
        return web.json_response({"status": "healthy", "tools_available": True})
    
    async def handle_models(self, request):
        """Return available models - proxy to Ollama"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.ollama_url}/api/tags") as resp:
                    ollama_models = await resp.json()
                    # Convert to OpenAI format
                    models = {
                        "object": "list",
                        "data": [
                            {
                                "id": model["name"],
                                "object": "model",
                                "created": 1677610602,
                                "owned_by": "ollama"
                            }
                            for model in ollama_models.get("models", [])
                        ]
                    }
                    return web.json_response(models)
            except Exception as e:
                return web.json_response({"error": str(e)}, status=500)
    
    async def handle_chat_completion(self, request):
        """Main chat completion handler with tool integration"""
        try:
            data = await request.json()
            messages = data.get("messages", [])
            model = data.get("model", "kozlov-hermes")
            
            if not messages:
                return web.json_response({"error": "No messages provided"}, status=400)
            
            # Get the latest user message
            user_message = None
            for msg in reversed(messages):
                if msg.get("role") == "user":
                    user_message = msg.get("content", "")
                    break
            
            if not user_message:
                return web.json_response({"error": "No user message found"}, status=400)
            
            logger.info(f"Processing request: {user_message[:100]}...")
            
            # Step 1: Check if tools are needed
            tool_calls = self.detect_tool_needs(user_message)
            
            if tool_calls:
                logger.info(f"Detected {len(tool_calls)} tool calls needed")
                
                # Step 2: Execute tools
                tool_results = []
                for tool_call in tool_calls:
                    try:
                        result = await self.execute_tool(tool_call["function"], tool_call["parameters"])
                        tool_results.append({
                            "tool": tool_call["function"],
                            "parameters": tool_call["parameters"], 
                            "result": result
                        })
                    except Exception as e:
                        logger.error(f"Tool execution failed: {e}")
                        tool_results.append({
                            "tool": tool_call["function"],
                            "parameters": tool_call["parameters"],
                            "error": str(e)
                        })
                
                # Step 3: Combine results with user message
                enhanced_message = self.create_enhanced_prompt(user_message, tool_results)
                
                # Step 4: Call Ollama with enhanced prompt
                response = await self.call_ollama(enhanced_message, model)
                
                # Step 5: Return in OpenAI format
                return web.json_response({
                    "id": f"chatcmpl-{datetime.now().timestamp()}",
                    "object": "chat.completion",
                    "created": int(datetime.now().timestamp()),
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(enhanced_message.split()),
                        "completion_tokens": len(response.split()),
                        "total_tokens": len(enhanced_message.split()) + len(response.split())
                    }
                })
            
            else:
                # No tools needed, direct call to Ollama
                response = await self.call_ollama(user_message, model)
                return web.json_response({
                    "id": f"chatcmpl-{datetime.now().timestamp()}",
                    "object": "chat.completion", 
                    "created": int(datetime.now().timestamp()),
                    "model": model,
                    "choices": [{
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": response
                        },
                        "finish_reason": "stop"
                    }],
                    "usage": {
                        "prompt_tokens": len(user_message.split()),
                        "completion_tokens": len(response.split()),
                        "total_tokens": len(user_message.split()) + len(response.split())
                    }
                })
                
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            return web.json_response({"error": str(e)}, status=500)
    
    def detect_tool_needs(self, message: str) -> List[Dict[str, Any]]:
        """Detect if the message requires tool usage"""
        tool_calls = []
        message_lower = message.lower()
        
        # Check for news-related queries
        news_keywords = ["news", "latest", "current events", "breaking", "artificial intelligence", 
                        "ukraine", "middle east", "politics", "technology", "today"]
        if any(keyword in message_lower for keyword in news_keywords):
            tool_calls.append({
                "function": "search_news",
                "parameters": {"query": self.extract_news_query(message)}
            })
        
        # Check for weather queries
        weather_keywords = ["weather", "temperature", "forecast", "climate"]
        if any(keyword in message_lower for keyword in weather_keywords):
            tool_calls.append({
                "function": "get_weather", 
                "parameters": {"location": self.extract_location(message)}
            })
        
        # Check for social media queries
        if "bluesky" in message_lower or "social media" in message_lower:
            tool_calls.append({
                "function": "search_bluesky",
                "parameters": {"query": self.extract_social_query(message)}
            })
        
        if "reddit" in message_lower:
            tool_calls.append({
                "function": "search_reddit", 
                "parameters": {"query": self.extract_social_query(message)}
            })
        
        # Check for comprehensive analysis requests
        analysis_keywords = ["intelligence brief", "comprehensive analysis", "full report"]
        if any(keyword in message_lower for keyword in analysis_keywords):
            tool_calls.append({
                "function": "comprehensive_intelligence_brief",
                "parameters": {"topic": self.extract_analysis_topic(message)}
            })
        
        return tool_calls
    
    def extract_news_query(self, message: str) -> str:
        """Extract search query from message for news"""
        # Simple keyword extraction
        keywords = []
        for word in message.split():
            if word.lower() in ["artificial", "intelligence", "ai", "ukraine", "russia", 
                               "middle", "east", "politics", "technology", "economy"]:
                keywords.append(word)
        
        if keywords:
            return " ".join(keywords)
        
        # Fallback to looking for quoted terms or key phrases
        if "about" in message.lower():
            parts = message.lower().split("about")
            if len(parts) > 1:
                return parts[1].strip()[:50]
        
        return "latest news"
    
    def extract_location(self, message: str) -> str:
        """Extract location from weather query"""
        # Simple location extraction
        common_locations = ["new york", "london", "paris", "tokyo", "berlin", "warsaw", "kyiv"]
        for location in common_locations:
            if location in message.lower():
                return location
        return "New York"
    
    def extract_social_query(self, message: str) -> str:
        """Extract query for social media search"""
        return self.extract_news_query(message)
    
    def extract_analysis_topic(self, message: str) -> str:
        """Extract topic for comprehensive analysis"""
        return self.extract_news_query(message)
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific tool"""
        try:
            if tool_name == "search_news":
                return await self.tools_api.search_news(
                    query=parameters.get("query", "latest news"),
                    max_results=parameters.get("max_results", 20),
                    language=parameters.get("language", "en")
                )
            elif tool_name == "get_weather":
                return await self.tools_api.get_weather(
                    location=parameters.get("location", "New York")
                )
            elif tool_name == "search_bluesky":
                return await self.tools_api.search_bluesky(
                    query=parameters.get("query", "")
                )
            elif tool_name == "search_reddit":
                return await self.tools_api.search_reddit(
                    query=parameters.get("query", "")
                )
            elif tool_name == "comprehensive_intelligence_brief":
                return await self.tools_api.comprehensive_intelligence_brief(
                    topic=parameters.get("topic", "")
                )
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_enhanced_prompt(self, user_message: str, tool_results: List[Dict[str, Any]]) -> str:
        """Create enhanced prompt with tool results"""
        prompt = f"""You are Viktor Kozlov, an elite intelligence analyst. You have been provided with real-time intelligence data to answer the user's question.

USER QUESTION: {user_message}

INTELLIGENCE DATA GATHERED:
"""
        
        for result in tool_results:
            if result.get("error"):
                prompt += f"\n❌ {result['tool']} failed: {result['error']}\n"
            else:
                tool_result = result["result"]
                if tool_result.get("success"):
                    prompt += f"\n✅ {result['tool'].upper()} RESULTS:\n"
                    
                    if result['tool'] == 'search_news':
                        articles = tool_result.get('articles', [])
                        prompt += f"Found {len(articles)} news articles:\n"
                        for i, article in enumerate(articles[:10], 1):
                            prompt += f"{i}. {article.get('title', 'No title')} - {article.get('source', {}).get('name', 'Unknown')}\n"
                            if article.get('description'):
                                prompt += f"   {article['description'][:200]}...\n"
                    
                    elif result['tool'] == 'get_weather':
                        location = tool_result.get('location', {})
                        current = tool_result.get('current', {})
                        prompt += f"Location: {location.get('city', 'Unknown')}, {location.get('state', 'Unknown')}\n"
                        if current:
                            prompt += f"Current: {current.get('temperature_f', 'N/A')}°F, {current.get('detailed_forecast', 'No details')}\n"
                    
                    elif result['tool'] in ['search_bluesky', 'search_reddit']:
                        posts = tool_result.get('posts', [])
                        prompt += f"Found {len(posts)} social media posts:\n"
                        for i, post in enumerate(posts[:5], 1):
                            prompt += f"{i}. {post.get('text', 'No content')[:150]}...\n"
                    
                    elif result['tool'] == 'comprehensive_intelligence_brief':
                        ai_analysis = tool_result.get('ai_analysis', {})
                        if ai_analysis.get('success'):
                            prompt += f"AI Analysis Complete:\n{ai_analysis.get('summary', 'No summary')}\n"
                        prompt += f"Total sources analyzed: {tool_result.get('total_sources', 0)}\n"
                else:
                    prompt += f"\n❌ {result['tool']} failed: {tool_result.get('error', 'Unknown error')}\n"
        
        prompt += """\n\nBased on this real-time intelligence, provide your professional analysis. Include:
1. Key findings from the gathered intelligence
2. Strategic assessment and implications  
3. Risk analysis
4. Actionable recommendations

Maintain your role as Viktor Kozlov - professional, analytical, and focused on strategic intelligence."""
        
        return prompt
    
    async def call_ollama(self, prompt: str, model: str) -> str:
        """Call Ollama API directly"""
        try:
            async with aiohttp.ClientSession() as session:
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
                
                async with session.post(f"{self.ollama_url}/api/generate", json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result.get("response", "No response from model")
                    else:
                        return f"Error: Ollama API returned status {resp.status}"
                        
        except Exception as e:
            # Fallback to subprocess if HTTP API fails
            try:
                cmd = ['ollama', 'run', model]
                process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                stdout, stderr = process.communicate(input=prompt)
                
                if process.returncode == 0:
                    return stdout.strip()
                else:
                    return f"Error calling Ollama: {stderr}"
                    
            except Exception as e2:
                return f"Error: {str(e2)}"
    
    async def start_server(self):
        """Start the server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"🚀 Ollama Tool Server started on port {self.port}")
        logger.info(f"📡 Proxying to Ollama at {self.ollama_url}")
        logger.info("🛠️  Available tools: search_news, get_weather, search_bluesky, search_reddit, comprehensive_intelligence_brief")
        
        # Keep the server running
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("🛑 Server shutting down...")

# ================= CLI INTERFACE =================

async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Ollama Tool Integration Server')
    parser.add_argument('--port', '-p', type=int, default=8080, help='Port to run server on')
    parser.add_argument('--ollama-url', '-o', default='http://localhost:11434', help='Ollama API URL')
    
    args = parser.parse_args()
    
    # Check if news server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://localhost:3000/health') as resp:
                if resp.status == 200:
                    logger.info("✅ News server is running")
                else:
                    logger.warning("⚠️  News server might not be running")
    except:
        logger.warning("⚠️  Cannot connect to news server at localhost:3000")
    
    # Start the server
    server = OllamaToolServer(port=args.port, ollama_url=args.ollama_url)
    await server.start_server()

if __name__ == "__main__":
    asyncio.run(main())
        
        # Add CORS middleware
        self.app.middlewares.append(self.cors_middleware)
    
    async def cors_middleware(self, request, handler):
        """Add CORS headers"""
        response = await handler(request)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    async def handle_options(self, request):
        """Handle CORS preflight"""
        return web.Response(status=200)
    
    async def handle_models(self, request):
        """Return available models"""
        return web.json_response({
            "object": "list",
            "data": [
                {
                    "id": "kozlov-hermes-tools",
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "viktor-intelligence"
                }
            ]
        })
    
    async def handle_chat_completion(self, request):
        """Handle chat completion with function calling"""
        try:
            data = await request.json()
            messages = data.get('messages', [])
            
            # Extract the last user message
            user_message = None
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_message = msg.get('content', '')
                    break
            
            if not user_message:
                return web.json_response({
                    "error": "No user message found"
                }, status=400)
            
            # Check if this is a tool request
            if self.is_tool_request(user_message):
                # Execute tools and get results
                tool_results = await self.execute_tools_for_query(user_message)
                
                # Format response with tool results
                response_content = await self.format_tool_response(user_message, tool_results)
            else:
                # Forward to regular Ollama
                response_content = await self.forward_to_ollama(messages)
            
            # Return OpenAI-compatible response
            return web.json_response({
                "id": "chatcmpl-viktor",
                "object": "chat.completion",
                "created": 1677652288,
                "model": "kozlov-hermes-tools",
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_content
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": len(user_message),
                    "completion_tokens": len(response_content),
                    "total_tokens": len(user_message) + len(response_content)
                }
            })
            
        except Exception as e:
            logger.error(f"Error handling chat completion: {e}")
            return web.json_response({
                "error": str(e)
            }, status=500)
    
    def is_tool_request(self, message: str) -> bool:
        """Check if message requests tool usage"""
        tool_triggers = [
            'eagle watchtower', 'check news', 'latest news', 'search news',
            'weather', 'forecast', 'social media', 'bluesky', 'reddit',
            'intelligence brief', 'current events', 'what\'s happening',
            'epstein case', 'ukraine', 'middle east', 'artificial intelligence'
        ]
        
        message_lower = message.lower()
        return any(trigger in message_lower for trigger in tool_triggers)
    
    async def execute_tools_for_query(self, query: str) -> Dict[str, Any]:
        """Execute appropriate tools based on query"""
        results = {}
        
        async with self.tools_api as api:
            # Always search news for intelligence requests
            logger.info(f"Searching news for: {query}")
            news_result = await api.search_news(query, max_results=20)
            results['news'] = news_result
            
            # Add weather if relevant
            if any(word in query.lower() for word in ['weather', 'forecast', 'temperature']):
                logger.info("Getting weather information")
                weather_result = await api.get_weather()
                results['weather'] = weather_result
            
            # Add social media if relevant
            if any(word in query.lower() for word in ['social', 'bluesky', 'reddit', 'discussion']):
                logger.info(f"Searching social media for: {query}")
                bluesky_task = api.search_bluesky(query, limit=15)
                reddit_task = api.search_reddit(query, limit=15)
                
                bluesky_result, reddit_result = await asyncio.gather(
                    bluesky_task, reddit_task, return_exceptions=True
                )
                
                if not isinstance(bluesky_result, Exception):
                    results['bluesky'] = bluesky_result
                if not isinstance(reddit_result, Exception):
                    results['reddit'] = reddit_result
        
        return results
    
    async def format_tool_response(self, query: str, tool_results: Dict[str, Any]) -> str:
        """Format tool results into Viktor's response"""
        response = "🛠️ EAGLE WATCHTOWER INTELLIGENCE ACCESSED\n"
        response += "="*50 + "\n\n"
        
        # Format news results
        if 'news' in tool_results and tool_results['news'].get('success'):
            articles = tool_results['news'].get('articles', [])
            response += f"📰 NEWS INTELLIGENCE ({len(articles)} articles):\n\n"
            
            for i, article in enumerate(articles[:10], 1):
                title = article.get('title', 'No title')
                source = article.get('source', {}).get('name', 'Unknown')
                description = article.get('description', '')[:200]
                response += f"{i}. {title}\n"
                response += f"   Source: {source}\n"
                response += f"   {description}...\n\n"
        
        # Format weather if available
        if 'weather' in tool_results and tool_results['weather'].get('success'):
            weather = tool_results['weather']
            location = weather.get('location', {})
            current = weather.get('current', {})
            response += f"🌤️ WEATHER INTELLIGENCE:\n"
            response += f"Location: {location.get('city', 'Unknown')}, {location.get('state', 'Unknown')}\n"
            if current:
                response += f"Current: {current.get('temperature_f', 'N/A')}°F\n"
            response += "\n"
        
        # Format social media if available
        if 'bluesky' in tool_results and tool_results['bluesky'].get('success'):
            posts = tool_results['bluesky'].get('posts', [])
            response += f"🦋 BLUESKY INTELLIGENCE ({len(posts)} posts):\n"
            for i, post in enumerate(posts[:5], 1):
                handle = post.get('author', {}).get('handle', 'unknown')
                text = post.get('text', '')[:100]
                response += f"{i}. @{handle}: {text}...\n"
            response += "\n"
        
        if 'reddit' in tool_results and tool_results['reddit'].get('success'):
            posts = tool_results['reddit'].get('posts', [])
            response += f"🟠 REDDIT INTELLIGENCE ({len(posts)} posts):\n"
            for i, post in enumerate(posts[:5], 1):
                subreddit = post.get('subreddit', 'unknown')
                title = post.get('title', '')[:80]
                response += f"{i}. r/{subreddit}: {title}\n"
            response += "\n"
        
        # Add Viktor's analysis
        response += "🧠 VIKTOR KOZLOV ANALYSIS:\n"
        response += "="*30 + "\n"
        
        # Call the actual model for analysis
        analysis = await self.get_viktor_analysis(query, tool_results)
        response += analysis
        
        return response
    
    async def get_viktor_analysis(self, query: str, tool_results: Dict[str, Any]) -> str:
        """Get Viktor's analysis of the intelligence"""
        # Prepare summary of intelligence for Viktor
        intelligence_summary = "INTELLIGENCE BRIEFING:\n"
        
        if 'news' in tool_results and tool_results['news'].get('success'):
            articles = tool_results['news'].get('articles', [])
            intelligence_summary += f"- {len(articles)} news articles gathered\n"
            if articles:
                intelligence_summary += f"- Key sources: {', '.join(set(a.get('source', {}).get('name', 'Unknown') for a in articles[:5]))}\n"
        
        # Create prompt for Viktor
        prompt = f"""You are Viktor Kozlov, elite intelligence analyst. You have just accessed Eagle Watchtower and gathered current intelligence.

QUERY: {query}

{intelligence_summary}

Provide a concise professional assessment including:
1. Key findings from the intelligence
2. Strategic implications
3. Risk assessment if relevant
4. Recommendations

Keep response focused and actionable. Maintain your analytical tone."""
        
        # Call Ollama for analysis
        return await self.forward_to_ollama([{"role": "user", "content": prompt}])
    
    async def forward_to_ollama(self, messages: List[Dict]) -> str:
        """Forward request to actual Ollama"""
        try:
            import subprocess
            
            # Extract the last user message
            user_message = ""
            for msg in reversed(messages):
                if msg.get('role') == 'user':
                    user_message = msg.get('content', '')
                    break
            
            # Call ollama
            process = subprocess.Popen(
                ['ollama', 'run', 'kozlov-hermes'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=user_message)
            
            if process.returncode == 0:
                return stdout.strip()
            else:
                return f"Error from Ollama: {stderr}"
                
        except Exception as e:
            return f"Error calling Ollama: {str(e)}"
    
    async def start_server(self):
        """Start the tool server"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', self.port)
        await site.start()
        logger.info(f"🚀 Ollama Tool Server running on http://localhost:{self.port}")
        logger.info("Viktor Kozlov now has access to Eagle Watchtower tools!")

async def main():
    """Start the tool integration server"""
    server = OllamaToolServer(port=8080)
    await server.start_server()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("🔒 Server shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
