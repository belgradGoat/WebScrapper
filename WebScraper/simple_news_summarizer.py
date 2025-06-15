import sys
import json
import os
import re
from collections import Counter, defaultdict

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    # Remove extra whitespace and normalize
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,!?;:-]', '', text)
    return text.strip()

def extract_keywords(text, num_keywords=15):
    """Extract key terms from text using frequency analysis"""
    # Convert to lowercase and split into words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    
    # Common stop words to filter out
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'from', 
        'up', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'as', 'is', 
        'was', 'are', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 
        'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 
        'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'said', 'says',
        'also', 'more', 'some', 'all', 'any', 'each', 'most', 'other', 'such', 'only', 'own', 'same',
        'so', 'than', 'too', 'very', 'just', 'now', 'then', 'here', 'there', 'when', 'where', 'why',
        'how', 'what', 'which', 'who', 'whom', 'whose', 'if', 'because', 'while', 'since', 'until',
        'although', 'though', 'unless', 'whether', 'both', 'either', 'neither', 'not', 'no', 'nor',
        'yes', 'well', 'get', 'got', 'make', 'made', 'take', 'took', 'come', 'came', 'go', 'went'
    }
    
    # Filter meaningful words
    meaningful_words = [word for word in words if len(word) > 3 and word not in stop_words]
    
    # Count frequency
    word_freq = Counter(meaningful_words)
    return word_freq.most_common(num_keywords)

def categorize_articles(articles):
    """Categorize articles by topic using keyword analysis"""
    categories = defaultdict(list)
    
    # Define category keywords
    category_keywords = {
        'ukraine_russia': ['ukraine', 'russia', 'putin', 'zelensky', 'kiev', 'kyiv', 'moscow', 'crimea', 'donbas'],
        'china_taiwan': ['china', 'taiwan', 'beijing', 'taipei', 'xi', 'jinping', 'strait'],
        'diplomacy': ['minister', 'foreign', 'diplomacy', 'embassy', 'ambassador', 'diplomatic', 'secretary', 'state'],
        'middle_east': ['israel', 'palestine', 'gaza', 'iran', 'syria', 'lebanon', 'saudi', 'arabia'],
        'military_security': ['military', 'defense', 'war', 'conflict', 'security', 'weapons', 'army', 'navy'],
        'economic': ['economic', 'economy', 'trade', 'market', 'financial', 'business', 'commerce'],
        'europe': ['europe', 'european', 'nato', 'brussels', 'germany', 'france', 'britain', 'uk'],
        'asia_pacific': ['japan', 'korea', 'india', 'australia', 'pacific', 'asean'],
        'africa': ['africa', 'african', 'nigeria', 'south africa', 'kenya', 'ethiopia'],
        'americas': ['america', 'canada', 'mexico', 'brazil', 'argentina', 'latin']
    }
    
    for article in articles:
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        combined_text = f"{title} {description}"
        
        # Find the best category match
        best_category = 'general'
        max_matches = 0
        
        for category, keywords in category_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in combined_text)
            if matches > max_matches:
                max_matches = matches
                best_category = category
        
        categories[best_category].append(article)
    
    return categories

def rank_articles_by_relevance(articles):
    """Rank articles by relevance using keyword importance"""
    # Keywords that indicate high importance
    important_keywords = [
        'president', 'minister', 'crisis', 'war', 'conflict', 'emergency', 'breaking',
        'urgent', 'major', 'significant', 'critical', 'summit', 'agreement', 'treaty',
        'sanctions', 'nuclear', 'missile', 'attack', 'invasion', 'peace', 'talks'
    ]
    
    scored_articles = []
    
    for article in articles:
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        combined_text = f"{title} {description}"
        
        # Calculate relevance score
        score = 0
        
        # High importance keywords get more points
        for keyword in important_keywords:
            if keyword in combined_text:
                score += 3
        
        # Recent keywords get bonus points
        recent_indicators = ['today', 'breaking', 'just', 'now', 'latest', 'update']
        for indicator in recent_indicators:
            if indicator in combined_text:
                score += 2
        
        # Length bonus (longer descriptions often mean more substantial articles)
        if len(description) > 100:
            score += 1
        
        scored_articles.append((score, article))
    
    # Sort by score (highest first) and return top 50
    scored_articles.sort(key=lambda x: x[0], reverse=True)
    return [article for score, article in scored_articles[:50]]

def generate_category_summary(category_name, articles):
    """Generate a summary for a specific category"""
    if not articles:
        return ""
    
    # Extract key information from articles in this category
    titles = [article.get('title', '') for article in articles]
    sources = list(set([article.get('source', '') for article in articles if article.get('source')]))
    
    # Clean category name for display
    display_name = category_name.replace('_', '/').title()
    if display_name == 'General':
        display_name = 'Other International News'
    
    summary = f"### {display_name}\n\n"
    summary += f"**Coverage**: {len(articles)} articles from {len(sources)} sources\n\n"
    
    # Add key headlines (top 3-5)
    key_headlines = titles[:min(5, len(titles))]
    summary += "**Key developments:**\n"
    for i, headline in enumerate(key_headlines, 1):
        if headline:
            # Clean and truncate headline
            clean_headline = clean_text(headline)
            if len(clean_headline) > 100:
                clean_headline = clean_headline[:97] + "..."
            summary += f"{i}. {clean_headline}\n"
    
    summary += "\n"
    
    # Add source information if available
    if sources:
        source_list = ", ".join(sources[:5])
        if len(sources) > 5:
            source_list += f" and {len(sources) - 5} others"
        summary += f"**Sources**: {source_list}\n\n"
    
    return summary

def create_comprehensive_summary(articles_data):
    """Create a comprehensive summary from article data"""
    try:
        # Parse articles
        articles = []
        all_text = ""
        
        for i, article_text in enumerate(articles_data):
            try:
                if not isinstance(article_text, str):
                    continue
                    
                lines = article_text.strip().split('\n')
                article = {'title': '', 'description': '', 'source': '', 'published': ''}
                
                for line in lines:
                    if line.startswith('Title: '):
                        article['title'] = clean_text(line[7:])
                    elif line.startswith('Description: '):
                        article['description'] = clean_text(line[13:])
                    elif line.startswith('Source: '):
                        article['source'] = clean_text(line[8:])
                    elif line.startswith('Published: '):
                        article['published'] = clean_text(line[11:])
                
                if article['title']:
                    articles.append(article)
                    all_text += f"{article['title']} {article['description']} "
                    
            except Exception as e:
                print(f"Error parsing article {i}: {e}", file=sys.stderr)
                continue
        
        if not articles:
            return "No valid articles found for analysis."
        
        print(f"Parsed {len(articles)} articles", file=sys.stderr)
        
        # Rank articles by relevance and take top 50
        top_articles = rank_articles_by_relevance(articles)
        print(f"Selected top {len(top_articles)} most relevant articles", file=sys.stderr)
        
        # Categorize the top articles
        categories = categorize_articles(top_articles)
        print(f"Categorized articles into {len(categories)} categories", file=sys.stderr)
        
        # Extract overall keywords
        keywords = extract_keywords(all_text, 20)
        
        # Get unique sources
        sources = list(set([article.get('source', '') for article in top_articles if article.get('source')]))
        
        # Build the comprehensive summary
        summary = f"""# Global Situation Update
*Generated from {len(top_articles)} most relevant news articles*

## Executive Summary

Based on analysis of {len(articles)} news articles, with {len(top_articles)} most relevant articles selected for detailed analysis, current global developments span multiple critical areas. The analysis covers reporting from {len(sources)} different sources, with key focus areas including international diplomacy, regional conflicts, and emerging global trends.

**Most frequently mentioned topics**: {', '.join([keyword[0].title() for keyword in keywords[:8]])}

## Detailed Analysis by Region/Topic

"""
        
        # Add category summaries
        # Sort categories by number of articles (most covered first)
        sorted_categories = sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)
        
        for category_name, category_articles in sorted_categories:
            if category_articles:  # Only include categories with articles
                category_summary = generate_category_summary(category_name, category_articles)
                summary += category_summary
        
        # Add key terms section
        summary += "## Most Significant Terms\n\n"
        for i, (term, count) in enumerate(keywords[:12], 1):
            summary += f"{i}. **{term.title()}** (mentioned {count} times)\n"
        
        # Add methodology and sources
        summary += f"""

## Analysis Overview

**Total Articles Processed**: {len(articles)}
**Most Relevant Articles Selected**: {len(top_articles)}
**Categories Identified**: {len([cat for cat, arts in categories.items() if arts])}
**Sources Analyzed**: {len(sources)}

**Top Sources**: {', '.join(sources[:10])}{'...' if len(sources) > 10 else ''}

## Key Insights

- Coverage spans {len([cat for cat, arts in categories.items() if arts])} major topic areas
- Analysis prioritized articles containing high-impact keywords and recent developments
- Geographic focus includes major regions with ongoing developments
- Diplomatic and security issues represent significant portions of current coverage

---
*This summary was generated using keyword analysis and content categorization of news articles. Information should be verified with primary sources.*
"""
        
        return summary
        
    except Exception as e:
        print(f"Error creating summary: {str(e)}", file=sys.stderr)
        return f"Error generating comprehensive summary: {str(e)}"

def main():
    try:
        if len(sys.argv) != 2:
            result = {'error': 'Usage: python simple_news_summarizer.py <json_file_path>'}
            print(json.dumps(result))
            sys.exit(1)
        
        # Read from file
        file_path = sys.argv[1]
        
        if not os.path.exists(file_path):
            result = {'error': f'Input file not found: {file_path}'}
            print(json.dumps(result))
            sys.exit(1)
        
        # Parse input from file
        with open(file_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        articles = input_data.get('articles', [])
        
        if not articles:
            result = {'error': 'No articles provided'}
            print(json.dumps(result))
            sys.exit(1)
        
        print(f"Processing {len(articles)} articles from file: {file_path}", file=sys.stderr)
        
        # Generate comprehensive summary
        summary = create_comprehensive_summary(articles)
        
        # Output result as JSON
        result = {'summary': summary}
        print(json.dumps(result))
        
    except json.JSONDecodeError as e:
        result = {'error': f'Invalid JSON in input file: {str(e)}'}
        print(json.dumps(result))
        sys.exit(1)
        
    except Exception as e:
        result = {'error': f'Unexpected error: {str(e)}'}
        print(json.dumps(result))
        sys.exit(1)

if __name__ == "__main__":
    main()