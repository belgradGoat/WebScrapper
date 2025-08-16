#!/usr/bin/env python3
"""
Viktor Kozlov Intelligence API Integration System
Creates a function-calling interface for Ollama to access news dashboard tools
"""

import json
import requests
import asyncio
import aiohttp
import argparse
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
import subprocess
import time
import os

class ViktorToolsAPI:
    """
    Tool interface that allows Viktor Kozlov (or any LLM) to access news dashboard functions
    """
    
    def __init__(self, base_url: str = "http://localhost:3000"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    # ================= TOOL DEFINITIONS =================
    
    async def search_news(self, query: str, max_results: int = 20, language: str = "en") -> Dict[str, Any]:
        """
        Search for news articles using the news dashboard API
        
        Args:
            query: Search keywords
            max_results: Maximum number of articles to return
            language: Language code (en, pl, etc.)
            
        Returns:
            Dict with articles, sources, and metadata
        """
        try:
            params = {
                'q': query,
                'max': max_results,
                'lang': language
            }
            
            async with self.session.get(f"{self.base_url}/api/news", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "tool": "search_news",
                        "query": query,
                        "total_articles": data.get('totalArticles', 0),
                        "articles": data.get('articles', []),
                        "sources": data.get('sources', []),
                        "timestamp": data.get('timestamp')
                    }
                else:
                    return {
                        "success": False,
                        "error": f"News search failed with status {response.status}",
                        "tool": "search_news"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"News search error: {str(e)}",
                "tool": "search_news"
            }
    
    async def get_weather(self, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        """
        Get weather information using the weather API
        
        Args:
            lat: Latitude (optional, uses default location if not provided)
            lon: Longitude (optional, uses default location if not provided)
            
        Returns:
            Dict with current weather, forecast, and location info
        """
        try:
            payload = {}
            if lat is not None and lon is not None:
                payload = {"lat": lat, "lon": lon}
                
            async with self.session.post(f"{self.base_url}/api/weather", 
                                       json=payload,
                                       headers={'Content-Type': 'application/json'}) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "tool": "get_weather",
                        "current": data.get('current'),
                        "forecast": data.get('forecast'),
                        "location": data.get('location'),
                        "alerts": data.get('alerts', [])
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Weather API failed with status {response.status}",
                        "tool": "get_weather"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Weather API error: {str(e)}",
                "tool": "get_weather"
            }
    
    async def search_bluesky(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """
        Search Bluesky social media posts
        
        Args:
            query: Search keywords
            limit: Maximum number of posts to return
            
        Returns:
            Dict with posts and engagement data
        """
        try:
            payload = {"query": query, "limit": limit}
            
            async with self.session.post(f"{self.base_url}/api/bluesky",
                                       json=payload,
                                       headers={'Content-Type': 'application/json'}) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "tool": "search_bluesky",
                        "query": query,
                        "total_posts": data.get('totalPosts', 0),
                        "posts": data.get('posts', [])
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Bluesky search failed with status {response.status}",
                        "tool": "search_bluesky"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Bluesky search error: {str(e)}",
                "tool": "search_bluesky"
            }
    
    async def search_reddit(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """
        Search Reddit posts
        
        Args:
            query: Search keywords
            limit: Maximum number of posts to return
            
        Returns:
            Dict with posts and engagement data
        """
        try:
            payload = {"query": query, "limit": limit}
            
            async with self.session.post(f"{self.base_url}/api/reddit",
                                       json=payload,
                                       headers={'Content-Type': 'application/json'}) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "tool": "search_reddit",
                        "query": query,
                        "total_posts": data.get('totalPosts', 0),
                        "posts": data.get('posts', [])
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Reddit search failed with status {response.status}",
                        "tool": "search_reddit"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Reddit search error: {str(e)}",
                "tool": "search_reddit"
            }
    
    async def generate_ai_summary(self, articles: List[Dict], prompt: str = "") -> Dict[str, Any]:
        """
        Generate an AI summary using Gemma model
        
        Args:
            articles: List of articles to summarize
            prompt: Custom prompt for the summary
            
        Returns:
            Dict with generated summary and metadata
        """
        try:
            payload = {
                "articles": articles,
                "prompt": prompt or "Provide a comprehensive analysis of these articles."
            }
            
            async with self.session.post(f"{self.base_url}/api/summarize-gemma",
                                       json=payload,
                                       headers={'Content-Type': 'application/json'}) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "tool": "generate_ai_summary",
                        "summary": data.get('summary'),
                        "summary_id": data.get('summary_id'),
                        "source_breakdown": data.get('source_breakdown'),
                        "timestamp": data.get('timestamp')
                    }
                else:
                    return {
                        "success": False,
                        "error": f"AI summary failed with status {response.status}",
                        "tool": "generate_ai_summary"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"AI summary error: {str(e)}",
                "tool": "generate_ai_summary"
            }
    
    async def get_summary_history(self) -> Dict[str, Any]:
        """
        Retrieve historical summaries from MongoDB
        
        Returns:
            Dict with list of previous summaries
        """
        try:
            async with self.session.get(f"{self.base_url}/api/summaries") as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "tool": "get_summary_history",
                        "summaries": data.get('summaries', []),
                        "source": data.get('source')
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Summary history failed with status {response.status}",
                        "tool": "get_summary_history"
                    }
        except Exception as e:
            return {
                "success": False,
                "error": f"Summary history error: {str(e)}",
                "tool": "get_summary_history"
            }
    
    # ================= TOOL ORCHESTRATION =================
    
    async def comprehensive_intelligence_brief(self, topic: str, include_social: bool = True) -> Dict[str, Any]:
        """
        Generate a comprehensive intelligence brief on a topic using multiple tools
        
        Args:
            topic: Main topic to investigate
            include_social: Whether to include social media data
            
        Returns:
            Dict with comprehensive analysis
        """
        results = {}
        
        try:
            # Step 1: Search news
            print(f"🔍 Searching news for '{topic}'...")
            news_result = await self.search_news(topic, max_results=50)
            results['news'] = news_result
            
            # Step 2: Get weather context
            print("🌤️ Getting weather context...")
            weather_result = await self.get_weather()
            results['weather'] = weather_result
            
            # Step 3: Search social media if requested
            if include_social:
                print(f"📱 Searching social media for '{topic}'...")
                bluesky_task = self.search_bluesky(topic, limit=30)
                reddit_task = self.search_reddit(topic, limit=30)
                
                bluesky_result, reddit_result = await asyncio.gather(bluesky_task, reddit_task)
                results['bluesky'] = bluesky_result
                results['reddit'] = reddit_result
            
            # Step 4: Compile all articles for AI analysis
            all_articles = []
            
            if news_result.get('success') and news_result.get('articles'):
                all_articles.extend(news_result['articles'])
            
            if include_social:
                # Add social media posts as articles
                if bluesky_result.get('success') and bluesky_result.get('posts'):
                    for post in bluesky_result['posts']:
                        all_articles.append({
                            'title': f"Bluesky: @{post.get('author', {}).get('handle', 'unknown')}",
                            'description': post.get('text', ''),
                            'source': {'name': 'Bluesky', 'type': 'social'},
                            'publishedAt': datetime.now().isoformat()
                        })
                
                if reddit_result.get('success') and reddit_result.get('posts'):
                    for post in reddit_result['posts']:
                        all_articles.append({
                            'title': post.get('title', ''),
                            'description': post.get('text', ''),
                            'source': {'name': f"Reddit r/{post.get('subreddit', 'unknown')}", 'type': 'social'},
                            'publishedAt': datetime.now().isoformat()
                        })
            
            # Step 5: Generate AI summary
            if all_articles:
                print(f"🤖 Generating AI analysis with {len(all_articles)} sources...")
                ai_prompt = f"""
                Viktor Kozlov Intelligence Analysis Request:
                
                Topic: {topic}
                Sources: {len(all_articles)} articles and posts
                
                Please provide a comprehensive strategic assessment including:
                1. Key developments and trends
                2. Geopolitical implications
                3. Risk assessment
                4. Strategic recommendations
                
                Focus on actionable intelligence and strategic insights.
                """
                
                summary_result = await self.generate_ai_summary(all_articles, ai_prompt)
                results['ai_analysis'] = summary_result
            
            return {
                "success": True,
                "tool": "comprehensive_intelligence_brief",
                "topic": topic,
                "total_sources": len(all_articles),
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Intelligence brief error: {str(e)}",
                "tool": "comprehensive_intelligence_brief",
                "partial_results": results
            }


# ================= OLLAMA INTEGRATION =================

class ViktorOllamaInterface:
    """
    Interface to integrate Viktor tools with Ollama
    """
    
    def __init__(self, model_name: str = "kozlov-hermes", ollama_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.tools_api = ViktorToolsAPI()
    
    def get_tools_definition(self) -> List[Dict[str, Any]]:
        """
        Define available tools for Ollama function calling
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "search_news",
                    "description": "Search for current news articles on any topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search keywords"},
                            "max_results": {"type": "integer", "description": "Maximum articles to return", "default": 20},
                            "language": {"type": "string", "description": "Language code (en, pl, etc.)", "default": "en"}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "get_weather",
                    "description": "Get current weather and forecast information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "lat": {"type": "number", "description": "Latitude (optional)"},
                            "lon": {"type": "number", "description": "Longitude (optional)"}
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_bluesky",
                    "description": "Search Bluesky social media for posts about a topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search keywords"},
                            "limit": {"type": "integer", "description": "Maximum posts to return", "default": 20}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_reddit",
                    "description": "Search Reddit for posts and discussions about a topic",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search keywords"},
                            "limit": {"type": "integer", "description": "Maximum posts to return", "default": 20}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "comprehensive_intelligence_brief",
                    "description": "Generate a comprehensive intelligence brief using all available sources",
                    "parameters": {
                        "type": "object", 
                        "properties": {
                            "topic": {"type": "string", "description": "Main topic to investigate"},
                            "include_social": {"type": "boolean", "description": "Include social media sources", "default": True}
                        },
                        "required": ["topic"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_summary_history",
                    "description": "Retrieve previous intelligence summaries and analyses",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool call
        """
        async with self.tools_api as api:
            if tool_name == "search_news":
                return await api.search_news(**parameters)
            elif tool_name == "get_weather":
                return await api.get_weather(**parameters)
            elif tool_name == "search_bluesky":
                return await api.search_bluesky(**parameters)
            elif tool_name == "search_reddit":
                return await api.search_reddit(**parameters)
            elif tool_name == "comprehensive_intelligence_brief":
                return await api.comprehensive_intelligence_brief(**parameters)
            elif tool_name == "get_summary_history":
                return await api.get_summary_history()
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}


# ================= CLI INTERFACE =================

async def main():
    parser = argparse.ArgumentParser(description='Viktor Kozlov Intelligence Tools API')
    parser.add_argument('command', choices=['test', 'brief', 'search', 'tools-list'], 
                       help='Command to execute')
    parser.add_argument('--topic', '-t', help='Topic to research')
    parser.add_argument('--social', action='store_true', help='Include social media')
    parser.add_argument('--query', '-q', help='Search query')
    
    args = parser.parse_args()
    
    interface = ViktorOllamaInterface()
    
    if args.command == 'test':
        print("🧪 Testing Viktor Tools API...")
        async with ViktorToolsAPI() as api:
            # Test news search
            result = await api.search_news("artificial intelligence", max_results=5)
            print(f"News search test: {'✅ Success' if result.get('success') else '❌ Failed'}")
            if result.get('success'):
                print(f"  Found {result.get('total_articles', 0)} articles")
            
            # Test weather
            weather = await api.get_weather()
            print(f"Weather test: {'✅ Success' if weather.get('success') else '❌ Failed'}")
            if weather.get('success'):
                location = weather.get('location', {})
                print(f"  Location: {location.get('city', 'Unknown')}, {location.get('state', 'Unknown')}")
    
    elif args.command == 'brief':
        if not args.topic:
            print("❌ Topic required for intelligence brief")
            return
        
        print(f"📊 Generating intelligence brief for: {args.topic}")
        async with ViktorToolsAPI() as api:
            result = await api.comprehensive_intelligence_brief(args.topic, include_social=args.social)
            
            if result.get('success'):
                print(f"✅ Brief generated with {result.get('total_sources', 0)} sources")
                
                # Print AI analysis if available
                ai_analysis = result.get('results', {}).get('ai_analysis', {})
                if ai_analysis.get('success'):
                    print("\n🤖 AI Analysis:")
                    print("=" * 50)
                    print(ai_analysis.get('summary', 'No summary available'))
                else:
                    print("⚠️ AI analysis not available")
            else:
                print(f"❌ Brief generation failed: {result.get('error', 'Unknown error')}")
    
    elif args.command == 'search':
        if not args.query:
            print("❌ Query required for search")
            return
        
        print(f"🔍 Searching for: {args.query}")
        async with ViktorToolsAPI() as api:
            result = await api.search_news(args.query, max_results=10)
            
            if result.get('success'):
                articles = result.get('articles', [])
                print(f"✅ Found {len(articles)} articles")
                
                for i, article in enumerate(articles[:5], 1):
                    print(f"\n{i}. {article.get('title', 'No title')}")
                    print(f"   Source: {article.get('source', {}).get('name', 'Unknown')}")
                    print(f"   URL: {article.get('url', 'No URL')}")
            else:
                print(f"❌ Search failed: {result.get('error', 'Unknown error')}")
    
    elif args.command == 'tools-list':
        print("🛠️ Available Viktor Tools:")
        tools = interface.get_tools_definition()
        for tool in tools:
            func = tool['function']
            print(f"\n• {func['name']}")
            print(f"  Description: {func['description']}")
            
            params = func['parameters']['properties']
            if params:
                print("  Parameters:")
                for param_name, param_info in params.items():
                    required = param_name in func['parameters'].get('required', [])
                    req_str = " (required)" if required else " (optional)"
                    print(f"    - {param_name}: {param_info.get('description', 'No description')}{req_str}")


if __name__ == "__main__":
    asyncio.run(main())
