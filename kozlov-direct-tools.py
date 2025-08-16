#!/usr/bin/env python3
"""
Direct Tool Integration for Kozlov-Hermes
Automatically detects when to use tools and provides real-time data to the model
"""

import asyncio
import aiohttp
import argparse
import sys
import os
import subprocess
import json
from typing import Dict, List, Any, Optional

# Import the tools
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("viktor_tools_api", "/Users/sebastianszewczyk/Documents/GitHub/WebScrapper/viktor-tools-api.py")
viktor_tools_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(viktor_tools_module)

ViktorToolsAPI = viktor_tools_module.ViktorToolsAPI

class KozlovDirectTools:
    """
    Direct tool integration that automatically provides real-time data to kozlov-hermes
    """
    
    def __init__(self, model_name: str = "kozlov-hermes"):
        self.model_name = model_name
        self.tools_api = ViktorToolsAPI()
    
    def should_use_tools(self, user_input: str) -> List[str]:
        """
        Determine if user input requires real-time tools
        """
        user_lower = user_input.lower()
        tools_needed = []
        
        # News-related keywords
        news_keywords = [
            'eagle watchtower', 'news', 'latest', 'current', 'recent', 'happening',
            'ukraine', 'russia', 'artificial intelligence', 'ai', 'politics', 
            'economy', 'middle east', 'china', 'election', 'market', 'stock',
            'climate', 'covid', 'technology', 'cybersecurity', 'military',
            'defense', 'trade', 'diplomacy', 'sanctions', 'inflation'
        ]
        
        # Social media keywords
        social_keywords = ['social media', 'reddit', 'bluesky', 'twitter', 'posts', 'discussion']
        
        # Check for news search need
        if any(keyword in user_lower for keyword in news_keywords):
            tools_needed.append('news')
        
        # Check for social media search need
        if any(keyword in user_lower for keyword in social_keywords):
            tools_needed.append('social')
        
        # Check for specific requests
        if 'search' in user_lower or 'find' in user_lower:
            tools_needed.append('news')
        
        if 'intelligence brief' in user_lower or 'comprehensive analysis' in user_lower:
            tools_needed.append('brief')
        
        return tools_needed
    
    def extract_search_query(self, user_input: str) -> str:
        """
        Extract the main search topic from user input
        """
        # Remove common prefixes
        query = user_input.lower()
        prefixes = [
            'search for', 'find', 'get news about', 'tell me about', 'what about',
            'latest on', 'news on', 'information about', 'what is happening with',
            'what\'s happening with', 'update on', 'search eagle watchtower',
            'search', 'news about'
        ]
        
        for prefix in prefixes:
            if query.startswith(prefix):
                query = query[len(prefix):].strip()
                break
        
        # Clean up
        query = query.replace('?', '').replace('.', '').strip()
        
        # If still contains common words, extract the key topic
        key_topics = {
            'eagle watchtower': 'eagle watchtower',
            'ukraine': 'Ukraine conflict',
            'artificial intelligence': 'artificial intelligence',
            'ai': 'artificial intelligence',
            'politics': 'US politics',
            'economy': 'economy',
            'middle east': 'Middle East',
            'china': 'China',
            'russia': 'Russia'
        }
        
        for topic, search_term in key_topics.items():
            if topic in query:
                return search_term
        
        return query if query else user_input
    
    async def gather_intelligence(self, query: str, tools_needed: List[str]) -> Dict[str, Any]:
        """
        Gather real-time intelligence using the specified tools
        """
        intelligence = {}
        
        async with self.tools_api as api:
            if 'news' in tools_needed or 'brief' in tools_needed:
                print(f"🔍 Searching news for: {query}")
                news_result = await api.search_news(query, max_results=15)
                intelligence['news'] = news_result
            
            if 'social' in tools_needed or 'brief' in tools_needed:
                print(f"📱 Searching social media for: {query}")
                # Search both platforms
                bluesky_task = api.search_bluesky(query, limit=10)
                reddit_task = api.search_reddit(query, limit=10)
                
                bluesky_result, reddit_result = await asyncio.gather(bluesky_task, reddit_task, return_exceptions=True)
                
                if not isinstance(bluesky_result, Exception):
                    intelligence['bluesky'] = bluesky_result
                if not isinstance(reddit_result, Exception):
                    intelligence['reddit'] = reddit_result
            
            if 'brief' in tools_needed:
                print(f"📊 Generating comprehensive intelligence brief...")
                brief_result = await api.comprehensive_intelligence_brief(query, include_social=True)
                intelligence['brief'] = brief_result
        
        return intelligence
    
    def format_intelligence_context(self, intelligence: Dict[str, Any], query: str) -> str:
        """
        Format the gathered intelligence into context for the model
        """
        context = f"=== REAL-TIME INTELLIGENCE BRIEFING ===\n"
        context += f"Query: {query}\n"
        context += f"Timestamp: {intelligence.get('timestamp', 'Current')}\n\n"
        
        # News section
        if 'news' in intelligence and intelligence['news'].get('success'):
            articles = intelligence['news'].get('articles', [])
            context += f"📰 NEWS INTELLIGENCE ({len(articles)} sources):\n"
            
            for i, article in enumerate(articles[:10], 1):
                context += f"\n{i}. {article.get('title', 'No title')}\n"
                context += f"   Source: {article.get('source', {}).get('name', 'Unknown')}\n"
                if article.get('description'):
                    context += f"   Summary: {article['description'][:150]}...\n"
                if article.get('url'):
                    context += f"   URL: {article['url']}\n"
        
        # Social media section
        if 'bluesky' in intelligence and intelligence['bluesky'].get('success'):
            posts = intelligence['bluesky'].get('posts', [])
            if posts:
                context += f"\n📱 BLUESKY SOCIAL INTELLIGENCE ({len(posts)} posts):\n"
                for i, post in enumerate(posts[:5], 1):
                    author = post.get('author', {}).get('handle', 'unknown')
                    text = post.get('text', '')[:100]
                    context += f"\n{i}. @{author}: {text}...\n"
        
        if 'reddit' in intelligence and intelligence['reddit'].get('success'):
            posts = intelligence['reddit'].get('posts', [])
            if posts:
                context += f"\n💬 REDDIT DISCUSSION INTELLIGENCE ({len(posts)} posts):\n"
                for i, post in enumerate(posts[:5], 1):
                    subreddit = post.get('subreddit', 'unknown')
                    title = post.get('title', '')
                    context += f"\n{i}. r/{subreddit}: {title}\n"
        
        # AI Analysis section
        if 'brief' in intelligence and intelligence['brief'].get('success'):
            ai_analysis = intelligence['brief'].get('results', {}).get('ai_analysis', {})
            if ai_analysis.get('success'):
                context += f"\n🤖 AI STRATEGIC ANALYSIS:\n"
                context += f"{ai_analysis.get('summary', 'No analysis available')}\n"
        
        context += "\n=== END INTELLIGENCE BRIEFING ===\n\n"
        return context
    
    async def call_ollama_with_context(self, user_input: str, intelligence_context: str = "") -> str:
        """
        Call Ollama with intelligence context
        """
        try:
            system_prompt = """You are Viktor Kozlov, an elite intelligence analyst. You have been provided with current, real-time intelligence data gathered from multiple sources including news outlets, social media, and AI analysis.

Your task is to analyze the provided real-time intelligence and respond to the user's query with professional assessment based on this current data. Always reference the specific sources and data provided in your intelligence briefing.

Key principles:
- Base your analysis on the real-time data provided
- Reference specific sources and findings
- Provide strategic assessment and implications
- Maintain professional, analytical tone
- Focus on actionable intelligence"""

            if intelligence_context:
                full_prompt = f"{intelligence_context}\nBased on the above real-time intelligence briefing, please respond to: {user_input}"
            else:
                full_prompt = user_input
            
            # Call Ollama
            cmd = ['ollama', 'run', self.model_name]
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            input_text = f"System: {system_prompt}\n\nUser: {full_prompt}"
            stdout, stderr = process.communicate(input=input_text)
            
            if process.returncode == 0:
                return stdout.strip()
            else:
                return f"Error calling Ollama: {stderr}"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def process_query(self, user_input: str) -> str:
        """
        Main processing function that handles tool detection and execution
        """
        # Step 1: Determine if tools are needed
        tools_needed = self.should_use_tools(user_input)
        
        if not tools_needed:
            # No tools needed, direct call to model
            return await self.call_ollama_with_context(user_input)
        
        # Step 2: Extract search query
        search_query = self.extract_search_query(user_input)
        
        # Step 3: Gather real-time intelligence
        print(f"🛠️ Tools activated: {', '.join(tools_needed)}")
        print(f"🎯 Target: {search_query}")
        
        intelligence = await self.gather_intelligence(search_query, tools_needed)
        
        # Step 4: Format intelligence context
        context = self.format_intelligence_context(intelligence, search_query)
        
        # Step 5: Get analysis from model with real-time data
        print("🧠 Analyzing with real-time intelligence...")
        response = await self.call_ollama_with_context(user_input, context)
        
        return f"🔍 **Intelligence Sources Used:** {', '.join(tools_needed).title()}\n\n{response}"


async def main():
    parser = argparse.ArgumentParser(description='Kozlov Direct Tools Integration')
    parser.add_argument('--query', '-q', help='Single query mode')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--model', '-m', default='kozlov-hermes', help='Ollama model name')
    
    args = parser.parse_args()
    
    system = KozlovDirectTools(args.model)
    
    if args.query:
        # Single query mode
        print(f"🧠 Viktor Kozlov Intelligence System")
        print("=" * 60)
        
        response = await system.process_query(args.query)
        print(response)
        
    elif args.interactive:
        # Interactive mode
        print("🌍 Viktor Kozlov Direct Intelligence Terminal")
        print("==============================================")
        print("Real-time intelligence tools automatically activated")
        print("Type 'exit' to quit\n")
        
        while True:
            try:
                user_input = input("Intelligence Query> ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("🔒 Intelligence session terminated.")
                    break
                
                if not user_input:
                    continue
                
                print()
                response = await system.process_query(user_input)
                print(response)
                print("\n" + "="*60 + "\n")
                
            except KeyboardInterrupt:
                print("\n🔒 Intelligence session terminated.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    else:
        # Show usage
        print("Kozlov Direct Tools Integration")
        print("Usage:")
        print(f"  {sys.argv[0]} --query 'Search eagle watchtower latest news'")
        print(f"  {sys.argv[0]} --interactive")


if __name__ == "__main__":
    asyncio.run(main())
