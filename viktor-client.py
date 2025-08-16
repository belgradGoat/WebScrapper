#!/usr/bin/env python3
"""
Viktor Kozlov Tool-Enabled Client
Demonstrates how to interact with the tool-enabled Ollama server
"""

import json
import requests
import asyncio
import aiohttp
import argparse
import sys
from typing import Dict, List, Any

class ViktorClient:
    """Client for Viktor Kozlov tool-enabled server"""
    
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def chat_completion(self, message: str, model: str = "kozlov-hermes") -> str:
        """Send a chat completion request"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": message}
            ]
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    return f"Error {response.status}: {error_text}"
                    
        except Exception as e:
            return f"Connection error: {str(e)}"
    
    async def health_check(self) -> bool:
        """Check if the server is healthy"""
        if not self.session:
            raise RuntimeError("Client not initialized. Use async context manager.")
        
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                return response.status == 200
        except:
            return False

async def interactive_mode(base_url: str):
    """Interactive chat mode"""
    print("🌍 Viktor Kozlov Intelligence Terminal (Tool-Enabled)")
    print("====================================================")
    print("Enhanced with real-time intelligence gathering")
    print("Type 'exit' to quit, 'help' for examples\n")
    
    async with ViktorClient(base_url) as client:
        # Health check
        if not await client.health_check():
            print("❌ Cannot connect to Viktor server. Make sure it's running:")
            print("   python3 ollama-tool-server.py")
            return
        
        print("✅ Connected to Viktor intelligence server\n")
        
        while True:
            try:
                user_input = input("Intelligence Query> ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("🔒 Intelligence session terminated.")
                    break
                
                if user_input.lower() == 'help':
                    print("\n📋 Example queries:")
                    print("• 'What's the latest news on artificial intelligence?'")
                    print("• 'Give me an intelligence brief on the Middle East'")
                    print("• 'What's happening in Ukraine today?'")
                    print("• 'Check the weather in Warsaw'")
                    print("• 'Search social media for recent AI developments'")
                    print("• 'Generate a comprehensive analysis of current technology trends'\n")
                    continue
                
                if not user_input:
                    continue
                
                print("\n🧠 Viktor Kozlov analyzing...")
                print("=" * 60)
                
                response = await client.chat_completion(user_input)
                print(response)
                print("=" * 60)
                print()
                
            except KeyboardInterrupt:
                print("\n🔒 Intelligence session terminated.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

async def single_query(query: str, base_url: str):
    """Single query mode"""
    async with ViktorClient(base_url) as client:
        if not await client.health_check():
            print("❌ Cannot connect to Viktor server. Make sure it's running:")
            print("   python3 ollama-tool-server.py")
            return
        
        print(f"🧠 Viktor Kozlov analyzing: {query}")
        print("=" * 60)
        
        response = await client.chat_completion(query)
        print(response)

def sync_request(query: str, base_url: str):
    """Synchronous request using requests library"""
    payload = {
        "model": "kozlov-hermes",
        "messages": [
            {"role": "user", "content": query}
        ]
    }
    
    try:
        response = requests.post(
            f"{base_url}/v1/chat/completions",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"Error {response.status_code}: {response.text}"
            
    except Exception as e:
        return f"Connection error: {str(e)}"

async def main():
    parser = argparse.ArgumentParser(description='Viktor Kozlov Tool-Enabled Client')
    parser.add_argument('--query', '-q', help='Single query mode')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    parser.add_argument('--sync', '-s', action='store_true', help='Use synchronous requests')
    parser.add_argument('--url', '-u', default='http://localhost:8080', help='Server URL')
    
    args = parser.parse_args()
    
    if args.query:
        if args.sync:
            print(f"🧠 Viktor Kozlov analyzing: {args.query}")
            print("=" * 60)
            response = sync_request(args.query, args.url)
            print(response)
        else:
            await single_query(args.query, args.url)
    elif args.interactive:
        await interactive_mode(args.url)
    else:
        print("Viktor Kozlov Tool-Enabled Client")
        print("=================================")
        print()
        print("This client connects to the Viktor tool server to provide")
        print("enhanced intelligence capabilities with real-time data access.")
        print()
        print("Usage:")
        print(f"  {sys.argv[0]} --query 'What is happening in Ukraine?'")
        print(f"  {sys.argv[0]} --interactive")
        print(f"  {sys.argv[0]} --sync --query 'Latest AI news'")
        print()
        print("Make sure the tool server is running:")
        print("  python3 ollama-tool-server.py")

if __name__ == "__main__":
    asyncio.run(main())
