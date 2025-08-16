#!/usr/bin/env python3
"""
Quick demo script for Viktor Kozlov Intelligence System
"""

import asyncio
import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from viktor_intelligence_agent import ViktorIntelligenceAgent

async def demo():
    print("🌍 Viktor Kozlov Intelligence System Demo")
    print("=========================================")
    
    agent = ViktorIntelligenceAgent()
    
    # Demo queries
    demo_queries = [
        "What's happening in Ukraine today?",
        "Tell me about recent economic developments",
        "What are people saying about renewable energy on social media?"
    ]
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n📊 Demo Query {i}: {query}")
        print("="*60)
        
        try:
            response = await agent.process_query(query)
            print(response)
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("\n" + "="*60)
        
        if i < len(demo_queries):
            input("\nPress Enter for next demo...")

if __name__ == "__main__":
    asyncio.run(demo())
