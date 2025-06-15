import sys
import json
from transformers import pipeline
import re
import warnings
warnings.filterwarnings("ignore")

class NewsSummarizer:
    def __init__(self):
        try:
            print("Loading BART summarization model...", file=sys.stderr)
            # Use a smaller, faster model for better reliability
            self.summarizer = pipeline(
                "summarization", 
                model="facebook/bart-large-cnn",
                max_length=1024,
                device=-1  # Force CPU usage to avoid GPU issues
            )
            print("Model loaded successfully!", file=sys.stderr)
        except Exception as e:
            print(f"Error loading model: {e}", file=sys.stderr)
            raise e
    
    def clean_text(self, text):
        """Clean and prepare text for summarization"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?;:-]', '', text)
        return text.strip()
    
    def chunk_text(self, text, max_length=800):
        """Split text into smaller chunks"""
        if len(text) <= max_length:
            return [text]
        
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks if chunks else [text[:max_length]]
    
    def generate_simple_brief(self, articles_data):
        """Generate a simpler, more reliable brief"""
        try:
            # Parse articles with better error handling
            articles = []
            for i, article_text in enumerate(articles_data):
                try:
                    lines = article_text.strip().split('\n')
                    article = {'title': '', 'description': '', 'source': ''}
                    
                    for line in lines:
                        if line.startswith('Title: '):
                            article['title'] = line[7:].strip()
                        elif line.startswith('Description: '):
                            article['description'] = line[13:].strip()
                        elif line.startswith('Source: '):
                            article['source'] = line[8:].strip()
                    
                    if article['title']:  # Only add if we have a title
                        articles.append(article)
                        
                except Exception as e:
                    print(f"Error parsing article {i}: {e}", file=sys.stderr)
                    continue
            
            if not articles:
                return "No valid articles found for summarization."
            
            print(f"Processing {len(articles)} articles...", file=sys.stderr)
            
            # Limit to 50 most recent/important articles
            articles = articles[:50]
            
            # Group articles by importance/relevance
            important_keywords = ['ukraine', 'russia', 'china', 'conflict', 'war', 'foreign minister', 'department of state', 'president', 'crisis', 'emergency']
            
            important_articles = []
            regular_articles = []
            
            for article in articles:
                text_to_check = (article['title'] + ' ' + article['description']).lower()
                if any(keyword in text_to_check for keyword in important_keywords):
                    important_articles.append(article)
                else:
                    regular_articles.append(article)
            
            # Prioritize important articles
            selected_articles = important_articles[:25] + regular_articles[:25]
            
            print(f"Selected {len(selected_articles)} articles (Important: {len(important_articles[:25])}, Regular: {len(regular_articles[:25])})", file=sys.stderr)
            
            # Create sections
            sections = []
            
            # Process in smaller batches
            batch_size = 10
            for i in range(0, len(selected_articles), batch_size):
                batch = selected_articles[i:i+batch_size]
                
                # Combine batch text
                combined_text = ""
                sources = set()
                
                for article in batch:
                    title = article.get('title', '').strip()
                    desc = article.get('description', '').strip()
                    source = article.get('source', '').strip()
                    
                    if title:
                        combined_text += f"{title}. "
                    if desc and desc != 'No description.':
                        combined_text += f"{desc}. "
                    if source:
                        sources.add(source)
                
                combined_text = self.clean_text(combined_text)
                
                if len(combined_text) > 50:
                    try:
                        # Summarize this batch
                        chunks = self.chunk_text(combined_text, max_length=700)
                        batch_summaries = []
                        
                        for chunk in chunks:
                            if len(chunk) > 50:
                                summary = self.summarizer(
                                    chunk, 
                                    max_length=100, 
                                    min_length=30, 
                                    do_sample=False,
                                    truncation=True
                                )[0]['summary_text']
                                batch_summaries.append(summary)
                        
                        if batch_summaries:
                            section_text = " ".join(batch_summaries)
                            source_list = ", ".join(list(sources)[:3])
                            sections.append(f"**Batch {i//batch_size + 1}** ({source_list}): {section_text}")
                            
                    except Exception as e:
                        print(f"Error summarizing batch {i//batch_size + 1}: {e}", file=sys.stderr)
                        # Add fallback content
                        sections.append(f"**Batch {i//batch_size + 1}**: Multiple developments reported from various sources.")
            
            # Generate executive summary from sections
            exec_summary = "Current global developments include multiple significant events across various regions and sectors."
            
            if sections:
                try:
                    combined_sections = " ".join(sections)
                    if len(combined_sections) > 100:
                        exec_chunks = self.chunk_text(combined_sections, max_length=600)
                        exec_parts = []
                        
                        for chunk in exec_chunks[:2]:  # Limit to 2 chunks
                            if len(chunk) > 50:
                                summary = self.summarizer(
                                    chunk, 
                                    max_length=80, 
                                    min_length=20, 
                                    do_sample=False,
                                    truncation=True
                                )[0]['summary_text']
                                exec_parts.append(summary)
                        
                        if exec_parts:
                            exec_summary = " ".join(exec_parts)
                            
                except Exception as e:
                    print(f"Error generating executive summary: {e}", file=sys.stderr)
            
            # Compile final brief
            brief = f"""# Global Situation Update
Generated from {len(selected_articles)} news sources

## Executive Summary

{exec_summary}

## Detailed Analysis

{chr(10).join(sections) if sections else "Multiple developments are being reported across various sectors and regions."}

## Key Points to Watch
- Monitor developments in the major themes identified above
- Cross-reference information across multiple sources
- Pay attention to emerging patterns and connections between different topics

---
*This brief was generated using AI-powered analysis of multiple news sources.*
"""
            
            return brief
            
        except Exception as e:
            print(f"Error in generate_simple_brief: {str(e)}", file=sys.stderr)
            return f"Error generating comprehensive brief: {str(e)}. Please try again."

def main():
    try:
        if len(sys.argv) != 2:
            result = {'error': 'Usage: python summarizer.py <json_data>'}
            print(json.dumps(result))
            sys.exit(1)
        
        # Parse input
        input_data = json.loads(sys.argv[1])
        articles = input_data.get('articles', [])
        
        if not articles:
            result = {'error': 'No articles provided'}
            print(json.dumps(result))
            sys.exit(1)
        
        print(f"Received {len(articles)} articles", file=sys.stderr)
        
        # Initialize summarizer and generate brief
        summarizer = NewsSummarizer()
        brief = summarizer.generate_simple_brief(articles)
        
        # Output result as JSON
        result = {'summary': brief}
        print(json.dumps(result))
        
    except json.JSONDecodeError as e:
        result = {'error': f'Invalid JSON input: {str(e)}'}
        print(json.dumps(result))
        sys.exit(1)
        
    except Exception as e:
        result = {'error': f'Unexpected error: {str(e)}'}
        print(json.dumps(result))
        sys.exit(1)

if __name__ == "__main__":
    main()