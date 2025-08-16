#!/usr/bin/env python3
"""
Viktor Kozlov Ollama Integration with News Dashboard Tools
Complete solution for LLM tool access
"""

import json
import asyncio
import aiohttp
import argparse
import sys
import re
import os
from typing import Dict, List, Any, Optional
import subprocess
from datetime import datetime

class NewsToolsAPI:
    """
    API interface for news dashboard tools
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
    
    async def search_news(self, query: str, max_results: int = 20, language: str = "en") -> Dict[str, Any]:
        """Search for news articles"""
        try:
            params = {'q': query, 'max': max_results, 'lang': language}
            async with self.session.get(f"{self.base_url}/api/news", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        "success": True,
                        "tool": "search_news",
                        "query": query,
                        "total_articles": data.get('totalArticles', 0),
                        "articles": data.get('articles', []),
                        "sources": data.get('sources', [])
                    }
                else:
                    return {"success": False, "error": f"News search failed with status {response.status}"}
        except Exception as e:
            return {"success": False, "error": f"News search error: {str(e)}"}
    
    async def get_weather(self, lat: Optional[float] = None, lon: Optional[float] = None) -> Dict[str, Any]:
        """Get weather information"""
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
                    return {"success": False, "error": f"Weather API failed with status {response.status}"}
        except Exception as e:
            return {"success": False, "error": f"Weather API error: {str(e)}"}
    
    async def search_bluesky(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search Bluesky posts"""
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
                    return {"success": False, "error": f"Bluesky search failed with status {response.status}"}
        except Exception as e:
            return {"success": False, "error": f"Bluesky search error: {str(e)}"}
    
    async def search_reddit(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """Search Reddit posts"""
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
                    return {"success": False, "error": f"Reddit search failed with status {response.status}"}
        except Exception as e:
            return {"success": False, "error": f"Reddit search error: {str(e)}"}


class ViktorIntelligenceAgent:
    """
    Viktor Kozlov Intelligence Agent with tool calling capabilities
    """
    
    def __init__(self, model_name: str = "kozlov-hermes"):
        self.model_name = model_name
        self.tools_api = NewsToolsAPI()
        
    def extract_tool_requests(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract tool usage requests from model output
        """
        tool_requests = []
        
        # Check the original query text for key topics that need current intelligence
        query_lower = text.lower()
        
        # If it mentions specific topics that need current data, add news search
        intelligence_topics = [
            'artificial intelligence', 'ai developments', 'middle east', 'ukraine', 'russia',
            'china', 'economy', 'economics', 'inflation', 'markets', 'politics', 'election',
            'climate', 'energy', 'technology', 'cybersecurity', 'military', 'defense',
            'trade', 'diplomacy', 'sanctions', 'covid', 'health', 'pandemic'
        ]
        
        # Check if query mentions any intelligence topics
        for topic in intelligence_topics:
            if topic in query_lower:
                # Extract the main subject for the search
                if 'middle east' in query_lower:
                    search_query = 'Middle East'
                elif 'artificial intelligence' in query_lower or 'ai' in query_lower:
                    search_query = 'artificial intelligence'
                elif 'ukraine' in query_lower:
                    search_query = 'Ukraine'
                elif 'economy' in query_lower or 'economic' in query_lower:
                    search_query = 'economy'
                elif 'politics' in query_lower or 'political' in query_lower:
                    search_query = 'politics'
                else:
                    search_query = topic
                
                tool_requests.append({
                    'tool': 'search_news',
                    'parameters': {'query': search_query, 'max_results': 20}
                })
                break  # Only add one news search per query
        
        # If the model explicitly mentions needing to search for something
        if 'need to search news' in query_lower or 'search news about' in query_lower:
            # Try to extract what to search for
            import re
            match = re.search(r'search news.*?(?:about|for)\s+([^".\n]+)', query_lower)
            if match:
                search_term = match.group(1).strip()
                tool_requests.append({
                    'tool': 'search_news',
                    'parameters': {'query': search_term, 'max_results': 20}
                })
        
        return tool_requests
    
    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool call"""
        async with self.tools_api as api:
            try:
                if tool_name == "search_news":
                    # Clean parameters for news search
                    clean_params = {
                        'query': parameters.get('query', ''),
                        'max_results': parameters.get('max_results', 20),
                        'language': parameters.get('language', 'en')
                    }
                    return await api.search_news(**clean_params)
                elif tool_name == "get_weather":
                    # Weather doesn't need cleaning, just lat/lon if provided
                    clean_params = {}
                    if 'lat' in parameters:
                        clean_params['lat'] = parameters['lat']
                    if 'lon' in parameters:
                        clean_params['lon'] = parameters['lon']
                    return await api.get_weather(**clean_params)
                elif tool_name == "search_bluesky":
                    # Clean parameters for Bluesky
                    clean_params = {
                        'query': parameters.get('query', ''),
                        'limit': parameters.get('limit', 15)
                    }
                    return await api.search_bluesky(**clean_params)
                elif tool_name == "search_reddit":
                    # Clean parameters for Reddit
                    clean_params = {
                        'query': parameters.get('query', ''),
                        'limit': parameters.get('limit', 15)
                    }
                    return await api.search_reddit(**clean_params)
                else:
                    return {"success": False, "error": f"Unknown tool: {tool_name}"}
            except Exception as e:
                return {"success": False, "error": f"Tool execution error: {str(e)}"}
    
    async def call_ollama(self, prompt: str) -> str:
        """Call Ollama model"""
        try:
            cmd = ['ollama', 'run', self.model_name]
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
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    def format_tool_results(self, tool_results: List[Dict]) -> str:
        """Format tool results for the model"""
        formatted = "\n📊 REAL-TIME INTELLIGENCE GATHERED:\n" + "="*50 + "\n"
        
        for result in tool_results:
            tool_name = result.get('tool', 'Unknown')
            tool_data = result.get('result', {})
            
            if not tool_data.get('success'):
                formatted += f"\n❌ {tool_name}: {tool_data.get('error', 'Unknown error')}\n"
                continue
            
            if tool_name == 'search_news':
                articles = tool_data.get('articles', [])
                formatted += f"\n📰 NEWS INTELLIGENCE ({len(articles)} articles):\n"
                for i, article in enumerate(articles[:10], 1):
                    title = article.get('title', 'No title')
                    source = article.get('source', {}).get('name', 'Unknown')
                    description = article.get('description', '')[:150]
                    formatted += f"{i}. {title}\n   Source: {source}\n   {description}...\n\n"
            
            elif tool_name == 'get_weather':
                location = tool_data.get('location', {})
                current = tool_data.get('current', {})
                formatted += f"\n🌤️ WEATHER INTELLIGENCE:\n"
                formatted += f"Location: {location.get('city', 'Unknown')}, {location.get('state', 'Unknown')}\n"
                if current:
                    formatted += f"Current: {current.get('temperature_f', 'N/A')}°F\n"
                    formatted += f"Conditions: {current.get('detailed_forecast', 'No details')}\n"
            
            elif tool_name == 'search_bluesky':
                posts = tool_data.get('posts', [])
                formatted += f"\n🦋 BLUESKY INTELLIGENCE ({len(posts)} posts):\n"
                for i, post in enumerate(posts[:5], 1):
                    handle = post.get('author', {}).get('handle', 'unknown')
                    text = post.get('text', '')[:100]
                    formatted += f"{i}. @{handle}: {text}...\n"
            
            elif tool_name == 'search_reddit':
                posts = tool_data.get('posts', [])
                formatted += f"\n🟠 REDDIT INTELLIGENCE ({len(posts)} posts):\n"
                for i, post in enumerate(posts[:5], 1):
                    subreddit = post.get('subreddit', 'unknown')
                    title = post.get('title', '')[:80]
                    score = post.get('engagement', {}).get('score', 0)
                    formatted += f"{i}. r/{subreddit}: {title} (Score: {score})\n"
        
        formatted += "\n" + "="*50 + "\n"
        return formatted
    
    async def process_query(self, user_query: str) -> str:
        """Process a user query with tool calling"""
        
        # Step 1: Create enhanced prompt for Viktor
        enhanced_prompt = f"""You are Viktor Kozlov, elite intelligence analyst. 

MISSION: Analyze the following query and indicate what intelligence you need to gather.

If you need current information, state exactly what you need:
- "I need to search news about [topic]" for news
- "I need to check weather conditions" for weather
- "I need to search social media for [topic]" for social intelligence
- "I need to search Bluesky for [topic]" for Bluesky
- "I need to search Reddit for [topic]" for Reddit

USER QUERY: {user_query}

First, indicate what intelligence gathering you need, then provide any initial assessment you can make."""

        # Step 2: Get model's initial response and tool requests
        initial_response = await self.call_ollama(enhanced_prompt)
        print(f"🧠 Viktor's initial assessment:\n{initial_response}\n")
        
        # Step 3: Extract tool requests
        tool_requests = self.extract_tool_requests(initial_response)
        
        if not tool_requests:
            # No tools needed, return initial response
            return initial_response
        
        print(f"🔧 Executing {len(tool_requests)} intelligence gathering operations...")
        
        # Step 4: Execute tools
        tool_results = []
        for request in tool_requests:
            print(f"   • {request['tool']} with parameters: {request['parameters']}")
            result = await self.call_tool(request['tool'], request['parameters'])
            tool_results.append({
                'tool': request['tool'],
                'parameters': request['parameters'],
                'result': result
            })
        
        # Step 5: Format tool results
        intelligence_data = self.format_tool_results(tool_results)
        
        # Step 6: Get final analysis with gathered intelligence
        analysis_prompt = f"""You are Viktor Kozlov. You requested intelligence gathering and received the following data:

{intelligence_data}

ORIGINAL USER QUERY: {user_query}

Now provide your comprehensive strategic intelligence assessment based on this real-time data. Include:

1. KEY FINDINGS: What the intelligence reveals
2. STRATEGIC ASSESSMENT: Implications and context
3. RISK ANALYSIS: Potential threats and opportunities  
4. RECOMMENDATIONS: Actionable intelligence

Maintain your professional analytical tone and focus on strategic insights."""

        final_analysis = await self.call_ollama(analysis_prompt)
        
        return f"🛠️ INTELLIGENCE TOOLS DEPLOYED: {', '.join([tr['tool'] for tr in tool_requests])}\n\n{final_analysis}"


async def main():
    parser = argparse.ArgumentParser(description='Viktor Kozlov Intelligence Agent with Tool Access')
    parser.add_argument('--model', '-m', default='kozlov-hermes', help='Ollama model name')
    parser.add_argument('--query', '-q', help='Single query mode')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--test', action='store_true', help='Test tool connectivity')
    
    args = parser.parse_args()
    
    agent = ViktorIntelligenceAgent(args.model)
    
    if args.test:
        print("🧪 Testing tool connectivity...")
        async with NewsToolsAPI() as api:
            # Test news search
            result = await api.search_news("test", max_results=1)
            print(f"News API: {'✅ Working' if result.get('success') else '❌ Failed'}")
            
            # Test weather
            result = await api.get_weather()
            print(f"Weather API: {'✅ Working' if result.get('success') else '❌ Failed'}")
        
        return
    
    if args.query:
        # Single query mode
        print(f"🌍 Viktor Kozlov Intelligence Analysis")
        print(f"Query: {args.query}")
        print("="*60)
        
        response = await agent.process_query(args.query)
        print(response)
        
    elif args.interactive:
        # Interactive mode
        print("🌍 Viktor Kozlov Intelligence Terminal")
        print("=====================================")
        print("Enhanced with real-time tool access")
        print("Type 'exit' to quit, 'help' for commands\n")
        
        while True:
            try:
                user_input = input("Intelligence Query> ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("🔒 Intelligence session terminated.")
                    break
                
                if user_input.lower() == 'help':
                    print("\nAvailable commands:")
                    print("• Ask any intelligence question")
                    print("• Viktor will automatically use tools to gather current information")
                    print("• Examples:")
                    print("  - 'What is happening in Ukraine?'")
                    print("  - 'Analyze the current economic situation'")
                    print("  - 'What are people saying about AI on social media?'")
                    print("• Type 'exit' to quit\n")
                    continue
                
                if not user_input:
                    continue
                
                print(f"\n🧠 Viktor Kozlov analyzing: {user_input}")
                print("="*50)
                
                response = await agent.process_query(user_input)
                print(response)
                print("="*50)
                print()
                
            except KeyboardInterrupt:
                print("\n🔒 Intelligence session terminated.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    else:
        # Show usage
        print("Viktor Kozlov Intelligence Agent")
        print("===============================")
        print("Usage:")
        print(f"  {sys.argv[0]} --query 'What is happening in Ukraine?'")
        print(f"  {sys.argv[0]} --interactive")
        print(f"  {sys.argv[0]} --test")
        print("\nMake sure the news server is running on localhost:3000")


if __name__ == "__main__":
    asyncio.run(main())
