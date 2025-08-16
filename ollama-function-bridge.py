#!/usr/bin/env python3
"""
Ollama Function Calling Bridge for Viktor Kozlov
Enables real-time tool access for the Ollama model
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

# Import from the local module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the classes we need
import importlib.util
spec = importlib.util.spec_from_file_location("viktor_tools_api", "/Users/sebastianszewczyk/Documents/GitHub/WebScrapper/viktor-tools-api.py")
viktor_tools_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(viktor_tools_module)

ViktorOllamaInterface = viktor_tools_module.ViktorOllamaInterface
ViktorToolsAPI = viktor_tools_module.ViktorToolsAPI

class OllamaFunctionCaller:
    """
    Bridge between Ollama and Viktor Tools API with function calling support
    """
    
    def __init__(self, model_name: str = "kozlov-hermes", ollama_url: str = "http://localhost:11434"):
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.interface = ViktorOllamaInterface(model_name, ollama_url)
        self.conversation_history = []
        
    def extract_tool_calls(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract tool calls from model output using various patterns
        """
        tool_calls = []
        
        # Pattern 1: Function call format - function_name(param1="value", param2="value")
        function_pattern = r'(\w+)\((.*?)\)'
        matches = re.finditer(function_pattern, text)
        
        for match in matches:
            func_name = match.group(1)
            params_str = match.group(2)
            
            # Check if this is a valid tool
            valid_tools = ["search_news", "get_weather", "search_bluesky", "search_reddit", 
                          "comprehensive_intelligence_brief", "get_summary_history"]
            
            if func_name in valid_tools:
                # Parse parameters
                params = {}
                if params_str.strip():
                    # Simple parameter parsing for common patterns
                    param_matches = re.findall(r'(\w+)=["\'](.*?)["\']', params_str)
                    for param_name, param_value in param_matches:
                        params[param_name] = param_value
                    
                    # Handle boolean and integer parameters
                    bool_matches = re.findall(r'(\w+)=(True|False)', params_str)
                    for param_name, param_value in bool_matches:
                        params[param_name] = param_value.lower() == 'true'
                    
                    int_matches = re.findall(r'(\w+)=(\d+)', params_str)
                    for param_name, param_value in int_matches:
                        params[param_name] = int(param_value)
                
                tool_calls.append({
                    "function": func_name,
                    "parameters": params
                })
        
        # Pattern 2: Structured format - TOOL: function_name PARAMS: {json}
        structured_pattern = r'TOOL:\s*(\w+)\s*PARAMS:\s*(\{.*?\})'
        matches = re.finditer(structured_pattern, text, re.DOTALL)
        
        for match in matches:
            func_name = match.group(1)
            params_json = match.group(2)
            
            try:
                params = json.loads(params_json)
                tool_calls.append({
                    "function": func_name,
                    "parameters": params
                })
            except json.JSONError:
                continue
        
        # Pattern 3: Intent detection - if model mentions needing to search, get weather, etc.
        intent_patterns = [
            (r'need to search.*?news.*?about\s+(.*?)(?:\.|$)', 'search_news', lambda m: {'query': m.group(1).strip()}),
            (r'search.*?news.*?for\s+(.*?)(?:\.|$)', 'search_news', lambda m: {'query': m.group(1).strip()}),
            (r'get.*?weather.*?(?:information|data|forecast)', 'get_weather', lambda m: {}),
            (r'check.*?weather', 'get_weather', lambda m: {}),
            (r'search.*?bluesky.*?for\s+(.*?)(?:\.|$)', 'search_bluesky', lambda m: {'query': m.group(1).strip()}),
            (r'search.*?reddit.*?for\s+(.*?)(?:\.|$)', 'search_reddit', lambda m: {'query': m.group(1).strip()}),
            (r'generate.*?intelligence.*?brief.*?(?:on|about)\s+(.*?)(?:\.|$)', 'comprehensive_intelligence_brief', lambda m: {'topic': m.group(1).strip()}),
            (r'comprehensive.*?analysis.*?(?:on|about)\s+(.*?)(?:\.|$)', 'comprehensive_intelligence_brief', lambda m: {'topic': m.group(1).strip()}),
        ]
        
        for pattern, tool_name, param_extractor in intent_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                params = param_extractor(match)
                if params.get('query') or params.get('topic') or not params:  # Valid parameters
                    tool_calls.append({
                        "function": tool_name,
                        "parameters": params
                    })
        
        return tool_calls
    
    async def call_ollama(self, prompt: str, system_prompt: str = None) -> str:
        """
        Call Ollama API directly
        """
        try:
            # Use subprocess to call ollama for simplicity
            cmd = ['ollama', 'run', self.model_name]
            
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"System: {system_prompt}\n\nUser: {prompt}"
            
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=full_prompt)
            
            if process.returncode == 0:
                return stdout.strip()
            else:
                return f"Error calling Ollama: {stderr}"
                
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def process_with_tools(self, user_input: str) -> str:
        """
        Process user input with tool calling capability
        """
        # System prompt that encourages tool usage
        system_prompt = """You are Viktor Kozlov, an elite intelligence analyst with access to real-time tools. 

CRITICAL: When you need current information, explicitly state what tools you need to use:
- To search news: say "I need to search news for [topic]"
- To get weather: say "I need to check weather information"
- To search social media: say "I need to search Bluesky/Reddit for [topic]"
- For comprehensive analysis: say "I need to generate intelligence brief on [topic]"

ALWAYS gather current intelligence before providing analysis. State your tool usage clearly."""

        # Step 1: Get initial response from model
        initial_response = await self.call_ollama(user_input, system_prompt)
        
        # Step 2: Extract tool calls from response
        tool_calls = self.extract_tool_calls(initial_response)
        
        if not tool_calls:
            # No tools detected, return the response as-is
            return initial_response
        
        print(f"🔧 Detected {len(tool_calls)} tool calls...")
        
        # Step 3: Execute tool calls
        tool_results = []
        for tool_call in tool_calls:
            func_name = tool_call['function']
            parameters = tool_call['parameters']
            
            print(f"   Executing: {func_name}({parameters})")
            
            try:
                result = await self.interface.call_tool(func_name, parameters)
                tool_results.append({
                    "tool": func_name,
                    "parameters": parameters,
                    "result": result
                })
            except Exception as e:
                tool_results.append({
                    "tool": func_name,
                    "parameters": parameters,
                    "error": str(e)
                })
        
        # Step 4: Provide tool results back to model for analysis
        tool_summary = ""
        for result in tool_results:
            if result.get('error'):
                tool_summary += f"\n{result['tool']} failed: {result['error']}"
            else:
                tool_result = result['result']
                if tool_result.get('success'):
                    tool_summary += f"\n\n{result['tool'].upper()} RESULTS:\n"
                    
                    if result['tool'] == 'search_news':
                        articles = tool_result.get('articles', [])
                        tool_summary += f"Found {len(articles)} articles:\n"
                        for i, article in enumerate(articles[:10], 1):
                            tool_summary += f"{i}. {article.get('title', 'No title')} - {article.get('source', {}).get('name', 'Unknown')}\n"
                            if article.get('description'):
                                tool_summary += f"   {article['description'][:200]}...\n"
                    
                    elif result['tool'] == 'get_weather':
                        location = tool_result.get('location', {})
                        current = tool_result.get('current', {})
                        tool_summary += f"Location: {location.get('city', 'Unknown')}, {location.get('state', 'Unknown')}\n"
                        if current:
                            tool_summary += f"Current: {current.get('temperature_f', 'N/A')}°F, {current.get('detailed_forecast', 'No details')}\n"
                    
                    elif result['tool'] in ['search_bluesky', 'search_reddit']:
                        posts = tool_result.get('posts', [])
                        tool_summary += f"Found {len(posts)} posts:\n"
                        for i, post in enumerate(posts[:5], 1):
                            if result['tool'] == 'search_bluesky':
                                tool_summary += f"{i}. @{post.get('author', {}).get('handle', 'unknown')}: {post.get('text', '')[:100]}...\n"
                            else:  # Reddit
                                tool_summary += f"{i}. r/{post.get('subreddit', 'unknown')}: {post.get('title', '')}\n"
                    
                    elif result['tool'] == 'comprehensive_intelligence_brief':
                        ai_analysis = tool_result.get('results', {}).get('ai_analysis', {})
                        if ai_analysis.get('success'):
                            tool_summary += f"AI Analysis Complete:\n{ai_analysis.get('summary', 'No summary')}\n"
                        tool_summary += f"Total sources analyzed: {tool_result.get('total_sources', 0)}\n"
                else:
                    tool_summary += f"\n{result['tool']} failed: {tool_result.get('error', 'Unknown error')}"
        
        # Step 5: Get final analysis with tool results
        analysis_prompt = f"""Based on the following real-time intelligence gathered by your tools:

{tool_summary}

User's original question: {user_input}

Provide your professional intelligence analysis incorporating this current data. Include:
1. Key findings from the gathered intelligence
2. Strategic assessment and implications
3. Risk analysis
4. Actionable recommendations

Maintain your role as Viktor Kozlov - professional, analytical, and focused on strategic intelligence."""

        final_response = await self.call_ollama(analysis_prompt)
        
        # Combine the tool gathering acknowledgment with the analysis
        return f"🛠️ Intelligence Tools Deployed:\n{', '.join([tc['function'] for tc in tool_calls])}\n\n{final_response}"


async def main():
    parser = argparse.ArgumentParser(description='Ollama Function Calling Bridge for Viktor Kozlov')
    parser.add_argument('--model', '-m', default='kozlov-hermes', help='Ollama model name')
    parser.add_argument('--query', '-q', help='Single query mode')
    parser.add_argument('--interactive', '-i', action='store_true', help='Interactive mode')
    
    args = parser.parse_args()
    
    caller = OllamaFunctionCaller(args.model)
    
    if args.query:
        # Single query mode
        print(f"🧠 Viktor Kozlov analyzing: {args.query}")
        print("=" * 60)
        
        response = await caller.process_with_tools(args.query)
        print(response)
        
    elif args.interactive:
        # Interactive mode
        print("🌍 Viktor Kozlov Intelligence Terminal")
        print("=====================================")
        print("Enhanced with real-time tool access")
        print("Type 'exit' to quit\n")
        
        while True:
            try:
                user_input = input("Intelligence Query> ").strip()
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("🔒 Intelligence session terminated.")
                    break
                
                if not user_input:
                    continue
                
                print("\n🧠 Viktor Kozlov analyzing...")
                print("=" * 50)
                
                response = await caller.process_with_tools(user_input)
                print(response)
                print("=" * 50)
                print()
                
            except KeyboardInterrupt:
                print("\n🔒 Intelligence session terminated.")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    else:
        # Default: show usage
        print("Viktor Kozlov Function Calling Bridge")
        print("Usage:")
        print(f"  {sys.argv[0]} --query 'What is happening in Ukraine?'")
        print(f"  {sys.argv[0]} --interactive")


if __name__ == "__main__":
    asyncio.run(main())
